"""
Property-based tests for node created event schema compliance.

**Feature: observability-schema-testing, Property 2: Node created event schema compliance**

This module tests that node_created events emitted by the ObservabilityLogger
conform to the DynamoDB schema defined in docs/data/README.md.

Requirements: 2.1, 2.2, 2.3, 2.4
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
    node_types,
    names,
    descriptions,
    contents,
    optional_metadata,
    MockEmitter,
)
from .schemas.dynamodb_schemas import NodeCreatedSchema


class TestNodeCreatedEventSchemaCompliance:
    """
    Property tests for node created event schema compliance.
    
    **Feature: observability-schema-testing, Property 2: Node created event schema compliance**
    **Validates: Requirements 2.1, 2.2, 2.3, 2.4**
    """

    @given(
        trace_id=trace_ids,
        node_id=node_ids,
        name=names,
        description=descriptions,
        content=contents,
        metadata=optional_metadata,
    )
    @settings(max_examples=100, deadline=None)
    def test_miscellaneous_node_created_event_schema(
        self,
        trace_id: str,
        node_id: str,
        name: str,
        description: str,
        content: str,
        metadata: dict,
    ):
        """
        Property: For any miscellaneous node creation with auto_complete=True,
        the emitted node_created event SHALL have status='completed' and include payload.
        
        **Feature: observability-schema-testing, Property 2: Node created event schema compliance**
        **Validates: Requirements 2.1, 2.2, 2.4**
        """
        # Create fresh mock emitter for this example
        mock_emitter = MockEmitter()
        with patch('observability_logger.core.emitter.get_emitter', return_value=mock_emitter):
            with patch('observability_logger.core.emitter._emitter', mock_emitter):
                # Create a miscellaneous node with auto_complete=True (default)
                node = MiscellaneousNode(
                    trace_id=trace_id,
                    node_id=node_id,
                    name=name,
                    description=description,
                    content=content,
                    metadata=metadata,
                    auto_complete=True
                )
                node.create()
                
                # Get the emitted node_created events
                node_events = mock_emitter.get_events_by_type('node_created')
                assert len(node_events) == 1, "Expected exactly one node_created event"
                
                event = node_events[0]
                
                # Verify event envelope structure
                assert event['event_type'] == 'node_created'
                assert event['trace_id'] == trace_id
                assert isinstance(event['timestamp'], int)
                assert event['timestamp'] > 0, "Timestamp must be positive integer in milliseconds"
                
                # Validate data against NodeCreatedSchema
                data = event['data']
                try:
                    validated = NodeCreatedSchema.model_validate(data)
                except ValidationError as e:
                    raise AssertionError(f"Event data failed schema validation: {e}")
                
                # Verify required fields
                assert validated.id == node_id
                assert validated.type == 'miscellaneous'
                assert validated.name == name
                assert validated.description == description
                
                # Verify auto-complete behavior: status='completed' and payload included
                assert validated.status == 'completed', "Auto-complete miscellaneous nodes must have status='completed'"
                assert validated.payload is not None, "Auto-complete nodes must include payload"
                
                # Verify payload structure for miscellaneous nodes
                payload = validated.payload
                assert payload['node_id'] == node_id
                assert payload['type'] == 'miscellaneous'
                assert payload['content'] == content
                assert payload['error'] is None
                if metadata:
                    assert payload['metadata'] == metadata

    @given(
        trace_id=trace_ids,
        node_id=node_ids,
        name=names,
        description=descriptions,
        content=contents,
        metadata=optional_metadata,
    )
    @settings(max_examples=100, deadline=None)
    def test_router_node_created_event_schema(
        self,
        trace_id: str,
        node_id: str,
        name: str,
        description: str,
        content: str,
        metadata: dict,
    ):
        """
        Property: For any router node creation with auto_complete=True,
        the emitted node_created event SHALL have status='completed' and include payload.
        
        **Feature: observability-schema-testing, Property 2: Node created event schema compliance**
        **Validates: Requirements 2.1, 2.2, 2.4**
        """
        # Create fresh mock emitter for this example
        mock_emitter = MockEmitter()
        with patch('observability_logger.core.emitter.get_emitter', return_value=mock_emitter):
            with patch('observability_logger.core.emitter._emitter', mock_emitter):
                # Create a router node with auto_complete=True (default)
                node = RouterNode(
                    trace_id=trace_id,
                    node_id=node_id,
                    name=name,
                    description=description,
                    content=content,
                    metadata=metadata,
                    auto_complete=True
                )
                node.create()
                
                # Get the emitted node_created events
                node_events = mock_emitter.get_events_by_type('node_created')
                assert len(node_events) == 1, "Expected exactly one node_created event"
                
                event = node_events[0]
                
                # Verify event envelope structure
                assert event['event_type'] == 'node_created'
                assert event['trace_id'] == trace_id
                assert isinstance(event['timestamp'], int)
                assert event['timestamp'] > 0, "Timestamp must be positive integer in milliseconds"
                
                # Validate data against NodeCreatedSchema
                data = event['data']
                try:
                    validated = NodeCreatedSchema.model_validate(data)
                except ValidationError as e:
                    raise AssertionError(f"Event data failed schema validation: {e}")
                
                # Verify required fields
                assert validated.id == node_id
                assert validated.type == 'router'
                assert validated.name == name
                assert validated.description == description
                
                # Verify auto-complete behavior: status='completed' and payload included
                assert validated.status == 'completed', "Auto-complete router nodes must have status='completed'"
                assert validated.payload is not None, "Auto-complete nodes must include payload"
                
                # Verify payload structure for router nodes
                payload = validated.payload
                assert payload['node_id'] == node_id
                assert payload['type'] == 'router'
                assert payload['content'] == content
                if metadata:
                    assert payload['metadata'] == metadata

    @given(
        trace_id=trace_ids,
        node_id=node_ids,
        name=names,
        description=descriptions,
        content=contents,
        metadata=optional_metadata,
    )
    @settings(max_examples=100, deadline=None)
    def test_parallel_node_created_event_schema(
        self,
        trace_id: str,
        node_id: str,
        name: str,
        description: str,
        content: str,
        metadata: dict,
    ):
        """
        Property: For any parallel node creation with auto_complete=False,
        the emitted node_created event SHALL have status='started' and no payload.
        
        **Feature: observability-schema-testing, Property 2: Node created event schema compliance**
        **Validates: Requirements 2.1, 2.2, 2.3**
        """
        # Create fresh mock emitter for this example
        mock_emitter = MockEmitter()
        with patch('observability_logger.core.emitter.get_emitter', return_value=mock_emitter):
            with patch('observability_logger.core.emitter._emitter', mock_emitter):
                # Create a parallel node (auto_complete=False by default)
                node = ParallelNode(
                    trace_id=trace_id,
                    node_id=node_id,
                    name=name,
                    description=description,
                    content=content,
                    metadata=metadata
                )
                node.create()
                
                # Get the emitted node_created events
                node_events = mock_emitter.get_events_by_type('node_created')
                assert len(node_events) == 1, "Expected exactly one node_created event"
                
                event = node_events[0]
                
                # Verify event envelope structure
                assert event['event_type'] == 'node_created'
                assert event['trace_id'] == trace_id
                assert isinstance(event['timestamp'], int)
                assert event['timestamp'] > 0, "Timestamp must be positive integer in milliseconds"
                
                # Validate data against NodeCreatedSchema
                data = event['data']
                try:
                    validated = NodeCreatedSchema.model_validate(data)
                except ValidationError as e:
                    raise AssertionError(f"Event data failed schema validation: {e}")
                
                # Verify required fields
                assert validated.id == node_id
                assert validated.type == 'parallel'
                assert validated.name == name
                assert validated.description == description
                
                # Verify non-auto-complete behavior: status='started' and no payload
                assert validated.status == 'started', "Non-auto-complete parallel nodes must have status='started'"
                # Payload should be None for non-auto-complete nodes
                assert validated.payload is None, "Non-auto-complete nodes should not include payload"

    @given(
        trace_id=trace_ids,
        node_id=node_ids,
        name=names,
        description=descriptions,
        metadata=optional_metadata,
    )
    @settings(max_examples=100, deadline=None)
    def test_agent_node_created_event_schema(
        self,
        trace_id: str,
        node_id: str,
        name: str,
        description: str,
        metadata: dict,
    ):
        """
        Property: For any agent node creation with auto_complete=False,
        the emitted node_created event SHALL have status='started' and no payload.
        
        **Feature: observability-schema-testing, Property 2: Node created event schema compliance**
        **Validates: Requirements 2.1, 2.2, 2.3**
        """
        # Create fresh mock emitter for this example
        mock_emitter = MockEmitter()
        with patch('observability_logger.core.emitter.get_emitter', return_value=mock_emitter):
            with patch('observability_logger.core.emitter._emitter', mock_emitter):
                # Create an agent node (auto_complete=False by default)
                node = AgentNode(
                    trace_id=trace_id,
                    node_id=node_id,
                    name=name,
                    description=description,
                    metadata=metadata
                )
                node.create()
                
                # Get the emitted node_created events
                node_events = mock_emitter.get_events_by_type('node_created')
                assert len(node_events) == 1, "Expected exactly one node_created event"
                
                event = node_events[0]
                
                # Verify event envelope structure
                assert event['event_type'] == 'node_created'
                assert event['trace_id'] == trace_id
                assert isinstance(event['timestamp'], int)
                assert event['timestamp'] > 0, "Timestamp must be positive integer in milliseconds"
                
                # Validate data against NodeCreatedSchema
                data = event['data']
                try:
                    validated = NodeCreatedSchema.model_validate(data)
                except ValidationError as e:
                    raise AssertionError(f"Event data failed schema validation: {e}")
                
                # Verify required fields
                assert validated.id == node_id
                assert validated.type == 'agent'
                assert validated.name == name
                assert validated.description == description
                
                # Verify non-auto-complete behavior: status='started' and no payload
                assert validated.status == 'started', "Non-auto-complete agent nodes must have status='started'"
                # Payload should be None for non-auto-complete nodes
                assert validated.payload is None, "Non-auto-complete nodes should not include payload"

    @given(
        trace_id=trace_ids,
        node_id=node_ids,
        node_type=node_types,
        name=names,
        description=descriptions,
    )
    @settings(max_examples=100, deadline=None)
    def test_all_node_types_have_valid_type_field(
        self,
        trace_id: str,
        node_id: str,
        node_type: str,
        name: str,
        description: str,
    ):
        """
        Property: For any node type, the emitted node_created event SHALL have
        a type field that is one of ["agent", "miscellaneous", "router", "parallel"].
        
        **Feature: observability-schema-testing, Property 2: Node created event schema compliance**
        **Validates: Requirements 2.2**
        """
        # Create fresh mock emitter for this example
        mock_emitter = MockEmitter()
        with patch('observability_logger.core.emitter.get_emitter', return_value=mock_emitter):
            with patch('observability_logger.core.emitter._emitter', mock_emitter):
                # Create node based on type
                if node_type == 'miscellaneous':
                    node = MiscellaneousNode(
                        trace_id=trace_id,
                        node_id=node_id,
                        name=name,
                        description=description
                    )
                elif node_type == 'router':
                    node = RouterNode(
                        trace_id=trace_id,
                        node_id=node_id,
                        name=name,
                        description=description
                    )
                elif node_type == 'parallel':
                    node = ParallelNode(
                        trace_id=trace_id,
                        node_id=node_id,
                        name=name,
                        description=description
                    )
                elif node_type == 'agent':
                    node = AgentNode(
                        trace_id=trace_id,
                        node_id=node_id,
                        name=name,
                        description=description
                    )
                else:
                    # This shouldn't happen with our strategy, but just in case
                    return
                
                node.create()
                
                # Get the emitted node_created events
                node_events = mock_emitter.get_events_by_type('node_created')
                assert len(node_events) == 1, "Expected exactly one node_created event"
                
                event = node_events[0]
                
                # Validate data against NodeCreatedSchema
                data = event['data']
                try:
                    validated = NodeCreatedSchema.model_validate(data)
                except ValidationError as e:
                    raise AssertionError(f"Event data failed schema validation: {e}")
                
                # Verify type field matches expected node type
                assert validated.type == node_type, f"Node type mismatch: expected {node_type}, got {validated.type}"
                
                # Verify type is one of the valid values
                valid_types = ['agent', 'miscellaneous', 'router', 'parallel']
                assert validated.type in valid_types, f"Invalid node type: {validated.type}"

    @given(
        trace_id=trace_ids,
        node_id=node_ids,
        name=names,
        description=descriptions,
    )
    @settings(max_examples=100, deadline=None)
    def test_node_created_event_contains_all_required_fields(
        self,
        trace_id: str,
        node_id: str,
        name: str,
        description: str,
    ):
        """
        Property: For any node creation, the emitted node_created event SHALL contain
        all required fields: id (string), type (string), name (string), description (string), status (string).
        
        **Feature: observability-schema-testing, Property 2: Node created event schema compliance**
        **Validates: Requirements 2.1**
        """
        # Create fresh mock emitter for this example
        mock_emitter = MockEmitter()
        with patch('observability_logger.core.emitter.get_emitter', return_value=mock_emitter):
            with patch('observability_logger.core.emitter._emitter', mock_emitter):
                # Create a simple miscellaneous node
                node = MiscellaneousNode(
                    trace_id=trace_id,
                    node_id=node_id,
                    name=name,
                    description=description
                )
                node.create()
                
                # Get the emitted node_created events
                node_events = mock_emitter.get_events_by_type('node_created')
                assert len(node_events) == 1, "Expected exactly one node_created event"
                
                event = node_events[0]
                
                # Validate data against NodeCreatedSchema
                data = event['data']
                try:
                    validated = NodeCreatedSchema.model_validate(data)
                except ValidationError as e:
                    raise AssertionError(f"Event data failed schema validation: {e}")
                
                # Verify all required fields are present and have correct types
                assert isinstance(validated.id, str), "id must be string"
                assert isinstance(validated.type, str), "type must be string"
                assert isinstance(validated.name, str), "name must be string"
                assert isinstance(validated.description, str), "description must be string"
                assert isinstance(validated.status, str), "status must be string"
                
                # Verify field values match input
                assert validated.id == node_id
                assert validated.type == 'miscellaneous'
                assert validated.name == name
                assert validated.description == description
                assert validated.status in ['started', 'completed', 'failed']