"""Provides a base class for post login handlers.

Authors:
    Ricky Setiawan (ricky.setiawan@gdplabs.id)

References:
    NONE
"""

from abc import ABC, abstractmethod
from typing import Any


class BasePostLoginHandler(ABC):
    """A base class for post login handlers.

    This interface defines the contract for handling post-authentication login flows.
    Implementations can customize user validation, data mapping, team assignment,
    and other login-related logic for different environments.
    """

    @abstractmethod
    async def handle_post_oauth_login(self, stackauth_user: Any, tenant_id: str, **kwargs: Any) -> Any:
        """Handle post OAuth login flow.

        This method is called after a successful OAuth authentication to complete
        the login process. It should handle user validation, team assignment,
        user data upsert, and return the appropriate user object.

        Args:
            stackauth_user (Any): Authenticated user object from StackAuth containing
                user information from the OAuth provider.
            tenant_id (str): Tenant identifier for multi-tenant applications.
            **kwargs (Any): Additional keyword arguments for extensibility.
                May contain request context, services, or other dependencies.

        Returns:
            Any: Current user object for the frontend session containing
                user information, roles, permissions, and tenant data.

        Raises:
            NotImplementedError: If the method is not implemented.
            HTTPException: If user validation or processing fails.
        """
        raise NotImplementedError

    @abstractmethod
    async def handle_post_credential_login(self, stackauth_user: Any, tenant_id: str, **kwargs: Any) -> Any:
        """Handle post credential (username/password) login flow.

        This method is called after a successful credential-based authentication
        to complete the login process. It should fetch existing user data,
        validate permissions, and return the appropriate user object.

        Args:
            stackauth_user (Any): Authenticated user object from StackAuth containing
                user information from credential authentication.
            tenant_id (str): Tenant identifier for multi-tenant applications.
            **kwargs (Any): Additional keyword arguments for extensibility.
                May contain request context, services, or other dependencies.

        Returns:
            Any: Current user object for the frontend session containing
                user information, roles, permissions, and tenant data.

        Raises:
            NotImplementedError: If the method is not implemented.
            HTTPException: If user validation or processing fails.
        """
        raise NotImplementedError
