from typing import Any, Dict

from pydantic import BaseModel, Field


class ModelDataExtractor(BaseModel):
    """Container for the result of a data extraction process.

    Attributes:
        data (BaseModel): The extracted data, structured using a Pydantic model.
    """

    data: BaseModel | Dict[Any, Any] | None = Field(
        ..., description="The extracted data, structured using a Pydantic model."
    )
