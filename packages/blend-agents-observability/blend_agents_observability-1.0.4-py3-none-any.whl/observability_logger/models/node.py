"""
Node models for observability logger.

This module defines the Node base class and all node type subclasses:
- MiscellaneousNode
- ParallelNode
- RouterNode
- AgentNode
"""

import json
import logging
from typing import Optional, Dict, Any, List, TYPE_CHECKING, Union

from ..core.emitter import get_emitter
from ..core.utils import get_current_timestamp_ms
from ..core.logging_manager import get_logging_manager
from ..models.events import (
    EventType,
    ObservabilityEvent,
    NodeCreatedData,
    NodeUpdatedData,
    NodeCompletedData,
    NodeType,
    NodeStatus
)

if TYPE_CHECKING:
    from .agent_logger import AgentLogger

logger = logging.getLogger(__name__)


class Node:
    """
    Abstract base class for all node types in the observability graph.

    Node provides the common lifecycle management, event emission, and state tracking
    for all node types (agent, router, parallel, miscellaneous).

    When instantiated directly (not through subclasses), Node acts as a lightweight
    container for node_id and basic properties without emitting any events. This
    allows creating Node instances purely for edge creation purposes.

    Attributes:
        trace_id: ID of the parent trace
        node_id: Unique identifier for this node
        node_type: Type of node ('agent', 'router', 'parallel', 'miscellaneous')
        name: Human-readable name for the node
        description: Optional description of the node's purpose
        parent_node_id: Optional parent node ID for hierarchical structures
        auto_complete: If True, node is completed on creation

    Properties:
        status: Current node status ('started', 'completed', 'failed')
        is_created: Whether node_created event has been emitted
        is_completed: Whether node_completed event has been emitted

    Note:
        - When instantiated directly: No events are emitted, useful for edge creation
        - When instantiated through subclasses: Full event emission functionality
        - Use concrete implementations for full observability: MiscellaneousNode, 
          ParallelNode, RouterNode, or AgentNode
    """

    def __init__(
        self,
        trace_id: str,
        node_id: str,
        node_type: NodeType = 'miscellaneous',
        name: str = "",
        description: str = "",
        parent_node_id: Optional[str] = None,
        auto_complete: bool = False,
        _enable_events: bool = False
    ):
        """
        Initialize a new node.

        Args:
            trace_id: ID of the parent trace
            node_id: Unique identifier for this node
            node_type: Type of node ('agent', 'router', 'parallel', 'miscellaneous')
            name: Human-readable name for the node
            description: Optional description of the node's purpose
            parent_node_id: Optional parent node ID for nested structures
            auto_complete: If True, node is completed during creation
            _enable_events: Internal flag to control event emission
                - None (default): Auto-detect based on class type
                - True: Force enable events (used by subclasses)
                - False: Force disable events (for direct Node instantiation)
        """
        self.trace_id = trace_id
        self.node_id = node_id
        self.node_type: NodeType = node_type
        self.name = name or f"Node {node_id}"
        self.description = description
        self.parent_node_id = parent_node_id
        self.auto_complete = auto_complete

        # Determine if events should be enabled
        if _enable_events is None:
            # Auto-detect: enable events only for subclasses, not direct Node instances
            self._events_enabled = type(self) != Node
        else:
            self._events_enabled = _enable_events

        # Initialize emitter and state only if events are enabled
        if self._events_enabled:
            self._emitter = get_emitter()
            self._created = False
            self._completed = False
            self._status: NodeStatus = "started"
        else:
            # Lightweight mode: no emitter, minimal state
            self._emitter = None
            self._created = False
            self._completed = False
            self._status: NodeStatus = "started"
            logger.debug(f"Created lightweight Node {node_id} (no events)")

    def _emit_created(
        self,
        payload: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        status: NodeStatus = "started",
        child_trace_id: Optional[str] = None,
        event_type: EventType = 'node_created'
    ) -> bool:
        """
        Emit a node creation event to Kinesis.

        This internal method sends the node creation event with all node data.
        For auto-complete nodes, the status can be set to 'completed' directly.

        Args:
            payload: Optional payload data to store in S3
            metadata: Optional metadata to include in the event
            status: Initial node status ('started', 'completed', 'failed')
            child_trace_id: Optional child trace ID for parallel nodes
            event_type: Type of event to emit (default: 'node_created')
                Can be 'node_created', 'node_updated', or other valid EventType

        Returns:
            True if the event was emitted successfully, False otherwise
        """
        # Skip emission if events are disabled
        if not self._events_enabled or self._emitter is None:
            logger.debug(f"Skipping event emission for Node {self.node_id} (events disabled)")
            return False

        if self._created:
            logger.warning(f"Node {self.node_id} already created. Skipping.")
            return False

        data = NodeCreatedData(
            id=self.node_id,
            type=self.node_type,
            name=self.name,
            description=self.description,
            status=status,
            payload=payload,
            metadata=metadata,
            parent_node_id=self.parent_node_id,
            child_trace_id=child_trace_id
        )

        event = ObservabilityEvent(
            event_type=event_type,
            timestamp=get_current_timestamp_ms(),
            trace_id=self.trace_id,
            data=data.model_dump(exclude_none=True)
        )

        success = self._emitter.emit(event)
        if success:
            self._created = True
            self._status = status
            if status in ['completed', 'failed']:
                self._completed = True
            logger.info(f"Created node: {self.node_id} ({self.node_type}) with event_type={event_type}")
            
            # Log node creation with enhanced logging strategy (Requirements 3.1)
            try:
                logging_manager = get_logging_manager()
                logging_manager.log_node_created(self)
            except Exception as e:
                # Fallback to standard logging if enhanced logging fails
                logger.debug(f"Enhanced logging failed for node creation: {e}")
        return success

    def complete(
        self,
        status: NodeStatus = "completed",
        payload: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        child_trace_id: Optional[str] = None
    ) -> bool:
        """
        Complete the node and emit the node_completed event.

        This method finalizes the node execution by emitting a node_completed
        event to Kinesis. The node must have been created first.

        Args:
            status: Final node status ('completed' or 'failed')
            payload: Optional payload data to store in S3
            metadata: Optional metadata to include in the event
            child_trace_id: Optional child trace ID for parallel nodes

        Returns:
            True if the event was emitted successfully, False otherwise

        Raises:
            Logs warning if node not created or already completed.
            Logs error if status is 'started' (invalid for completion).
        """
        # Skip emission if events are disabled
        if not self._events_enabled or self._emitter is None:
            logger.debug(f"Skipping completion event for Node {self.node_id} (events disabled)")
            self._completed = True
            self._status = status
            return False

        if not self._created:
            logger.warning(f"Node {self.node_id} not created yet.")
            return False

        if self._completed:
            logger.warning(f"Node {self.node_id} already completed. Skipping.")
            return False

        if status == 'started':
            logger.error("Cannot complete node with status 'started'.")
            return False

        data = NodeCompletedData(
            id=self.node_id,
            status=status,
            payload=payload,
            metadata=metadata,
            child_trace_id=child_trace_id
        )

        event = ObservabilityEvent(
            event_type='node_completed',
            timestamp=get_current_timestamp_ms(),
            trace_id=self.trace_id,
            data=data.model_dump(exclude_none=True)
        )

        success = self._emitter.emit(event)
        if success:
            self._completed = True
            self._status = status
            logger.info(f"Completed node: {self.node_id} with status {status}")
            
            # Log node completion with enhanced logging strategy (Requirements 3.2)
            try:
                logging_manager = get_logging_manager()
                logging_manager.log_node_completed(self)
            except Exception as e:
                # Fallback to standard logging if enhanced logging fails
                logger.debug(f"Enhanced logging failed for node completion: {e}")
        return success

    def create(self, event_type: EventType = 'node_created') -> bool:
        """
        Create the node by emitting a creation event.

        For direct Node instances (events disabled), this method does nothing
        and returns False. For subclass instances, this method must be implemented.

        Args:
            event_type: Type of event to emit (default: 'node_created')

        Returns:
            True if the event was emitted successfully, False otherwise
        """
        if not self._events_enabled:
            logger.debug(f"Skipping create() for Node {self.node_id} (events disabled)")
            return False
        
        # For direct Node instances that somehow have events enabled,
        # provide a basic implementation
        return self._emit_created(status='started', event_type=event_type)

    @property
    def status(self) -> NodeStatus:
        """Get the current node status ('started', 'completed', or 'failed')."""
        return self._status

    @property
    def is_created(self) -> bool:
        """Check if the node has been created (node_created event emitted)."""
        return self._created

    @property
    def is_completed(self) -> bool:
        """Check if the node has been completed (node_completed event emitted)."""
        return self._completed

    @property
    def events_enabled(self) -> bool:
        """Check if event emission is enabled for this node."""
        return self._events_enabled


class MiscellaneousNode(Node):
    """
    Node for general operations like tool calls, validation, or output formatting.

    MiscellaneousNode is auto-completed by default, meaning it emits both
    node_created and node_completed events during creation. This makes it
    ideal for simple, synchronous operations.

    The payload structure follows the schema:
        {
            "node_id": "node_xxx",
            "type": "miscellaneous",
            "content": "Operation result or description",
            "metadata": {...},
            "error": null
        }

    Attributes:
        content: Text content or result of the operation
        metadata: Additional context about the operation

    Example:
        >>> output = MiscellaneousNode(
        ...     trace_id=trace_id,
        ...     node_id="node_123",
        ...     name="Final Output",
        ...     content="Processed successfully",
        ...     metadata={"items_processed": 100}
        ... )
        >>> output.create()  # Auto-completes
    """

    def __init__(
        self,
        trace_id: str,
        node_id: str,
        name: str,
        description: str = "",
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        parent_node_id: Optional[str] = None,
        auto_complete: bool = True
    ):
        """
        Initialize a MiscellaneousNode.

        Args:
            trace_id: ID of the parent trace
            node_id: Unique identifier for this node
            name: Human-readable name for the node
            description: Optional description of the operation
            content: Optional content/result of the operation
            metadata: Optional metadata dict for additional context
            parent_node_id: Optional parent node ID
            auto_complete: If True (default), node completes on creation
        """
        super().__init__(
            trace_id=trace_id,
            node_id=node_id,
            node_type='miscellaneous',
            name=name,
            description=description,
            parent_node_id=parent_node_id,
            auto_complete=auto_complete,
            _enable_events=True  # Ensure events are enabled for subclasses
        )
        self.content = content
        self.metadata = metadata

    def create(self, event_type: EventType = 'node_created') -> bool:
        """
        Create and optionally auto-complete the node.

        If auto_complete is True (default), this method emits both
        node_created and node_completed events with status='completed'.

        Args:
            event_type: Type of event to emit (default: 'node_created')

        Returns:
            True if the event(s) were emitted successfully, False otherwise
        """
        if self.auto_complete:
            # Build payload according to docs/data/README.md schema
            payload = {
                'node_id': self.node_id,
                'type': 'miscellaneous',
                'content': self.content,
                'error': None
            }
            if self.metadata:
                payload['metadata'] = self.metadata
            return self._emit_created(
                status='completed',
                payload=payload,
                metadata=None,  # metadata is now inside payload
                event_type=event_type
            )
        return self._emit_created(status='started', event_type=event_type)


class ParallelNode(Node):
    """
    Node for concurrent execution branches.

    ParallelNode represents operations where sub-workflows execute concurrently.
    Each parallel node can link to a child trace via the subTrace() method,
    enabling hierarchical trace structures.

    The payload structure follows the schema:
        {
            "node_id": "node_parallel_xxx",
            "type": "parallel",
            "content": "Description of parallel execution",
            "metadata": {
                "parallel_count": 5,
                "max_concurrent": 10,
                "total_execution_time_ms": 12500,
                "avg_execution_time_ms": 2500
            }
        }

    Attributes:
        content: Description of the parallel operation
        metadata: Execution metrics and metadata

    Example:
        >>> parallel = ParallelNode(
        ...     trace_id=parent_trace_id,
        ...     node_id="node_parallel_123",
        ...     name="Process Items",
        ...     metadata={"parallel_count": 3}
        ... )
        >>> parallel.create()
        >>> parallel.subTrace(child_logger)  # Link child trace
        >>> # ... child trace executes ...
        >>> parallel.complete(status="completed")
    """

    def __init__(
        self,
        trace_id: str,
        node_id: str,
        name: str,
        description: str = "",
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        parent_node_id: Optional[str] = None
    ):
        """
        Initialize a ParallelNode.

        Args:
            trace_id: ID of the parent trace
            node_id: Unique identifier for this node
            name: Human-readable name for the node
            description: Optional description of the parallel operation
            content: Optional content describing the operation
            metadata: Optional metadata (e.g., parallel_count, max_concurrent)
            parent_node_id: Optional parent node ID
        """
        super().__init__(
            trace_id=trace_id,
            node_id=node_id,
            node_type='parallel',
            name=name,
            description=description,
            parent_node_id=parent_node_id,
            auto_complete=False,
            _enable_events=True  # Ensure events are enabled for subclasses
        )
        self.content = content
        self.metadata = metadata
        self._child_trace_id: Optional[str] = None

    def create(self, event_type: EventType = 'node_created') -> bool:
        """
        Create the parallel node with status='started'.

        Args:
            event_type: Type of event to emit (default: 'node_created')

        Returns:
            True if the event was emitted successfully, False otherwise
        """
        return self._emit_created(status='started', event_type=event_type)

    def subTrace(self, child_logger: 'AgentLogger') -> 'AgentLogger':
        """
        Associate a child trace with this parallel node.

        Emits a node_updated event to link the child_trace_id in DynamoDB.
        The child trace will have parent_trace_id set to this node's trace_id.

        Args:
            child_logger: AgentLogger instance for the child trace

        Returns:
            The child_logger for chaining
        """
        if not self._created:
            logger.warning(f"Parallel node {self.node_id} not created yet.")
            return child_logger

        if self._child_trace_id == child_logger.trace_id:
            logger.warning(f"Child trace {child_logger.trace_id} already associated.")
            return child_logger

        # Set parent relationship on child logger
        child_logger._parent_trace_id = self.trace_id
        self._child_trace_id = child_logger.trace_id

        # Skip emission if events are disabled
        if not self._events_enabled or self._emitter is None:
            logger.debug(f"Skipping node_updated emission for ParallelNode {self.node_id} (events disabled)")
            return child_logger

        # Emit node_updated event to update DynamoDB with child_trace_id
        data = NodeUpdatedData(
            id=self.node_id,
            child_trace_id=child_logger.trace_id
        )

        event = ObservabilityEvent(
            event_type='node_updated',
            timestamp=get_current_timestamp_ms(),
            trace_id=self.trace_id,
            data=data.model_dump(exclude_none=True)
        )

        success = self._emitter.emit(event)
        if success:
            logger.info(f"Associated child trace {child_logger.trace_id} with parallel node {self.node_id}")
        else:
            logger.error(f"Failed to emit node_updated for parallel node {self.node_id}")

        return child_logger

    def complete(
        self,
        status: NodeStatus = "completed",
        payload: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        child_trace_id: Optional[str] = None,
        execution_time_ms: Optional[int] = None
    ) -> bool:
        """
        Complete the parallel node.

        Args:
            status: Node status (completed, failed)
            payload: Custom payload (if None, auto-constructed following schema)
            metadata: Execution metrics and metadata
            child_trace_id: Optional child trace ID (defaults to internal value)
            execution_time_ms: Total execution time in milliseconds

        Returns:
            True if completion succeeded
        """
        # Build payload according to docs/data/README.md schema
        if payload is None:
            final_metadata = metadata or self.metadata or {}

            # Add execution time if provided
            if execution_time_ms is not None:
                final_metadata = {**final_metadata, 'total_execution_time_ms': execution_time_ms}
                if 'parallel_count' in final_metadata:
                    count = final_metadata.get('parallel_count', 1)
                    avg_time = execution_time_ms // count if count > 0 else 0
                    final_metadata['avg_execution_time_ms'] = avg_time

            payload = {
                'node_id': self.node_id,
                'type': 'parallel',
                'content': self.content
            }

            if final_metadata:
                payload['metadata'] = final_metadata

        # child_trace_id goes to event (for DynamoDB), NOT in payload (S3)
        # Use provided child_trace_id or fall back to internal value
        final_child_trace_id = child_trace_id if child_trace_id is not None else self._child_trace_id
        return super().complete(
            status=status,
            payload=payload,
            metadata=None,
            child_trace_id=final_child_trace_id
        )


class RouterNode(Node):
    """
    Node for routing/branching decisions in the workflow.

    RouterNode represents decision points where the workflow determines
    which path to take. Typically used as entry points or branch conditions.

    RouterNode is auto-completed by default, meaning it emits both
    node_created and node_completed events during creation. This makes it
    ideal for routing/decision points that don't require explicit completion,
    reducing verbosity in agentic workflow code.

    The payload structure follows the schema:
        {
            "node_id": "node_router_xxx",
            "type": "router",
            "content": "Routing decision description",
            "metadata": {...}
        }

    Attributes:
        content: Description of the routing decision
        metadata: Additional routing context

    Example:
        >>> router = RouterNode(
        ...     trace_id=trace_id,
        ...     node_id="node_router_123",
        ...     name="Workflow Router",
        ...     metadata={"input_length": 150}
        ... )
        >>> router.create()  # Auto-completes, no need to call complete()
    """

    def __init__(
        self,
        trace_id: str,
        node_id: str,
        name: str,
        description: str = "",
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        parent_node_id: Optional[str] = None,
        auto_complete: bool = True
    ):
        """
        Initialize a RouterNode.

        Args:
            trace_id: ID of the parent trace
            node_id: Unique identifier for this node
            name: Human-readable name for the node
            description: Optional description of the routing logic
            content: Optional content describing the decision
            metadata: Optional routing context (e.g., input_length)
            parent_node_id: Optional parent node ID
            auto_complete: If True (default), node completes on creation
        """
        super().__init__(
            trace_id=trace_id,
            node_id=node_id,
            node_type='router',
            name=name,
            description=description,
            parent_node_id=parent_node_id,
            auto_complete=auto_complete,
            _enable_events=True  # Ensure events are enabled for subclasses
        )
        self.content = content
        self.metadata = metadata

    def create(self, event_type: EventType = 'node_created') -> bool:
        """
        Create and optionally auto-complete the router node.

        If auto_complete is True (default), this method emits both
        node_created and node_completed events with status='completed'.

        Args:
            event_type: Type of event to emit (default: 'node_created')

        Returns:
            True if the event(s) were emitted successfully, False otherwise
        """
        if self.auto_complete:
            # Build payload according to docs/data/README.md schema
            payload = {
                'node_id': self.node_id,
                'type': 'router',
                'content': self.content,
            }
            if self.metadata:
                payload['metadata'] = self.metadata
            return self._emit_created(
                status='completed',
                payload=payload,
                metadata=None,  # metadata is now inside payload
                event_type=event_type
            )
        return self._emit_created(status='started', metadata=self.metadata, event_type=event_type)

    def complete(
        self,
        status: NodeStatus = "completed",
        payload: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        child_trace_id: Optional[str] = None
    ) -> bool:
        """
        Complete the router node (only needed if auto_complete=False).

        Args:
            status: Final node status ('completed' or 'failed')
            payload: Custom payload (if None, auto-constructed)
            metadata: Optional metadata to include in payload

        Returns:
            True if the event was emitted successfully, False otherwise

        Note:
            When auto_complete=True (default), this method is not needed
            as the node is completed during create().
        """
        # Build payload according to docs/data/README.md schema
        if payload is None:
            payload = {
                'node_id': self.node_id,
                'type': 'router',
                'content': self.content,
            }
            final_metadata = metadata or self.metadata
            if final_metadata:
                payload['metadata'] = final_metadata
        return super().complete(
            status=status,
            payload=payload,
            metadata=None,  # metadata is now inside payload
            child_trace_id=child_trace_id
        )



class AgentNode(Node):
    """
    Node for AI agent execution with real-time event capture.

    AgentNode captures agent input/output, step-by-step execution (text reasoning
    and tool use), and performance metrics. It implements the callback handler
    interface for Strands Agents, enabling real-time capture of streaming events.

    The payload structure follows the schema:
        {
            "node_id": "node_agent_xxx",
            "type": "agent",
            "input": "User prompt",
            "output": "Agent response",
            "execution_time_ms": 1500,
            "steps": [
                {"type": "text", "content": "Reasoning...", "timestamp": 1700000000000},
                {"type": "tool_use", "name": "tool_name", "input": {...}, "output": {...}}
            ],
            "token_usage": {"input_tokens": 100, "output_tokens": 50, "total_tokens": 150},
            "error": null
        }

    Attributes:
        metadata: Additional agent context

    Example:
        >>> agent_node = logger.strands.agent(
        ...     node_id=generate_id("node_"),
        ...     config={"name": "Assistant", "description": "Helpful agent"}
        ... )
        >>> agent_node.set_input(prompt)
        >>> result = agent(prompt, callback_handler=agent_node)
        >>> agent_node.complete(result=result)

    Note:
        Use as callback_handler in Strands Agent calls to capture streaming events.
    """

    def __init__(
        self,
        trace_id: str,
        node_id: str,
        name: str,
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        parent_node_id: Optional[str] = None
    ):
        """
        Initialize an AgentNode.

        Args:
            trace_id: ID of the parent trace
            node_id: Unique identifier for this node
            name: Human-readable name for the agent
            description: Optional description of the agent's purpose
            metadata: Optional metadata (e.g., tools, model config)
            parent_node_id: Optional parent node ID
        """
        super().__init__(
            trace_id=trace_id,
            node_id=node_id,
            node_type='agent',
            name=name,
            description=description,
            parent_node_id=parent_node_id,
            auto_complete=False,
            _enable_events=True  # Ensure events are enabled for subclasses
        )
        self.metadata = metadata

        # Execution tracking
        self._input: Optional[str] = None
        self._output: Optional[str] = None
        self._steps: List[Dict[str, Any]] = []
        self._start_time: Optional[int] = None
        self._error: Optional[str] = None
        self._error_type: str = 'Error'
        self._token_usage: Optional[Dict[str, int]] = None

        # Streaming text buffer
        self._text_buffer: str = ""
        self._text_buffer_start_time: Optional[int] = None

    def create(self, event_type: EventType = 'node_created') -> bool:
        """
        Create the agent node and start execution timing.

        Args:
            event_type: Type of event to emit (default: 'node_created')

        Returns:
            True if the event was emitted successfully, False otherwise
        """
        self._start_time = get_current_timestamp_ms()
        return self._emit_created(status='started', metadata=self.metadata, event_type=event_type)

    def set_input(self, input_text: str) -> None:
        """
        Set the agent input prompt.

        Call this before executing the agent to record what was sent.

        Args:
            input_text: The prompt or input given to the agent
        """
        self._input = input_text

    def set_output(self, output_text: str) -> None:
        """
        Set the agent output manually.

        Note: When using complete(result=result), output is extracted automatically.
        Use this method for custom output handling.

        Args:
            output_text: The agent's response text
        """
        self._output = output_text

    def set_error(self, error: Union[str, Exception]) -> None:
        """
        Set error information for failed execution.

        Args:
            error: Error message string or Exception object.
                If Exception, the type name is extracted automatically.
        """
        if isinstance(error, Exception):
            self._error = str(error)
            self._error_type = type(error).__name__
        else:
            self._error = error
            self._error_type = 'Error'

    def set_token_usage(self, input_tokens: int, output_tokens: int, total_tokens: Optional[int] = None) -> None:
        """
        Set token usage metrics manually.

        Note: When using complete(result=result), token usage is extracted
        automatically from result.metrics if available.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            total_tokens: Total tokens (calculated if not provided)
        """
        self._token_usage = {
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': total_tokens or (input_tokens + output_tokens)
        }

    def _flush_text_buffer(self) -> None:
        """Flush accumulated text buffer to steps as a text step."""
        if self._text_buffer.strip():
            step = {
                'type': 'text',
                'content': self._text_buffer,
                'timestamp': self._text_buffer_start_time or get_current_timestamp_ms()
            }
            self._steps.append(step)
            logger.debug(f"Flushed text buffer ({len(self._text_buffer)} chars)")
        self._text_buffer = ""
        self._text_buffer_start_time = None

    def _parse_tool_input(self, tool_input: Any) -> Dict[str, Any]:
        """Parse tool input to ensure it's a dict."""
        if not tool_input or tool_input == "":
            return {}
        if isinstance(tool_input, dict):
            return tool_input
        if isinstance(tool_input, str):
            try:
                parsed = json.loads(tool_input)
                return parsed if isinstance(parsed, dict) else {"value": parsed}
            except (json.JSONDecodeError, TypeError):
                return {"raw": tool_input}
        return {"value": tool_input}

    def _parse_tool_output(self, output_text: str) -> Dict[str, Any]:
        """Parse tool output to ensure it's a dict."""
        try:
            parsed = json.loads(output_text)
            return parsed if isinstance(parsed, dict) else {"result": parsed}
        except (json.JSONDecodeError, TypeError):
            return {"result": output_text}

    def __call__(self, **kwargs) -> None:
        """
        Callback handler for Strands Agent streaming events.

        Pass this AgentNode as callback_handler to capture real-time events
        from agent execution. Handles the following event types:

        - init_event_loop: Initializes timing
        - data: Streaming text chunks (accumulated in buffer)
        - current_tool_use: Tool invocation events
        - message: Complete message events (assistant/user roles)
        - tool_result: Tool execution results
        - complete: Final completion signal

        Example:
            >>> agent_node.set_input(prompt)
            >>> result = agent(prompt, callback_handler=agent_node)
            >>> # Steps are automatically captured during execution

        Args:
            **kwargs: Event data from Strands Agent streaming
        """
        timestamp = get_current_timestamp_ms()

        # Init event
        if kwargs.get("init_event_loop", False):
            if not self._start_time:
                self._start_time = timestamp
            return

        # Text data (streaming chunks)
        if "data" in kwargs:
            data = kwargs["data"]
            if data:
                if not self._text_buffer_start_time:
                    self._text_buffer_start_time = timestamp
                self._text_buffer += data

        # Tool use events
        if "current_tool_use" in kwargs:
            tool_use = kwargs["current_tool_use"]
            tool_name = tool_use.get("name")
            if tool_name:
                self._flush_text_buffer()
                tool_use_id = tool_use.get("toolUseId")
                
                # Check for existing step
                existing = next(
                    (s for s in self._steps if s.get("type") == "tool_use" and s.get("tool_use_id") == tool_use_id),
                    None
                )
                
                tool_input = self._parse_tool_input(tool_use.get("input"))
                
                if existing:
                    if tool_input and not existing.get('input'):
                        existing['input'] = tool_input
                else:
                    self._steps.append({
                        'type': 'tool_use',
                        'name': tool_name,
                        'description': f"Tool: {tool_name}",
                        'tool_use_id': tool_use_id,
                        'input': tool_input,
                        'output': None,
                        'timestamp': timestamp
                    })

        # Message events (complete tool data)
        if "message" in kwargs:
            message = kwargs["message"]
            if message.get("role") == "assistant":
                self._flush_text_buffer()
                for block in message.get("content", []):
                    if "toolUse" in block:
                        tool_use = block["toolUse"]
                        tool_use_id = tool_use.get("toolUseId")
                        complete_input = self._parse_tool_input(tool_use.get("input"))
                        for step in self._steps:
                            if step.get("type") == "tool_use" and step.get("tool_use_id") == tool_use_id:
                                step["input"] = complete_input
                                break

            elif message.get("role") == "user":
                for block in message.get("content", []):
                    if "toolResult" in block:
                        tool_result = block["toolResult"]
                        tool_use_id = tool_result.get("toolUseId")
                        output_parts = []
                        for result_block in tool_result.get("content", []):
                            if "text" in result_block:
                                output_parts.append(result_block["text"])
                        output_data = self._parse_tool_output("".join(output_parts))
                        for step in self._steps:
                            if step.get("type") == "tool_use" and step.get("tool_use_id") == tool_use_id:
                                step["output"] = output_data
                                break

        # Tool result events
        if "tool_result" in kwargs:
            tool_result = kwargs["tool_result"]
            tool_use_id = tool_result.get("toolUseId")
            output_parts = []
            for block in tool_result.get("content", []):
                if "text" in block:
                    output_parts.append(block["text"])
            output_data = self._parse_tool_output("".join(output_parts))
            for step in reversed(self._steps):
                if step.get("type") == "tool_use" and step.get("tool_use_id") == tool_use_id:
                    step["output"] = output_data
                    break

        # Completion event
        if kwargs.get("complete", False):
            self._flush_text_buffer()

    def complete(
        self,
        status: NodeStatus = "completed",
        payload: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        child_trace_id: Optional[str] = None,
        result: Optional[Any] = None,
        error: Optional[Exception] = None,
        skipped: bool = False
    ) -> bool:
        """
        Complete the agent node.

        Supports three modes:
        1. With result: Extracts data from agent execution result
        2. With skipped=True: Marks as completed without agent execution
        3. With payload: Uses custom payload directly

        Args:
            status: Node status (completed, failed)
            payload: Custom payload (if None, will be auto-constructed)
            metadata: Custom metadata
            child_trace_id: Optional child trace ID (not used by AgentNode)
            result: Agent execution result (extracts output, tokens, etc.)
            error: Exception if execution failed
            skipped: True if agent was skipped/unnecessary

        Returns:
            True if completion succeeded
        """
        try:
            # Mode 1: Process result from agent execution
            if result is not None:
                self._flush_text_buffer()

                # Extract output
                raw_output = getattr(result, 'message', None)
                if raw_output is None:
                    self._output = str(result)
                elif isinstance(raw_output, str):
                    self._output = raw_output
                elif isinstance(raw_output, dict):
                    content = raw_output.get('content', [])
                    if isinstance(content, list):
                        text_parts = [b['text'] for b in content if isinstance(b, dict) and 'text' in b]
                        self._output = '\n'.join(text_parts) if text_parts else str(raw_output)
                    else:
                        self._output = str(raw_output)
                else:
                    self._output = str(raw_output)

                # Extract token usage from EventLoopMetrics.accumulated_usage
                # Strands stores tokens in accumulated_usage dict with camelCase keys
                # See: https://strandsagents.com/latest/documentation/docs/user-guide/observability-evaluation/metrics/
                if hasattr(result, 'metrics') and result.metrics:
                    metrics = result.metrics
                    try:
                        usage = getattr(metrics, 'accumulated_usage', None)
                        if usage and isinstance(usage, dict):
                            input_tokens = usage.get('inputTokens', 0)
                            output_tokens = usage.get('outputTokens', 0)
                            total_tokens = usage.get('totalTokens', 0)
                            if input_tokens or output_tokens:
                                self._token_usage = {
                                    'input_tokens': input_tokens,
                                    'output_tokens': output_tokens,
                                    'total_tokens': total_tokens or (input_tokens + output_tokens)
                                }
                    except Exception:
                        pass

                # Determine status based on error
                if error:
                    self._error = str(error)
                    self._error_type = type(error).__name__
                    status = "failed"
                else:
                    status = "completed"

            # Mode 2: Agent was skipped/unnecessary
            elif skipped:
                self._flush_text_buffer()
                status = status or "completed"

            # Mode 3: No result or skipped - use existing node data
            else:
                self._flush_text_buffer()
                if error:
                    self._error = str(error)
                    self._error_type = type(error).__name__

            # Build payload if not provided
            if payload is None:
                execution_time_ms = None
                if self._start_time is not None:
                    execution_time_ms = get_current_timestamp_ms() - self._start_time

                error_obj = None
                if self._error:
                    error_obj = {
                        'error_message': self._error,
                        'error_type': self._error_type,
                        'stack_trace': None
                    }

                payload = {
                    'node_id': self.node_id,
                    'type': 'agent',
                    'input': self._input,
                    'output': self._output,
                    'execution_time_ms': execution_time_ms,
                    'steps': self._steps if not skipped else [],
                    'error': error_obj
                }

                if self._token_usage:
                    payload['token_usage'] = self._token_usage

                # Include metadata inside payload if provided
                if metadata or self.metadata:
                    payload['metadata'] = metadata or self.metadata

            return super().complete(status=status, payload=payload, metadata=None)

        except Exception as e:
            logger.error(f"Error completing node {self.node_id}: {e}")
            self._error = str(e)
            return super().complete(status="failed", payload=None, metadata=None)

