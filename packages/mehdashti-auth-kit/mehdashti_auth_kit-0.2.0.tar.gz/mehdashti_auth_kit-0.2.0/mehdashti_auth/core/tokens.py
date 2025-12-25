"""
JWT Token Management

JWT token creation, decoding, and validation utilities.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt
from loguru import logger

ALGORITHM = "HS256"
DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
DEFAULT_REFRESH_TOKEN_EXPIRE_DAYS = 7


def create_access_token(
    subject: str,
    secret_key: str,
    roles: list[str] | None = None,
    tenant_id: str | None = None,
    expires_delta: Optional[timedelta] = None,
    **extra_claims: Any,
) -> str:
    """
    Create a JWT access token with roles and tenant.

    Args:
        subject: User identifier (uid)
        secret_key: Secret key for signing
        roles: User roles (e.g., ["admin", "user"])
        tenant_id: Tenant identifier (for multi-tenancy)
        expires_delta: Token expiration time (default: 30 minutes)
        **extra_claims: Additional claims to include

    Returns:
        Encoded JWT token

    Example:
        >>> token = create_access_token(
        ...     subject="user-uuid",
        ...     secret_key="secret",
        ...     roles=["admin", "api_user"],
        ...     tenant_id="tenant-123"
        ... )
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES
        )

    # Build token payload
    to_encode = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }

    # Add roles and tenant if provided
    if roles:
        to_encode["roles"] = roles
    if tenant_id:
        to_encode["tenant_id"] = tenant_id

    # Add extra claims
    to_encode.update(extra_claims)

    # Encode JWT
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(
    subject: str,
    secret_key: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT refresh token.

    Refresh tokens have longer expiry and minimal claims.

    Args:
        subject: User identifier (uid)
        secret_key: Secret key for signing
        expires_delta: Token expiration time (default: 7 days)

    Returns:
        Encoded JWT refresh token
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=DEFAULT_REFRESH_TOKEN_EXPIRE_DAYS
        )

    to_encode = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
    }

    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str, secret_key: str) -> Optional[dict[str, Any]]:
    """
    Decode and verify a JWT token.

    Args:
        token: JWT token to decode
        secret_key: Secret key for verification

    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        return None


def verify_token_type(payload: dict[str, Any], expected_type: str) -> bool:
    """
    Verify the token type (access or refresh).

    Args:
        payload: Decoded token payload
        expected_type: Expected token type

    Returns:
        True if token type matches, False otherwise
    """
    return payload.get("type") == expected_type
