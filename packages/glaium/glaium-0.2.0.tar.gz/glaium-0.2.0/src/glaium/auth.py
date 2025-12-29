"""Authentication utilities for Glaium SDK."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime

from glaium.exceptions import AuthenticationError, TokenExpiredError

# Environment variable name for API key
GLAIUM_API_KEY_ENV = "GLAIUM_API_KEY"

# Default base URL
DEFAULT_BASE_URL = "https://api.glaium.com"
BASE_URL_ENV = "GLAIUM_BASE_URL"


@dataclass
class TokenInfo:
    """Information extracted from a JWT token."""

    agent_id: str
    organization_id: int
    expires_at: datetime | None = None

    @property
    def is_expired(self) -> bool:
        """Check if the token is expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at


def get_api_key(api_key: str | None = None) -> str:
    """
    Get the API key from parameter or environment variable.

    Args:
        api_key: Explicit API key (takes precedence).

    Returns:
        The API key to use.

    Raises:
        AuthenticationError: If no API key is available.
    """
    if api_key:
        return api_key

    env_key = os.environ.get(GLAIUM_API_KEY_ENV)
    if env_key:
        return env_key

    raise AuthenticationError(
        f"No API key provided. Either pass api_key parameter or set {GLAIUM_API_KEY_ENV} environment variable."
    )


def get_base_url(base_url: str | None = None) -> str:
    """
    Get the base URL from parameter or environment variable.

    Args:
        base_url: Explicit base URL (takes precedence).

    Returns:
        The base URL to use.
    """
    if base_url:
        return base_url.rstrip("/")

    env_url = os.environ.get(BASE_URL_ENV)
    if env_url:
        return env_url.rstrip("/")

    return DEFAULT_BASE_URL


def decode_token(token: str) -> TokenInfo:
    """
    Decode a JWT token to extract information.

    Note: This does NOT verify the token signature.
    It's only for client-side inspection of token contents.

    Args:
        token: The JWT token string.

    Returns:
        TokenInfo with extracted data.

    Raises:
        AuthenticationError: If token is malformed.
        TokenExpiredError: If token has expired.
    """
    try:
        import jwt

        # Decode without verification (server will verify)
        payload = jwt.decode(token, options={"verify_signature": False})

        expires_at = None
        if "exp" in payload:
            expires_at = datetime.utcfromtimestamp(payload["exp"])

        info = TokenInfo(
            agent_id=payload.get("agent_id", ""),
            organization_id=payload.get("organization_id", 0),
            expires_at=expires_at,
        )

        if info.is_expired:
            raise TokenExpiredError(
                "Token has expired. Please re-register the agent.",
                details={"expired_at": expires_at.isoformat() if expires_at else None},
            )

        return info

    except jwt.InvalidTokenError as e:
        raise AuthenticationError(f"Invalid token format: {e}")
    except ImportError:
        # PyJWT not installed, return minimal info
        return TokenInfo(agent_id="unknown", organization_id=0)


def validate_api_key_format(api_key: str) -> bool:
    """
    Validate API key format.

    Expected formats:
    - glaium_org{org_id}_ak_{random}
    - test-{anything} (for testing)

    Args:
        api_key: The API key to validate.

    Returns:
        True if format is valid.
    """
    if api_key.startswith("test-"):
        return True

    if api_key.startswith("glaium_org") and "_ak_" in api_key:
        return True

    return False
