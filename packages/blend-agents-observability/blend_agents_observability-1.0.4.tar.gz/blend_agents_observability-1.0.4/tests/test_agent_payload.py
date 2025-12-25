"""
Property-based tests for agent payload schema compliance.

Tests that agent nodes generate S3 payloads that conform to the schema
defined in docs/data/README.md.

Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from pydantic import ValidationError
from unittest.mock import patch

from observability_logger.models.agent_logger import AgentLogger
from observability_logger.models.node import AgentNode
from observability_logger.core.utils import generate_id

from .conftest import (
    trace_ids, node_ids, names, descriptions, contents, metadata,
    agent_steps_list, optional_token_usage, execution_time_ms,
    error_objects, optional_error, MockEmitter
)
from .schemas.s3_payload_schemas import AgentPayloadSchema


class TestAgentPayloadSchemaCompliance:
    """
    Property-based tests for agent payload schema compliance.
    
    **Feature: observability-schema-testing, Property 5: Agent payload schema compliance**
    **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7**
    """

    @given(
        trace_id=trace_ids,
        node_id=node_ids,
        name=names,
        description=descriptions,
        input_text=st.one_of(st.none(), contents),
        output_text=st.one_of(st.none(), contents),
        steps=agent_steps_list,
        token_usage=optional_token_usage,
        exec_time=st.one_of(st.none(), execution_time_ms),
        node_metadata=st.one_of(st.none(), metadata),
        error_obj=optional_error
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_agent_payload_schema_compliance(
        self,
        trace_id,
        node_id,
        name,
        description,
        input_text,
        output_text,
        steps,
        token_usage,
        exec_time,
        node_metadata,
        error_obj
    ):
        """
        **Property 5: Agent payload schema compliance**
        
        *For any* completed agent node, the payload SHALL contain required fields 
        node_id and type="agent", optional fields input/output/steps/token_usage/error 
        SHALL have correct types when present, steps SHALL have type "text" or "tool_use" 
        with appropriate fields, and failed agents SHALL have error object with 
        error_message and error_type.
        
        **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7**
        """
        # Create mock emitter for this test run
        mock_emitter = MockEmitter()
        
        # Patch the emitter for this test
        with patch('observability_logger.core.emitter.get_emitter', return_value=mock_emitter):
            with patch('observability_logger.core.emitter._emitter', mock_emitter):
                # Create agent node
                agent_node = AgentNode(
                    trace_id=trace_id,
                    node_id=node_id,
                    name=name,
                    description=description,
                    metadata=node_metadata
                )
                
                # Create the node (emits node_created event)
                success = agent_node.create()
                assert success, "Agent node creation should succeed"
                
                # Set input if provided
                if input_text is not None:
                    agent_node.set_input(input_text)
                
                # Set output if provided
                if output_text is not None:
                    agent_node.set_output(output_text)
                
                # Add steps if provided
                for step in steps:
                    agent_node._steps.append(step)
                
                # Set token usage if provided
                if token_usage is not None:
                    agent_node.set_token_usage(
                        input_tokens=token_usage['input_tokens'],
                        output_tokens=token_usage['output_tokens'],
                        total_tokens=token_usage.get('total_tokens')
                    )
                
                # Set execution time if provided
                original_get_time = None
                if exec_time is not None:
                    agent_node._start_time = 1000000000000  # Fixed start time
                    # Mock current time to create execution time
                    import observability_logger.core.utils as utils
                    original_get_time = utils.get_current_timestamp_ms
                    utils.get_current_timestamp_ms = lambda: 1000000000000 + exec_time
                
                # Set error if provided (determines status)
                status = "completed"
                if error_obj is not None:
                    agent_node.set_error(error_obj['error_message'])
                    agent_node._error_type = error_obj['error_type']
                    status = "failed"
                
                try:
                    # Complete the node (emits node_completed event with payload)
                    success = agent_node.complete(status=status)
                    assert success, "Agent node completion should succeed"
                    
                    # Get the node_completed event
                    completed_events = mock_emitter.get_events_by_type('node_completed')
                    assert len(completed_events) == 1, "Should have exactly one node_completed event"
                    
                    completed_event = completed_events[0]
                    assert 'data' in completed_event, "Event should have data field"
                    
                    event_data = completed_event['data']
                    assert 'payload' in event_data, "Event data should have payload field"
                    
                    payload = event_data['payload']
                    assert payload is not None, "Payload should not be None"
                    
                    # Validate payload against schema
                    try:
                        validated_payload = AgentPayloadSchema.model_validate(payload)
                        
                        # Verify required fields (Requirements 5.1)
                        assert validated_payload.node_id == node_id, "node_id should match"
                        assert validated_payload.type == "agent", "type should be 'agent'"
                        
                        # Verify optional input field (Requirements 5.2)
                        if input_text is not None:
                            assert validated_payload.input == input_text, "input should match when provided"
                        
                        # Verify optional output field (Requirements 5.3)
                        if output_text is not None:
                            assert validated_payload.output == output_text, "output should match when provided"
                        
                        # Verify steps structure (Requirements 5.4, 5.5, 5.6)
                        if steps:
                            assert validated_payload.steps is not None, "steps should be present when provided"
                            assert len(validated_payload.steps) == len(steps), "steps count should match"
                            
                            for i, step in enumerate(validated_payload.steps):
                                original_step = steps[i]
                                step_type = step.get('type')
                                
                                # Verify step type is valid
                                assert step_type in ['text', 'tool_use'], f"Step {i} type should be 'text' or 'tool_use'"
                                
                                # Verify text steps have required fields (Requirements 5.5)
                                if step_type == 'text':
                                    assert 'content' in step, f"Text step {i} should have content field"
                                    assert 'timestamp' in step, f"Text step {i} should have timestamp field"
                                    assert isinstance(step['content'], str), f"Text step {i} content should be string"
                                    assert isinstance(step['timestamp'], int), f"Text step {i} timestamp should be int"
                                    assert step['timestamp'] > 0, f"Text step {i} timestamp should be positive"
                                
                                # Verify tool_use steps have required fields (Requirements 5.6)
                                elif step_type == 'tool_use':
                                    assert 'name' in step, f"Tool step {i} should have name field"
                                    assert 'input' in step, f"Tool step {i} should have input field"
                                    assert 'timestamp' in step, f"Tool step {i} should have timestamp field"
                                    assert isinstance(step['name'], str), f"Tool step {i} name should be string"
                                    assert isinstance(step['input'], dict), f"Tool step {i} input should be dict"
                                    assert isinstance(step['timestamp'], int), f"Tool step {i} timestamp should be int"
                                    assert step['timestamp'] > 0, f"Tool step {i} timestamp should be positive"
                                    # output can be None or dict
                                    if 'output' in step and step['output'] is not None:
                                        assert isinstance(step['output'], dict), f"Tool step {i} output should be dict or None"
                        
                        # Verify token usage structure
                        if token_usage is not None:
                            assert validated_payload.token_usage is not None, "token_usage should be present when provided"
                            assert isinstance(validated_payload.token_usage, dict), "token_usage should be dict"
                            assert 'input_tokens' in validated_payload.token_usage, "token_usage should have input_tokens"
                            assert 'output_tokens' in validated_payload.token_usage, "token_usage should have output_tokens"
                        
                        # Verify error structure for failed agents (Requirements 5.7)
                        if status == "failed" and error_obj is not None:
                            assert validated_payload.error is not None, "Failed agents should have error object"
                            assert isinstance(validated_payload.error, dict), "error should be dict"
                            assert 'error_message' in validated_payload.error, "error should have error_message field"
                            assert 'error_type' in validated_payload.error, "error should have error_type field"
                            assert isinstance(validated_payload.error['error_message'], str), "error_message should be string"
                            assert isinstance(validated_payload.error['error_type'], str), "error_type should be string"
                            assert len(validated_payload.error['error_message']) > 0, "error_message should not be empty"
                            assert len(validated_payload.error['error_type']) > 0, "error_type should not be empty"
                        
                        # Verify successful agents don't have error
                        if status == "completed":
                            # Error can be None or null for successful completions
                            if validated_payload.error is not None:
                                # If error is present, it should be null/None (not an error object)
                                assert validated_payload.error is None, "Successful agents should not have error object"
                        
                    except ValidationError as e:
                        pytest.fail(f"Agent payload failed schema validation: {e}")
                        
                finally:
                    # Restore original time function if we mocked it
                    if original_get_time is not None:
                        import observability_logger.core.utils as utils
                        utils.get_current_timestamp_ms = original_get_time

    @given(
        trace_id=trace_ids,
        node_id=node_ids,
        name=names,
        description=descriptions
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_minimal_agent_payload_schema_compliance(
        self,
        trace_id,
        node_id,
        name,
        description
    ):
        """
        Test minimal agent payload with only required fields.
        
        Verifies that an agent node with minimal data still produces
        a valid payload that passes schema validation.
        """
        # Create mock emitter for this test run
        mock_emitter = MockEmitter()
        
        # Patch the emitter for this test
        with patch('observability_logger.core.emitter.get_emitter', return_value=mock_emitter):
            with patch('observability_logger.core.emitter._emitter', mock_emitter):
                # Create minimal agent node
                agent_node = AgentNode(
                    trace_id=trace_id,
                    node_id=node_id,
                    name=name,
                    description=description
                )
                
                # Create and complete the node
                success = agent_node.create()
                assert success, "Agent node creation should succeed"
                
                success = agent_node.complete(status="completed")
                assert success, "Agent node completion should succeed"
                
                # Get the payload
                completed_events = mock_emitter.get_events_by_type('node_completed')
                assert len(completed_events) == 1, "Should have exactly one node_completed event"
                
                payload = completed_events[0]['data']['payload']
                
                # Validate minimal payload
                try:
                    validated_payload = AgentPayloadSchema.model_validate(payload)
                    
                    # Verify required fields are present
                    assert validated_payload.node_id == node_id, "node_id should match"
                    assert validated_payload.type == "agent", "type should be 'agent'"
                    
                    # Optional fields can be None
                    # This tests that the schema allows None for optional fields
                    
                except ValidationError as e:
                    pytest.fail(f"Minimal agent payload failed schema validation: {e}")

    def test_agent_payload_with_invalid_step_type_fails_validation(self):
        """
        Test that agent payload with invalid step type fails validation.
        
        This is an edge case test to ensure the schema properly rejects
        invalid step types.
        """
        # Create mock emitter for this test run
        mock_emitter = MockEmitter()
        
        # Patch the emitter for this test
        with patch('observability_logger.core.emitter.get_emitter', return_value=mock_emitter):
            with patch('observability_logger.core.emitter._emitter', mock_emitter):
                # Create agent node with invalid step
                agent_node = AgentNode(
                    trace_id="test_trace",
                    node_id="test_node",
                    name="Test Agent",
                    description="Test"
                )
                
                agent_node.create()
                
                # Add invalid step directly to bypass node validation
                invalid_step = {
                    'type': 'invalid_type',  # Invalid step type
                    'content': 'some content',
                    'timestamp': 1700000000000
                }
                agent_node._steps.append(invalid_step)
                
                agent_node.complete(status="completed")
                
                # Get the payload
                completed_events = mock_emitter.get_events_by_type('node_completed')
                payload = completed_events[0]['data']['payload']
                
                # Validation should fail due to invalid step type
                with pytest.raises(ValidationError) as exc_info:
                    AgentPayloadSchema.model_validate(payload)
                
                # Verify the error is about step validation
                error_str = str(exc_info.value)
                assert "step type must be 'text' or 'tool_use'" in error_str

    def test_agent_payload_missing_step_fields_fails_validation(self):
        """
        Test that agent payload with missing required step fields fails validation.
        """
        # Create mock emitter for this test run
        mock_emitter = MockEmitter()
        
        # Patch the emitter for this test
        with patch('observability_logger.core.emitter.get_emitter', return_value=mock_emitter):
            with patch('observability_logger.core.emitter._emitter', mock_emitter):
                # Create agent node
                agent_node = AgentNode(
                    trace_id="test_trace",
                    node_id="test_node", 
                    name="Test Agent",
                    description="Test"
                )
                
                agent_node.create()
                
                # Add text step missing required content field
                invalid_text_step = {
                    'type': 'text',
                    # Missing 'content' field
                    'timestamp': 1700000000000
                }
                agent_node._steps.append(invalid_text_step)
                
                agent_node.complete(status="completed")
                
                # Get the payload
                completed_events = mock_emitter.get_events_by_type('node_completed')
                payload = completed_events[0]['data']['payload']
                
                # Validation should fail due to missing content field
                with pytest.raises(ValidationError) as exc_info:
                    AgentPayloadSchema.model_validate(payload)
                
                error_str = str(exc_info.value)
                assert "text step must have 'content' field" in error_str

    def test_agent_payload_missing_error_fields_fails_validation(self):
        """
        Test that agent payload with incomplete error object fails validation.
        """
        # Create mock emitter for this test run
        mock_emitter = MockEmitter()
        
        # Patch the emitter for this test
        with patch('observability_logger.core.emitter.get_emitter', return_value=mock_emitter):
            with patch('observability_logger.core.emitter._emitter', mock_emitter):
                # Create agent node
                agent_node = AgentNode(
                    trace_id="test_trace",
                    node_id="test_node",
                    name="Test Agent", 
                    description="Test"
                )
                
                agent_node.create()
                
                # Manually set incomplete error (missing error_type)
                agent_node._error = "Some error message"
                # Don't set _error_type, so it will be missing in payload
                
                # Complete with custom payload that has incomplete error
                incomplete_error_payload = {
                    'node_id': 'test_node',
                    'type': 'agent',
                    'input': None,
                    'output': None,
                    'execution_time_ms': None,
                    'steps': [],
                    'error': {
                        'error_message': 'Some error'
                        # Missing 'error_type' field
                    }
                }
                
                agent_node.complete(status="failed", payload=incomplete_error_payload)
                
                # Get the payload
                completed_events = mock_emitter.get_events_by_type('node_completed')
                payload = completed_events[0]['data']['payload']
                
                # Validation should fail due to missing error_type field
                with pytest.raises(ValidationError) as exc_info:
                    AgentPayloadSchema.model_validate(payload)
                
                error_str = str(exc_info.value)
                assert "error must have 'error_type' field" in error_str