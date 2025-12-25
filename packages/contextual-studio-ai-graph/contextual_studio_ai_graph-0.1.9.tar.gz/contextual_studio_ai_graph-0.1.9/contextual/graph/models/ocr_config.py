from pydantic import BaseModel, Field, SecretStr

from .llm_model import LlmModel


class OCRConfig(BaseModel):
    llm: LlmModel = Field(
        description="LLM model to use with Zerox (e.g., gpt-4o, gpt-4-turbo, etc.)"
    )
    api_key: SecretStr = Field(description="API key for accessing the LLM provider (e.g., OpenAI)")
