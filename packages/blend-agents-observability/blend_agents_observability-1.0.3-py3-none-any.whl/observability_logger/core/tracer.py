"""Core tracing functionality for the observability logger.

This module provides the `TraceManager`, a class responsible for managing the
lifecycle of a single trace. It handles the creation and completion events of a
trace, ensuring that state transitions are valid and that the corresponding
events are emitted to Kinesis.

This is an internal component used by the `AgentLogger` and is not intended for
direct use by end-users.
"""

import logging
from typing import Optional, Dict, Any

from ..core.emitter import get_emitter
from ..core.utils import get_current_timestamp_ms
from ..models.events import (
    ObservabilityEvent,
    TraceUpdatedData,
    TraceStatus,
)

logger = logging.getLogger(__name__)


class TraceManager:
    """Manages the lifecycle and event emission for a single trace.

    This class is responsible for emitting `trace_updated` events to Kinesis.
    It tracks the state of a trace to ensure a valid lifecycle (a trace must be
    created before it can be updated or completed).

    The backend service performs an "upsert" operation for traces, meaning that
    the first `trace_updated` event for a given `trace_id` will create the
    trace record.

    Attributes:
        trace_id (str): The unique identifier for this trace.
        workflow_id (str): An identifier for grouping related traces.
        title (str): A human-readable title for the trace.
        parent_trace_id (Optional[str]): The ID of a parent trace, used for
            creating hierarchical traces.
    """

    def __init__(
        self,
        trace_id: str,
        workflow_id: str,
        title: str,
        parent_trace_id: Optional[str] = None,
        assume_created: bool = False,
    ):
        """Initializes the TraceManager.

        Args:
            trace_id: A unique identifier for the trace.
            workflow_id: The identifier for the overarching workflow.
            title: A human-readable title for display purposes.
            parent_trace_id: An optional parent trace ID for child traces.
            assume_created: If True, assumes the trace was already created by
                another instance (used when auto_create=False in AgentLogger).
        """
        self.trace_id = trace_id
        self.workflow_id = workflow_id
        self.title = title
        self.parent_trace_id = parent_trace_id
        self._emitter = get_emitter()
        self._created = assume_created
        self._completed = False

    def create(self) -> bool:
        """Emits a `trace_updated` event to create or upsert the trace.

        This method sends the initial event for a trace with a status of
        'running'. The backend service will create a new trace record if one
        does not already exist for the `trace_id`.

        Returns:
            True if the event was emitted successfully, False otherwise.
        """
        if self._created:
            logger.warning("Trace %s already created. Skipping.", self.trace_id)
            return False

        data = TraceUpdatedData(
            status="running",
            workflow_id=self.workflow_id,
            title=self.title,
            parent_trace_id=self.parent_trace_id,
            final_output=None,
        )

        event = ObservabilityEvent(
            event_type="trace_updated",
            timestamp=get_current_timestamp_ms(),
            trace_id=self.trace_id,
            data=data.model_dump(exclude_none=True),
        )

        success = self._emitter.emit(event)
        if success:
            self._created = True
            logger.info("Created trace: %s", self.trace_id)
        return success

    def update(
        self,
        status: TraceStatus,
        final_output: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Emits a `trace_updated` event to update the trace's status.

        This method should be called to mark a trace as 'completed', 'failed',
        or 'partial'. It requires that the trace has already been created.
        Once a trace is marked as 'completed' or 'failed', no further updates
        are allowed.

        Args:
            status: The final status of the trace.
            final_output: An optional dictionary containing the final result
                or a summary of the workflow's execution. This data is stored
                with the trace for later analysis.

        Returns:
            True if the event was emitted successfully, False otherwise.
        """
        if not self._created:
            logger.warning(
                "Trace %s not created yet. Call create() before update().",
                self.trace_id,
            )
            return False

        if self._completed:
            logger.warning(
                "Trace %s already completed. Skipping update.", self.trace_id
            )
            return False

        data = TraceUpdatedData(
            status=status,
            workflow_id=self.workflow_id,
            title=self.title,
            parent_trace_id=self.parent_trace_id,
            final_output=final_output,
        )

        event = ObservabilityEvent(
            event_type="trace_updated",
            timestamp=get_current_timestamp_ms(),
            trace_id=self.trace_id,
            data=data.model_dump(exclude_none=True),
        )

        success = self._emitter.emit(event)
        if success and status in ["completed", "failed"]:
            self._completed = True
            logger.info(
                "Completed trace: %s with status %s", self.trace_id, status
            )
        return success
