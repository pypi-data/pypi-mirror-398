"""
Smart Auth Kit

Authentication utilities for Smart Platform.
"""

from smart_auth.core.password import hash_password, verify_password
from smart_auth.core.tokens import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_type,
)
from smart_auth.services.auth_service import AuthService, AuthServiceConfig
from smart_auth.dependencies.current_user import get_current_user, require_roles

__version__ = "0.0.1"

__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "verify_token_type",
    "AuthService",
    "AuthServiceConfig",
    "get_current_user",
    "require_roles",
]
