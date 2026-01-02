"""Abstract interfaces for vector store implementations."""

from abc import ABC, abstractmethod
from typing import Any, Generic, Sequence, TypeVar

from pydantic import Field

from ..base import BaseComponent

T = TypeVar("T")  # Input type (e.g., document, dict)
R = TypeVar("R")  # Output type (e.g., query result, dict)


class VectorStore(BaseComponent, ABC, Generic[T, R]):
    """Backend-agnostic interface for vector store operations."""

    store_name: str | None = Field(
        default=None, description="Name used to identify the store instance."
    )
    config: dict[str, Any] | None = Field(
        default_factory=dict, description="Implementation-specific configuration options."
    )

    @abstractmethod
    def add(self, items: Sequence[T]) -> Any:
        """Add items (documents or vectors) to the store synchronously.

        Args:
            items (Sequence[T]): Batch of items to be persisted.

        Returns:
            Any: Implementation-defined result of the insertion.
        """
        pass

    @abstractmethod
    def query(self, query: Any, top_k: int = 5) -> list[R]:
        """Query the store for the most similar items synchronously.

        Args:
            query (Any): Query payload used by the backend.
            top_k (int): Maximum number of matches to retrieve.

        Returns:
            list[R]: Ranked collection of query results.
        """
        pass

    @abstractmethod
    def delete_by_id(self, ids: Sequence[Any]) -> Any:
        """Delete items by identifiers synchronously.

        Args:
            ids (Sequence[Any]): Identifiers for the items to delete.

        Returns:
            Any: Backend response after deletion.
        """
        pass

    @abstractmethod
    def delete_by_metadata_field(self, metadata_field: str, metadata_value: str) -> Any:
        """Delete items by a metadata field-value pair.

        Args:
            metadata_field (str): Key within the metadata payload.
            metadata_value (str): Value to match for deletion.

        Returns:
            Any: Backend response after deletion.
        """
        pass

    @abstractmethod
    def update_by_metadata_field(
        self, metadata_field: str, metadata_value: str, updates: dict[str, Any]
    ) -> Any:
        """Update items by matching a metadata field-value pair.

        Args:
            metadata_field (str): Key within the metadata payload.
            metadata_value (str): Value to match for the update operation.
            updates (dict[str, Any]): Key-value pairs describing the update.

        Returns:
            Any: Backend response or updated records.
        """
        pass

    @abstractmethod
    async def async_add(self, items: Sequence[T]) -> Any:
        """Add items asynchronously.

        Args:
            items (Sequence[T]): Batch of items to be persisted.

        Returns:
            Any: Implementation-defined result of the insertion.
        """
        pass

    @abstractmethod
    async def async_query(self, query: Any, top_k: int = 5) -> list[R]:
        """Query the store for the most similar items asynchronously.

        Args:
            query (Any): Query payload used by the backend.
            top_k (int): Maximum number of matches to retrieve.

        Returns:
            list[R]: Ranked collection of query results.
        """
        pass

    @abstractmethod
    async def async_delete_by_id(self, ids: Sequence[Any]) -> Any:
        """Delete items by identifiers asynchronously.

        Args:
            ids (Sequence[Any]): Identifiers for the items to delete.

        Returns:
            Any: Backend response after deletion.
        """
        pass

    @abstractmethod
    async def async_delete_by_metadata_field(self, metadata_field: str, metadata_value: str) -> Any:
        """Delete items by a metadata field-value pair asynchronously.

        Args:
            metadata_field (str): Key within the metadata payload.
            metadata_value (str): Value to match for deletion.

        Returns:
            Any: Backend response after deletion.
        """
        pass

    @abstractmethod
    async def async_update_by_metadata_field(
        self, metadata_field: str, metadata_value: str, updates: dict[str, Any]
    ) -> Any:
        """Update items by matching a metadata field-value pair asynchronously.

        Args:
            metadata_field (str): Key within the metadata payload.
            metadata_value (str): Value to match for the update operation.
            updates (dict[str, Any]): Key-value pairs describing the update.

        Returns:
            Any: Backend response or updated records.
        """
        pass
