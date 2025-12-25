from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class FilterSchema(BaseModel):
    """A Pydantic model representing a generic filter query for MongoDB operations.

    This model is designed to handle filters that require a unique
    identifier, particularly for database systems like MongoDB that
    use the `_id` field convention.

    It uses a Pydantic alias to map the Python-friendly `id` attribute
    to the external `_id` field.
    """

    id: str = Field(
        ...,
        alias="_id",
        description="The unique identifier for the document or resource.",
        examples=["60d5ec49e9c2e0f0b4a1b2c3", "unique-item-id-123"],
    )

    name: Optional[str] = Field(
        default=None,
        description="An optional filter for the item's name.",
        examples=["Example Item"],
    )

    def model_dump(self, **kwargs: Any) -> Dict[str, Any]:
        """Serialize the model including only non-None fields with MongoDB field aliases.

        Args:
            **kwargs (Any): Optional keyword arguments for customizing the extraction workflow.

        This override ensures that only fields with values are included in the output
        and uses field aliases suitable for MongoDB operations.

        Args:
            **kwargs: Additional arguments to pass to the base model_dump method.

        Returns:
            Dict[str, Any]: A dictionary containing only non-None fields with their aliases.
        """
        return super().model_dump(exclude_none=True, by_alias=True, **kwargs)
