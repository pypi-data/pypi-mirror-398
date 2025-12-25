from abc import ABC, abstractmethod
from typing import Any

from contextual.graph.components.base import BaseComponent
from contextual.graph.models import ModelDataExtractor


class DataExtractor(BaseComponent, ABC):
    """Abstract interface for extracting data given.

    a) the text from which the data is extracted
    b) a extractor_schema (BaseModel)
    """

    @abstractmethod
    async def extract(
        self, text: str | None, model_schema: Any, **kwargs: Any
    ) -> ModelDataExtractor:
        """Extract structured data from the given text using a extractor_schema.

        Args:
            text (str): The input text to process.
            model_schema (Any): Model schema using during extraction.
            **kwargs: Optional keyword arguments for customization or additional parameters.

        Returns:
            ModelDataExtractor:
                A structured model containing the extracted data.
        """
        pass
