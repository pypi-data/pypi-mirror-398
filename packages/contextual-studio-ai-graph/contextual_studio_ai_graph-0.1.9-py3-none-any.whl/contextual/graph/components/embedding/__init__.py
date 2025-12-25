"""Convenience exports for embedding interfaces."""

from .base import Embedding
from .openai_embedding import OpenAIEmbedding

__all__ = ["Embedding", "OpenAIEmbedding"]
