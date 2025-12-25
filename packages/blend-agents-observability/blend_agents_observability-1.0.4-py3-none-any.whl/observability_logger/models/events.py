"""
Event models for observability logger.

This module defines the event schemas that match the Lambda ingestion pipeline's
expected format. All events are validated before emission.
"""

from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field, field_validator


# Event type literals
EventType = Literal['trace_updated', 'node_created', 'node_updated', 'node_completed', 'edge_created', 'multi_step']
NodeType = Literal['agent', 'miscellaneous', 'router', 'parallel']
NodeStatus = Literal['started', 'completed', 'failed']
TraceStatus = Literal['running', 'completed', 'failed', 'partial']


class TraceUpdatedData(BaseModel):
    """
    Data for trace_updated event.
    
    This model supports both trace creation (upsert) and updates:
    - For creation: include workflow_id, title, and optionally parent_trace_id
    - For updates: include status and optionally final_output
    """
    status: TraceStatus = Field(..., description="Trace status")
    workflow_id: Optional[str] = Field(None, description="Workflow identifier (for upsert/creation)")
    title: Optional[str] = Field(None, description="Human-readable trace title (for upsert/creation)")
    parent_trace_id: Optional[str] = Field(None, description="Parent trace ID for subtraces")
    final_output: Optional[Dict[str, Any]] = Field(None, description="Final output payload")


class NodeCreatedData(BaseModel):
    """Data for node_created event."""
    id: str = Field(..., description="Node identifier")
    type: NodeType = Field(..., description="Node type")
    name: str = Field(..., description="Node name")
    description: str = Field(default="", description="Node description")
    status: NodeStatus = Field(default="started", description="Initial node status")
    payload: Optional[Dict[str, Any]] = Field(None, description="Node payload (for auto-completed nodes)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Node metadata (for auto-completed nodes)")
    parent_node_id: Optional[str] = Field(None, description="Parent node ID for nested structures")
    child_trace_id: Optional[str] = Field(None, description="Child trace ID for parallel nodes")


class NodeUpdatedData(BaseModel):
    """Data for node_updated event (e.g., linking child_trace_id to parallel nodes)."""
    id: str = Field(..., description="Node identifier")
    child_trace_id: Optional[str] = Field(None, description="Child trace ID for parallel nodes")


class NodeCompletedData(BaseModel):
    """Data for node_completed event."""
    id: str = Field(..., description="Node identifier")
    status: NodeStatus = Field(..., description="Node completion status")
    payload: Optional[Dict[str, Any]] = Field(None, description="Node payload")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Node metadata")
    child_trace_id: Optional[str] = Field(None, description="Child trace ID for parallel nodes (DynamoDB only)")

    @field_validator('status')
    @classmethod
    def validate_completion_status(cls, v: str) -> str:
        """Validate that status is completed or failed (not started)."""
        if v == 'started':
            raise ValueError("node_completed status cannot be 'started', must be 'completed' or 'failed'")
        return v


class EdgeCreatedData(BaseModel):
    """Data for edge_created event."""
    id: str = Field(..., description="Edge identifier")
    source_node_id: str = Field(..., description="Source node ID")
    target_node_id: str = Field(..., description="Target node ID")


class ObservabilityEvent(BaseModel):
    """
    Base event model for all observability events.

    This matches the Lambda ingestion pipeline's expected schema.
    """
    event_type: EventType = Field(..., description="Type of event")
    timestamp: int = Field(..., description="Unix timestamp in milliseconds")
    trace_id: str = Field(..., description="Trace identifier")
    data: Dict[str, Any] = Field(..., description="Event-specific data")

    @field_validator('timestamp')
    @classmethod
    def validate_timestamp(cls, v: int) -> int:
        """Validate that timestamp is a positive integer."""
        if v <= 0:
            raise ValueError("timestamp must be a positive integer")
        return v
