from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .mongodb_crud_repository import MongoDBRepository


class ExecutionRepository(MongoDBRepository):
    """Repository specialized in managing extraction executions and traces."""

    async def add_trace_step(
        self, execution_id: str, step_name: str, status: str, error: Optional[str] = None
    ) -> None:
        """Adds a trace step to the execution record and updates status."""

        step_data = {"step": step_name, "status": status, "timestamp": datetime.now(timezone.utc)}

        if error:
            step_data["error"] = error

        update_ops: Dict[str, Any] = {
            "$set": {"current_step": step_name, "updated_at": datetime.now(timezone.utc)},
            "$push": {"trace": step_data},
        }

        # If the step failed, we might also want to mark the whole execution as failed or just the step.
        # Requirements said: "pass execution state to FAILED in DB".
        if status == "FAILED":
            update_ops["$set"]["status"] = "FAILED"
            update_ops["$set"]["error_details"] = error

        await self.async_update({"execution_id": execution_id}, update_ops)

    async def update_status(
        self, execution_id: str, status: str, error: Optional[str] = None
    ) -> None:
        """Updates the overall status of the execution."""
        update_data = {"status": status, "updated_at": datetime.now(timezone.utc)}

        if error:
            update_data["error_details"] = error

        await self.async_update({"execution_id": execution_id}, {"$set": update_data})
