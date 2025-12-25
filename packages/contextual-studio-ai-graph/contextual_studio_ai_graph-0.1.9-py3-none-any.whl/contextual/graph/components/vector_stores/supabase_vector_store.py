"""Concrete Supabase-backed vector store implementation."""

from functools import cached_property
from typing import Any, Sequence, cast

from langchain_community.vectorstores import SupabaseVectorStore as LangchainSupabaseVectorStore
from langchain_core.documents import Document
from supabase import Client

from ..embedding.base import Embedding
from ..repositories.supabase_crud_repository import SupabaseCRUD
from .base import VectorStore


class SupabaseVectorStore(VectorStore[Document, Document]):
    """Vector store adapter backed by Supabase infrastructure."""

    client: Client
    embedding: Embedding
    table_name: str = "documents"
    chunk_size: int = 500
    query_name: str = "match_documents"

    @cached_property
    def vector_store(self) -> LangchainSupabaseVectorStore:
        """Lazily initialized LangChain SupabaseVectorStore."""
        return LangchainSupabaseVectorStore(
            client=self.client,
            embedding=self.embedding,
            table_name=self.table_name,
            chunk_size=self.chunk_size,
            query_name=self.query_name,
        )

    def add(self, items: Sequence[Document]) -> Any:
        """Add documents to the vector store.

        Args:
            items (Sequence[Document]): Documents that should be persisted.

        Returns:
            Any: Backend response produced by the insertion call.
        """
        return self.vector_store.add_documents(list(items))

    def query(self, query: Any, top_k: int = 5) -> list[Document]:
        """Query the vector store for similar documents.

        Args:
            query (Any): Query payload, typically a text string.
            top_k (int): Maximum number of similar documents to return.

        Returns:
            list[Document]: Retrieved documents ordered by similarity.
        """
        results = self.vector_store.similarity_search(query, k=top_k)
        return cast(list[Document], results)

    def delete_by_id(self, ids: Sequence[Any]) -> Any:
        """Delete documents by IDs.

        Args:
            ids (Sequence[Any]): Identifiers of the documents to delete.

        Returns:
            Any: Backend response from the deletion.
        """
        return self.vector_store.delete(list(ids))

    def delete_by_metadata_field(self, metadata_field: str, metadata_value: str) -> Any:
        """Delete documents by any metadata field and value.

        Args:
            metadata_field (str): Metadata key used to filter candidates.
            metadata_value (str): Metadata value that must match for deletion.

        Returns:
            Any: Backend response from the deletion.
        """
        crud_client = SupabaseCRUD(client=self.client, table=self.table_name)
        filter_key = f"metadata->>{metadata_field}"
        documents = crud_client.read(filters={filter_key: metadata_value})
        ids_to_delete = [doc["id"] for doc in documents]
        return self.vector_store.delete(ids_to_delete)

    def update_by_metadata_field(
        self, metadata_field: str, metadata_value: str, updates: dict[str, Any]
    ) -> list[dict[str, Any]] | None:
        """Update documents by any metadata field and value, merging metadata fields instead of overwriting.

        Args:
            metadata_field (str): Metadata key used to filter candidates.
            metadata_value (str): Metadata value that must match for updating.
            updates (dict[str, Any]): Field updates to apply to each matching record.

        Returns:
            list[dict[str, Any]] | None: Updated documents or None if no records matched.
        """
        crud_client = SupabaseCRUD(client=self.client, table=self.table_name)
        filter_key = f"metadata->>{metadata_field}"
        documents = crud_client.read(filters={filter_key: metadata_value})
        if not documents:
            return None
        updated_docs = []
        for doc in documents:
            doc_id = doc["id"]
            current_metadata = doc.get("metadata", {})
            # Merge updates into current_metadata if updates is for metadata
            merged_metadata = current_metadata.copy()
            if "metadata" in updates and isinstance(updates["metadata"], dict):
                merged_metadata.update(updates["metadata"])
                update_payload = {**updates, "metadata": merged_metadata}
            else:
                update_payload = updates
            crud_client.update(match={"id": doc_id}, updates=update_payload)
            updated_docs.append({**doc, **update_payload})
        return updated_docs

    async def async_add(self, items: Sequence[Document]) -> Any:
        """Asynchronous wrapper for the add method.

        Args:
            items (Sequence[Document]): Documents that should be persisted.

        Returns:
            Any: Backend response produced by the insertion call.
        """
        return self.add(items)

    async def async_query(self, query: Any, top_k: int = 5) -> list[Document]:
        """Asynchronous wrapper for the query method.

        Args:
            query (Any): Query payload, typically a text string.
            top_k (int): Maximum number of similar documents to return.

        Returns:
            list[Document]: Retrieved documents ordered by similarity.
        """
        return self.query(query, top_k=top_k)

    async def async_delete_by_id(self, ids: Sequence[Any]) -> Any:
        """Asynchronous wrapper for the delete_by_id method.

        Args:
            ids (Sequence[Any]): Identifiers of the documents to delete.

        Returns:
            Any: Backend response from the deletion.
        """
        return self.delete_by_id(ids)

    async def async_delete_by_metadata_field(self, metadata_field: str, metadata_value: str) -> Any:
        """Asynchronous wrapper for the delete_by_metadata_field method.

        Args:
            metadata_field (str): Metadata key used to filter candidates.
            metadata_value (str): Metadata value that must match for deletion.

        Returns:
            Any: Backend response from the deletion.
        """
        return self.delete_by_metadata_field(metadata_field, metadata_value)

    async def async_update_by_metadata_field(
        self, metadata_field: str, metadata_value: str, updates: dict[str, Any]
    ) -> Any:
        """Asynchronous wrapper for the update_by_metadata_field method.

        Args:
            metadata_field (str): Metadata key used to filter candidates.
            metadata_value (str): Metadata value that must match for updating.
            updates (dict[str, Any]): Field updates to apply to each matching record.

        Returns:
            Any: Updated documents or backend response if no records matched.
        """
        return self.update_by_metadata_field(metadata_field, metadata_value, updates)
