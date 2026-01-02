from pydantic import BaseModel, Field

from .llm_model import LlmModel
from .mongodb_config import MongoDBConfig


class DataSchemaConfig(BaseModel):
    llm: LlmModel = Field(
        description="LLM model to use with Zerox (e.g., gpt-4o, gpt-4-turbo, etc.)"
    )
    mongodb: MongoDBConfig = Field(description="MongoDB config to retrieve extractor_schema")
