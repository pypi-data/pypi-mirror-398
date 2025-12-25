"""OpenAI-powered embedding backend."""

from functools import cached_property
from typing import Sequence, cast

from langchain_openai import OpenAIEmbeddings

from .base import Embedding

# TODO: Add a checking either here or in config to ensure the OPENAI_API_KEY is set (probably here it makes the most sense)


class OpenAIEmbedding(Embedding):

    @cached_property
    def embedding_backend(self) -> OpenAIEmbeddings:
        """Backend used for create embedding given a embedding model."""
        return (
            OpenAIEmbeddings(model=self.model_name)
            if self.model_name is not None
            else OpenAIEmbeddings()
        )

    @property
    def embedding_size(self) -> int:
        """Return the size (dimension) of the embedding vector.

        Returns:
            int: Number of features produced by the embedding model.
        """
        # Specified within the models documentation
        if self.model_name == "text-embedding-ada-002":
            return 1536
        else:
            return len(self.embedding_backend.embed_query("test"))

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query.

        Args:
            text (str): Text to embed.

        Returns:
            list[float]: Embedding vector for the query.
        """
        embedding = cast(Sequence[float], self.embedding_backend.embed_query(text))
        return list(embedding)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of documents.

        Args:
            texts (list[str]): Documents to embed.

        Returns:
            list[list[float]]: Embeddings for each input document.
        """
        embeddings = cast(Sequence[Sequence[float]], self.embedding_backend.embed_documents(texts))
        return [list(vector) for vector in embeddings]
