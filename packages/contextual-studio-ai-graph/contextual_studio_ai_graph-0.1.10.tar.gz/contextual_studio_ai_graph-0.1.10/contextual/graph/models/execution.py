from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ExecutionStep(BaseModel):
    step: str
    status: str  # "SUCCESS", "FAILED", "IN_PROGRESS"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    error: Optional[str] = None


class Execution(BaseModel):
    execution_id: str
    user_id: str
    schema_id: str
    status: str  # "COMPLETED", "FAILED", "IN_PROGRESS"
    current_step: Optional[str] = None
    trace: List[ExecutionStep] = []
    error_details: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
