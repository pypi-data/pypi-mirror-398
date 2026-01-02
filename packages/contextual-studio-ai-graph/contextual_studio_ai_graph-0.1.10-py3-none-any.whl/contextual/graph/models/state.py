"""State representation exchanged between graph nodes."""

from typing import Any, Dict, Optional, Type

from pydantic import BaseModel, Field

from .filters_schema import FilterSchema


class State(BaseModel):
    """State.

    Immutable snapshot that links raw text, the extractor_schema used to parse it,
    and the structured data extracted with that extractor_schema.

    Attributes:
        text (str): The original text to process.
        model_schema (FilterSchema): The extractor_schema model used to interpret the text.
        data_extracted (BaseModel): The structured data extracted from the text.
    """

    text: str | None = Field(None, description="The original text to process.")
    file_path: str | None = Field(None, description="Path to the file to process.")
    model_schema: Optional[BaseModel | Type[BaseModel] | FilterSchema] = Field(
        ..., description="The extractor_schema model used to interpret the text."
    )

    data_extracted: BaseModel | None | Dict[Any, Any] = Field(
        None, description="The structured data extracted from the text."
    )
    ocr_custom_prompt: Optional[str] = Field(
        None, description="Optional system prompt to override the default behavior."
    )
    dataextractor_custom_prompt: Optional[str] = Field(
        None, description="Optional custom prompt for the data extractor."
    )
    maintain_format: bool = Field(
        False, description="Whether to maintain the format (sequential processing)."
    )
    execution_id: Optional[str] = Field(
        None, description="The unique ID of the execution for tracing."
    )
