"""Main AgentLogger class for observability logger.

This module provides the primary user-facing API for instrumenting agent
workflows. It defines the `AgentLogger` class, which acts as the main entry
point for creating traces, nodes, and edges.

Example:
    >>> from observability_logger import AgentLogger, generate_id
    >>>
    >>> logger = AgentLogger(trace_id=generate_id("trace_"))
    >>> node1 = logger.miscellaneous("node_1", {"name": "Start"})
    >>> node2 = logger.miscellaneous("node_2", {"name": "End"})
    >>> logger.edge(node1, node2)
    >>> logger.end()
"""

import logging
from typing import Optional, Dict, Any

from ..core.tracer import TraceManager, TraceStatus
from ..core.utils import generate_id, get_current_timestamp_ms
from ..core.emitter import get_emitter
from ..core.logging_manager import LoggingManager, get_logging_manager
from ..config.logging_config import LoggingLevel
from ..models.events import ObservabilityEvent, EdgeCreatedData, EventType
from ..models.node import (
    MiscellaneousNode,
    ParallelNode,
    RouterNode,
    AgentNode,
    Node,
    NodeType,
)

logger = logging.getLogger(__name__)


class Edge:
    """Represents a directed edge between two nodes in the execution graph.

    Edges define the flow of execution between nodes. They are automatically
    created and their corresponding event is emitted upon instantiation.

    Attributes:
        trace_id (str): The ID of the trace this edge belongs to.
        source_node (Node): The origin node of the edge.
        target_node (Node): The destination node of the edge.
        edge_id (str): A unique identifier for this edge.
    """

    def __init__(
        self,
        trace_id: str,
        source_node: Node,
        target_node: Node,
        edge_id: Optional[str] = None,
    ):
        """Initializes and creates an edge between two nodes.

        Args:
            trace_id: The ID of the parent trace.
            source_node: The node where the edge originates.
            target_node: The node where the edge points to.
            edge_id: An optional custom edge ID. If not provided, one is
                auto-generated with an 'edge_' prefix.
        """
        self.trace_id = trace_id
        self.source_node = source_node
        self.target_node = target_node
        self.edge_id = edge_id or generate_id("edge_")
        self._emitter = get_emitter()
        self._logging_manager = get_logging_manager()
        self._created = False
        self.create()

    def create(self) -> bool:
        """Emits the `edge_created` event to Kinesis.

        This method is called automatically during `__init__`. Calling it again
        will log a warning and have no effect.

        Returns:
            True if the event was emitted successfully, False otherwise.
        """
        if self._created:
            logger.warning(f"Edge {self.edge_id} already created. Skipping.")
            return False

        data = EdgeCreatedData(
            id=self.edge_id,
            source_node_id=self.source_node.node_id,
            target_node_id=self.target_node.node_id,
        )

        event = ObservabilityEvent(
            event_type="edge_created",
            timestamp=get_current_timestamp_ms(),
            trace_id=self.trace_id,
            data=data.model_dump(),
        )

        success = self._emitter.emit(event)
        if success:
            self._created = True
            logger.info(
                f"Created edge: {self.edge_id} "
                f"({self.source_node.node_id} -> {self.target_node.node_id})"
            )
            # Add enhanced logging for edge creation
            try:
                self._logging_manager.log_edge_created(self)
            except Exception as e:
                # Error handling with logging override (requirement 4.5)
                self._logging_manager.log_error(
                    "Failed to log edge creation",
                    error=e,
                    context={'edge_id': self.edge_id, 'trace_id': self.trace_id}
                )
        return success


class StrandsHelper:
    """Helper class for creating Strands Agents-specific nodes.

    This class provides factory methods for creating nodes that are specific
    to the Strands Agents framework. It is accessed via the `.strands`
    attribute of an `AgentLogger` instance.

    Example:
        >>> logger = AgentLogger(trace_id="my_trace")
        >>> agent_node = logger.strands.agent("agent_1", {"name": "My Agent"})
    """

    def __init__(self, agent_logger: "AgentLogger"):
        """Initializes the StrandsHelper.

        Args:
            agent_logger: The parent `AgentLogger` instance.
        """
        self._logger = agent_logger

    def agent(
        self,
        node_id: str,
        config: Dict[str, str],
        metadata: Optional[Dict[str, Any]] = None,
        event_type: 'EventType' = 'node_created',
    ) -> AgentNode:
        """Creates an agent node for Strands Agent integration.

        This node type is designed to capture the execution details of a
        Strands Agent, including its reasoning steps and tool usage.

        Args:
            node_id: A unique identifier for the node.
            config: A dictionary containing the node's 'name' and 'description'.
            metadata: An optional dictionary for additional metadata.
            event_type: Type of event to emit on creation (default: 'node_created').
                Can be 'node_created', 'node_updated', etc.

        Returns:
            An `AgentNode` instance, ready to be instrumented.
        """
        name = config.get("name", "Unnamed Agent")
        description = config.get("description", "")

        agent_node = AgentNode(
            trace_id=self._logger.trace_id,
            node_id=node_id,
            name=name,
            description=description,
            metadata=metadata,
        )
        agent_node.create(event_type=event_type)
        return agent_node


class AgentLogger:
    """Main entry point for creating and managing observability traces.

    `AgentLogger` manages the lifecycle of a trace, from its creation to its
    completion. It provides factory methods for creating different types of
    nodes (`miscellaneous`, `parallel`, `router`) and for linking them together
    with edges.

    It also provides a `.strands` helper for creating nodes specific to the
    Strands Agents framework.

    Attributes:
        trace_id (str): The unique identifier for this trace.
        workflow_id (str): An identifier for the overarching workflow.
        title (str): A human-readable title for the trace.
        strands (StrandsHelper): A helper for creating Strands-specific nodes.
    """

    def __init__(
        self,
        trace_id: str,
        workflow_id: Optional[str] = None,
        title: Optional[str] = None,
        parent_trace_id: Optional[str] = None,
        auto_create: bool = True,
        logging_level: Optional[LoggingLevel] = None,
    ):
        """Initializes a new `AgentLogger` and optionally creates the trace.

        Args:
            trace_id: A unique identifier for this trace. It's recommended to
                use `generate_id("trace_")` to create one.
            workflow_id: An optional identifier for the workflow. If not
                provided, it defaults to the `trace_id`.
            title: An optional human-readable title. If not provided, it
                defaults to the `trace_id`.
            parent_trace_id: An optional parent trace ID for creating
                hierarchical traces, used in features like parallel execution.
            auto_create: If True (the default), automatically emits the
                `trace_created` event upon initialization. Set to False to
                defer creation.
            logging_level: Optional logging level for enhanced logging output.
                If not provided, uses configuration from environment variables.
        """
        self.trace_id = trace_id
        self.workflow_id = workflow_id or trace_id
        self.title = title or trace_id
        self._parent_trace_id = parent_trace_id

        # Initialize LoggingManager instance (requirement 1.1, 1.2)
        self._logging_manager = get_logging_manager(logging_level)

        self._trace_manager = TraceManager(
            trace_id=self.trace_id,
            workflow_id=self.workflow_id,
            title=self.title,
            parent_trace_id=self._parent_trace_id,
            assume_created=not auto_create,
        )

        if auto_create:
            self._create_trace_with_logging()

        self.strands = StrandsHelper(self)

    def _create_trace_with_logging(self) -> bool:
        """Create trace with enhanced logging for trace creation (requirement 3.4)."""
        try:
            success = self._trace_manager.create()
            if success:
                # Add enhanced logging for trace creation
                self._logging_manager.log_trace_created(
                    trace_id=self.trace_id,
                    title=self.title,
                    workflow_id=self.workflow_id,
                    parent_trace_id=self._parent_trace_id
                )
            return success
        except Exception as e:
            # Error handling with logging override (requirement 4.5)
            self._logging_manager.log_error(
                "Failed to create trace",
                error=e,
                context={ 
                    'trace_id': self.trace_id,
                    'workflow_id': self.workflow_id,
                    'title': self.title
                }
            )
            return False

    def set_logging_level(self, level: LoggingLevel) -> None:
        """
        Change the logging level dynamically during execution (requirement 1.3).
        
        Args:
            level: New LoggingLevel to apply
        """
        try:
            self._logging_manager.set_level(level)
        except Exception as e:
            # Error handling with logging override (requirement 4.5)
            self._logging_manager.log_error(
                "Failed to change logging level",
                error=e,
                context={'requested_level': level.value if level else None}
            )

    def get_logging_level(self) -> LoggingLevel:
        """
        Get the current logging level.
        
        Returns:
            Current LoggingLevel
        """
        return self._logging_manager.get_level()

    def is_logging_enabled(self) -> bool:
        """
        Check if logging is enabled (not silent).
        
        Returns:
            True if logging level is not SILENT, False otherwise
        """
        return self._logging_manager.is_enabled()

    def miscellaneous(
        self,
        node_id: str,
        config: Dict[str, str],
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        event_type: 'EventType' = 'node_created',
    ) -> MiscellaneousNode:
        """Creates a miscellaneous node for general-purpose operations.

        Miscellaneous nodes are auto-completed on creation and are ideal for
        representing simple, synchronous operations like tool calls, data
        validations, or output formatting.

        Args:
            node_id: A unique identifier for this node.
            config: A dictionary containing the node's 'name' and optional
                'description'.
            content: Optional content representing the result of the operation.
            metadata: An optional dictionary for additional context.
            event_type: Type of event to emit on creation (default: 'node_created').
                Can be 'node_created', 'node_updated', etc.

        Returns:
            A `MiscellaneousNode` instance (already completed).
        """
        name = config.get("name", "Unnamed Miscellaneous Node")
        description = config.get("description", "")

        node = MiscellaneousNode(
            trace_id=self.trace_id,
            node_id=node_id,
            name=name,
            description=description,
            content=content,
            metadata=metadata,
            auto_complete=True,
        )
        node.create(event_type=event_type)
        return node

    def parallel(
        self,
        node_id: str,
        config: Dict[str, str],
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        event_type: 'EventType' = 'node_created',
    ) -> ParallelNode:
        """Creates a parallel node to represent concurrent execution branches.

        Parallel nodes are used to model "fan-out" scenarios where multiple
        sub-workflows can execute simultaneously. Each parallel branch can be
        represented by a child trace linked to this node.

        This node must be manually completed by calling its `.complete()` method.

        Args:
            node_id: A unique identifier for this node.
            config: A dictionary containing the node's 'name' and optional
                'description'.
            content: An optional description of the parallel operation.
            metadata: Optional metadata, such as the number of parallel branches.
            event_type: Type of event to emit on creation (default: 'node_created').
                Can be 'node_created', 'node_updated', etc.

        Returns:
            A `ParallelNode` instance that requires manual completion.
        """
        name = config.get("name", "Unnamed Parallel Node")
        description = config.get("description", "")

        node = ParallelNode(
            trace_id=self.trace_id,
            node_id=node_id,
            name=name,
            description=description,
            content=content,
            metadata=metadata,
        )
        node.create(event_type=event_type)
        return node

    def router(
        self,
        node_id: str,
        config: Dict[str, str],
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        event_type: 'EventType' = 'node_created',
    ) -> RouterNode:
        """Creates a router node for representing branching decisions.

        Router nodes are auto-completed on creation and are useful for marking
        decision points in a workflow where the execution path is chosen based
        on certain conditions.

        Args:
            node_id: A unique identifier for this node.
            config: A dictionary containing the node's 'name' and optional
                'description'.
            content: An optional description of the routing decision.
            metadata: Optional metadata, such as the condition that was evaluated.
            event_type: Type of event to emit on creation (default: 'node_created').
                Can be 'node_created', 'node_updated', etc.

        Returns:
            A `RouterNode` instance (already completed).
        """
        name = config.get("name", "Unnamed Router Node")
        description = config.get("description", "")

        node = RouterNode(
            trace_id=self.trace_id,
            node_id=node_id,
            name=name,
            description=description,
            content=content,
            metadata=metadata,
            auto_complete=True,
        )
        node.create(event_type=event_type)
        return node

    def edge(self, source_node: Node, target_node: Node) -> Edge:
        """Creates a directed edge between two nodes.

        Edges define the execution flow in the workflow graph. They are
        automatically created and emitted upon calling this method.

        Args:
            source_node: The origin node (where execution comes from).
            target_node: The destination node (where execution goes to).

        Returns:
            An `Edge` instance (already created and emitted).
        """
        return Edge(
            trace_id=self.trace_id, source_node=source_node, target_node=target_node
        )

    def node(
        self,
        node_id: str,
        name: Optional[str] = None,
        node_type: NodeType = 'miscellaneous',
    ) -> Node:
        """Creates a lightweight node without emitting events.

        This method creates a basic Node instance that does NOT emit any events
        to Kinesis. It's useful for:
        - Creating nodes purely for edge creation (connecting to existing nodes)
        - Referencing nodes from other traces or external systems
        - Testing and development without triggering observability events

        The node will have `events_enabled=False` and can be used as source or
        target for edges.

        Args:
            node_id: A unique identifier for this node.
            name: Optional human-readable name for the node. Defaults to node_id.
            node_type: The type of node ('agent', 'router', 'parallel', 
                'miscellaneous'). Defaults to 'miscellaneous'.

        Returns:
            A lightweight `Node` instance (no events emitted).

        Example:
            >>> # Reference an existing node from another trace for edge creation
            >>> external_node = logger.node("existing_node_id", "External Node")
            >>> logger.edge(my_node, external_node)
        """
        return Node(
            trace_id=self.trace_id,
            node_id=node_id,
            node_type=node_type,
            name=name or node_id,
            _enable_events=False,
        )

    def end(
        self,
        status: TraceStatus = "completed",
        final_output: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Ends the trace and emits the final `trace_updated` event.

        This method should be called when the workflow has finished. It updates
        the trace with a final status and an optional output payload.

        Args:
            status: The final status of the trace. Common values are
                "completed", "failed", or "partial".
            final_output: An optional dictionary containing the final result
                or a summary of the workflow's execution.

        Returns:
            True if the update event was emitted successfully, False otherwise.
        """
        try:
            success = self._trace_manager.update(
                status=status, final_output=final_output
            )
            if success:
                # Add enhanced logging for trace completion (requirement 3.5)
                self._logging_manager.log_trace_completed(
                    trace_id=self.trace_id,
                    title=self.title,
                    status=status,
                    duration_ms=None,  # Duration calculation could be added later
                    final_output=final_output
                )
            return success
        except Exception as e:
            # Error handling with logging override (requirement 4.5)
            self._logging_manager.log_error(
                "Failed to complete trace",
                error=e,
                context={
                    'trace_id': self.trace_id,
                    'status': status,
                    'has_final_output': final_output is not None
                }
            )
            return False
