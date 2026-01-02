from pydantic import BaseModel, Field

from .mongodb_config import MongoDBConfig


class ExecutionTracingConfig(BaseModel):
    mongodb: MongoDBConfig = Field(description="MongoDB config to retrieve execution tracing")
