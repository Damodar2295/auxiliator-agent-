"""Environment bootstrapping with process > mounted secrets > .env precedence."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import dotenv_values

SECRETS_MOUNT_PATH = "/opt/gke/vault/secrets/secrets"


def load_environment() -> None:
    """Populate unset environment values without overwriting earlier sources."""
    secrets_path = Path(os.getenv("SECRETS_MOUNT_PATH", SECRETS_MOUNT_PATH))
    if secrets_path.exists():
        try:
            from jproperties import Properties

            props = Properties()
            with secrets_path.open("rb") as stream:
                props.load(stream)
            for key, value in props.items():
                os.environ.setdefault(str(key), str(value.data))
        except ImportError:
            for key, value in dotenv_values(secrets_path).items():
                if value is not None:
                    os.environ.setdefault(key, value)

    for key, value in dotenv_values(".env").items():
        if value is not None:
            os.environ.setdefault(key, value)
