from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseExecutionTracer(ABC):
    """Interface defining the contract for execution tracing."""

    @abstractmethod
    async def log_step(
        self,
        execution_id: str,
        step_name: str,
        status: str,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Logs a step status change in the execution trace."""
        pass

    @abstractmethod
    async def update_status(
        self, execution_id: str, status: str, error: Optional[str] = None
    ) -> None:
        """Updates the overall status of the execution."""
        pass

    @abstractmethod
    async def start_execution(self, execution_data: Dict[str, Any]) -> str:
        """Starts a new execution tracking record.

        Args:
            execution_data: Dictionary containing initial execution data (id, user, schema, etc.)

        Returns:
            The execution_id.
        """
        pass
