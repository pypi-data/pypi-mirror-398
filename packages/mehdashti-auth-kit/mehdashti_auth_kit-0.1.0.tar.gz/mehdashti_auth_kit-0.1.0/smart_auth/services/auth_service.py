"""
Authentication Service

Extensible authentication service with customizable user operations.
"""

from typing import Any, Optional, Protocol
from uuid import UUID

from loguru import logger
from pydantic import BaseModel

from smart_auth.core.password import verify_password
from smart_auth.core.tokens import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_type,
)


class AuthServiceConfig(BaseModel):
    """
    Configuration for AuthService.

    Attributes:
        secret_key: Secret key for JWT signing
        access_token_expire_minutes: Access token expiration (default: 30)
        refresh_token_expire_days: Refresh token expiration (default: 7)
    """

    secret_key: str
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7


class UserProvider(Protocol):
    """
    Protocol for user data provider.

    Projects must implement this to connect AuthService to their user storage.
    """

    async def get_user_by_email(self, email: str) -> Optional[dict[str, Any]]:
        """
        Get user by email.

        Returns:
            User dict with at least: uid, email, hashed_password, is_active, roles
        """
        ...

    async def get_user_by_uid(self, uid: UUID) -> Optional[dict[str, Any]]:
        """
        Get user by UID.

        Returns:
            User dict with at least: uid, email, is_active, roles
        """
        ...

    async def create_user(self, user_data: dict[str, Any]) -> dict[str, Any]:
        """
        Create new user.

        Args:
            user_data: User data including hashed_password

        Returns:
            Created user dict
        """
        ...


class AuthService:
    """
    Authentication service with extension points.

    This service handles JWT token operations and delegates user
    management to a UserProvider implementation.

    Extension Points:
    - UserProvider: Customize user storage and retrieval
    - get_user_roles: Override to customize role extraction
    - validate_login: Override to add custom login validation
    """

    def __init__(self, config: AuthServiceConfig, user_provider: UserProvider):
        """
        Initialize auth service.

        Args:
            config: Auth configuration
            user_provider: User data provider
        """
        self.config = config
        self.user_provider = user_provider

    async def login(self, email: str, password: str) -> dict:
        """
        Login user and generate tokens.

        Args:
            email: User email
            password: User password

        Returns:
            Dict with access_token, refresh_token, and user info

        Raises:
            ValueError: If authentication fails
        """
        # Get user from provider
        user = await self.user_provider.get_user_by_email(email)
        if not user:
            raise ValueError("Invalid email or password")

        # Verify password
        if not verify_password(password, user["hashed_password"]):
            raise ValueError("Invalid email or password")

        # Check if user is active
        if not user.get("is_active", True):
            raise ValueError("User account is inactive")

        # Custom validation hook
        await self.validate_login(user)

        # Get user roles
        roles = self.get_user_roles(user)

        # Generate tokens
        access_token = create_access_token(
            subject=str(user["uid"]),
            secret_key=self.config.secret_key,
            roles=roles,
            email=user["email"],
        )

        refresh_token = create_refresh_token(
            subject=str(user["uid"]),
            secret_key=self.config.secret_key,
        )

        logger.info(f"User logged in: {email}")

        # Remove sensitive data before returning
        user_safe = {k: v for k, v in user.items() if k != "hashed_password"}

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user_safe,
        }

    async def refresh_access_token(self, refresh_token: str) -> dict:
        """
        Generate new access token from refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            Dict with new access_token

        Raises:
            ValueError: If refresh token is invalid
        """
        # Decode refresh token
        payload = decode_token(refresh_token, self.config.secret_key)
        if not payload:
            raise ValueError("Invalid refresh token")

        # Verify token type
        if not verify_token_type(payload, "refresh"):
            raise ValueError("Invalid token type")

        # Get user UID from token
        user_uid_str = payload.get("sub")
        if not user_uid_str:
            raise ValueError("Invalid token payload")

        try:
            user_uid = UUID(user_uid_str)
        except ValueError:
            raise ValueError("Invalid user identifier")

        # Verify user still exists and is active
        user = await self.user_provider.get_user_by_uid(user_uid)
        if not user:
            raise ValueError("User not found")
        if not user.get("is_active", True):
            raise ValueError("User account is inactive")

        # Get user roles
        roles = self.get_user_roles(user)

        # Generate new access token
        access_token = create_access_token(
            subject=user_uid_str,
            secret_key=self.config.secret_key,
            roles=roles,
            email=user["email"],
        )

        logger.info(f"Access token refreshed for user: {user['email']}")

        return {
            "access_token": access_token,
            "token_type": "bearer",
        }

    async def validate_access_token(self, token: str) -> dict:
        """
        Validate access token and return payload.

        Args:
            token: Access token to validate

        Returns:
            Token payload if valid

        Raises:
            ValueError: If token is invalid
        """
        # Decode token
        payload = decode_token(token, self.config.secret_key)
        if not payload:
            raise ValueError("Invalid or expired token")

        # Verify token type
        if not verify_token_type(payload, "access"):
            raise ValueError("Invalid token type")

        # Verify user still exists and is active
        user_uid_str = payload.get("sub")
        if not user_uid_str:
            raise ValueError("Invalid token payload")

        try:
            user_uid = UUID(user_uid_str)
        except ValueError:
            raise ValueError("Invalid user identifier")

        user = await self.user_provider.get_user_by_uid(user_uid)
        if not user:
            raise ValueError("User not found")
        if not user.get("is_active", True):
            raise ValueError("User account is inactive")

        return payload

    # Extension Points

    def get_user_roles(self, user: dict[str, Any]) -> list[str]:
        """
        Extract roles from user data.

        Override this to customize role extraction.

        Args:
            user: User dict

        Returns:
            List of role strings
        """
        # Default: single role field
        if "role" in user:
            return [user["role"]]
        # Or multiple roles
        if "roles" in user:
            return user["roles"]
        return []

    async def validate_login(self, user: dict[str, Any]) -> None:
        """
        Custom login validation hook.

        Override this to add custom validation logic (e.g., MFA, IP check).

        Args:
            user: User dict

        Raises:
            ValueError: If validation fails
        """
        pass  # Default: no additional validation
