from typing import Any, Dict

from pydantic import Field

from contextual.graph.factories.langgraph import ExtractorLangGraphFactory
from contextual.graph.models import FilterSchema, ModelDataExtractor, State

from .base import DataExtractor


class DataExtractorLG(DataExtractor):
    """Implementation of a data extractor that uses a prompt-driven graph-based workflow.

    This class extends the `DataExtractor` interface and utilizes a `GraphFactory`
    to extract structured information from raw text using a predefined extractor_schema.
    """

    graph_factory: ExtractorLangGraphFactory = Field(
        ..., description="Factory to build the graph-based extraction pipeline."
    )

    async def extract(
        self, text: str | None, model_schema: FilterSchema, **kwargs: Dict[Any, Any]
    ) -> ModelDataExtractor:
        """Extracts structured data from input text using a extractor_schema and prompt-driven graph.

        The method creates an extraction graph using the provided factory, applies it
        to the input text and extractor_schema, and returns structured extraction results.

        Args:
            text (str | None): Raw input text to be processed.
            **kwargs (Dict[Any, Any]): Optional keyword arguments for customizing the extraction workflow.

        Returns:
            ModelDataExtractor: Returning structured extraction results.
        """

        graph = self.graph_factory.build(state=State)
        file_path: str | None = kwargs.get("file_path")  # type: ignore[assignment]

        ocr_custom_prompt: str | None = kwargs.get("ocr_custom_prompt")  # type: ignore[assignment]
        dataextractor_custom_prompt: str | None = kwargs.get("dataextractor_custom_prompt")  # type: ignore[assignment]
        maintain_format: bool = kwargs.get("maintain_format", False)  # type: ignore[assignment]
        execution_id: str | None = kwargs.get("execution_id")  # type: ignore[assignment]

        initial_state = State(
            text=text,
            model_schema=model_schema,
            file_path=file_path,
            data_extracted={},
            ocr_custom_prompt=ocr_custom_prompt,
            dataextractor_custom_prompt=dataextractor_custom_prompt,
            maintain_format=maintain_format,
            execution_id=execution_id,
        )

        output = await graph.ainvoke(initial_state)

        # Handle dict output
        if isinstance(output, dict):
            if "data_extracted" not in output:
                raise Exception("Graph output missing data_extracted field")
            return ModelDataExtractor(data=output["data_extracted"])

        # Handle State object
        if isinstance(output, State):
            if output.data_extracted is None:
                raise ValueError("State data_extracted field is None")
            return ModelDataExtractor(data=output.data_extracted)

        # Invalid type
        raise TypeError(f"Expected State or dict, got {type(output).__name__}")
