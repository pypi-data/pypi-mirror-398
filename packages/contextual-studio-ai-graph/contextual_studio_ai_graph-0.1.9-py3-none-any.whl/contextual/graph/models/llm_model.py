"""Language model descriptors for contextual agents."""

from pydantic import BaseModel


class LlmModel(BaseModel):
    """Configuration describing a LLM model selection."""

    model_name: str
