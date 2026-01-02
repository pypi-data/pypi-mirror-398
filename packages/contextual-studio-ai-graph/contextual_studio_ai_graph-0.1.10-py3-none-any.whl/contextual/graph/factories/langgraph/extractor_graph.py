from typing import Any, Dict, Optional

from langgraph.graph import StateGraph

from contextual.graph.components.extractor_schema import SchemaExtractor
from contextual.graph.components.observability import MongoExecutionTracer, TraceNodeMiddleware
from contextual.graph.components.ocr import ZeroxOCR

from ...components.nodes import ExtractorNode, ZeroxOCRNode
from ...components.repositories.mongodb_crud_repository import MongoDBRepository
from ...models import DataExtractorConfig, State
from ..llm_services import GoogleLLMFactory
from .base import GraphFactory


class ExtractorLangGraphFactory(GraphFactory):
    """Factory for constructing LangGraph StateGraph instances based on defined architectures.

    This class currently supports a basic single-node architecture where the same
    node serves as both entry and exit. It can be extended to support more complex workflows.

    Attributes:
        schema_extractor (SchemaExtractor): SchemaExtractor component to extract schemas used.
        architecture (str): The type of graph architecture to construct.
    """

    def __init__(
        self,
        schema_extractor: SchemaExtractor,
        ocr_service: Optional[ZeroxOCR] = None,
        architecture: str = "simple",
        config: Optional[DataExtractorConfig] = None,
        execution_tracing_repository: Optional[MongoDBRepository] = None,
    ):
        """Initializes the LangGraphFactory with a specified graph architecture.

        TODO create different architectures or define scalability for future applications

        Args:
            schema_extractor (SchemaExtractor): An instance used to extract extractor_schema
                information for building the graph.
            ocr_service (Optional[ZeroxOCR], optional): An instance of ZeroxOCR used for OCR processing.
                Defaults to None.
            architecture (str, optional): Identifier for the graph architecture
                to build (e.g., "simple"). Defaults to "simple".
            config (Optional[DataExtractorConfig], optional): Configuration for the data extractor.
                Defaults to None.
            execution_tracing_repository (Optional[MongoDBRepository], optional): Repository for tracing.
                Defaults to None.
        """
        self.schema_extractor: SchemaExtractor = schema_extractor
        self.ocr_service: Optional[ZeroxOCR] = ocr_service
        self.architecture = architecture
        self.config: Optional[DataExtractorConfig] = config
        self.execution_tracing_repository: Optional[MongoDBRepository] = (
            execution_tracing_repository
        )

    def build(self, state: type[Any]) -> StateGraph:
        """Builds and compiles a LangGraph StateGraph using the defined architecture.

        Constructs the graph by adding nodes and configuring entry/exit behavior
        based on the selected architecture.

        Args:
            state (type['State']): The State class representing the shape of the execution state.

        Returns:
            StateGraph: A compiled LangGraph StateGraph ready for execution.

        Raises:
            NotImplementedError: If the specified architecture is not supported.
        """
        graph = StateGraph(state)
        if self.architecture == "simple":
            self._build_simple_graph(graph)
        else:
            raise NotImplementedError(f"Architecture '{self.architecture}' is not implemented.")

        return graph.compile()

    def _get_llm_service(self) -> Any:
        """Helper to create LLM service with configuration."""
        llm_kwargs: Dict[str, Any] = {}
        if self.config:
            if self.config.api_key:
                llm_kwargs["api_key"] = self.config.api_key.get_secret_value()
            if self.config.llm:
                llm_kwargs["model"] = self.config.llm.model_name

        return GoogleLLMFactory.create(**llm_kwargs)

    def _build_simple_graph(self, graph: StateGraph) -> None:
        """Configures a simple graph topology with one processing node.

        The single node is used as both the entry point and the finish point,
        suitable for linear single-step graph flows.

        Args:
            graph (StateGraph): The graph instance to be configured.
        """
        # Instantiate Tracer
        # Instantiate Tracer
        tracer: Optional[MongoExecutionTracer] = None
        if self.execution_tracing_repository:
            tracer = MongoExecutionTracer(repository=self.execution_tracing_repository)

        node_name = "extractor_node"

        llm_service = self._get_llm_service()
        extractor_node = ExtractorNode(
            llm_service=llm_service, schema_extractor=self.schema_extractor
        )

        if tracer:
            traced_extractor = TraceNodeMiddleware(
                inner_node=extractor_node, tracer=tracer, step_name="DATA_EXTRACTION"
            )
            graph.add_node(node_name, traced_extractor.as_langgraph_node())
        else:
            graph.add_node(node_name, extractor_node.as_langgraph_node())

        if self.ocr_service:
            ocr_node_name = "zerox_ocr"
            ocr_node = ZeroxOCRNode(ocr_service=self.ocr_service)

            if tracer:
                traced_ocr = TraceNodeMiddleware(
                    inner_node=ocr_node, tracer=tracer, step_name="OCR"
                )
                graph.add_node(ocr_node_name, traced_ocr.as_langgraph_node())
            else:
                graph.add_node(ocr_node_name, ocr_node.as_langgraph_node())

            def route_input(state: State) -> str:
                if state.file_path:
                    return ocr_node_name
                return node_name

            graph.set_conditional_entry_point(
                route_input, {ocr_node_name: ocr_node_name, node_name: node_name}
            )
            graph.add_edge(ocr_node_name, node_name)
        else:
            graph.set_entry_point(node_name)

        graph.set_finish_point(node_name)
