from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class BaseComponent(BaseModel):
    """Base Component."""

    component_id: str = Field(default_factory=lambda: str(uuid4()), description="Component ID")

    model_config = ConfigDict(arbitrary_types_allowed=True)
