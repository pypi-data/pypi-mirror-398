"""
Current User Dependencies

FastAPI dependencies for extracting current user from JWT token.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from mehdashti_auth.services.auth_service import AuthService

# HTTP Bearer security scheme
security = HTTPBearer()


def create_get_current_user_dependency(auth_service: AuthService):
    """
    Factory function to create get_current_user dependency.

    Usage:
        auth_service = AuthService(config, user_provider)
        get_current_user = create_get_current_user_dependency(auth_service)

        @app.get("/users/me")
        async def read_users_me(current_user: Annotated[dict, Depends(get_current_user)]):
            return current_user

    Args:
        auth_service: Configured AuthService instance

    Returns:
        FastAPI dependency function
    """

    async def get_current_user(
        credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
    ) -> dict:
        """
        Extract current user from JWT token.

        Args:
            credentials: HTTP Bearer credentials

        Returns:
            Token payload with user info

        Raises:
            HTTPException: If authentication fails
        """
        token = credentials.credentials

        try:
            payload = await auth_service.validate_access_token(token)
            return payload
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
                headers={"WWW-Authenticate": "Bearer"},
            )

    return get_current_user


def create_require_roles_dependency(auth_service: AuthService, required_roles: list[str]):
    """
    Factory function to create role-based access control dependency.

    Usage:
        require_admin = create_require_roles_dependency(auth_service, ["admin"])

        @app.delete("/users/{user_id}")
        async def delete_user(
            user_id: str,
            current_user: Annotated[dict, Depends(require_admin)]
        ):
            # Only admins can access this endpoint
            pass

    Args:
        auth_service: Configured AuthService instance
        required_roles: List of roles required to access

    Returns:
        FastAPI dependency function
    """
    get_current_user = create_get_current_user_dependency(auth_service)

    async def require_roles(
        current_user: Annotated[dict, Depends(get_current_user)]
    ) -> dict:
        """
        Verify user has required roles.

        Args:
            current_user: Current user from token

        Returns:
            Current user if authorized

        Raises:
            HTTPException: If user doesn't have required roles
        """
        user_roles = current_user.get("roles", [])

        # Check if user has any of the required roles
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of: {', '.join(required_roles)}",
            )

        return current_user

    return require_roles


# Convenience exports for common patterns
get_current_user = None  # To be initialized by application
require_roles = None  # To be initialized by application
