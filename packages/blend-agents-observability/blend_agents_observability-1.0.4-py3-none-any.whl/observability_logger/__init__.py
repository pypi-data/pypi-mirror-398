"""
Observability Logger for Strands Agents.

This package provides instrumentation for capturing execution graphs
of multi-step AI agent workflows.

Usage:
    from observability_logger import AgentLogger

    logger = AgentLogger(trace_id="trace_123")
    node = logger.miscellaneous("node_1", {"name": "Validation"}, "content")
    logger.end()
"""

import logging

from .models.agent_logger import AgentLogger, Edge
from .models.node import (
    Node,
    MiscellaneousNode,
    ParallelNode,
    RouterNode,
    AgentNode
)
from .config.settings import ObservabilityConfig, get_config, reset_config
from .config.logging_config import LoggingLevel, LoggingConfig
from .core.utils import generate_id, get_current_timestamp_ms
from .core.logging_manager import (
    get_logging_manager,
    set_logging_level,
    is_logging_enabled,
    get_compatibility_info,
    validate_logging_compatibility,
    restore_original_logging
)

# Version
__version__ = "0.1.0"

# Public API
__all__ = [
    'AgentLogger',
    'Edge',
    'Node',
    'MiscellaneousNode',
    'ParallelNode',
    'RouterNode',
    'AgentNode',
    'ObservabilityConfig',
    'get_config',
    'reset_config',
    'generate_id',
    'get_current_timestamp_ms',
    'LoggingLevel',
    'LoggingConfig',
    'get_logging_manager',
    'set_logging_level',
    'is_logging_enabled',
    'get_compatibility_info',
    'validate_logging_compatibility',
    'restore_original_logging'
]

# Configure package-level logger
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
