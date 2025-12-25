"""Abstract embedding interfaces."""

from abc import ABC, abstractmethod

from pydantic import Field

from ..base import BaseComponent


class Embedding(BaseComponent, ABC):
    """Base interface for embedding backends."""

    model_name: str | None = Field(
        default=None, description="Provider-specific identifier for the embedding model."
    )

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        """Embed a single text snippet.

        Args:
            text (str): Text to embed.

        Returns:
            list[float]: Embedding vector for the query.
        """
        pass

    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of documents.

        Args:
            texts (list[str]): Documents to embed.

        Returns:
            list[list[float]]: Embeddings for each input document.
        """
        pass

    @property
    @abstractmethod
    def embedding_size(self) -> int:
        """Return the dimensionality of the embedding vector.

        Returns:
            int: Number of features produced by the embedding model.
        """
        pass
