"""Provides a base class for user service.

Authors:
    Immanuel Rhesa (immanuel.rhesa@gdplabs.id)
    Hermes Vincentius Gani (hermes.v.gani@gdplabs.id)
    Ricky Setiawan (ricky.setiawan@gdplabs.id)

References:
    NONE
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseUserService(ABC):
    """A base class for user service."""

    @abstractmethod
    async def get_user_id(self, **kwargs: Any) -> str | None:
        """Abstract method to get the user id.

        Args:
            **kwargs (Any): Additional keyword arguments for user identification.

        Returns:
            str | None: user id, None if not found.

        Raises:
            NotImplementedError: If the method is not implemented.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_user_session(self, **kwargs: Any) -> Any | None:
        """Abstract method to get the user session.

        Args:
            **kwargs (Any): Additional keyword arguments for user session retrieval.

        Returns:
            Any | None: User session, None if not found.

        Raises:
            NotImplementedError: If the method is not implemented.
        """
        raise NotImplementedError

    @abstractmethod
    async def register(self, **kwargs: Any):
        """Abstract method to register a new user.

        Args:
            **kwargs (Any): Additional keyword arguments for user registration.

        Raises:
            NotImplementedError: If the method is not implemented.
        """
        raise NotImplementedError

    @abstractmethod
    async def login(self, **kwargs: Any):
        """Abstract method to authenticate and login a user.

        Args:
            **kwargs (Any): Additional keyword arguments for user login.

        Raises:
            NotImplementedError: If the method is not implemented.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_applications(self, **kwargs: Any) -> Any:
        """Abstract method to get user applications.

        Args:
            **kwargs (Any): Additional keyword arguments for retrieving applications.

        Returns:
            Any: User applications data.

        Raises:
            NotImplementedError: If the method is not implemented.
        """
        raise NotImplementedError

    @abstractmethod
    async def set_user_applications(self, **kwargs: Any):
        """Abstract method to set user applications.

        Args:
            **kwargs (Any): Additional keyword arguments for setting user applications.

        Raises:
            NotImplementedError: If the method is not implemented.
        """
        raise NotImplementedError
