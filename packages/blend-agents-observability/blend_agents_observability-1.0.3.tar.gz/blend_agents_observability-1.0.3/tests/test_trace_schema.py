"""
Property-based tests for trace event schema compliance.

**Feature: observability-schema-testing, Property 1: Trace event schema compliance**

This module tests that trace_updated events emitted by the ObservabilityLogger
conform to the DynamoDB schema defined in docs/data/README.md.

Requirements: 1.1, 1.2, 1.3, 1.4
"""

from hypothesis import given, settings
from pydantic import ValidationError
from unittest.mock import patch

from observability_logger.models.agent_logger import AgentLogger

from .conftest import (
    trace_ids,
    workflow_ids,
    names,
    trace_statuses,
    MockEmitter,
)
from .schemas.dynamodb_schemas import TraceSchema


class TestTraceEventSchemaCompliance:
    """
    Property tests for trace event schema compliance.
    
    **Feature: observability-schema-testing, Property 1: Trace event schema compliance**
    **Validates: Requirements 1.1, 1.2, 1.3, 1.4**
    """

    @given(
        trace_id=trace_ids,
        workflow_id=workflow_ids,
        title=names,
    )
    @settings(max_examples=100, deadline=None)
    def test_trace_creation_emits_valid_schema(
        self,
        trace_id: str,
        workflow_id: str,
        title: str,
    ):
        """
        Property: For any valid trace creation parameters, the emitted trace_updated
        event SHALL contain all required fields with correct types and status='running'.
        
        **Feature: observability-schema-testing, Property 1: Trace event schema compliance**
        **Validates: Requirements 1.1, 1.2, 1.4**
        """
        # Create fresh mock emitter for this example
        mock_emitter = MockEmitter()
        with patch('observability_logger.core.emitter.get_emitter', return_value=mock_emitter):
            with patch('observability_logger.core.emitter._emitter', mock_emitter):
                # Create a trace with random valid data
                AgentLogger(
                    trace_id=trace_id,
                    workflow_id=workflow_id,
                    title=title,
                )
                
                # Get the emitted trace_updated events
                trace_events = mock_emitter.get_events_by_type('trace_updated')
                assert len(trace_events) == 1, "Expected exactly one trace_updated event"
                
                event = trace_events[0]
                
                # Verify event envelope structure
                assert event['event_type'] == 'trace_updated'
                assert event['trace_id'] == trace_id
                assert isinstance(event['timestamp'], int)
                assert event['timestamp'] > 0, "Timestamp must be positive integer in milliseconds"
                
                # Validate data against TraceSchema
                data = event['data']
                try:
                    validated = TraceSchema.model_validate(data)
                except ValidationError as e:
                    raise AssertionError(f"Event data failed schema validation: {e}")
                
                # Verify initial creation has status='running'
                assert validated.status == 'running', "Initial trace status must be 'running'"
                
                # Verify workflow_id and title are present for creation
                assert validated.workflow_id == workflow_id
                assert validated.title == title

    @given(
        trace_id=trace_ids,
        workflow_id=workflow_ids,
        title=names,
        completion_status=trace_statuses.filter(lambda s: s != 'running'),
    )
    @settings(max_examples=100, deadline=None)
    def test_trace_completion_emits_valid_schema(
        self,
        trace_id: str,
        workflow_id: str,
        title: str,
        completion_status: str,
    ):
        """
        Property: For any valid trace completion, the emitted trace_updated event
        SHALL contain status field with valid value from ["completed", "failed", "partial"].
        
        **Feature: observability-schema-testing, Property 1: Trace event schema compliance**
        **Validates: Requirements 1.2, 1.4**
        """
        # Create fresh mock emitter for this example
        mock_emitter = MockEmitter()
        with patch('observability_logger.core.emitter.get_emitter', return_value=mock_emitter):
            with patch('observability_logger.core.emitter._emitter', mock_emitter):
                # Create and complete a trace
                logger = AgentLogger(
                    trace_id=trace_id,
                    workflow_id=workflow_id,
                    title=title,
                )
                logger.end(status=completion_status, final_output={"result": "test"})
                
                # Get all trace_updated events (creation + completion)
                trace_events = mock_emitter.get_events_by_type('trace_updated')
                assert len(trace_events) == 2, "Expected two trace_updated events (creation + completion)"
                
                # Validate completion event (second one)
                completion_event = trace_events[1]
                
                # Verify event envelope
                assert completion_event['event_type'] == 'trace_updated'
                assert completion_event['trace_id'] == trace_id
                assert isinstance(completion_event['timestamp'], int)
                assert completion_event['timestamp'] > 0
                
                # Validate data against TraceSchema
                data = completion_event['data']
                try:
                    validated = TraceSchema.model_validate(data)
                except ValidationError as e:
                    raise AssertionError(f"Completion event data failed schema validation: {e}")
                
                # Verify completion status matches
                assert validated.status == completion_status

    @given(
        trace_id=trace_ids,
        parent_trace_id=trace_ids,
        workflow_id=workflow_ids,
        title=names,
    )
    @settings(max_examples=100, deadline=None)
    def test_child_trace_includes_parent_trace_id(
        self,
        trace_id: str,
        parent_trace_id: str,
        workflow_id: str,
        title: str,
    ):
        """
        Property: For any child trace created with a parent_trace_id, the emitted
        trace_updated event SHALL include parent_trace_id field pointing to the parent trace.
        
        **Feature: observability-schema-testing, Property 1: Trace event schema compliance**
        **Validates: Requirements 1.3**
        """
        # Create fresh mock emitter for this example
        mock_emitter = MockEmitter()
        with patch('observability_logger.core.emitter.get_emitter', return_value=mock_emitter):
            with patch('observability_logger.core.emitter._emitter', mock_emitter):
                # Create a child trace with parent_trace_id
                AgentLogger(
                    trace_id=trace_id,
                    workflow_id=workflow_id,
                    title=title,
                    parent_trace_id=parent_trace_id,
                )
                
                # Get the emitted trace_updated events
                trace_events = mock_emitter.get_events_by_type('trace_updated')
                assert len(trace_events) == 1, "Expected exactly one trace_updated event"
                
                event = trace_events[0]
                
                # Validate data against TraceSchema
                data = event['data']
                try:
                    validated = TraceSchema.model_validate(data)
                except ValidationError as e:
                    raise AssertionError(f"Child trace event data failed schema validation: {e}")
                
                # Verify parent_trace_id is included
                assert validated.parent_trace_id == parent_trace_id, \
                    f"Child trace must include parent_trace_id. Expected {parent_trace_id}, got {validated.parent_trace_id}"

    @given(
        trace_id=trace_ids,
        workflow_id=workflow_ids,
        title=names,
    )
    @settings(max_examples=100, deadline=None)
    def test_trace_timestamp_is_positive_milliseconds(
        self,
        trace_id: str,
        workflow_id: str,
        title: str,
    ):
        """
        Property: For any trace event, the timestamp field SHALL be a positive integer
        representing Unix epoch time in milliseconds.
        
        **Feature: observability-schema-testing, Property 1: Trace event schema compliance**
        **Validates: Requirements 1.4**
        """
        # Create fresh mock emitter for this example
        mock_emitter = MockEmitter()
        with patch('observability_logger.core.emitter.get_emitter', return_value=mock_emitter):
            with patch('observability_logger.core.emitter._emitter', mock_emitter):
                # Create a trace
                AgentLogger(
                    trace_id=trace_id,
                    workflow_id=workflow_id,
                    title=title,
                )
                
                # Get the emitted trace_updated events
                trace_events = mock_emitter.get_events_by_type('trace_updated')
                assert len(trace_events) == 1
                
                event = trace_events[0]
                timestamp = event['timestamp']
                
                # Verify timestamp is positive integer
                assert isinstance(timestamp, int), f"Timestamp must be int, got {type(timestamp)}"
                assert timestamp > 0, "Timestamp must be positive"
                
                # Verify timestamp is in milliseconds range (reasonable bounds)
                # Unix epoch in ms for year 2020: ~1577836800000
                # Unix epoch in ms for year 2100: ~4102444800000
                assert timestamp > 1577836800000, "Timestamp appears to be in seconds, not milliseconds"
                assert timestamp < 4102444800000, "Timestamp is unreasonably far in the future"
