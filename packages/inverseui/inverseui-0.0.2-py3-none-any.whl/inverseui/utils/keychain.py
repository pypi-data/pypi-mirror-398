"""macOS Keychain integration for secure token storage."""

import json
from dataclasses import dataclass
from datetime import datetime

import keyring

SERVICE_NAME = "inverseui"


@dataclass
class TokenData:
    """Stored token data."""

    access_token: str
    refresh_token: str | None
    expires_at: datetime | None
    user_email: str | None


def store_tokens(
    access_token: str,
    refresh_token: str | None = None,
    expires_at: datetime | None = None,
    user_email: str | None = None,
) -> None:
    """Store tokens in Keychain."""
    data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_at": expires_at.isoformat() if expires_at else None,
        "user_email": user_email,
    }
    keyring.set_password(SERVICE_NAME, "tokens", json.dumps(data))


def get_tokens() -> TokenData | None:
    """Retrieve tokens from Keychain."""
    try:
        data_str = keyring.get_password(SERVICE_NAME, "tokens")
        if not data_str:
            return None
        data = json.loads(data_str)
        return TokenData(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            user_email=data.get("user_email"),
        )
    except (json.JSONDecodeError, KeyError):
        return None


def clear_tokens() -> None:
    """Remove tokens from Keychain."""
    try:
        keyring.delete_password(SERVICE_NAME, "tokens")
    except keyring.errors.PasswordDeleteError:
        pass  # Already deleted


def get_access_token() -> str | None:
    """Get just the access token."""
    tokens = get_tokens()
    return tokens.access_token if tokens else None


def is_token_expired() -> bool:
    """Check if the access token is expired."""
    tokens = get_tokens()
    if not tokens or not tokens.expires_at:
        return True
    return datetime.now() >= tokens.expires_at
