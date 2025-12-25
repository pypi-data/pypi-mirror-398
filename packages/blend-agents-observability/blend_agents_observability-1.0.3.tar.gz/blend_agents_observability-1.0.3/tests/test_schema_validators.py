

import pytest
from pydantic import ValidationError

from tests.schemas import (
    TraceSchema,
    NodeCreatedSchema,
    NodeCompletedSchema,
    EdgeCreatedSchema,
    AgentPayloadSchema,
    MiscellaneousPayloadSchema,
    RouterPayloadSchema,
    ParallelPayloadSchema,
)


class TestTraceSchema:
    """Tests for TraceSchema validator."""
    
    def test_valid_running_trace(self):
        """Test valid trace with running status."""
        data = {
            "status": "running",
            "workflow_id": "test_workflow",
            "title": "Test Trace"
        }
        schema = TraceSchema(**data)
        assert schema.status == "running"
        assert schema.workflow_id == "test_workflow"
        assert schema.title == "Test Trace"
    
    def test_valid_completed_trace(self):
        """Test valid trace with completed status."""
        data = {
            "status": "completed",
            "final_output": {"result": "success"}
        }
        schema = TraceSchema(**data)
        assert schema.status == "completed"
        assert schema.final_output == {"result": "success"}
    
    def test_valid_child_trace(self):
        """Test valid child trace with parent_trace_id."""
        data = {
            "status": "running",
            "workflow_id": "child_workflow",
            "title": "Child Trace",
            "parent_trace_id": "parent_trace_123"
        }
        schema = TraceSchema(**data)
        assert schema.parent_trace_id == "parent_trace_123"
    
    def test_invalid_status(self):
        """Test that invalid status raises ValidationError."""
        data = {
            "status": "invalid_status",
            "workflow_id": "test"
        }
        with pytest.raises(ValidationError):
            TraceSchema(**data)
    
    def test_missing_status(self):
        """Test that missing status raises ValidationError."""
        data = {
            "workflow_id": "test"
        }
        with pytest.raises(ValidationError):
            TraceSchema(**data)
    
    def test_optional_fields_handled(self):
        """Test that optional fields are handled correctly."""
        data = {"status": "running"}
        schema = TraceSchema(**data)
        assert schema.workflow_id is None
        assert schema.title is None
        assert schema.parent_trace_id is None
        assert schema.final_output is None


class TestNodeCreatedSchema:
    """Tests for NodeCreatedSchema validator."""
    
    def test_valid_agent_node(self):
        """Test valid agent node creation."""
        data = {
            "id": "node_123",
            "type": "agent",
            "name": "Test Agent",
            "description": "A test agent",
            "status": "started"
        }
        schema = NodeCreatedSchema(**data)
        assert schema.id == "node_123"
        assert schema.type == "agent"
        assert schema.status == "started"
    
    def test_valid_auto_complete_node(self):
        """Test valid auto-complete node with payload."""
        data = {
            "id": "node_456",
            "type": "miscellaneous",
            "name": "Output Node",
            "description": "",
            "status": "completed",
            "payload": {"node_id": "node_456", "type": "miscellaneous", "content": "result"}
        }
        schema = NodeCreatedSchema(**data)
        assert schema.status == "completed"
        assert schema.payload is not None
    
    def test_invalid_node_type(self):
        """Test that invalid node type raises ValidationError."""
        data = {
            "id": "node_123",
            "type": "invalid_type",
            "name": "Test",
            "description": ""
        }
        with pytest.raises(ValidationError):
            NodeCreatedSchema(**data)
    
    def test_all_node_types_valid(self):
        """Test that all valid node types are accepted."""
        for node_type in ['agent', 'miscellaneous', 'router', 'parallel']:
            data = {
                "id": f"node_{node_type}",
                "type": node_type,
                "name": f"Test {node_type}",
                "description": ""
            }
            schema = NodeCreatedSchema(**data)
            assert schema.type == node_type
    
    def test_missing_required_fields(self):
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError):
            NodeCreatedSchema(id="node_123")  # missing type, name


class TestNodeCompletedSchema:
    """Tests for NodeCompletedSchema validator."""
    
    def test_valid_completed_node(self):
        """Test valid completed node."""
        data = {
            "id": "node_123",
            "status": "completed",
            "payload": {"node_id": "node_123", "type": "agent"}
        }
        schema = NodeCompletedSchema(**data)
        assert schema.id == "node_123"
        assert schema.status == "completed"
    
    def test_valid_failed_node(self):
        """Test valid failed node."""
        data = {
            "id": "node_123",
            "status": "failed",
            "payload": {"node_id": "node_123", "type": "agent", "error": {"error_message": "fail", "error_type": "Error"}}
        }
        schema = NodeCompletedSchema(**data)
        assert schema.status == "failed"
    
    def test_invalid_started_status(self):
        """Test that 'started' status raises ValidationError."""
        data = {
            "id": "node_123",
            "status": "started"
        }
        with pytest.raises(ValidationError) as exc_info:
            NodeCompletedSchema(**data)
        assert "started" in str(exc_info.value)
    
    def test_parallel_node_with_child_trace(self):
        """Test parallel node with child_trace_id."""
        data = {
            "id": "node_parallel_123",
            "status": "completed",
            "child_trace_id": "child_trace_456"
        }
        schema = NodeCompletedSchema(**data)
        assert schema.child_trace_id == "child_trace_456"


class TestEdgeCreatedSchema:
    """Tests for EdgeCreatedSchema validator."""
    
    def test_valid_edge(self):
        """Test valid edge creation."""
        data = {
            "id": "edge_123",
            "source_node_id": "node_1",
            "target_node_id": "node_2"
        }
        schema = EdgeCreatedSchema(**data)
        assert schema.id == "edge_123"
        assert schema.source_node_id == "node_1"
        assert schema.target_node_id == "node_2"
    
    def test_missing_source_node(self):
        """Test that missing source_node_id raises ValidationError."""
        data = {
            "id": "edge_123",
            "target_node_id": "node_2"
        }
        with pytest.raises(ValidationError):
            EdgeCreatedSchema(**data)
    
    def test_missing_target_node(self):
        """Test that missing target_node_id raises ValidationError."""
        data = {
            "id": "edge_123",
            "source_node_id": "node_1"
        }
        with pytest.raises(ValidationError):
            EdgeCreatedSchema(**data)


class TestAgentPayloadSchema:
    """Tests for AgentPayloadSchema validator."""
    
    def test_valid_agent_payload(self):
        """Test valid agent payload with all fields."""
        data = {
            "node_id": "node_agent_123",
            "type": "agent",
            "input": "Test input",
            "output": "Test output",
            "execution_time_ms": 1500,
            "steps": [
                {"type": "text", "content": "Thinking...", "timestamp": 1700000000000}
            ],
            "token_usage": {"input_tokens": 100, "output_tokens": 50, "total_tokens": 150}
        }
        schema = AgentPayloadSchema(**data)
        assert schema.node_id == "node_agent_123"
        assert schema.type == "agent"
    
    def test_valid_minimal_agent_payload(self):
        """Test valid agent payload with only required fields."""
        data = {
            "node_id": "node_agent_123",
            "type": "agent"
        }
        schema = AgentPayloadSchema(**data)
        assert schema.input is None
        assert schema.output is None
        assert schema.steps is None
    
    def test_valid_text_step(self):
        """Test valid text step in agent payload."""
        data = {
            "node_id": "node_123",
            "type": "agent",
            "steps": [
                {"type": "text", "content": "Reasoning step", "timestamp": 1700000000000}
            ]
        }
        schema = AgentPayloadSchema(**data)
        assert len(schema.steps) == 1
        assert schema.steps[0]["type"] == "text"
    
    def test_valid_tool_use_step(self):
        """Test valid tool_use step in agent payload."""
        data = {
            "node_id": "node_123",
            "type": "agent",
            "steps": [
                {
                    "type": "tool_use",
                    "name": "search_tool",
                    "input": {"query": "test"},
                    "output": {"results": []},
                    "timestamp": 1700000000000
                }
            ]
        }
        schema = AgentPayloadSchema(**data)
        assert schema.steps[0]["type"] == "tool_use"
        assert schema.steps[0]["name"] == "search_tool"
    
    def test_invalid_text_step_missing_content(self):
        """Test that text step without content raises ValidationError."""
        data = {
            "node_id": "node_123",
            "type": "agent",
            "steps": [
                {"type": "text", "timestamp": 1700000000000}
            ]
        }
        with pytest.raises(ValidationError) as exc_info:
            AgentPayloadSchema(**data)
        assert "content" in str(exc_info.value)
    
    def test_invalid_tool_use_step_missing_name(self):
        """Test that tool_use step without name raises ValidationError."""
        data = {
            "node_id": "node_123",
            "type": "agent",
            "steps": [
                {"type": "tool_use", "input": {}, "timestamp": 1700000000000}
            ]
        }
        with pytest.raises(ValidationError) as exc_info:
            AgentPayloadSchema(**data)
        assert "name" in str(exc_info.value)
    
    def test_valid_failed_agent_with_error(self):
        """Test valid failed agent payload with error object."""
        data = {
            "node_id": "node_123",
            "type": "agent",
            "error": {
                "error_message": "Connection timeout",
                "error_type": "TimeoutError"
            }
        }
        schema = AgentPayloadSchema(**data)
        assert schema.error["error_message"] == "Connection timeout"
        assert schema.error["error_type"] == "TimeoutError"
    
    def test_invalid_error_missing_message(self):
        """Test that error without error_message raises ValidationError."""
        data = {
            "node_id": "node_123",
            "type": "agent",
            "error": {"error_type": "Error"}
        }
        with pytest.raises(ValidationError) as exc_info:
            AgentPayloadSchema(**data)
        assert "error_message" in str(exc_info.value)


class TestMiscellaneousPayloadSchema:
    """Tests for MiscellaneousPayloadSchema validator."""
    
    def test_valid_miscellaneous_payload(self):
        """Test valid miscellaneous payload."""
        data = {
            "node_id": "node_misc_123",
            "type": "miscellaneous",
            "content": "Operation completed",
            "metadata": {"items_processed": 10},
            "error": None
        }
        schema = MiscellaneousPayloadSchema(**data)
        assert schema.node_id == "node_misc_123"
        assert schema.type == "miscellaneous"
        assert schema.error is None
    
    def test_valid_minimal_miscellaneous_payload(self):
        """Test valid miscellaneous payload with only required fields."""
        data = {
            "node_id": "node_misc_123",
            "type": "miscellaneous"
        }
        schema = MiscellaneousPayloadSchema(**data)
        assert schema.content is None
        assert schema.metadata is None
    
    def test_invalid_type(self):
        """Test that wrong type raises ValidationError."""
        data = {
            "node_id": "node_123",
            "type": "agent"
        }
        with pytest.raises(ValidationError):
            MiscellaneousPayloadSchema(**data)


class TestRouterPayloadSchema:
    """Tests for RouterPayloadSchema validator."""
    
    def test_valid_router_payload(self):
        """Test valid router payload."""
        data = {
            "node_id": "node_router_123",
            "type": "router",
            "content": "Routing to agent A",
            "metadata": {"route_count": 3}
        }
        schema = RouterPayloadSchema(**data)
        assert schema.node_id == "node_router_123"
        assert schema.type == "router"
    
    def test_valid_minimal_router_payload(self):
        """Test valid router payload with only required fields."""
        data = {
            "node_id": "node_router_123",
            "type": "router"
        }
        schema = RouterPayloadSchema(**data)
        assert schema.content is None
        assert schema.metadata is None


class TestParallelPayloadSchema:
    """Tests for ParallelPayloadSchema validator."""
    
    def test_valid_parallel_payload(self):
        """Test valid parallel payload."""
        data = {
            "node_id": "node_parallel_123",
            "type": "parallel",
            "content": "Processing 5 items in parallel",
            "metadata": {"parallel_count": 5, "max_concurrent": 10}
        }
        schema = ParallelPayloadSchema(**data)
        assert schema.node_id == "node_parallel_123"
        assert schema.type == "parallel"
    
    def test_valid_minimal_parallel_payload(self):
        """Test valid parallel payload with only required fields."""
        data = {
            "node_id": "node_parallel_123",
            "type": "parallel"
        }
        schema = ParallelPayloadSchema(**data)
        assert schema.content is None
        assert schema.metadata is None
