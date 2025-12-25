from pydantic import BaseModel, Field, SecretStr

from .llm_model import LlmModel


class DataExtractorConfig(BaseModel):
    """Configuration for the Data Extractor service.

    Attributes:
        llm (LlmModel): The LLM model configuration.
        api_key (Optional[SecretStr]): The API key for the LLM service.
    """

    llm: LlmModel = Field(
        description="LLM model to use in the data extractor node (e.g., gemini-2.5-flash)"
    )
    api_key: SecretStr = Field(description="API Key for the LLM provider")
