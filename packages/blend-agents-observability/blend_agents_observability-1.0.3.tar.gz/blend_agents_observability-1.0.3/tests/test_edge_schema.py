"""
Property-based tests for edge created event schema compliance.

**Feature: observability-schema-testing, Property 4: Edge event schema compliance**

This module tests that edge_created events emitted by the ObservabilityLogger
conform to the DynamoDB schema defined in docs/data/README.md.

Requirements: 4.1, 4.2, 4.3
"""

from hypothesis import given, settings
from pydantic import ValidationError
from unittest.mock import patch

from observability_logger.models.agent_logger import Edge
from observability_logger.models.node import (
    MiscellaneousNode,
    ParallelNode,
    RouterNode,
    AgentNode
)

from .conftest import (
    trace_ids,
    node_ids,
    edge_ids,
    names,
    descriptions,
    node_types,
    MockEmitter,
)
from .schemas.dynamodb_schemas import EdgeCreatedSchema


class TestEdgeCreatedEventSchemaCompliance:
    """
    Property tests for edge created event schema compliance.
    
    **Feature: observability-schema-testing, Property 4: Edge event schema compliance**
    **Validates: Requirements 4.1, 4.2, 4.3**
    """

    @given(
        trace_id=trace_ids,
        source_node_id=node_ids,
        target_node_id=node_ids,
        edge_id=edge_ids,
        source_name=names,
        target_name=names,
        source_description=descriptions,
        target_description=descriptions,
    )
    @settings(max_examples=100, deadline=None)
    def test_edge_created_event_schema_compliance(
        self,
        trace_id: str,
        source_node_id: str,
        target_node_id: str,
        edge_id: str,
        source_name: str,
        target_name: str,
        source_description: str,
        target_description: str,
    ):
        """
        Property: For any edge created between two nodes, the emitted edge_created event
        SHALL contain all required fields: id (string), source_node_id (string), 
        target_node_id (string), the trace_id SHALL match the parent trace, and 
        timestamp SHALL be a positive integer in milliseconds.
        
        **Feature: observability-schema-testing, Property 4: Edge event schema compliance**
        **Validates: Requirements 4.1, 4.2, 4.3**
        """
        # Create fresh mock emitter for this example
        mock_emitter = MockEmitter()
        with patch('observability_logger.core.emitter.get_emitter', return_value=mock_emitter):
            with patch('observability_logger.core.emitter._emitter', mock_emitter):
                # Create source and target nodes (don't emit events for them)
                source_node = MiscellaneousNode(
                    trace_id=trace_id,
                    node_id=source_node_id,
                    name=source_name,
                    description=source_description,
                    auto_complete=False  # Don't auto-complete to avoid extra events
                )
                
                target_node = MiscellaneousNode(
                    trace_id=trace_id,
                    node_id=target_node_id,
                    name=target_name,
                    description=target_description,
                    auto_complete=False  # Don't auto-complete to avoid extra events
                )
                
                # Clear any events from node creation
                mock_emitter.clear()
                
                # Create edge between the nodes
                edge = Edge(
                    trace_id=trace_id,
                    source_node=source_node,
                    target_node=target_node,
                    edge_id=edge_id
                )
                
                # Get the emitted edge_created events
                edge_events = mock_emitter.get_events_by_type('edge_created')
                assert len(edge_events) == 1, "Expected exactly one edge_created event"
                
                event = edge_events[0]
                
                # Verify event envelope structure
                assert event['event_type'] == 'edge_created'
                assert event['trace_id'] == trace_id, "trace_id must match parent trace"
                assert isinstance(event['timestamp'], int)
                assert event['timestamp'] > 0, "Timestamp must be positive integer in milliseconds"
                
                # Validate data against EdgeCreatedSchema
                data = event['data']
                try:
                    validated = EdgeCreatedSchema.model_validate(data)
                except ValidationError as e:
                    raise AssertionError(f"Event data failed schema validation: {e}")
                
                # Verify all required fields are present and have correct types
                assert isinstance(validated.id, str), "id must be string"
                assert isinstance(validated.source_node_id, str), "source_node_id must be string"
                assert isinstance(validated.target_node_id, str), "target_node_id must be string"
                
                # Verify field values match input
                assert validated.id == edge_id
                assert validated.source_node_id == source_node_id
                assert validated.target_node_id == target_node_id

    @given(
        trace_id=trace_ids,
        source_node_id=node_ids,
        target_node_id=node_ids,
        source_type=node_types,
        target_type=node_types,
        source_name=names,
        target_name=names,
        source_description=descriptions,
        target_description=descriptions,
    )
    @settings(max_examples=100, deadline=None)
    def test_edge_between_different_node_types(
        self,
        trace_id: str,
        source_node_id: str,
        target_node_id: str,
        source_type: str,
        target_type: str,
        source_name: str,
        target_name: str,
        source_description: str,
        target_description: str,
    ):
        """
        Property: For any edge created between nodes of different types,
        the emitted edge_created event SHALL contain all required fields
        and the trace_id SHALL match the parent trace.
        
        **Feature: observability-schema-testing, Property 4: Edge event schema compliance**
        **Validates: Requirements 4.1, 4.2, 4.3**
        """
        # Create fresh mock emitter for this example
        mock_emitter = MockEmitter()
        with patch('observability_logger.core.emitter.get_emitter', return_value=mock_emitter):
            with patch('observability_logger.core.emitter._emitter', mock_emitter):
                # Create source node based on type
                if source_type == 'miscellaneous':
                    source_node = MiscellaneousNode(
                        trace_id=trace_id,
                        node_id=source_node_id,
                        name=source_name,
                        description=source_description,
                        auto_complete=False
                    )
                elif source_type == 'router':
                    source_node = RouterNode(
                        trace_id=trace_id,
                        node_id=source_node_id,
                        name=source_name,
                        description=source_description,
                        auto_complete=False
                    )
                elif source_type == 'parallel':
                    source_node = ParallelNode(
                        trace_id=trace_id,
                        node_id=source_node_id,
                        name=source_name,
                        description=source_description
                    )
                elif source_type == 'agent':
                    source_node = AgentNode(
                        trace_id=trace_id,
                        node_id=source_node_id,
                        name=source_name,
                        description=source_description
                    )
                else:
                    return  # Skip invalid types
                
                # Create target node based on type
                if target_type == 'miscellaneous':
                    target_node = MiscellaneousNode(
                        trace_id=trace_id,
                        node_id=target_node_id,
                        name=target_name,
                        description=target_description,
                        auto_complete=False
                    )
                elif target_type == 'router':
                    target_node = RouterNode(
                        trace_id=trace_id,
                        node_id=target_node_id,
                        name=target_name,
                        description=target_description,
                        auto_complete=False
                    )
                elif target_type == 'parallel':
                    target_node = ParallelNode(
                        trace_id=trace_id,
                        node_id=target_node_id,
                        name=target_name,
                        description=target_description
                    )
                elif target_type == 'agent':
                    target_node = AgentNode(
                        trace_id=trace_id,
                        node_id=target_node_id,
                        name=target_name,
                        description=target_description
                    )
                else:
                    return  # Skip invalid types
                
                # Clear any events from node creation
                mock_emitter.clear()
                
                # Create edge between the nodes
                edge = Edge(
                    trace_id=trace_id,
                    source_node=source_node,
                    target_node=target_node
                )
                
                # Get the emitted edge_created events
                edge_events = mock_emitter.get_events_by_type('edge_created')
                assert len(edge_events) == 1, "Expected exactly one edge_created event"
                
                event = edge_events[0]
                
                # Verify event envelope structure
                assert event['event_type'] == 'edge_created'
                assert event['trace_id'] == trace_id, "trace_id must match parent trace"
                assert isinstance(event['timestamp'], int)
                assert event['timestamp'] > 0, "Timestamp must be positive integer in milliseconds"
                
                # Validate data against EdgeCreatedSchema
                data = event['data']
                try:
                    validated = EdgeCreatedSchema.model_validate(data)
                except ValidationError as e:
                    raise AssertionError(f"Event data failed schema validation: {e}")
                
                # Verify field values match the nodes
                assert validated.source_node_id == source_node_id
                assert validated.target_node_id == target_node_id
                assert isinstance(validated.id, str), "Edge ID must be string"
                assert len(validated.id) > 0, "Edge ID must not be empty"

    @given(
        trace_id=trace_ids,
        source_node_id=node_ids,
        target_node_id=node_ids,
        source_name=names,
        target_name=names,
    )
    @settings(max_examples=100, deadline=None)
    def test_edge_auto_generated_id_format(
        self,
        trace_id: str,
        source_node_id: str,
        target_node_id: str,
        source_name: str,
        target_name: str,
    ):
        """
        Property: For any edge created without specifying an edge_id,
        the system SHALL auto-generate an edge_id that is a non-empty string.
        
        **Feature: observability-schema-testing, Property 4: Edge event schema compliance**
        **Validates: Requirements 4.1**
        """
        # Create fresh mock emitter for this example
        mock_emitter = MockEmitter()
        with patch('observability_logger.core.emitter.get_emitter', return_value=mock_emitter):
            with patch('observability_logger.core.emitter._emitter', mock_emitter):
                # Create source and target nodes
                source_node = MiscellaneousNode(
                    trace_id=trace_id,
                    node_id=source_node_id,
                    name=source_name,
                    auto_complete=False
                )
                
                target_node = MiscellaneousNode(
                    trace_id=trace_id,
                    node_id=target_node_id,
                    name=target_name,
                    auto_complete=False
                )
                
                # Clear any events from node creation
                mock_emitter.clear()
                
                # Create edge without specifying edge_id (should auto-generate)
                edge = Edge(
                    trace_id=trace_id,
                    source_node=source_node,
                    target_node=target_node
                    # edge_id not specified - should auto-generate
                )
                
                # Get the emitted edge_created events
                edge_events = mock_emitter.get_events_by_type('edge_created')
                assert len(edge_events) == 1, "Expected exactly one edge_created event"
                
                event = edge_events[0]
                data = event['data']
                
                # Validate data against EdgeCreatedSchema
                try:
                    validated = EdgeCreatedSchema.model_validate(data)
                except ValidationError as e:
                    raise AssertionError(f"Event data failed schema validation: {e}")
                
                # Verify auto-generated ID is valid
                assert isinstance(validated.id, str), "Auto-generated edge ID must be string"
                assert len(validated.id) > 0, "Auto-generated edge ID must not be empty"
                assert validated.id.startswith('edge_'), "Auto-generated edge ID should start with 'edge_'"

    @given(
        trace_id=trace_ids,
        source_node_id=node_ids,
        target_node_id=node_ids,
        source_name=names,
        target_name=names,
    )
    @settings(max_examples=100, deadline=None)
    def test_edge_event_contains_all_required_fields(
        self,
        trace_id: str,
        source_node_id: str,
        target_node_id: str,
        source_name: str,
        target_name: str,
    ):
        """
        Property: For any edge creation, the emitted edge_created event SHALL contain
        all required fields: id (string), source_node_id (string), target_node_id (string).
        
        **Feature: observability-schema-testing, Property 4: Edge event schema compliance**
        **Validates: Requirements 4.1**
        """
        # Create fresh mock emitter for this example
        mock_emitter = MockEmitter()
        with patch('observability_logger.core.emitter.get_emitter', return_value=mock_emitter):
            with patch('observability_logger.core.emitter._emitter', mock_emitter):
                # Create source and target nodes
                source_node = MiscellaneousNode(
                    trace_id=trace_id,
                    node_id=source_node_id,
                    name=source_name,
                    auto_complete=False
                )
                
                target_node = MiscellaneousNode(
                    trace_id=trace_id,
                    node_id=target_node_id,
                    name=target_name,
                    auto_complete=False
                )
                
                # Clear any events from node creation
                mock_emitter.clear()
                
                # Create edge
                edge = Edge(
                    trace_id=trace_id,
                    source_node=source_node,
                    target_node=target_node
                )
                
                # Get the emitted edge_created events
                edge_events = mock_emitter.get_events_by_type('edge_created')
                assert len(edge_events) == 1, "Expected exactly one edge_created event"
                
                event = edge_events[0]
                data = event['data']
                
                # Validate data against EdgeCreatedSchema
                try:
                    validated = EdgeCreatedSchema.model_validate(data)
                except ValidationError as e:
                    raise AssertionError(f"Event data failed schema validation: {e}")
                
                # Verify all required fields are present and have correct types
                assert hasattr(validated, 'id'), "id field must be present"
                assert hasattr(validated, 'source_node_id'), "source_node_id field must be present"
                assert hasattr(validated, 'target_node_id'), "target_node_id field must be present"
                
                assert isinstance(validated.id, str), "id must be string"
                assert isinstance(validated.source_node_id, str), "source_node_id must be string"
                assert isinstance(validated.target_node_id, str), "target_node_id must be string"
                
                # Verify field values are not empty
                assert len(validated.id) > 0, "id must not be empty"
                assert len(validated.source_node_id) > 0, "source_node_id must not be empty"
                assert len(validated.target_node_id) > 0, "target_node_id must not be empty"