"""
Property-based tests for router payload schema compliance.

Tests that router nodes generate S3 payloads that conform to the schema
defined in docs/data/README.md.

Requirements: 7.1, 7.2, 7.3
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from pydantic import ValidationError
from unittest.mock import patch

from observability_logger.models.node import RouterNode
from observability_logger.core.utils import generate_id

from .conftest import (
    trace_ids, node_ids, names, descriptions, contents, metadata,
    optional_metadata, MockEmitter
)
from .schemas.s3_payload_schemas import RouterPayloadSchema


class TestRouterPayloadSchemaCompliance:
    """
    Property-based tests for router payload schema compliance.
    
    **Feature: observability-schema-testing, Property 7: Router payload schema compliance**
    **Validates: Requirements 7.1, 7.2, 7.3**
    """

    @given(
        trace_id=trace_ids,
        node_id=node_ids,
        name=names,
        description=descriptions,
        content=st.one_of(st.none(), contents),
        node_metadata=optional_metadata
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_router_payload_schema_compliance(
        self,
        trace_id,
        node_id,
        name,
        description,
        content,
        node_metadata
    ):
        """
        **Property 7: Router payload schema compliance**
        
        *For any* completed router node, the payload SHALL contain required fields 
        node_id and type="router", optional content SHALL be string, and optional 
        metadata SHALL be object.
        
        **Validates: Requirements 7.1, 7.2, 7.3**
        """
        # Create mock emitter for this test run
        mock_emitter = MockEmitter()
        
        # Patch the emitter for this test
        with patch('observability_logger.core.emitter.get_emitter', return_value=mock_emitter):
            with patch('observability_logger.core.emitter._emitter', mock_emitter):
                # Create router node with auto_complete=False to test explicit completion
                router_node = RouterNode(
                    trace_id=trace_id,
                    node_id=node_id,
                    name=name,
                    description=description,
                    content=content,
                    metadata=node_metadata,
                    auto_complete=False
                )
                
                # Create the node
                success = router_node.create()
                assert success, "Router node creation should succeed"
                
                # Build payload for completion
                payload = {
                    'node_id': node_id,
                    'type': 'router',
                    'content': content,
                }
                if node_metadata is not None:
                    payload['metadata'] = node_metadata
                
                # Complete the node (emits node_completed event with payload)
                success = router_node.complete(status="completed", payload=payload)
                assert success, "Router node completion should succeed"
                
                # Get the node_completed event
                completed_events = mock_emitter.get_events_by_type('node_completed')
                assert len(completed_events) == 1, "Should have exactly one node_completed event"
                
                completed_event = completed_events[0]
                assert 'data' in completed_event, "Event should have data field"
                
                event_data = completed_event['data']
                assert 'payload' in event_data, "Event data should have payload field"
                
                payload_from_event = event_data['payload']
                assert payload_from_event is not None, "Payload should not be None"
                
                # Validate payload against schema
                try:
                    validated_payload = RouterPayloadSchema.model_validate(payload_from_event)
                    
                    # Verify required fields (Requirements 7.1)
                    assert validated_payload.node_id == node_id, "node_id should match"
                    assert validated_payload.type == "router", "type should be 'router'"
                    
                    # Verify optional content field (Requirements 7.2)
                    if content is not None:
                        assert validated_payload.content == content, "content should match when provided"
                        assert isinstance(validated_payload.content, str), "content should be string when provided"
                    else:
                        # Content can be None
                        assert validated_payload.content is None, "content should be None when not provided"
                    
                    # Verify optional metadata field (Requirements 7.3)
                    if node_metadata is not None:
                        assert validated_payload.metadata == node_metadata, "metadata should match when provided"
                        assert isinstance(validated_payload.metadata, dict), "metadata should be dict when provided"
                    else:
                        # Metadata can be None
                        assert validated_payload.metadata is None, "metadata should be None when not provided"
                    
                except ValidationError as e:
                    pytest.fail(f"Router payload failed schema validation: {e}")

    @given(
        trace_id=trace_ids,
        node_id=node_ids,
        name=names,
        description=descriptions
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_minimal_router_payload_schema_compliance(
        self,
        trace_id,
        node_id,
        name,
        description
    ):
        """
        Test minimal router payload with only required fields.
        
        Verifies that a router node with minimal data still produces
        a valid payload that passes schema validation.
        """
        # Create mock emitter for this test run
        mock_emitter = MockEmitter()
        
        # Patch the emitter for this test
        with patch('observability_logger.core.emitter.get_emitter', return_value=mock_emitter):
            with patch('observability_logger.core.emitter._emitter', mock_emitter):
                # Create minimal router node with auto_complete=False
                router_node = RouterNode(
                    trace_id=trace_id,
                    node_id=node_id,
                    name=name,
                    description=description,
                    auto_complete=False
                    # content=None, metadata=None by default
                )
                
                # Create the node
                success = router_node.create()
                assert success, "Router node creation should succeed"
                
                # Build minimal payload for completion
                payload = {
                    'node_id': node_id,
                    'type': 'router',
                    'content': None,
                }
                
                # Complete the node (emits node_completed event with payload)
                success = router_node.complete(status="completed", payload=payload)
                assert success, "Router node completion should succeed"
                
                # Get the payload
                completed_events = mock_emitter.get_events_by_type('node_completed')
                assert len(completed_events) == 1, "Should have exactly one node_completed event"
                
                payload_from_event = completed_events[0]['data']['payload']
                
                # Validate minimal payload
                try:
                    validated_payload = RouterPayloadSchema.model_validate(payload_from_event)
                    
                    # Verify required fields are present
                    assert validated_payload.node_id == node_id, "node_id should match"
                    assert validated_payload.type == "router", "type should be 'router'"
                    
                    # Optional fields should be None
                    assert validated_payload.content is None, "content should be None when not provided"
                    assert validated_payload.metadata is None, "metadata should be None when not provided"
                    
                except ValidationError as e:
                    pytest.fail(f"Minimal router payload failed schema validation: {e}")

    def test_router_payload_with_all_optional_fields(self):
        """
        Test router payload with all optional fields populated.
        
        Verifies that when all optional fields are provided, they are
        correctly included in the payload and pass validation.
        """
        # Create mock emitter for this test run
        mock_emitter = MockEmitter()
        
        # Patch the emitter for this test
        with patch('observability_logger.core.emitter.get_emitter', return_value=mock_emitter):
            with patch('observability_logger.core.emitter._emitter', mock_emitter):
                # Create router node with all optional fields
                test_content = "Routing to agent A based on input complexity"
                test_metadata = {
                    "route_decision": "agent_a",
                    "input_complexity": "high",
                    "confidence": 0.95
                }
                
                router_node = RouterNode(
                    trace_id="test_trace",
                    node_id="test_node",
                    name="Test Router",
                    description="Test routing decision",
                    content=test_content,
                    metadata=test_metadata,
                    auto_complete=False
                )
                
                # Create the node
                success = router_node.create()
                assert success, "Router node creation should succeed"
                
                # Build payload with all optional fields
                payload = {
                    'node_id': "test_node",
                    'type': 'router',
                    'content': test_content,
                    'metadata': test_metadata,
                }
                
                # Complete the node (emits node_completed event with payload)
                success = router_node.complete(status="completed", payload=payload)
                assert success, "Router node completion should succeed"
                
                # Get the payload
                completed_events = mock_emitter.get_events_by_type('node_completed')
                payload_from_event = completed_events[0]['data']['payload']
                
                # Validate payload with all fields
                try:
                    validated_payload = RouterPayloadSchema.model_validate(payload_from_event)
                    
                    # Verify all fields are present and correct
                    assert validated_payload.node_id == "test_node", "node_id should match"
                    assert validated_payload.type == "router", "type should be 'router'"
                    assert validated_payload.content == test_content, "content should match"
                    assert validated_payload.metadata == test_metadata, "metadata should match"
                    
                except ValidationError as e:
                    pytest.fail(f"Full router payload failed schema validation: {e}")

    def test_router_payload_with_invalid_type_fails_validation(self):
        """
        Test that router payload with invalid type fails validation.
        
        This is an edge case test to ensure the schema properly rejects
        invalid node types.
        """
        # Create invalid payload with wrong type
        invalid_payload = {
            'node_id': 'test_node',
            'type': 'invalid_type',  # Should be 'router'
            'content': 'some content',
            'metadata': {'key': 'value'},
        }
        
        # Validation should fail due to invalid type
        with pytest.raises(ValidationError) as exc_info:
            RouterPayloadSchema.model_validate(invalid_payload)
        
        # Verify the error is about type validation
        error_str = str(exc_info.value)
        assert "type" in error_str.lower()

    def test_router_payload_missing_required_fields_fails_validation(self):
        """
        Test that router payload with missing required fields fails validation.
        """
        # Test missing node_id
        payload_missing_node_id = {
            'type': 'router',
            'content': 'some content',
        }
        
        with pytest.raises(ValidationError) as exc_info:
            RouterPayloadSchema.model_validate(payload_missing_node_id)
        
        error_str = str(exc_info.value)
        assert "node_id" in error_str.lower()
        
        # Test missing type
        payload_missing_type = {
            'node_id': 'test_node',
            'content': 'some content',
        }
        
        with pytest.raises(ValidationError) as exc_info:
            RouterPayloadSchema.model_validate(payload_missing_type)
        
        error_str = str(exc_info.value)
        assert "type" in error_str.lower()

    def test_router_payload_with_wrong_content_type_fails_validation(self):
        """
        Test that router payload with wrong content type fails validation.
        
        Content should be string or None, not other types.
        """
        # Test with integer content (should be string)
        invalid_payload = {
            'node_id': 'test_node',
            'type': 'router',
            'content': 123,  # Should be string, not int
        }
        
        with pytest.raises(ValidationError) as exc_info:
            RouterPayloadSchema.model_validate(invalid_payload)
        
        error_str = str(exc_info.value)
        assert "content" in error_str.lower() or "str" in error_str.lower()

    def test_router_payload_with_wrong_metadata_type_fails_validation(self):
        """
        Test that router payload with wrong metadata type fails validation.
        
        Metadata should be dict or None, not other types.
        """
        # Test with string metadata (should be dict)
        invalid_payload = {
            'node_id': 'test_node',
            'type': 'router',
            'content': 'some content',
            'metadata': 'should_be_dict',  # Should be dict, not string
        }
        
        with pytest.raises(ValidationError) as exc_info:
            RouterPayloadSchema.model_validate(invalid_payload)
        
        error_str = str(exc_info.value)
        assert "metadata" in error_str.lower() or "dict" in error_str.lower()

    def test_auto_complete_router_payload_schema_compliance(self):
        """
        Test router payload schema compliance for auto-complete nodes.
        
        Verifies that router nodes with auto_complete=True (default) produce
        valid payloads in the node_created event that pass schema validation.
        Auto-complete nodes only emit node_created events with status='completed'
        and include the payload directly, skipping node_completed events.
        """
        # Create mock emitter for this test run
        mock_emitter = MockEmitter()
        
        # Patch the emitter for this test
        with patch('observability_logger.core.emitter.get_emitter', return_value=mock_emitter):
            with patch('observability_logger.core.emitter._emitter', mock_emitter):
                # Create router node with auto_complete=True (default)
                test_content = "Auto-routing to default path"
                test_metadata = {"auto_route": True}
                
                router_node = RouterNode(
                    trace_id="test_trace",
                    node_id="test_node",
                    name="Auto Router",
                    description="Auto-completing router",
                    content=test_content,
                    metadata=test_metadata
                    # auto_complete=True by default
                )
                
                # Create the node (auto-completes)
                success = router_node.create()
                assert success, "Router node creation should succeed"
                
                # For auto-complete nodes, payload is in node_created event, not node_completed
                created_events = mock_emitter.get_events_by_type('node_created')
                assert len(created_events) == 1, "Should have exactly one node_created event"
                
                created_event = created_events[0]
                assert created_event['data']['status'] == 'completed', "Auto-complete node should have status='completed'"
                
                payload_from_event = created_event['data']['payload']
                assert payload_from_event is not None, "Auto-complete payload should not be None"
                
                # Validate auto-complete payload
                try:
                    validated_payload = RouterPayloadSchema.model_validate(payload_from_event)
                    
                    # Verify required fields
                    assert validated_payload.node_id == "test_node", "node_id should match"
                    assert validated_payload.type == "router", "type should be 'router'"
                    assert validated_payload.content == test_content, "content should match"
                    assert validated_payload.metadata == test_metadata, "metadata should match"
                    
                except ValidationError as e:
                    pytest.fail(f"Auto-complete router payload failed schema validation: {e}")
                
                # Verify no node_completed event is emitted for auto-complete nodes
                completed_events = mock_emitter.get_events_by_type('node_completed')
                assert len(completed_events) == 0, "Auto-complete nodes should not emit node_completed events"