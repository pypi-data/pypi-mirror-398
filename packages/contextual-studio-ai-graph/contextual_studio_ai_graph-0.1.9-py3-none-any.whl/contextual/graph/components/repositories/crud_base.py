"""Abstract repository interfaces for CRUD workflows."""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from ..base import BaseComponent

T = TypeVar("T")  # Input type (e.g., Pydantic model)
R = TypeVar("R")  # Output type (e.g., dict or model)


class CRUDRepository(BaseComponent, ABC, Generic[T, R]):
    """Generic contract defining CRUD operations for any data model."""

    @abstractmethod
    def create(self, obj: T) -> R:
        """Insert a record synchronously.

        Args:
            obj (T): Domain object to persist.

        Returns:
            R: Persisted record or backend response.
        """
        pass

    @abstractmethod
    def read(self, filters: dict[str, Any] | None = None) -> list[R]:
        """Read records synchronously.

        Args:
            filters (dict[str, Any] | None): Optional filters applied to the query.

        Returns:
            list[R]: Records retrieved from the data source.
        """
        pass

    @abstractmethod
    def update(self, match: dict[str, Any], updates: dict[str, Any]) -> R:
        """Update records synchronously.

        Args:
            match (dict[str, Any]): Criteria that select records to update.
            updates (dict[str, Any]): Fields and values to apply to matching records.

        Returns:
            R: Updated records or backend response.
        """
        pass

    @abstractmethod
    def delete(self, match: dict[str, Any]) -> R:
        """Delete records synchronously.

        Args:
            match (dict[str, Any]): Criteria that select records to delete.

        Returns:
            R: Deleted records or backend response.
        """
        pass

    @abstractmethod
    async def async_create(self, obj: T) -> R:
        """Insert a record asynchronously.

        Args:
            obj (T): Domain object to persist.

        Returns:
            R: Persisted record or backend response.
        """
        pass

    @abstractmethod
    async def async_read(self, filters: dict[str, Any] | None = None) -> list[R]:
        """Read records asynchronously.

        Args:
            filters (dict[str, Any] | None): Optional filters applied to the query.

        Returns:
            list[R]: Records retrieved from the data source.
        """
        pass

    @abstractmethod
    async def async_update(self, match: dict[str, Any], updates: dict[str, Any]) -> R:
        """Update records asynchronously.

        Args:
            match (dict[str, Any]): Criteria that select records to update.
            updates (dict[str, Any]): Fields and values to apply to matching records.

        Returns:
            R: Updated records or backend response.
        """
        pass

    @abstractmethod
    async def async_delete(self, match: dict[str, Any]) -> R:
        """Delete records asynchronously.

        Args:
            match (dict[str, Any]): Criteria that select records to delete.

        Returns:
            R: Deleted records or backend response.
        """
        pass
