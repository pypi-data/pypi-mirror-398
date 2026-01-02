from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable

from pydantic import ValidationError

from ...models.state import State
from ..base import BaseComponent


class BaseNode(BaseComponent, ABC):
    """Abstract interface for all graph nodes."""

    @abstractmethod
    async def process(self, state: State, config: dict[str, Any] | None = None) -> dict[str, Any]:
        """Processes the state and returns a dictionary of fields to update.

        Args:
            state: The current graph state object.
            config: Optional runtime configuration.

        Returns:
            A dictionary containing only the state fields to be updated.
        """
        pass

    def as_langgraph_node(
        self,
    ) -> Callable[[State | dict[str, Any], dict[str, Any] | None], Awaitable[dict[str, Any]]]:
        """Converts this node into a callable format required by LangGraph.

        This wrapper handles state instantiation (dict -> State) and ensures
        the node's process method is called correctly, returning its
        partial state update dictionary.

        Returns:
            A callable function that accepts the graph's state, processes it,
            and returns a dictionary of updates to be merged.
        """

        async def _node_wrapper(
            state: State | dict[str, Any],
            config: dict[str, Any] | None = None,
        ) -> dict[str, Any]:
            """Internal wrapper to handle state conversion before processing."""
            state_obj: State
            if isinstance(state, dict):
                try:
                    state_obj = State(**state)
                except ValidationError as e:
                    raise ValueError("Input dictionary could not be converted to State.") from e
            elif isinstance(state, State):
                state_obj = state
            else:
                raise TypeError(
                    f"Invalid input type for node. Expected State or dict, " f"got {type(state)}."
                )

            return await self.process(state_obj, config)

        return _node_wrapper
