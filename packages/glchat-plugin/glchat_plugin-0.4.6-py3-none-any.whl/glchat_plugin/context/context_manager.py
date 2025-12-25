"""Provides a class for context manager.

Authors:
    Ricky Setiawan (ricky.setiawan@gdplabs.id)
    Ryan Ignatius Hadiwijaya (ryan.i.hadiwijaya@gdplabs.id)

References:
    NONE
"""

from contextvars import ContextVar
from typing import Any


class ContextManager:
    """A Context Manager.

    This class is used to manage the context of the application.
    """

    _tenant: ContextVar[str | None] = ContextVar("tenant_id", default=None)
    _user: ContextVar[str | None] = ContextVar("user_id", default=None)
    _user_session: ContextVar[Any | None] = ContextVar("user_session", default=None)

    @classmethod
    def set_tenant(cls, tenant_id: str | None) -> None:
        """Set the tenant id in the context.

        Args:
            tenant_id (str | None): The tenant id.
        """
        cls._tenant.set(tenant_id)

    @classmethod
    def get_tenant(cls) -> str | None:
        """Get the tenant id from the context.

        Returns:
            str | None: The tenant id.
        """
        tenant_id = cls._tenant.get()
        return tenant_id

    @classmethod
    def set_user(cls, user_id: str | None) -> None:
        """Set the user id in the context.

        Args:
            user_id (str | None): The user id.
        """
        cls._user.set(user_id)

    @classmethod
    def get_user(cls) -> str | None:
        """Get the user id from the context.

        Returns:
            str | None: The user id.
        """
        return cls._user.get()

    @classmethod
    def set_user_session(cls, user_session: Any | None) -> None:
        """Set the user session in the context.

        Args:
            user_session (Any | None): The user session.
        """
        cls._user_session.set(user_session)

    @classmethod
    def get_user_session(cls) -> Any | None:
        """Get the user session from the context.

        Returns:
            Any | None: The user session.
        """
        return cls._user_session.get()
