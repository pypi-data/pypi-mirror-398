from datetime import datetime, timezone
from typing import Any, Dict, Optional

from ..repositories.mongodb_crud_repository import MongoDBRepository
from .tracer_interface import BaseExecutionTracer


class MongoExecutionTracer(BaseExecutionTracer):
    """MongoDB implementation of the execution tracer."""

    def __init__(self, repository: MongoDBRepository):
        self.repository = repository

    async def start_execution(self, execution_data: Dict[str, Any]) -> str:
        """Starts a new execution tracing record."""
        # Ensure ID exists or is handled by caller, assuming data follows Execution model structure
        await self.repository.async_create(execution_data)
        return str(execution_data.get("execution_id", ""))

    async def log_step(
        self,
        execution_id: str,
        step_name: str,
        status: str,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Logs a step status change."""

        step_data = {"step": step_name, "status": status, "timestamp": datetime.now(timezone.utc)}

        if error:
            step_data["error"] = error

        if metadata:
            step_data["metadata"] = metadata

        update_ops: Dict[str, Any] = {
            "$set": {"current_step": step_name, "updated_at": datetime.now(timezone.utc)},
            "$push": {"trace": step_data},
        }

        if status == "FAILED":
            update_ops["$set"]["status"] = "FAILED"
            update_ops["$set"]["error_details"] = error

        await self.repository.async_update({"execution_id": execution_id}, update_ops)

    async def update_status(
        self, execution_id: str, status: str, error: Optional[str] = None
    ) -> None:
        """Updates the overall status of the execution."""
        update_data = {"status": status, "updated_at": datetime.now(timezone.utc)}

        if error:
            update_data["error_details"] = error

        await self.repository.async_update({"execution_id": execution_id}, {"$set": update_data})
