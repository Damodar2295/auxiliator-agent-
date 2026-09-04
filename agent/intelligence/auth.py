"""POC-only identity and authorization adapter."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass

from agent.intelligence.contracts import Identity, UserRole
from agent.intelligence.errors import AuthorizationDeniedError

POC_AUTH_NOTICE = "SYNTHETIC POC AUTHENTICATION — not production IAM"
_ITERATIONS = 210_000
_DEMO_USERS = {
    "viewer": ("Viewer Demo", UserRole.VIEWER, "084c6bc97b65a654a18b5dce22ef033b417aef3a34ec160c6578eb2747080023"),
    "author": ("Author Demo", UserRole.AUTHOR, "4b7360e5093188d4bfd9060ee40c3cfa99f07964d1c2995dec6e5ad9469ef764"),
    "reviewer": (
        "Reviewer Demo",
        UserRole.REVIEWER,
        "4c37ad475ddc750e79d37459b0d0e5f19910081384cc8862f59e70ca111b8984",
    ),
    "admin": ("Admin Demo", UserRole.ADMIN, "c6c1d5c0ef11aca721b52d40367f3b71446fdf793bd2e8ca9fcc7fbbcb91f5bb"),
}
_PERMISSIONS = {
    UserRole.VIEWER: {"catalog:read", "intelligence:execute"},
    UserRole.AUTHOR: {
        "catalog:read",
        "intelligence:execute",
        "skill:draft",
        "skill:validate",
        "skill:submit_review",
        "evaluation:run",
        "evaluation:read",
    },
    UserRole.REVIEWER: {"catalog:read", "intelligence:execute", "review:decide", "evaluation:read"},
    UserRole.ADMIN: {"*"},
}


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


@dataclass(frozen=True)
class MockAuthorizationService:
    secret: bytes
    token_ttl_seconds: int = 3600

    @classmethod
    def from_environment(cls) -> MockAuthorizationService:
        secret = os.getenv("DEMO_AUTH_SECRET", "synthetic-poc-secret-change-me")
        ttl = int(os.getenv("DEMO_AUTH_TOKEN_TTL_SECONDS", "3600"))
        return cls(secret=secret.encode(), token_ttl_seconds=ttl)

    def login(self, username: str, password: str) -> tuple[str, Identity]:
        record = _DEMO_USERS.get(username.lower())
        if record is None:
            raise AuthorizationDeniedError("Invalid synthetic credentials")
        display_name, role, expected_hash = record
        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            f"intelligence-poc-{username.lower()}".encode(),
            _ITERATIONS,
        ).hex()
        if not hmac.compare_digest(actual, expected_hash):
            raise AuthorizationDeniedError("Invalid synthetic credentials")
        identity = Identity(user_id=f"demo-{username.lower()}", display_name=display_name, role=role)
        return self.issue_token(identity), identity

    def issue_token(self, identity: Identity) -> str:
        payload = {
            "sub": identity.user_id,
            "name": identity.display_name,
            "role": identity.role.value,
            "exp": int(time.time()) + self.token_ttl_seconds,
            "synthetic": True,
        }
        body = _encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode())
        signature = _encode(hmac.new(self.secret, body.encode(), hashlib.sha256).digest())
        return f"{body}.{signature}"

    def authenticate(self, token: str) -> Identity:
        try:
            body, signature = token.split(".", 1)
            expected = _encode(hmac.new(self.secret, body.encode(), hashlib.sha256).digest())
            if not hmac.compare_digest(signature, expected):
                raise ValueError("signature")
            payload = json.loads(_decode(body))
            if int(payload["exp"]) < int(time.time()) or payload.get("synthetic") is not True:
                raise ValueError("expired")
            return Identity(
                user_id=payload["sub"],
                display_name=payload["name"],
                role=UserRole(payload["role"]),
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise AuthorizationDeniedError("Invalid or expired demo token") from exc

    def authorize(self, identity: Identity, permission: str) -> None:
        allowed = _PERMISSIONS[identity.role]
        if "*" not in allowed and permission not in allowed:
            raise AuthorizationDeniedError(f"Role {identity.role.value} lacks permission {permission}")
