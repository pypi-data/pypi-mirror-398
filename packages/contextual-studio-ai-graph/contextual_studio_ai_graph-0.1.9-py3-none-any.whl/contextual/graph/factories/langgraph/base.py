"""Abstract factories for LangGraph builders."""

from abc import ABC, abstractmethod

from ...models import State


class GraphFactory(ABC):
    """Contract for building state graphs."""

    @abstractmethod
    def build(self, state: type[State]) -> object:
        """Build and compile a graph object for the given state type.

        Args:
            state (type[State]): The class representing the state for which the graph is built.

        Returns:
            object: The compiled state graph instance.
        """
        pass
