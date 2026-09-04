import pytest

from agent.intelligence.auth import MockAuthorizationService
from agent.intelligence.errors import AuthorizationDeniedError


def test_demo_login_uses_signed_token_and_preserves_role():
    service = MockAuthorizationService(secret=b"test-secret", token_ttl_seconds=60)
    token, identity = service.login("reviewer", "Demo123!")
    assert identity.role.value == "reviewer"
    assert service.authenticate(token) == identity


def test_invalid_password_and_role_escalation_are_denied():
    service = MockAuthorizationService(secret=b"test-secret")
    with pytest.raises(AuthorizationDeniedError):
        service.login("viewer", "wrong")
    _, viewer = service.login("viewer", "Demo123!")
    with pytest.raises(AuthorizationDeniedError, match="lacks permission"):
        service.authorize(viewer, "skill:draft")


def test_tampered_token_is_denied():
    service = MockAuthorizationService(secret=b"test-secret")
    token, _ = service.login("admin", "Demo123!")
    with pytest.raises(AuthorizationDeniedError):
        service.authenticate(token + "tampered")
