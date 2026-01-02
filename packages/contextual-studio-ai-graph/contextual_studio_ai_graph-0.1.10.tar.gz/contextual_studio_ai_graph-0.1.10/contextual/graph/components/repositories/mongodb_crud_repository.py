import asyncio

# Agregamos 'cast' para forzar el tipo para mypy
from typing import Any, Dict, List, Optional, cast

from pydantic import BaseModel, ConfigDict, Field
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from .crud_base import CRUDRepository

# Esto ya estaba correcto:
JSONDict = Dict[str, Any]


class MongoDBRepository(CRUDRepository[JSONDict, JSONDict]):
    """MongoDB-backed implementation of the CRUDRepository interface.

    This repository uses JSONDict (dictionaries) for filtering operations,
    maintaining compatibility with MongoDB.
    """

    collection: Collection[Dict[str, Any]] = Field(
        ..., description="A pymongo.collection.Collection instance for data operations."
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # --- Synchronous Methods ---

    def create(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a new record into the collection.

        Args:
            obj (Dict[str, Any]): The domain object to persist (Pydantic BaseModel or dict).

        Returns:
            Dict[str, Any]: The persisted document as returned by MongoDB,
                            including its '_id'.

        Raises:
            TypeError: If the input object is not a BaseModel or dict.
            ValueError: If the document is not found after insertion.
            Exception: Wraps any PyMongoError.
        """
        try:
            if isinstance(obj, BaseModel):
                data = obj.model_dump()
            elif isinstance(obj, dict):
                data = obj
            else:
                raise TypeError(f"Object of type {type(obj)} is not supported")

            result = self.collection.insert_one(data)
            found = self.collection.find_one({"_id": result.inserted_id})

            if found is None:
                raise ValueError("Created document not found after insertion")

            # TO FIX: TYPE OF RETURN
            return cast(Dict[str, Any], found)

        except PyMongoError as e:
            raise Exception(f"MongoDB create error: {str(e)}") from e

    def read(self, filters: Optional[JSONDict] = None) -> List[Dict[str, Any]]:
        """Read records from the collection, with optional filtering.

        Args:
            filters: A dictionary for query parameters.

        Returns:
            List[Dict[str, Any]]: A list of documents matching the filter.

        Raises:
            ValueError: If an '_id' string is provided but is not valid.
            Exception: Wraps any PyMongoError.
        """
        try:
            cursor = self.collection.find(filters)
            return list(cursor)
        except PyMongoError as e:
            raise Exception(f"MongoDB read error: {str(e)}") from e

    def update(self, match: JSONDict, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a single document matching the criteria.

        Args:
            match: A dictionary to locate the document.
            updates: The update operations to apply (e.g., {'$set': {...}}).

        Returns:
            Dict[str, Any]: The updated document.

        Raises:
            ValueError: If no document matches the 'match' criteria.
            Exception: Wraps any PyMongoError.
        """
        try:
            result = self.collection.find_one_and_update(match, updates, return_document=True)

            if result is None:
                raise ValueError("Document not found for update")

            # TO FIX: TYPE OF RETURN
            return cast(Dict[str, Any], result)

        except PyMongoError as e:
            raise Exception(f"MongoDB update error: {str(e)}") from e

    def delete(self, match: JSONDict) -> Dict[str, Any]:
        """Delete a single document matching the criteria.

        Args:
            match: A dictionary to locate the document to delete.

        Returns:
            Dict[str, Any]: The document that was deleted.

        Raises:
            ValueError: If no document matches the 'match' criteria.
            Exception: Wraps any PyMongoError.
        """
        try:
            result = self.collection.find_one_and_delete(match)
            if result is None:
                raise ValueError("Document not found for deletion")

            # TO FIX: TYPE OF RETURN
            return cast(Dict[str, Any], result)

        except PyMongoError as e:
            raise Exception(f"MongoDB delete error: {str(e)}") from e

    # --- Asynchronous Wrappers ---

    async def async_create(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        """Asynchronously insert a new record.

        Wraps the synchronous 'create' method in a separate thread
        to avoid blocking the asyncio event loop.

        Args:
            obj (Dict[str, Any]): The domain object to persist.

        Returns:
            Dict[str, Any]: The persisted record.
        """
        return await asyncio.to_thread(self.create, obj)

    async def async_read(self, filters: Optional[JSONDict] = None) -> List[Dict[str, Any]]:
        """Asynchronously read records from the collection.

        Wraps the synchronous 'read' method in a separate thread
        to avoid blocking the asyncio event loop.

        Args:
            filters: Optional dictionary for query filters.

        Returns:
            List[Dict[str, Any]]: A list of matching documents.
        """
        return await asyncio.to_thread(self.read, filters)

    async def async_update(self, match: JSONDict, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Asynchronously update a single document.

        Wraps the synchronous 'update' method in a separate thread
        to avoid blocking the asyncio event loop.

        Args:
            match: Dictionary to find the document.
            updates: The update operations to apply.

        Returns:
            Dict[str, Any]: The updated document.
        """
        return await asyncio.to_thread(self.update, match, updates)

    async def async_delete(self, match: JSONDict) -> Dict[str, Any]:
        """Asynchronously delete a single document.

        Wraps the synchronous 'delete' method in a separate thread
        to avoid blocking the asyncio event loop.

        Args:
            match: Dictionary to find the document.

        Returns:
            Dict[str, Any]: The document that was deleted.
        """
        return await asyncio.to_thread(self.delete, match)
