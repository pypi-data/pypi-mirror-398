from abc import ABC, abstractmethod
from typing import Any, Dict

from contextual.graph.models import ModelSchemaExtractor

from ..base import BaseComponent


class SchemaExtractor(BaseComponent, ABC):
    """Abstract interface for extracting a extractor_schema (BaseModel) given an id (string)."""

    @abstractmethod
    async def extract(self, filters: Any, **kwargs: Dict[str, Any]) -> ModelSchemaExtractor:
        """Asynchronously extracts a structured extractor_schema based on the provided extractor_schema ID.

        Args:
            filters (Any): Any filters used during extraction.
            **kwargs (Dict[str, Any]): Optional keyword arguments for customization or additional parameters.

        Returns:
            ModelSchemaExtractor:
                A model containing the extracted extractor_schema.
        """
        pass
