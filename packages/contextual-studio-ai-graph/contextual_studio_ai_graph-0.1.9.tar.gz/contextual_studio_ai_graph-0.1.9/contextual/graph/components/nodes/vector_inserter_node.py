"""LangGraph node that persists state into a vector store."""

from typing import Any

from langchain.schema import Document
from pydantic import Field

from ...models import State
from ..vector_stores import VectorStore
from .base import BaseNode


class VectorInserterNode(BaseNode):
    """Node responsible for inserting documents into the vector store/database.

    This node receives state input, creates a Document, and inserts it into the vector store.
    Intended to be used within a LangGraph processing pipeline.
    """

    vector_store_client: VectorStore[Document, Document] = Field(
        ..., description="The vector store client used for document insertion."
    )

    async def process(self, state: State, config: dict[str, Any] | None = None) -> dict[str, Any]:
        """Processes the input state and inserts a document into the vector store.

        Args:
            state (State): Input state containing text and metadata for the document.
            config (Optional[Dict[str, Any]]): Optional configuration parameters (unused).

        Returns:
            Dict[str, Any]: A dictionary containing the insertion status and/or document info.
        """
        if state.data_extracted is None or isinstance(state.data_extracted, dict):
            raise Exception(
                "Error while processing the input state and inserting a document into the vector store."
            )
        doc = Document(page_content=state.text, metadata=state.data_extracted.model_dump())
        self.vector_store_client.add([doc])
        return {"insertion_status": "success", "inserted_metadata": doc.metadata}
