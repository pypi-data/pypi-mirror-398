"""
Property-based tests for miscellaneous payload schema compliance.

Tests that miscellaneous nodes generate S3 payloads that conform to the schema
defined in docs/data/README.md.

Requirements: 6.1, 6.2, 6.3, 6.4
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from pydantic import ValidationError
from unittest.mock import patch

from observability_logger.models.node import MiscellaneousNode
from observability_logger.core.utils import generate_id

from .conftest import (
    trace_ids, node_ids, names, descriptions, contents, metadata,
    optional_metadata, MockEmitter
)
from .schemas.s3_payload_schemas import MiscellaneousPayloadSchema


class TestMiscellaneousPayloadSchemaCompliance:
    """
    Property-based tests for miscellaneous payload schema compliance.
    
    **Feature: observability-schema-testing, Property 6: Miscellaneous payload schema compliance**
    **Validates: Requirements 6.1, 6.2, 6.3, 6.4**
    """

    @given(
        trace_id=trace_ids,
        node_id=node_ids,
        name=names,
        description=descriptions,
        content=st.one_of(st.none(), contents),
        node_metadata=optional_metadata
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_miscellaneous_payload_schema_compliance(
        self,
        trace_id,
        node_id,
        name,
        description,
        content,
        node_metadata
    ):
        """
        **Property 6: Miscellaneous payload schema compliance**
        
        *For any* completed miscellaneous node, the payload SHALL contain required fields 
        node_id and type="miscellaneous", optional content SHALL be string, optional 
        metadata SHALL be object, and error SHALL be null for successful completions.
        
        **Validates: Requirements 6.1, 6.2, 6.3, 6.4**
        """
        # Create mock emitter for this test run
        mock_emitter = MockEmitter()
        
        # Patch the emitter for this test
        with patch('observability_logger.core.emitter.get_emitter', return_value=mock_emitter):
            with patch('observability_logger.core.emitter._emitter', mock_emitter):
                # Create miscellaneous node with auto_complete=False to test explicit completion
                misc_node = MiscellaneousNode(
                    trace_id=trace_id,
                    node_id=node_id,
                    name=name,
                    description=description,
                    content=content,
                    metadata=node_metadata,
                    auto_complete=False
                )
                
                # Create the node
                success = misc_node.create()
                assert success, "Miscellaneous node creation should succeed"
                
                # Build payload for completion
                payload = {
                    'node_id': node_id,
                    'type': 'miscellaneous',
                    'content': content,
                    'error': None
                }
                if node_metadata is not None:
                    payload['metadata'] = node_metadata
                
                # Complete the node (emits node_completed event with payload)
                success = misc_node.complete(status="completed", payload=payload)
                assert success, "Miscellaneous node completion should succeed"
                
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
                    validated_payload = MiscellaneousPayloadSchema.model_validate(payload_from_event)
                    
                    # Verify required fields (Requirements 6.1)
                    assert validated_payload.node_id == node_id, "node_id should match"
                    assert validated_payload.type == "miscellaneous", "type should be 'miscellaneous'"
                    
                    # Verify optional content field (Requirements 6.2)
                    if content is not None:
                        assert validated_payload.content == content, "content should match when provided"
                        assert isinstance(validated_payload.content, str), "content should be string when provided"
                    else:
                        # Content can be None
                        assert validated_payload.content is None, "content should be None when not provided"
                    
                    # Verify optional metadata field (Requirements 6.3)
                    if node_metadata is not None:
                        assert validated_payload.metadata == node_metadata, "metadata should match when provided"
                        assert isinstance(validated_payload.metadata, dict), "metadata should be dict when provided"
                    else:
                        # Metadata can be None
                        assert validated_payload.metadata is None, "metadata should be None when not provided"
                    
                    # Verify error is null for successful completions (Requirements 6.4)
                    assert validated_payload.error is None, "error should be null for successful completions"
                    
                except ValidationError as e:
                    pytest.fail(f"Miscellaneous payload failed schema validation: {e}")

    @given(
        trace_id=trace_ids,
        node_id=node_ids,
        name=names,
        description=descriptions
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_minimal_miscellaneous_payload_schema_compliance(
        self,
        trace_id,
        node_id,
        name,
        description
    ):
        """
        Test minimal miscellaneous payload with only required fields.
        
        Verifies that a miscellaneous node with minimal data still produces
        a valid payload that passes schema validation.
        """
        # Create mock emitter for this test run
        mock_emitter = MockEmitter()
        
        # Patch the emitter for this test
        with patch('observability_logger.core.emitter.get_emitter', return_value=mock_emitter):
            with patch('observability_logger.core.emitter._emitter', mock_emitter):
                # Create minimal miscellaneous node with auto_complete=False
                misc_node = MiscellaneousNode(
                    trace_id=trace_id,
                    node_id=node_id,
                    name=name,
                    description=description,
                    auto_complete=False
                    # content=None, metadata=None by default
                )
                
                # Create the node
                success = misc_node.create()
                assert success, "Miscellaneous node creation should succeed"
                
                # Build minimal payload for completion
                payload = {
                    'node_id': node_id,
                    'type': 'miscellaneous',
                    'content': None,
                    'error': None
                }
                
                # Complete the node (emits node_completed event with payload)
                success = misc_node.complete(status="completed", payload=payload)
                assert success, "Miscellaneous node completion should succeed"
                
                # Get the payload
                completed_events = mock_emitter.get_events_by_type('node_completed')
                assert len(completed_events) == 1, "Should have exactly one node_completed event"
                
                payload_from_event = completed_events[0]['data']['payload']
                
                # Validate minimal payload
                try:
                    validated_payload = MiscellaneousPayloadSchema.model_validate(payload_from_event)
                    
                    # Verify required fields are present
                    assert validated_payload.node_id == node_id, "node_id should match"
                    assert validated_payload.type == "miscellaneous", "type should be 'miscellaneous'"
                    
                    # Optional fields should be None
                    assert validated_payload.content is None, "content should be None when not provided"
                    assert validated_payload.metadata is None, "metadata should be None when not provided"
                    assert validated_payload.error is None, "error should be None for successful completion"
                    
                except ValidationError as e:
                    pytest.fail(f"Minimal miscellaneous payload failed schema validation: {e}")

    def test_miscellaneous_payload_with_all_optional_fields(self):
        """
        Test miscellaneous payload with all optional fields populated.
        
        Verifies that when all optional fields are provided, they are
        correctly included in the payload and pass validation.
        """
        # Create mock emitter for this test run
        mock_emitter = MockEmitter()
        
        # Patch the emitter for this test
        with patch('observability_logger.core.emitter.get_emitter', return_value=mock_emitter):
            with patch('observability_logger.core.emitter._emitter', mock_emitter):
                # Create miscellaneous node with all optional fields
                test_content = "Operation completed successfully"
                test_metadata = {
                    "operation_type": "validation",
                    "items_processed": 42,
                    "success_rate": 0.95
                }
                
                misc_node = MiscellaneousNode(
                    trace_id="test_trace",
                    node_id="test_node",
                    name="Test Operation",
                    description="Test miscellaneous operation",
                    content=test_content,
                    metadata=test_metadata,
                    auto_complete=False
                )
                
                # Create the node
                success = misc_node.create()
                assert success, "Miscellaneous node creation should succeed"
                
                # Build payload with all optional fields
                payload = {
                    'node_id': "test_node",
                    'type': 'miscellaneous',
                    'content': test_content,
                    'metadata': test_metadata,
                    'error': None
                }
                
                # Complete the node (emits node_completed event with payload)
                success = misc_node.complete(status="completed", payload=payload)
                assert success, "Miscellaneous node completion should succeed"
                
                # Get the payload
                completed_events = mock_emitter.get_events_by_type('node_completed')
                payload_from_event = completed_events[0]['data']['payload']
                
                # Validate payload with all fields
                try:
                    validated_payload = MiscellaneousPayloadSchema.model_validate(payload_from_event)
                    
                    # Verify all fields are present and correct
                    assert validated_payload.node_id == "test_node", "node_id should match"
                    assert validated_payload.type == "miscellaneous", "type should be 'miscellaneous'"
                    assert validated_payload.content == test_content, "content should match"
                    assert validated_payload.metadata == test_metadata, "metadata should match"
                    assert validated_payload.error is None, "error should be None for successful completion"
                    
                except ValidationError as e:
                    pytest.fail(f"Full miscellaneous payload failed schema validation: {e}")

    def test_miscellaneous_payload_with_invalid_type_fails_validation(self):
        """
        Test that miscellaneous payload with invalid type fails validation.
        
        This is an edge case test to ensure the schema properly rejects
        invalid node types.
        """
        # Create invalid payload with wrong type
        invalid_payload = {
            'node_id': 'test_node',
            'type': 'invalid_type',  # Should be 'miscellaneous'
            'content': 'some content',
            'metadata': {'key': 'value'},
            'error': None
        }
        
        # Validation should fail due to invalid type
        with pytest.raises(ValidationError) as exc_info:
            MiscellaneousPayloadSchema.model_validate(invalid_payload)
        
        # Verify the error is about type validation
        error_str = str(exc_info.value)
        assert "type" in error_str.lower()

    def test_miscellaneous_payload_missing_required_fields_fails_validation(self):
        """
        Test that miscellaneous payload with missing required fields fails validation.
        """
        # Test missing node_id
        payload_missing_node_id = {
            'type': 'miscellaneous',
            'content': 'some content',
            'error': None
        }
        
        with pytest.raises(ValidationError) as exc_info:
            MiscellaneousPayloadSchema.model_validate(payload_missing_node_id)
        
        error_str = str(exc_info.value)
        assert "node_id" in error_str.lower()
        
        # Test missing type
        payload_missing_type = {
            'node_id': 'test_node',
            'content': 'some content',
            'error': None
        }
        
        with pytest.raises(ValidationError) as exc_info:
            MiscellaneousPayloadSchema.model_validate(payload_missing_type)
        
        error_str = str(exc_info.value)
        assert "type" in error_str.lower()

    def test_miscellaneous_payload_with_wrong_content_type_fails_validation(self):
        """
        Test that miscellaneous payload with wrong content type fails validation.
        
        Content should be string or None, not other types.
        """
        # Test with integer content (should be string)
        invalid_payload = {
            'node_id': 'test_node',
            'type': 'miscellaneous',
            'content': 123,  # Should be string, not int
            'error': None
        }
        
        with pytest.raises(ValidationError) as exc_info:
            MiscellaneousPayloadSchema.model_validate(invalid_payload)
        
        error_str = str(exc_info.value)
        assert "content" in error_str.lower() or "str" in error_str.lower()

    def test_miscellaneous_payload_with_wrong_metadata_type_fails_validation(self):
        """
        Test that miscellaneous payload with wrong metadata type fails validation.
        
        Metadata should be dict or None, not other types.
        """
        # Test with string metadata (should be dict)
        invalid_payload = {
            'node_id': 'test_node',
            'type': 'miscellaneous',
            'content': 'some content',
            'metadata': 'should_be_dict',  # Should be dict, not string
            'error': None
        }
        
        with pytest.raises(ValidationError) as exc_info:
            MiscellaneousPayloadSchema.model_validate(invalid_payload)
        
        error_str = str(exc_info.value)
        assert "metadata" in error_str.lower() or "dict" in error_str.lower()