from typing import Any, Dict, Optional

from pydantic import Field

from ...models import State
from ..nodes.base import BaseNode
from .tracer_interface import BaseExecutionTracer


class TraceNodeMiddleware(BaseNode):
    """Middleware wrapper to add execution tracing to graph nodes."""

    inner_node: BaseNode = Field(..., description="The node to be wrapped.")
    tracer: BaseExecutionTracer = Field(..., description="The tracer service.")
    step_name: str = Field(..., description="The name of the step for tracing.")

    async def process(
        self, state: State, config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Wraps the inner node process with logging calls."""

        execution_id = state.execution_id

        if not execution_id:
            return await self.inner_node.process(state, config)

        try:
            await self.tracer.log_step(execution_id, self.step_name, "IN_PROGRESS")

            # Inject the tracer into the inner node so it can log granular updates
            # This is critical for ZeroxOCRNode to access the tracer via self._tracer
            object.__setattr__(self.inner_node, "_tracer", self.tracer)

            result = await self.inner_node.process(state, config)

            await self.tracer.log_step(execution_id, self.step_name, "SUCCESS")

            return result
        except Exception as e:
            await self.tracer.log_step(execution_id, self.step_name, "FAILED", str(e))
            raise e
