"""
Property-based tests for discrete level filtering logic.

Tests that discrete logging level only shows principal events and filters out
non-principal events as specified in Requirements 4.1.

Requirements: 4.1
"""

import pytest
import io
from contextlib import redirect_stdout, redirect_stderr
from hypothesis import given, strategies as st, settings, HealthCheck
from unittest.mock import patch

from observability_logger.config.logging_config import LoggingLevel
from observability_logger.core.logging_manager import LoggingManager
from observability_logger.models.node import Node

from .conftest import (
    trace_ids, node_ids, names, descriptions, node_types, 
    execution_time_ms, MockEmitter
)


class MockNode:
    """Mock node for testing purposes."""
    
    def __init__(self, node_id: str, name: str, node_type: str, trace_id: str):
        self.node_id = node_id
        self.name = name
        self.node_type = node_type
        self.trace_id = trace_id
        self.status = "created"
        self.description = f"Test {node_type} node"
        self.parent_node_id = None
        self.created_at = None
        self.completed_at = None
        self.output = None
        self.error = None


class TestDiscreteLevelFiltering:
    """
    Property-based tests for discrete level filtering logic.
    
    **Feature: enhanced-logging-strategy, Property 10: Discrete Level Filtering**
    **Validates: Requirements 4.1**
    """

    @given(
        trace_id=trace_ids,
        workflow_id=trace_ids,  # Reuse trace_ids strategy for workflow_id
        title=names,
        node_id=node_ids,
        node_name=names,
        node_type=node_types,
        duration_ms=st.one_of(st.none(), execution_time_ms)
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_discrete_level_shows_only_principal_events(
        self,
        trace_id,
        workflow_id,
        title,
        node_id,
        node_name,
        node_type,
        duration_ms
    ):
        """
        **Property 10: Discrete Level Filtering**
        
        *For any* set of logging events when level is discrete, only principal events 
        (node creation, trace completion) should appear in the output.
        
        **Validates: Requirements 4.1**
        """
        # Capture output to verify filtering
        output = io.StringIO()
        
        with redirect_stdout(output), redirect_stderr(output):
            # Create manager with discrete level
            manager = LoggingManager(LoggingLevel.DISCRETE)
            
            # Test principal events - these SHOULD appear in discrete mode
            manager.log_trace_created(trace_id, title, workflow_id)
            
            mock_node = MockNode(node_id, node_name, node_type, trace_id)
            manager.log_node_created(mock_node)
            manager.log_node_completed(mock_node, duration_ms)
            
            manager.log_trace_completed(trace_id, title, "completed", duration_ms)
            
            # Test non-principal events - these should NOT appear in discrete mode
            manager.log_debug("Debug message that should be filtered", {
                'component': 'test',
                'operation': 'filtering'
            })
            
            # Create a mock edge for edge logging test
            class MockEdge:
                def __init__(self, edge_id: str, source_node: MockNode, target_node: MockNode, trace_id: str):
                    self.edge_id = edge_id
                    self.source_node = source_node
                    self.target_node = target_node
                    self.trace_id = trace_id
                    self.created_at = None
                    self.edge_type = "default"
            
            target_node = MockNode(node_id + "_target", node_name + "_target", node_type, trace_id)
            mock_edge = MockEdge(node_id + "_edge", mock_node, target_node, trace_id)
            manager.log_edge_created(mock_edge)
        
        output_text = output.getvalue()
        
        # Verify principal events are present
        # Note: The exact format may vary, but key information should be present
        
        # Check for trace events (principal)
        trace_indicators = ["Started:", "TRACE STARTED", title]
        has_trace_start = any(indicator in output_text for indicator in trace_indicators)
        assert has_trace_start, f"Trace creation should appear in discrete mode. Output: {output_text}"
        
        completion_indicators = ["completed", "✅", "TRACE", title]
        has_trace_completion = any(indicator in output_text for indicator in completion_indicators)
        assert has_trace_completion, f"Trace completion should appear in discrete mode. Output: {output_text}"
        
        # Check for node events (principal)
        node_indicators = [node_name, node_type, "📦", "NODE"]
        has_node_creation = any(indicator in output_text for indicator in node_indicators)
        assert has_node_creation, f"Node creation should appear in discrete mode. Output: {output_text}"
        
        # Verify non-principal events are filtered out
        # Debug messages should not appear in discrete mode
        debug_indicators = ["DEBUG:", "Debug message", "component", "operation"]
        has_debug = any(indicator in output_text for indicator in debug_indicators)
        assert not has_debug, f"Debug messages should be filtered out in discrete mode. Output: {output_text}"
        
        # Edge events should not appear in discrete mode (they are verbose-only)
        edge_indicators = ["EDGE CREATED", "🔗", "edge"]
        has_edge = any(indicator in output_text for indicator in edge_indicators)
        assert not has_edge, f"Edge events should be filtered out in discrete mode. Output: {output_text}"

    @given(
        trace_id=trace_ids,
        workflow_id=trace_ids,
        title=names
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_discrete_level_error_override(
        self,
        trace_id,
        workflow_id,
        title
    ):
        """
        Test that errors always display in discrete mode (Requirements 4.5).
        
        This verifies the error display override behavior where errors
        should appear regardless of the logging level.
        """
        # Capture output to verify error display
        output = io.StringIO()
        
        with redirect_stdout(output), redirect_stderr(output):
            # Create manager with discrete level
            manager = LoggingManager(LoggingLevel.DISCRETE)
            
            # Log an error - should always appear regardless of level
            error_message = f"Test error for trace {trace_id}"
            test_exception = Exception("Test exception")
            manager.log_error(error_message, test_exception)
            
            # Log a warning - should appear in discrete mode
            warning_message = f"Test warning for trace {trace_id}"
            manager.log_warning(warning_message)
        
        output_text = output.getvalue()
        
        # Verify error appears (Requirements 4.5)
        error_indicators = ["ERROR:", error_message, "❌"]
        has_error = any(indicator in output_text for indicator in error_indicators)
        assert has_error, f"Errors should always display regardless of logging level. Output: {output_text}"
        
        # Verify warning appears (warnings are principal events)
        warning_indicators = ["WARNING:", warning_message, "⚠️"]
        has_warning = any(indicator in output_text for indicator in warning_indicators)
        assert has_warning, f"Warnings should appear in discrete mode. Output: {output_text}"

    @given(
        trace_id=trace_ids,
        node_id=node_ids,
        node_name=names,
        node_type=node_types
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_discrete_vs_verbose_filtering_difference(
        self,
        trace_id,
        node_id,
        node_name,
        node_type
    ):
        """
        Test that discrete and verbose modes show different amounts of information.
        
        This verifies that verbose mode shows more events than discrete mode,
        confirming the filtering logic works correctly.
        """
        # Test discrete mode
        discrete_output = io.StringIO()
        with redirect_stdout(discrete_output), redirect_stderr(discrete_output):
            discrete_manager = LoggingManager(LoggingLevel.DISCRETE)
            
            mock_node = MockNode(node_id, node_name, node_type, trace_id)
            discrete_manager.log_node_created(mock_node)
            discrete_manager.log_debug("Debug message for discrete test")
        
        discrete_text = discrete_output.getvalue()
        
        # Test verbose mode
        verbose_output = io.StringIO()
        with redirect_stdout(verbose_output), redirect_stderr(verbose_output):
            verbose_manager = LoggingManager(LoggingLevel.VERBOSE)
            
            mock_node = MockNode(node_id, node_name, node_type, trace_id)
            verbose_manager.log_node_created(mock_node)
            verbose_manager.log_debug("Debug message for verbose test")
        
        verbose_text = verbose_output.getvalue()
        
        # Verify both modes show node creation (principal event)
        node_indicators = [node_name, node_type]
        discrete_has_node = any(indicator in discrete_text for indicator in node_indicators)
        verbose_has_node = any(indicator in verbose_text for indicator in node_indicators)
        
        assert discrete_has_node, f"Discrete mode should show node creation. Output: {discrete_text}"
        assert verbose_has_node, f"Verbose mode should show node creation. Output: {verbose_text}"
        
        # Verify only verbose mode shows debug messages
        debug_indicators = ["DEBUG:", "Debug message"]
        discrete_has_debug = any(indicator in discrete_text for indicator in debug_indicators)
        verbose_has_debug = any(indicator in verbose_text for indicator in debug_indicators)
        
        assert not discrete_has_debug, f"Discrete mode should not show debug messages. Output: {discrete_text}"
        assert verbose_has_debug, f"Verbose mode should show debug messages. Output: {verbose_text}"
        
        # Verify verbose mode generally produces more output
        # This is a general check that verbose mode is more verbose
        assert len(verbose_text) >= len(discrete_text), "Verbose mode should produce at least as much output as discrete mode"

    def test_principal_events_classification(self):
        """
        Test that the principal events classification is correct.
        
        This is a unit test to verify the _is_principal_event method
        correctly identifies which events are principal.
        """
        manager = LoggingManager(LoggingLevel.DISCRETE)
        
        # Principal events (should return True)
        principal_events = [
            'trace_created',
            'trace_completed', 
            'node_created',
            'node_completed',
            'error',
            'warning'
        ]
        
        for event_type in principal_events:
            is_principal = manager._is_principal_event(event_type)
            assert is_principal, f"'{event_type}' should be classified as a principal event"
        
        # Non-principal events (should return False)
        non_principal_events = [
            'edge_created',
            'debug',
            'internal_event',
            'metadata_update',
            'performance_metric'
        ]
        
        for event_type in non_principal_events:
            is_principal = manager._is_principal_event(event_type)
            assert not is_principal, f"'{event_type}' should not be classified as a principal event"

    @given(
        event_types=st.lists(
            st.sampled_from([
                'trace_created', 'trace_completed', 'node_created', 'node_completed',
                'error', 'warning', 'edge_created', 'debug', 'internal_event'
            ]),
            min_size=1,
            max_size=10
        )
    )
    def test_should_log_event_consistency(self, event_types):
        """
        Test that _should_log_event method is consistent with level settings.
        
        This property test verifies that the filtering logic is consistent
        across different combinations of event types and logging levels.
        """
        # Test all three logging levels
        levels = [LoggingLevel.SILENT, LoggingLevel.DISCRETE, LoggingLevel.VERBOSE]
        
        for level in levels:
            manager = LoggingManager(level)
            
            for event_type in event_types:
                should_log = manager._should_log_event(event_type)
                
                if level == LoggingLevel.SILENT:
                    # Silent mode: no events should be logged
                    assert not should_log, f"SILENT level should not log any events, but would log '{event_type}'"
                
                elif level == LoggingLevel.VERBOSE:
                    # Verbose mode: all events should be logged
                    assert should_log, f"VERBOSE level should log all events, but would not log '{event_type}'"
                
                elif level == LoggingLevel.DISCRETE:
                    # Discrete mode: only principal events should be logged
                    is_principal = manager._is_principal_event(event_type)
                    assert should_log == is_principal, f"DISCRETE level should log principal events only, but '{event_type}' (principal={is_principal}) would be logged={should_log}"