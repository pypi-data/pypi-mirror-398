"""
LoggingManager for enhanced observability logging strategy.

This module provides:
- LoggingManager singleton class for global logging management
- Thread-safe logging operations
- Level-based filtering logic
- Methods for logging different event types (trace, node, edge)
- Integration with ColoredFormatter and LoggingConfig
- Python logging compatibility and namespace isolation
"""

import logging
import threading
import sys
from typing import Optional, Dict, Any, TYPE_CHECKING, List
from datetime import datetime

from ..config.logging_config import LoggingConfig, LoggingLevel, get_logging_config, validate_logging_level
from ..core.formatter import ColoredFormatter, create_colored_formatter

if TYPE_CHECKING:
    from ..models.node import Node
    from ..models.agent_logger import Edge

# Global logger for this module
logger = logging.getLogger(__name__)


class LoggingManager:
    """
    Singleton class for managing observability logging across the application.
    
    LoggingManager provides centralized control over logging behavior, including:
    - Level-based filtering (silent, discrete, verbose)
    - Thread-safe logging operations
    - Colored output formatting
    - Event type-specific logging methods
    - Dynamic level changes during execution
    
    The manager integrates with the existing Python logging infrastructure
    while providing observability-specific functionality and formatting.
    
    Attributes:
        _instance: Singleton instance (class attribute)
        _lock: Thread lock for singleton creation (class attribute)
        _config: LoggingConfig instance for current settings
        _logger: Python logger instance for output
        _handler: StreamHandler for console output
        _formatter: ColoredFormatter for message formatting
        _instance_lock: Thread lock for instance operations
    """
    
    _instance: Optional['LoggingManager'] = None
    _lock: threading.Lock = threading.Lock()
    
    def __new__(cls, level: Optional[LoggingLevel] = None) -> 'LoggingManager':
        """
        Create or return the singleton LoggingManager instance.
        
        Thread-safe singleton implementation that ensures only one instance
        exists across the application. The first call determines the initial
        logging level.
        
        Args:
            level: Optional logging level for initialization. Only used on first call.
            
        Returns:
            LoggingManager singleton instance
        """
        if cls._instance is None:
            with cls._lock:
                # Double-check locking pattern
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, level: Optional[LoggingLevel] = None):
        """
        Initialize the LoggingManager singleton.
        
        This method is called every time the singleton is accessed, but
        initialization only happens once due to the _initialized flag.
        
        Args:
            level: Optional logging level. If None, uses configuration from environment.
        """
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        # Thread lock for instance operations
        self._instance_lock = threading.Lock()
        
        # Load configuration with validation and fallback
        self._config = get_logging_config()
        if level is not None:
            # Validate the provided level and apply fallback if needed (Requirements 6.3, 6.4)
            validated_level, warning = validate_logging_level(level)
            if warning:
                logger.warning(f"LoggingManager initialization: {warning}")
            self._config.level = validated_level
        
        # Store original logging state for compatibility (Requirement 5.5)
        self._original_logging_state = self._capture_logging_state()
        
        # Set up Python logger with namespace isolation (Requirement 5.5)
        self._logger = logging.getLogger('observability_logger.enhanced')
        self._logger.setLevel(logging.DEBUG)  # Let formatter handle filtering
        
        # Clear any existing handlers to avoid duplicates
        self._logger.handlers.clear()
        
        # Create and configure handler and formatter
        self._handler = logging.StreamHandler()
        self._formatter = create_colored_formatter(self._config)
        self._handler.setFormatter(self._formatter)
        
        # Add handler to logger
        self._logger.addHandler(self._handler)
        
        # Prevent propagation to avoid duplicate messages and conflicts (Requirement 5.5)
        self._logger.propagate = False
        
        # Perform compatibility checks
        self._compatibility_warnings = self._check_logging_compatibility()
        
        self._initialized = True
        
        # Log initialization if not silent
        if self._config.level != LoggingLevel.SILENT:
            self._log_internal(
                f"Enhanced logging initialized (level: {self._config.level.value})",
                level=logging.INFO,
                format_type='success'
            )
            
            # Log compatibility warnings if any
            for warning in self._compatibility_warnings:
                self._log_internal(
                    f"Compatibility warning: {warning}",
                    level=logging.WARNING,
                    format_type='warning'
                )
    
    @classmethod
    def get_instance(cls, level: Optional[LoggingLevel] = None) -> 'LoggingManager':
        """
        Get the singleton LoggingManager instance.
        
        Convenience method for accessing the singleton without calling constructor.
        
        Args:
            level: Optional logging level for initialization
            
        Returns:
            LoggingManager singleton instance
        """
        return cls(level)
    
    def set_level(self, level: LoggingLevel) -> None:
        """
        Change the logging level dynamically during execution with validation.
        
        This method updates the configuration and applies the new level
        immediately to all subsequent logging events. Thread-safe operation.
        Invalid levels are automatically corrected with warnings.
        
        Args:
            level: New LoggingLevel to apply
            
        Example:
            >>> manager = LoggingManager.get_instance()
            >>> manager.set_level(LoggingLevel.VERBOSE)
        """
        with self._instance_lock:
            old_level = self._config.level
            
            # Validate the new level and apply fallback if needed (Requirements 6.3, 6.4)
            validated_level, warning = validate_logging_level(level)
            if warning:
                self._log_internal(
                    f"Level validation warning: {warning}",
                    level=logging.WARNING,
                    format_type='warning'
                )
            
            self._config.level = validated_level
            
            # Update formatter configuration
            self._formatter.config = self._config
            
            # Log the level change if not silent
            if validated_level != LoggingLevel.SILENT:
                self._log_internal(
                    f"Logging level changed: {old_level.value} → {validated_level.value}",
                    level=logging.INFO,
                    format_type='info'
                )
    
    def get_level(self) -> LoggingLevel:
        """
        Get the current logging level.
        
        Returns:
            Current LoggingLevel
        """
        return self._config.level
    
    def is_enabled(self) -> bool:
        """
        Check if logging is enabled (not silent).
        
        Returns:
            True if logging level is not SILENT, False otherwise
        """
        return self._config.level != LoggingLevel.SILENT
    
    def _should_log_event(self, event_type: str) -> bool:
        """
        Determine if an event type should be logged based on current level.
        
        Implements level-based filtering logic (Requirements 4.1, 4.2):
        - SILENT: No events logged
        - DISCRETE: Only principal events (node creation, trace completion)
        - VERBOSE: All events logged
        
        Args:
            event_type: Type of event ('trace_created', 'node_created', etc.)
            
        Returns:
            True if event should be logged, False otherwise
        """
        if self._config.level == LoggingLevel.SILENT:
            return False
        
        if self._config.level == LoggingLevel.VERBOSE:
            return True
        
        # DISCRETE level: only principal events (Requirements 4.1)
        return self._is_principal_event(event_type)
    
    def _log_internal(
        self,
        message: str,
        level: int = logging.INFO,
        event_type: Optional[str] = None,
        node_type: Optional[str] = None,
        format_type: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Internal method for logging messages with proper attributes.
        
        This method handles the actual logging with appropriate record attributes
        for the ColoredFormatter to process. Thread-safe operation.
        
        Args:
            message: Log message text
            level: Python logging level (DEBUG, INFO, WARNING, ERROR)
            event_type: Observability event type for coloring
            node_type: Node type for coloring ('agent', 'router', etc.)
            format_type: Special formatting type ('success', 'bold', 'dim')
            extra_data: Additional data for verbose mode
        """
        if not self.is_enabled():
            return
        
        with self._instance_lock:
            # Create log record with custom attributes
            extra = {}
            
            if event_type:
                extra['event_type'] = event_type
            
            if node_type:
                extra['node_type'] = node_type
            
            if format_type:
                extra['format_type'] = format_type
            
            # Enhanced verbose mode data formatting (Requirements 4.2, 4.3)
            if self._config.level == LoggingLevel.VERBOSE and extra_data:
                if self._config.show_metadata:
                    # Format metadata in a more readable way for verbose mode
                    metadata_parts = []
                    for k, v in extra_data.items():
                        # Skip timestamp and event_type as they're handled separately
                        if k not in ['timestamp', 'event_type']:
                            if isinstance(v, bool):
                                metadata_parts.append(f"{k}={str(v).lower()}")
                            elif isinstance(v, (int, float)):
                                metadata_parts.append(f"{k}={v}")
                            else:
                                # Truncate long strings for readability
                                str_val = str(v)
                                if len(str_val) > 50:
                                    str_val = str_val[:47] + "..."
                                metadata_parts.append(f"{k}='{str_val}'")
                    
                    if metadata_parts:
                        metadata_str = ', '.join(metadata_parts)
                        message = f"{message} [{metadata_str}]"
                
                # Add extra data to the log record for formatter access
                extra['verbose_data'] = extra_data
            
            # Log the message
            self._logger.log(level, message, extra=extra)
    
    def log_trace_created(
        self,
        trace_id: str,
        title: str,
        workflow_id: str,
        parent_trace_id: Optional[str] = None
    ) -> None:
        """
        Log trace creation event.
        
        Logs the start of a new trace with identification information.
        Includes parent trace information for hierarchical traces.
        
        Args:
            trace_id: Unique trace identifier
            title: Human-readable trace title
            workflow_id: Workflow identifier
            parent_trace_id: Optional parent trace ID for sub-traces
        """
        if not self._should_log_event('trace_created'):
            return
        
        # Format message based on verbosity level
        if self._config.level == LoggingLevel.VERBOSE:
            # Verbose mode: detailed information with metadata and debugging info (Requirements 4.2, 4.3)
            message = f"🚀 TRACE STARTED: {title}"
            extra_data = {
                'trace_id': trace_id,
                'workflow_id': workflow_id,
                'timestamp': datetime.now().isoformat(),
                'event_type': 'trace_created',
                'hierarchy_level': 1 if not parent_trace_id else 2
            }
            if parent_trace_id:
                extra_data['parent_trace_id'] = parent_trace_id
                extra_data['is_subtrace'] = True
            else:
                extra_data['is_subtrace'] = False
        else:
            # Discrete level - simpler format (Requirements 4.1)
            parent_info = f" (child of {parent_trace_id[:8]}...)" if parent_trace_id else ""
            message = f"🚀 Started: {title}{parent_info}"
            extra_data = None
        
        self._log_internal(
            message,
            level=logging.INFO,
            event_type='trace',
            extra_data=extra_data
        )
    
    def log_trace_completed(
        self,
        trace_id: str,
        title: str,
        status: str,
        duration_ms: Optional[int] = None,
        final_output: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log trace completion event.
        
        Logs the end of a trace with final status and optional timing information.
        
        Args:
            trace_id: Unique trace identifier
            title: Human-readable trace title
            status: Final trace status ('completed', 'failed', 'partial')
            duration_ms: Optional execution duration in milliseconds
            final_output: Optional final output data
        """
        if not self._should_log_event('trace_completed'):
            return
        
        # Choose appropriate emoji and format type based on status
        if status == 'completed':
            emoji = "✅"
            format_type = 'success'
        elif status == 'failed':
            emoji = "❌"
            format_type = 'error_event'
        else:
            emoji = "⚠️"
            format_type = 'warning'
        
        # Format message based on verbosity level
        if self._config.level == LoggingLevel.VERBOSE:
            # Verbose mode: detailed information with metadata and debugging info (Requirements 4.2, 4.3)
            message = f"{emoji} TRACE {status.upper()}: {title}"
            extra_data = {
                'trace_id': trace_id,
                'status': status,
                'timestamp': datetime.now().isoformat(),
                'event_type': 'trace_completed'
            }
            if duration_ms is not None:
                extra_data['duration_ms'] = duration_ms
                extra_data['duration_seconds'] = duration_ms / 1000.0
            if final_output:
                extra_data['has_output'] = True
                extra_data['output_size'] = len(str(final_output)) if final_output else 0
        else:
            # Discrete level - simpler format with duration if available (Requirements 4.1)
            duration_info = f" ({duration_ms}ms)" if duration_ms is not None else ""
            message = f"{emoji} {status.title()}: {title}{duration_info}"
            extra_data = None
        
        # Determine log level based on status
        log_level = logging.ERROR if status == 'failed' else logging.INFO
        
        self._log_internal(
            message,
            level=log_level,
            event_type='trace',
            format_type=format_type,
            extra_data=extra_data
        )
    
    def log_node_created(self, node: 'Node') -> None:
        """
        Log node creation event.
        
        Logs when a new node is created with type-specific formatting
        and required information display.
        
        Args:
            node: Node instance that was created
        """
        if not self._should_log_event('node_created'):
            return
        
        # Get node type for coloring
        node_type = node.node_type
        
        # Format message based on verbosity level
        if self._config.level == LoggingLevel.VERBOSE:
            # Verbose mode: detailed information with metadata and debugging info (Requirements 4.2, 4.3)
            message = f"📦 NODE CREATED: {node.name} ({node_type})"
            extra_data = {
                'node_id': node.node_id,
                'node_type': node_type,
                'trace_id': node.trace_id,
                'timestamp': datetime.now().isoformat(),
                'event_type': 'node_created',
                'node_name': node.name
            }
            if hasattr(node, 'description') and node.description:
                extra_data['description'] = node.description
            if hasattr(node, 'parent_node_id') and node.parent_node_id:
                extra_data['parent_node_id'] = node.parent_node_id
                extra_data['is_child_node'] = True
            else:
                extra_data['is_child_node'] = False
            
            # Add debugging information for verbose mode
            if hasattr(node, 'status'):
                extra_data['initial_status'] = node.status
            if hasattr(node, 'created_at'):
                extra_data['created_at'] = str(node.created_at)
        else:
            # Discrete level - show essential info only (Requirements 4.1)
            message = f"📦 {node.name} ({node_type})"
            extra_data = None
        
        self._log_internal(
            message,
            level=logging.INFO,
            node_type=node_type,
            extra_data=extra_data
        )
    
    def log_node_completed(self, node: 'Node', duration_ms: Optional[int] = None) -> None:
        """
        Log node completion event.
        
        Logs when a node completes execution with visual completion indicators
        and status information.
        
        Args:
            node: Node instance that completed
            duration_ms: Optional execution duration in milliseconds
        """
        if not self._should_log_event('node_completed'):
            return
        
        # Get node type and status for formatting
        node_type = node.node_type
        status = getattr(node, 'status', 'completed')  # Default to completed if no status
        
        # Choose appropriate emoji and format type based on status
        if status == 'completed':
            emoji = "✓"
            format_type = 'success'
        elif status == 'failed':
            emoji = "✗"
            format_type = 'error_event'
        else:
            emoji = "⚠"
            format_type = 'warning'
        
        # Format message based on verbosity level
        if self._config.level == LoggingLevel.VERBOSE:
            # Verbose mode: detailed information with metadata and debugging info (Requirements 4.2, 4.3)
            message = f"  {emoji} NODE {status.upper()}: {node.name}"
            extra_data = {
                'node_id': node.node_id,
                'status': status,
                'node_type': node_type,
                'timestamp': datetime.now().isoformat(),
                'event_type': 'node_completed',
                'node_name': node.name
            }
            if duration_ms is not None:
                extra_data['duration_ms'] = duration_ms
                extra_data['duration_seconds'] = duration_ms / 1000.0
            
            # Add debugging information for verbose mode
            if hasattr(node, 'completed_at'):
                extra_data['completed_at'] = str(node.completed_at)
            if hasattr(node, 'output'):
                extra_data['has_output'] = node.output is not None
            if hasattr(node, 'error'):
                extra_data['has_error'] = node.error is not None
        else:
            # Discrete level - simple completion indicator (Requirements 4.1)
            duration_info = f" ({duration_ms}ms)" if duration_ms is not None else ""
            message = f"  {emoji} {node.name}{duration_info}"
            extra_data = None
        
        # Determine log level based on status
        log_level = logging.ERROR if status == 'failed' else logging.INFO
        
        self._log_internal(
            message,
            level=log_level,
            node_type=node_type,
            format_type=format_type,
            extra_data=extra_data
        )
    
    def log_edge_created(self, edge: 'Edge') -> None:
        """
        Log edge creation event.
        
        Logs when a new edge is created with source/target information
        and visual connection indicators.
        
        Args:
            edge: Edge instance that was created
        """
        if not self._should_log_event('edge_created'):
            return
        
        # Format message based on verbosity level
        if self._config.level == LoggingLevel.VERBOSE:
            # Verbose mode: detailed information with metadata and debugging info (Requirements 4.2, 4.3)
            message = f"🔗 EDGE CREATED: {edge.source_node.name} → {edge.target_node.name}"
            extra_data = {
                'edge_id': edge.edge_id,
                'source_node_id': edge.source_node.node_id,
                'target_node_id': edge.target_node.node_id,
                'trace_id': edge.trace_id,
                'timestamp': datetime.now().isoformat(),
                'event_type': 'edge_created',
                'source_node_name': edge.source_node.name,
                'target_node_name': edge.target_node.name
            }
            
            # Add debugging information for verbose mode
            if hasattr(edge, 'created_at'):
                extra_data['created_at'] = str(edge.created_at)
            if hasattr(edge, 'edge_type'):
                extra_data['edge_type'] = edge.edge_type
        else:
            # Discrete level - edges are not shown in discrete mode for cleaner output (Requirements 4.1)
            # This follows the principal events only rule for discrete level
            return
        
        self._log_internal(
            message,
            level=logging.INFO,
            event_type='edge',
            extra_data=extra_data
        )
    
    def log_error(
        self,
        message: str,
        error: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log error events with override behavior.
        
        Error logging always displays regardless of logging level,
        as specified in the requirements.
        
        Args:
            message: Error message
            error: Optional Exception object
            context: Optional context information
        """
        # Errors always display regardless of level (requirement 4.5)
        error_message = message
        
        if error:
            error_message = f"{message}: {str(error)}"
        
        # Format message based on verbosity level
        if self._config.level == LoggingLevel.VERBOSE:
            extra_data = context or {}
            if error:
                extra_data.update({
                    'error_type': type(error).__name__,
                    'error_message': str(error)
                })
        else:
            extra_data = None
        
        self._log_internal(
            f"❌ ERROR: {error_message}",
            level=logging.ERROR,
            event_type='error',
            extra_data=extra_data
        )
    
    def log_warning(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log warning events.
        
        Args:
            message: Warning message
            context: Optional context information
        """
        if not self.is_enabled():
            return
        
        extra_data = context if self._config.level == LoggingLevel.VERBOSE else None
        
        self._log_internal(
            f"⚠️ WARNING: {message}",
            level=logging.WARNING,
            format_type='warning',
            extra_data=extra_data
        )
    
    def log_debug(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log debug information (verbose mode only).
        
        Debug information is only shown in verbose mode as part of
        detailed information display (Requirements 4.2, 4.3).
        
        Args:
            message: Debug message
            context: Optional context information
        """
        if self._config.level != LoggingLevel.VERBOSE:
            return
        
        # Enhanced debug information for verbose mode
        extra_data = context or {}
        extra_data.update({
            'timestamp': datetime.now().isoformat(),
            'event_type': 'debug',
            'log_level': 'DEBUG'
        })
        
        self._log_internal(
            f"🔍 DEBUG: {message}",
            level=logging.DEBUG,
            format_type='dim',
            extra_data=extra_data
        )
    
    def _is_principal_event(self, event_type: str) -> bool:
        """
        Check if an event type is considered a principal event for discrete logging.
        
        Principal events are the most important workflow milestones that should
        be shown in discrete mode (Requirements 4.1). This implements discrete
        level filtering logic to show only essential workflow events.
        
        Args:
            event_type: Type of event to check
            
        Returns:
            True if the event is a principal event, False otherwise
        """
        # Principal events for discrete mode (Requirements 4.1)
        principal_events = {
            'trace_created',     # Workflow start - essential milestone
            'trace_completed',   # Workflow end - essential milestone
            'node_created',      # Node creation - core workflow events
            'node_completed',    # Node completion - core workflow events
            'error',             # Always show errors (Requirements 4.5)
            'warning'            # Show warnings for user awareness
        }
        
        # Non-principal events (filtered out in discrete mode):
        # - 'edge_created': Connection details (verbose only)
        # - 'debug': Debug information (verbose only)
        # - Internal system events (verbose only)
        
        return event_type in principal_events
    
    def _capture_logging_state(self) -> Dict[str, Any]:
        """
        Capture the current state of Python's logging system for compatibility.
        
        This method records the current logging configuration to ensure
        our enhanced logging doesn't interfere with existing setups.
        
        Returns:
            Dictionary containing current logging state information
        """
        root_logger = logging.getLogger()
        
        state = {
            'root_level': root_logger.level,
            'root_handlers_count': len(root_logger.handlers),
            'root_propagate': root_logger.propagate,
            'existing_loggers': list(logging.Logger.manager.loggerDict.keys()),
            'basicConfig_called': hasattr(logging, '_defaultFormatter'),
            'stream_handlers': [],
            'file_handlers': [],
            'other_handlers': []
        }
        
        # Categorize existing handlers
        for handler in root_logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                if not isinstance(handler, logging.FileHandler):
                    state['stream_handlers'].append({
                        'type': type(handler).__name__,
                        'stream': getattr(handler, 'stream', None),
                        'level': handler.level
                    })
            elif isinstance(handler, logging.FileHandler):
                state['file_handlers'].append({
                    'type': type(handler).__name__,
                    'filename': getattr(handler, 'baseFilename', 'unknown'),
                    'level': handler.level
                })
            else:
                state['other_handlers'].append({
                    'type': type(handler).__name__,
                    'level': handler.level
                })
        
        return state
    
    def _check_logging_compatibility(self) -> List[str]:
        """
        Check for potential compatibility issues with existing logging configurations.
        
        This method analyzes the current logging setup and identifies potential
        conflicts or issues that users should be aware of.
        
        Returns:
            List of warning messages about compatibility issues
        """
        warnings = []
        root_logger = logging.getLogger()
        
        # Check for existing StreamHandlers that might conflict
        existing_stream_handlers = [
            h for h in root_logger.handlers 
            if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
        ]
        
        for handler in existing_stream_handlers:
            if hasattr(handler, 'stream') and handler.stream in (sys.stdout, sys.stderr):
                warnings.append(
                    f"Existing StreamHandler detected on {handler.stream.name}. "
                    "This may cause duplicate console output."
                )
        
        # Check for very low root logger levels that might interfere
        if root_logger.level < logging.INFO:
            warnings.append(
                f"Root logger level is set to {logging.getLevelName(root_logger.level)}. "
                "This may cause verbose output from other libraries."
            )
        
        # Check for existing loggers in our namespace
        our_namespace = 'observability_logger'
        conflicting_loggers = [
            name for name in logging.Logger.manager.loggerDict.keys()
            if name.startswith(our_namespace) and name != our_namespace
        ]
        
        if conflicting_loggers:
            warnings.append(
                f"Existing loggers detected in our namespace: {conflicting_loggers}. "
                "This may cause configuration conflicts."
            )
        
        # Check for custom formatters that might be overridden
        custom_formatters = []
        for handler in root_logger.handlers:
            if handler.formatter and not isinstance(handler.formatter, logging.Formatter):
                custom_formatters.append(type(handler.formatter).__name__)
        
        if custom_formatters:
            warnings.append(
                f"Custom formatters detected: {custom_formatters}. "
                "Our enhanced logging uses its own formatter."
            )
        
        # Check for disabled logging
        if logging.getLogger().disabled:
            warnings.append(
                "Root logger is disabled. Enhanced logging may not work as expected."
            )
        
        return warnings
    
    def get_compatibility_info(self) -> Dict[str, Any]:
        """
        Get detailed information about Python logging compatibility.
        
        This method provides comprehensive information about the current
        logging setup and any compatibility considerations.
        
        Returns:
            Dictionary containing compatibility information
        """
        current_state = self._capture_logging_state()
        
        return {
            'original_state': self._original_logging_state,
            'current_state': current_state,
            'warnings': self._compatibility_warnings,
            'namespace_isolated': not self._logger.propagate,
            'handler_count': len(self._logger.handlers),
            'formatter_type': type(self._formatter).__name__,
            'conflicts_detected': len(self._compatibility_warnings) > 0
        }
    
    def restore_logging_state(self) -> None:
        """
        Restore the original Python logging state (for testing or cleanup).
        
        This method attempts to restore the logging system to its state
        before our enhanced logging was initialized. Use with caution.
        """
        if not hasattr(self, '_original_logging_state'):
            logger.warning("No original logging state captured. Cannot restore.")
            return
        
        try:
            # Remove our handlers
            self._logger.handlers.clear()
            
            # Reset our logger
            self._logger.setLevel(logging.NOTSET)
            self._logger.propagate = True
            
            logger.info("Logging state restored to original configuration.")
            
        except Exception as e:
            logger.error(f"Failed to restore logging state: {e}")
    
    def validate_namespace_isolation(self) -> bool:
        """
        Validate that our logging is properly isolated from the root logger.
        
        This method checks that our enhanced logging doesn't interfere
        with existing Python logging configurations.
        
        Returns:
            True if namespace isolation is working correctly, False otherwise
        """
        try:
            # Check that our logger doesn't propagate
            if self._logger.propagate:
                return False
            
            # Check that we're using our own handlers
            if not self._logger.handlers:
                return False
            
            # Check that our handlers are not in the root logger
            root_handlers = logging.getLogger().handlers
            our_handlers = self._logger.handlers
            
            for our_handler in our_handlers:
                if our_handler in root_handlers:
                    return False
            
            # Check that we're using the correct namespace
            if not self._logger.name.startswith('observability_logger'):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to validate namespace isolation: {e}")
            return False


# Convenience functions for global access
def get_logging_manager(level: Optional[LoggingLevel] = None) -> LoggingManager:
    """
    Get the global LoggingManager singleton instance.
    
    Args:
        level: Optional logging level for initialization
        
    Returns:
        LoggingManager singleton instance
    """
    return LoggingManager.get_instance(level)


def set_logging_level(level: LoggingLevel) -> None:
    """
    Set the global logging level.
    
    Args:
        level: New LoggingLevel to apply globally
    """
    manager = get_logging_manager()
    manager.set_level(level)


def is_logging_enabled() -> bool:
    """
    Check if logging is globally enabled.
    
    Returns:
        True if logging is enabled (not silent), False otherwise
    """
    manager = get_logging_manager()
    return manager.is_enabled()


def get_compatibility_info() -> Dict[str, Any]:
    """
    Get Python logging compatibility information.
    
    Returns:
        Dictionary containing compatibility information and warnings
    """
    manager = get_logging_manager()
    return manager.get_compatibility_info()


def validate_logging_compatibility() -> bool:
    """
    Validate that enhanced logging is compatible with existing Python logging.
    
    Returns:
        True if no compatibility issues detected, False otherwise
    """
    manager = get_logging_manager()
    return manager.validate_namespace_isolation()


def restore_original_logging() -> None:
    """
    Restore Python logging to its original state before enhanced logging.
    
    This function is primarily for testing and cleanup purposes.
    """
    manager = get_logging_manager()
    manager.restore_logging_state()