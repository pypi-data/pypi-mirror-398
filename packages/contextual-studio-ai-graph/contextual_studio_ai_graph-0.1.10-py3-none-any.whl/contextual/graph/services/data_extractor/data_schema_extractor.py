from typing import Any

from contextual.graph.components.extractor_schema import SchemaExtractor
from contextual.graph.models import FilterSchema, ModelDataExtractor

from .base import DataExtractor


class DataSchemaExtractor:
    """Use case for extracting structured data from raw text using multiple data extractors.

    Attributes:
        data_extractors (dict[str, DataExtractor]): A dictionary of named data extractors used for processing text.
        schema_extractor (SchemaExtractor): Component responsible for extracting extractor_schema metadata.
        data (dict[str, ModelDataExtractor]): Stores extracted data after execution.
    """

    def __init__(
        self, data_extractors: dict[str, DataExtractor], schema_extractor: SchemaExtractor
    ):
        """Initializes the ExtractTextUseCase.

        Args:
            data_extractors (dict[str, DataExtractor]): Mapping of extractor names to extractor instances.
            schema_extractor (SchemaExtractor): Schema extractor to retrieve extraction extractor_schema definitions.
        """
        self.data_extractors = data_extractors
        self.schema_extractor: SchemaExtractor = schema_extractor
        self.data: dict[str, ModelDataExtractor] = {}

    async def execute(
        self, text: str | None, model_schema: FilterSchema, **kwargs: Any
    ) -> dict[str, ModelDataExtractor]:
        """Executes the data extraction workflow using the provided text and extractor_schema ID.

        Retrieves the extractor_schema, applies each data extractor to the text using that extractor_schema,
        and logs the extracted data.

        Args:
            text (str | None): The raw input text to extract structured data from.
            model_schema (FilterSchema): The extractor_schema used for extraction.
            **kwargs (Any): Additional arguments passed to extractors.

        Returns:
            dict[str, ModelDataExtractor]: A dictionary containing extracted data for each extractor.
        """
        for name, d_extractor in self.data_extractors.items():
            data_extracted: ModelDataExtractor = await d_extractor.extract(
                text=text, model_schema=model_schema, **kwargs
            )
            self.data[name] = data_extracted
            # TODO: Loggear still do be adapted since it was a feature of data-extractor (Same goes for ocr)

        return self.data
