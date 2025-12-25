"""
Unit tests for MockEmitter class.

Tests verify that MockEmitter correctly captures and filters events
without requiring AWS connectivity.

Requirements: 9.1
"""

import sys
from pathlib import Path

import pytest

# Add tests directory to path to import conftest
sys.path.insert(0, str(Path(__file__).parent))

from observability_logger.models.events import ObservabilityEvent
from observability_logger.core.utils import get_current_timestamp_ms

# Import MockEmitter from conftest (pytest loads it automatically, but we need direct import for tests)
from tests.conftest import MockEmitter


class TestMockEmitter:
    """Tests for MockEmitter functionality."""
    
    def test_emit_captures_event(self):
        """Test that emit() captures events correctly."""
        emitter = MockEmitter()
        
        event = ObservabilityEvent(
            event_type='trace_updated',
            timestamp=get_current_timestamp_ms(),
            trace_id='test_trace_1',
            data={'status': 'running', 'workflow_id': 'test_workflow'}
        )
        
        result = emitter.emit(event)
        
        assert result is True
        assert len(emitter.events) == 1
        assert len(emitter.event_dicts) == 1
        assert emitter.events[0] == event
        assert emitter.event_dicts[0]['trace_id'] == 'test_trace_1'
        assert emitter.event_dicts[0]['event_type'] == 'trace_updated'
    
    def test_emit_captures_multiple_events(self):
        """Test that emit() captures multiple events in order."""
        emitter = MockEmitter()
        
        events = [
            ObservabilityEvent(
                event_type='trace_updated',
                timestamp=get_current_timestamp_ms(),
                trace_id='test_trace_1',
                data={'status': 'running'}
            ),
            ObservabilityEvent(
                event_type='node_created',
                timestamp=get_current_timestamp_ms(),
                trace_id='test_trace_1',
                data={'id': 'node_1', 'type': 'agent', 'name': 'Test', 'description': ''}
            ),
            ObservabilityEvent(
                event_type='node_completed',
                timestamp=get_current_timestamp_ms(),
                trace_id='test_trace_1',
                data={'id': 'node_1', 'status': 'completed'}
            )
        ]
        
        for event in events:
            emitter.emit(event)
        
        assert len(emitter.events) == 3
        assert emitter.events[0].event_type == 'trace_updated'
        assert emitter.events[1].event_type == 'node_created'
        assert emitter.events[2].event_type == 'node_completed'
    
    def test_get_events_by_type_filters_correctly(self):
        """Test that get_events_by_type() filters events by type."""
        emitter = MockEmitter()
        
        # Emit mixed event types
        emitter.emit(ObservabilityEvent(
            event_type='trace_updated',
            timestamp=get_current_timestamp_ms(),
            trace_id='trace_1',
            data={'status': 'running'}
        ))
        emitter.emit(ObservabilityEvent(
            event_type='node_created',
            timestamp=get_current_timestamp_ms(),
            trace_id='trace_1',
            data={'id': 'node_1', 'type': 'agent', 'name': 'Test', 'description': ''}
        ))
        emitter.emit(ObservabilityEvent(
            event_type='trace_updated',
            timestamp=get_current_timestamp_ms(),
            trace_id='trace_1',
            data={'status': 'completed'}
        ))
        emitter.emit(ObservabilityEvent(
            event_type='edge_created',
            timestamp=get_current_timestamp_ms(),
            trace_id='trace_1',
            data={'id': 'edge_1', 'source_node_id': 'node_1', 'target_node_id': 'node_2'}
        ))
        
        # Filter by type
        trace_events = emitter.get_events_by_type('trace_updated')
        node_events = emitter.get_events_by_type('node_created')
        edge_events = emitter.get_events_by_type('edge_created')
        nonexistent = emitter.get_events_by_type('nonexistent_type')
        
        assert len(trace_events) == 2
        assert len(node_events) == 1
        assert len(edge_events) == 1
        assert len(nonexistent) == 0
        
        # Verify content
        assert all(e['event_type'] == 'trace_updated' for e in trace_events)
        assert trace_events[0]['data']['status'] == 'running'
        assert trace_events[1]['data']['status'] == 'completed'
    
    def test_clear_resets_state(self):
        """Test that clear() removes all captured events."""
        emitter = MockEmitter()
        
        # Add some events
        emitter.emit(ObservabilityEvent(
            event_type='trace_updated',
            timestamp=get_current_timestamp_ms(),
            trace_id='trace_1',
            data={'status': 'running'}
        ))
        emitter.emit(ObservabilityEvent(
            event_type='node_created',
            timestamp=get_current_timestamp_ms(),
            trace_id='trace_1',
            data={'id': 'node_1', 'type': 'agent', 'name': 'Test', 'description': ''}
        ))
        
        assert len(emitter.events) == 2
        assert len(emitter.event_dicts) == 2
        
        # Clear
        emitter.clear()
        
        assert len(emitter.events) == 0
        assert len(emitter.event_dicts) == 0
        assert emitter.get_events_count() == 0
    
    def test_get_last_event(self):
        """Test that get_last_event() returns the most recent event."""
        emitter = MockEmitter()
        
        # No events
        assert emitter.get_last_event() is None
        
        # Add events
        emitter.emit(ObservabilityEvent(
            event_type='trace_updated',
            timestamp=1000,
            trace_id='trace_1',
            data={'status': 'running'}
        ))
        
        last = emitter.get_last_event()
        assert last is not None
        assert last['event_type'] == 'trace_updated'
        
        emitter.emit(ObservabilityEvent(
            event_type='node_created',
            timestamp=2000,
            trace_id='trace_1',
            data={'id': 'node_1', 'type': 'agent', 'name': 'Test', 'description': ''}
        ))
        
        last = emitter.get_last_event()
        assert last['event_type'] == 'node_created'
    
    def test_get_events_count(self):
        """Test that get_events_count() returns correct count."""
        emitter = MockEmitter()
        
        assert emitter.get_events_count() == 0
        
        emitter.emit(ObservabilityEvent(
            event_type='trace_updated',
            timestamp=get_current_timestamp_ms(),
            trace_id='trace_1',
            data={'status': 'running'}
        ))
        
        assert emitter.get_events_count() == 1
        
        emitter.emit(ObservabilityEvent(
            event_type='node_created',
            timestamp=get_current_timestamp_ms(),
            trace_id='trace_1',
            data={'id': 'node_1', 'type': 'agent', 'name': 'Test', 'description': ''}
        ))
        
        assert emitter.get_events_count() == 2



class TestMockEmitterFixtures:
    """Tests for pytest fixtures using MockEmitter."""
    
    def test_mock_emitter_fixture(self, mock_emitter):
        """Test that mock_emitter fixture provides working MockEmitter."""
        from observability_logger.models.agent_logger import AgentLogger
        
        # Create a logger - this should use the mock emitter
        logger = AgentLogger(
            trace_id="fixture_test_trace",
            workflow_id="test_workflow",
            title="Fixture Test"
        )
        
        # Verify events were captured
        assert mock_emitter.get_events_count() >= 1
        trace_events = mock_emitter.get_events_by_type('trace_updated')
        assert len(trace_events) >= 1
        assert trace_events[0]['trace_id'] == "fixture_test_trace"
    
    def test_agent_logger_fixture(self, agent_logger, mock_emitter):
        """Test that agent_logger fixture provides pre-configured logger."""
        # agent_logger should already have created a trace
        assert agent_logger.trace_id == "test_trace_123"
        assert agent_logger.workflow_id == "test_workflow"
        
        # Verify trace event was captured
        trace_events = mock_emitter.get_events_by_type('trace_updated')
        assert len(trace_events) >= 1
        assert trace_events[0]['trace_id'] == "test_trace_123"
    
    def test_mock_emitter_isolation(self, mock_emitter):
        """Test that mock_emitter provides clean state for each test."""
        # Should start with no events (from previous tests)
        # Note: This test verifies isolation between tests
        from observability_logger.models.agent_logger import AgentLogger
        
        logger = AgentLogger(
            trace_id="isolation_test",
            workflow_id="test",
            title="Isolation Test"
        )
        
        # Only events from this test should be present
        all_events = mock_emitter.event_dicts
        assert all(e['trace_id'] == "isolation_test" for e in all_events)
