"""Factory that wires a simple LangGraph-based inserter pipeline."""

from langchain_core.documents import Document
from langgraph.graph import StateGraph
from supabase import Client

from ...components.embedding import Embedding, OpenAIEmbedding
from ...components.nodes import BaseNode, VectorInserterNode
from ...components.vector_stores import SupabaseVectorStore, VectorStore
from ...models import State, SupabaseConfig
from ..client.supabase_client_factory import SupabaseClientFactory
from .base import GraphFactory


class InserterLangGraphFactory(GraphFactory):
    """Factory for constructing LangGraph StateGraph instances based on defined architectures.

    This class currently supports a basic single-node architecture where the same
    node serves as both entry and exit. It can be extended to support more complex workflows.

    Attributes:
        architecture (str): The type of graph architecture to construct.
    """

    def __init__(self, config: SupabaseConfig, architecture: str = "simple") -> None:
        """Initialize the factory with a specified graph architecture.

        Notes:
            TODO: Create additional architectures or define scalability for future applications.

        Args:
            config (SupabaseConfig): Application configuration that provides Supabase credentials.
            architecture (str): Identifier for the graph architecture (e.g., "simple").
        """
        self.architecture = architecture
        self.config: SupabaseConfig = config

    def build(self, state: type[State]) -> StateGraph:
        """Builds and compiles a LangGraph StateGraph using the defined architecture.

        Constructs the graph by adding nodes and configuring entry/exit behavior
        based on the selected architecture.

        Args:
            state (type[State]): The State class representing the shape of the execution state.

        Returns:
            StateGraph: A compiled LangGraph StateGraph ready for execution.

        Raises:
            NotImplementedError: If the specified architecture is not supported.
        """
        graph = StateGraph[State](state)

        if self.architecture == "simple":
            self._create_simple_arquitecture(graph)
        else:
            raise NotImplementedError(f"Architecture '{self.architecture}' is not implemented.")

        return graph.compile()

    def _create_simple_arquitecture(self, graph: StateGraph) -> None:
        """Create the minimal single-node architecture.

        Args:
            graph (StateGraph): Graph under construction that receives the nodes.
        """
        supabase: Client = SupabaseClientFactory.create(self.config)
        embedding: Embedding = OpenAIEmbedding()
        vector_store: VectorStore[Document, Document] = SupabaseVectorStore(
            client=supabase, embedding=embedding
        )
        inserter_node: BaseNode = VectorInserterNode(vector_store_client=vector_store)
        graph.add_node("inserter_node", inserter_node.as_langgraph_node())
        graph.set_entry_point("inserter_node")
        graph.set_finish_point("inserter_node")
