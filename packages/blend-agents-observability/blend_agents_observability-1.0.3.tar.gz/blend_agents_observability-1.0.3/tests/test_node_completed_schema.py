"""
Property-based tests for node completed event schema compliance.

**Feature: observability-schema-testing, Property 3: Node completed event schema compliance**

This module tests that node_completed events emitted by the ObservabilityLogger
conform to the DynamoDB schema defined in docs/data/README.md.

Requirements: 3.1, 3.2, 3.3
"""

from hypothesis import given, settings
from pydantic import ValidationError
from unittest.mock import patch

from observability_logger.models.node import (
    MiscellaneousNode,
    ParallelNode,
    RouterNode,
    AgentNode
)

from .conftest import (
    trace_ids,
    node_ids,
    names,
    descriptions,
    contents,
    optional_metadata,
    completion_statuses,
    MockEmitter,
)
from .schemas.dynamodb_schemas import NodeCompletedSchema


class TestNodeCompletedEventSchemaCompliance:
    """
    Property tests for node completed event schema compliance.
    
    **Feature: observability-schema-testing, Property 3: Node completed event schema compliance**
    **Validates: Requirements 3.1, 3.2, 3.3**
    """

    @given(
        trace_id=trace_ids,
        node_id=node_ids,
        name=names,
        description=descriptions,
        content=contents,
        metadata=optional_metadata,
        status=completion_statuses,
    )
    @settings(max_examples=100, deadline=None)
    def test_miscellaneous_node_completed_event_schema(
        self,
        trace_id: str,
        node_id: str,
        name: str,
        description: str,
        content: str,
        metadata: dict,
        status: str,
    ):
        """
        Property: For any miscellaneous node completion with valid status,
        the emitted node_completed event SHALL contain required fields and
        status SHALL never be "started".
        
        **Feature: observability-schema-testing, Property 3: Node completed event schema compliance**
        **Validates: Requirements 3.1, 3.2**
        """
        # Create fresh mock emitter for this example
        mock_emitter = MockEmitter()
        with patch('observability_logger.core.emitter.get_emitter', return_value=mock_emitter):
            with patch('observability_logger.core.emitter._emitter', mock_emitter):
                # Create a miscellaneous node with auto_complete=False to test explicit completion
                node = MiscellaneousNode(
                    trace_id=trace_id,
                    node_id=node_id,
                    name=name,
                    description=description,
                    content=content,
                    metadata=metadata,
                    auto_complete=False
                )
                node.create()
                
                # Clear the node_created event to focus on completion
                mock_emitter.clear()
                
                # Complete the node
                node.complete(status=status)
                
                # Get the emitted node_completed events
                completed_events = mock_emitter.get_events_by_type('node_completed')
                assert len(completed_events) == 1, "Expected exactly one node_completed event"
                
                event = completed_events[0]
                
                # Verify event envelope structure
                assert event['event_type'] == 'node_completed'
                assert event['trace_id'] == trace_id
                assert isinstance(event['timestamp'], int)
                assert event['timestamp'] > 0, "Timestamp must be positive integer in milliseconds"
                
                # Validate data against NodeCompletedSchema
                data = event['data']
                try:
                    validated = NodeCompletedSchema.model_validate(data)
                except ValidationError as e:
                    raise AssertionError(f"Event data failed schema validation: {e}")
                
                # Verify required fields
                assert validated.id == node_id
                assert validated.status == status
                
                # Verify status is never "started"
                assert validated.status != 'started', "node_completed status cannot be 'started'"
                assert validated.status in ['completed', 'failed'], f"Invalid completion status: {validated.status}"
                
                # Verify payload structure for miscellaneous nodes
                if validated.payload:
                    payload = validated.payload
                    assert payload['node_id'] == node_id
                    assert payload['type'] == 'miscellaneous'

    @given(
        trace_id=trace_ids,
        node_id=node_ids,
        name=names,
        description=descriptions,
        content=contents,
        metadata=optional_metadata,
        status=completion_statuses,
    )
    @settings(max_examples=100, deadline=None)
    def test_router_node_completed_event_schema(
        self,
        trace_id: str,
        node_id: str,
        name: str,
        description: str,
        content: str,
        metadata: dict,
        status: str,
    ):
        """
        Property: For any router node completion with valid status,
        the emitted node_completed event SHALL contain required fields and
        status SHALL never be "started".
        
        **Feature: observability-schema-testing, Property 3: Node completed event schema compliance**
        **Validates: Requirements 3.1, 3.2**
        """
        # Create fresh mock emitter for this example
        mock_emitter = MockEmitter()
        with patch('observability_logger.core.emitter.get_emitter', return_value=mock_emitter):
            with patch('observability_logger.core.emitter._emitter', mock_emitter):
                # Create a router node with auto_complete=False to test explicit completion
                node = RouterNode(
                    trace_id=trace_id,
                    node_id=node_id,
                    name=name,
                    description=description,
                    content=content,
                    metadata=metadata,
                    auto_complete=False
                )
                node.create()
                
                # Clear the node_created event to focus on completion
                mock_emitter.clear()
                
                # Complete the node
                node.complete(status=status)
                
                # Get the emitted node_completed events
                completed_events = mock_emitter.get_events_by_type('node_completed')
                assert len(completed_events) == 1, "Expected exactly one node_completed event"
                
                event = completed_events[0]
                
                # Verify event envelope structure
                assert event['event_type'] == 'node_completed'
                assert event['trace_id'] == trace_id
                assert isinstance(event['timestamp'], int)
                assert event['timestamp'] > 0, "Timestamp must be positive integer in milliseconds"
                
                # Validate data against NodeCompletedSchema
                data = event['data']
                try:
                    validated = NodeCompletedSchema.model_validate(data)
                except ValidationError as e:
                    raise AssertionError(f"Event data failed schema validation: {e}")
                
                # Verify required fields
                assert validated.id == node_id
                assert validated.status == status
                
                # Verify status is never "started"
                assert validated.status != 'started', "node_completed status cannot be 'started'"
                assert validated.status in ['completed', 'failed'], f"Invalid completion status: {validated.status}"
                
                # Verify payload structure for router nodes
                if validated.payload:
                    payload = validated.payload
                    assert payload['node_id'] == node_id
                    assert payload['type'] == 'router'

    @given(
        trace_id=trace_ids,
        node_id=node_ids,
        name=names,
        description=descriptions,
        content=contents,
        metadata=optional_metadata,
        status=completion_statuses,
    )
    @settings(max_examples=100, deadline=None)
    def test_parallel_node_completed_event_schema_with_child_trace(
        self,
        trace_id: str,
        node_id: str,
        name: str,
        description: str,
        content: str,
        metadata: dict,
        status: str,
    ):
        """
        Property: For any parallel node completion with associated child trace,
        the emitted node_completed event SHALL include child_trace_id field.
        
        **Feature: observability-schema-testing, Property 3: Node completed event schema compliance**
        **Validates: Requirements 3.1, 3.2, 3.3**
        """
        # Create fresh mock emitter for this example
        mock_emitter = MockEmitter()
        with patch('observability_logger.core.emitter.get_emitter', return_value=mock_emitter):
            with patch('observability_logger.core.emitter._emitter', mock_emitter):
                # Create a parallel node
                node = ParallelNode(
                    trace_id=trace_id,
                    node_id=node_id,
                    name=name,
                    description=description,
                    content=content,
                    metadata=metadata
                )
                node.create()
                
                # Simulate associating a child trace by setting the internal attribute
                child_trace_id = f"child_{trace_id}"
                node._child_trace_id = child_trace_id
                
                # Clear events to focus on completion
                mock_emitter.clear()
                
                # Complete the node (child_trace_id will be included automatically)
                node.complete(status=status)
                
                # Get the emitted node_completed events
                completed_events = mock_emitter.get_events_by_type('node_completed')
                assert len(completed_events) == 1, "Expected exactly one node_completed event"
                
                event = completed_events[0]
                
                # Verify event envelope structure
                assert event['event_type'] == 'node_completed'
                assert event['trace_id'] == trace_id
                assert isinstance(event['timestamp'], int)
                assert event['timestamp'] > 0, "Timestamp must be positive integer in milliseconds"
                
                # Validate data against NodeCompletedSchema
                data = event['data']
                try:
                    validated = NodeCompletedSchema.model_validate(data)
                except ValidationError as e:
                    raise AssertionError(f"Event data failed schema validation: {e}")
                
                # Verify required fields
                assert validated.id == node_id
                assert validated.status == status
                
                # Verify status is never "started"
                assert validated.status != 'started', "node_completed status cannot be 'started'"
                assert validated.status in ['completed', 'failed'], f"Invalid completion status: {validated.status}"
                
                # Verify child_trace_id is included for parallel nodes
                assert validated.child_trace_id == child_trace_id, "Parallel nodes with child traces must include child_trace_id"
                
                # Verify payload structure for parallel nodes
                if validated.payload:
                    payload = validated.payload
                    assert payload['node_id'] == node_id
                    assert payload['type'] == 'parallel'

    @given(
        trace_id=trace_ids,
        node_id=node_ids,
        name=names,
        description=descriptions,
        metadata=optional_metadata,
        status=completion_statuses,
    )
    @settings(max_examples=100, deadline=None)
    def test_agent_node_completed_event_schema(
        self,
        trace_id: str,
        node_id: str,
        name: str,
        description: str,
        metadata: dict,
        status: str,
    ):
        """
        Property: For any agent node completion with valid status,
        the emitted node_completed event SHALL contain required fields and
        status SHALL never be "started".
        
        **Feature: observability-schema-testing, Property 3: Node completed event schema compliance**
        **Validates: Requirements 3.1, 3.2**
        """
        # Create fresh mock emitter for this example
        mock_emitter = MockEmitter()
        with patch('observability_logger.core.emitter.get_emitter', return_value=mock_emitter):
            with patch('observability_logger.core.emitter._emitter', mock_emitter):
                # Create an agent node
                node = AgentNode(
                    trace_id=trace_id,
                    node_id=node_id,
                    name=name,
                    description=description,
                    metadata=metadata
                )
                node.create()
                
                # Clear the node_created event to focus on completion
                mock_emitter.clear()
                
                # Complete the node
                node.complete(status=status)
                
                # Get the emitted node_completed events
                completed_events = mock_emitter.get_events_by_type('node_completed')
                assert len(completed_events) == 1, "Expected exactly one node_completed event"
                
                event = completed_events[0]
                
                # Verify event envelope structure
                assert event['event_type'] == 'node_completed'
                assert event['trace_id'] == trace_id
                assert isinstance(event['timestamp'], int)
                assert event['timestamp'] > 0, "Timestamp must be positive integer in milliseconds"
                
                # Validate data against NodeCompletedSchema
                data = event['data']
                try:
                    validated = NodeCompletedSchema.model_validate(data)
                except ValidationError as e:
                    raise AssertionError(f"Event data failed schema validation: {e}")
                
                # Verify required fields
                assert validated.id == node_id
                assert validated.status == status
                
                # Verify status is never "started"
                assert validated.status != 'started', "node_completed status cannot be 'started'"
                assert validated.status in ['completed', 'failed'], f"Invalid completion status: {validated.status}"
                
                # Verify payload structure for agent nodes
                if validated.payload:
                    payload = validated.payload
                    assert payload['node_id'] == node_id
                    assert payload['type'] == 'agent'

    @given(
        trace_id=trace_ids,
        node_id=node_ids,
        name=names,
        description=descriptions,
        status=completion_statuses,
    )
    @settings(max_examples=100, deadline=None)
    def test_node_completed_event_contains_all_required_fields(
        self,
        trace_id: str,
        node_id: str,
        name: str,
        description: str,
        status: str,
    ):
        """
        Property: For any node completion, the emitted node_completed event SHALL contain
        all required fields: id (string) and status (string).
        
        **Feature: observability-schema-testing, Property 3: Node completed event schema compliance**
        **Validates: Requirements 3.1**
        """
        # Create fresh mock emitter for this example
        mock_emitter = MockEmitter()
        with patch('observability_logger.core.emitter.get_emitter', return_value=mock_emitter):
            with patch('observability_logger.core.emitter._emitter', mock_emitter):
                # Create a simple miscellaneous node with auto_complete=False
                node = MiscellaneousNode(
                    trace_id=trace_id,
                    node_id=node_id,
                    name=name,
                    description=description,
                    auto_complete=False
                )
                node.create()
                
                # Clear the node_created event to focus on completion
                mock_emitter.clear()
                
                # Complete the node
                node.complete(status=status)
                
                # Get the emitted node_completed events
                completed_events = mock_emitter.get_events_by_type('node_completed')
                assert len(completed_events) == 1, "Expected exactly one node_completed event"
                
                event = completed_events[0]
                
                # Validate data against NodeCompletedSchema
                data = event['data']
                try:
                    validated = NodeCompletedSchema.model_validate(data)
                except ValidationError as e:
                    raise AssertionError(f"Event data failed schema validation: {e}")
                
                # Verify all required fields are present and have correct types
                assert isinstance(validated.id, str), "id must be string"
                assert isinstance(validated.status, str), "status must be string"
                
                # Verify field values match input
                assert validated.id == node_id
                assert validated.status == status
                assert validated.status in ['completed', 'failed']

    @given(
        trace_id=trace_ids,
        node_id=node_ids,
        name=names,
        description=descriptions,
    )
    @settings(max_examples=100, deadline=None)
    def test_node_completed_status_validation(
        self,
        trace_id: str,
        node_id: str,
        name: str,
        description: str,
    ):
        """
        Property: For any node completion, the status field SHALL be one of
        ["completed", "failed"] and SHALL NOT be "started".
        
        **Feature: observability-schema-testing, Property 3: Node completed event schema compliance**
        **Validates: Requirements 3.2**
        """
        # Create fresh mock emitter for this example
        mock_emitter = MockEmitter()
        with patch('observability_logger.core.emitter.get_emitter', return_value=mock_emitter):
            with patch('observability_logger.core.emitter._emitter', mock_emitter):
                # Create a simple miscellaneous node with auto_complete=False
                node = MiscellaneousNode(
                    trace_id=trace_id,
                    node_id=node_id,
                    name=name,
                    description=description,
                    auto_complete=False
                )
                node.create()
                
                # Test that attempting to complete with "started" status fails
                # The node.complete() method should reject this, but let's verify
                # the schema validation would also catch it
                
                # Try completing with "completed" status (should work)
                mock_emitter.clear()
                success = node.complete(status="completed")
                assert success, "Completing with 'completed' status should succeed"
                
                completed_events = mock_emitter.get_events_by_type('node_completed')
                assert len(completed_events) == 1, "Expected exactly one node_completed event"
                
                event = completed_events[0]
                data = event['data']
                
                # Validate against schema
                try:
                    validated = NodeCompletedSchema.model_validate(data)
                    assert validated.status == "completed"
                except ValidationError as e:
                    raise AssertionError(f"Valid completion status failed schema validation: {e}")
                
                # Verify that "started" status would be rejected by schema
                invalid_data = {**data, 'status': 'started'}
                try:
                    NodeCompletedSchema.model_validate(invalid_data)
                    raise AssertionError("Schema should reject 'started' status for node_completed events")
                except ValidationError:
                    # This is expected - the schema should reject "started" status
                    pass