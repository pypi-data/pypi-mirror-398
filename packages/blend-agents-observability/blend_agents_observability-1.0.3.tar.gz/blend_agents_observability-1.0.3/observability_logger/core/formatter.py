"""
ColoredFormatter for enhanced observability logging strategy.

This module provides:
- ColoredFormatter class with ANSI color support
- Node type-specific color formatting
- Level-based formatting (discrete vs verbose)
- Terminal environment detection and color stripping
"""

import logging
import sys
import os
from typing import Dict, Any, Optional
from datetime import datetime

from ..config.logging_config import LoggingConfig, LoggingLevel, get_logging_config


class ColoredFormatter(logging.Formatter):
    """
    Custom logging formatter that applies ANSI colors based on node types and event types.
    
    This formatter provides:
    - Node type-specific colors (Agent, Router, Parallel, Miscellaneous)
    - Event type colors (Trace, Edge, Error)
    - Level-based formatting (discrete vs verbose)
    - Automatic color stripping for non-terminal environments
    - Consistent format structure across different verbosity levels
    
    The formatter integrates with LoggingConfig to respect user color preferences
    and environment detection.
    
    Attributes:
        config: LoggingConfig instance for color and format settings
        base_format: Base format string for all log messages
        verbose_format: Extended format string for verbose logging
    """
    
    def __init__(self, config: Optional[LoggingConfig] = None):
        """
        Initialize the ColoredFormatter.
        
        Args:
            config: Optional LoggingConfig instance. If None, uses global config.
        """
        self.config = config or get_logging_config()
        
        # Base format for all levels - consistent structure
        self.base_format = "%(message)s"
        
        # Extended format for verbose mode with timestamps and metadata
        self.verbose_format = "[%(asctime)s] %(levelname)s: %(message)s"
        
        # Initialize with base format
        super().__init__(self.base_format)
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record with appropriate colors and level-specific formatting.
        
        This method:
        1. Determines the appropriate format based on logging level
        2. Applies node type or event type colors
        3. Handles color stripping for non-terminal environments
        4. Maintains format consistency across levels
        5. Adds verbose mode enhancements (timestamps, debugging info)
        
        Args:
            record: LogRecord instance to format
            
        Returns:
            Formatted log message string with colors (if enabled)
        """
        # Determine format based on logging level
        if self.config.level == LoggingLevel.VERBOSE:
            # Use verbose format with timestamps and metadata (Requirements 4.2, 4.3)
            self._style._fmt = self.verbose_format
            if self.config.show_timestamps:
                # Ensure asctime is available for verbose mode
                record.asctime = self.formatTime(record, self.datefmt)
        else:
            # Use base format for discrete and silent levels (Requirements 4.1, 4.4)
            self._style._fmt = self.base_format
        
        # Enhanced verbose mode formatting (Requirements 4.2, 4.3)
        if self.config.level == LoggingLevel.VERBOSE:
            formatted_message = self._format_verbose_message(record)
        else:
            # Get the base formatted message for discrete/silent levels
            formatted_message = super().format(record)
        
        # Apply colors based on record attributes
        colored_message = self._apply_colors(formatted_message, record)
        
        return colored_message
    
    def _apply_colors(self, message: str, record: logging.LogRecord) -> str:
        """
        Apply appropriate colors to the message based on record attributes.
        
        Colors are determined by:
        1. Node type (if node_type attribute present)
        2. Event type (if event_type attribute present)  
        3. Log level (ERROR, WARNING, etc.)
        4. Special formatting (if format_type attribute present)
        
        Args:
            message: The formatted message string
            record: LogRecord with potential color attributes
            
        Returns:
            Message with ANSI color codes applied (if colors enabled)
        """
        if not self.config.use_colors:
            return message
        
        # Priority 1: Node type colors
        if hasattr(record, 'node_type') and record.node_type:
            color_key = self._get_node_type_color_key(record.node_type)
            return self.config.apply_color(message, color_key)
        
        # Priority 2: Event type colors
        if hasattr(record, 'event_type') and record.event_type:
            color_key = self._get_event_type_color_key(record.event_type)
            return self.config.apply_color(message, color_key)
        
        # Priority 3: Log level colors
        if record.levelno >= logging.ERROR:
            return self.config.apply_color(message, 'error_event')
        elif record.levelno >= logging.WARNING:
            return self.config.apply_color(message, 'warning')
        elif record.levelno >= logging.INFO:
            return self.config.apply_color(message, 'info')
        
        # Priority 4: Special formatting
        if hasattr(record, 'format_type') and record.format_type:
            format_type = record.format_type
            if format_type == 'success':
                return self.config.apply_color(message, 'success')
            elif format_type == 'bold':
                return self.config.apply_color(message, 'bold')
            elif format_type == 'dim':
                return self.config.apply_color(message, 'dim')
        
        # Default: no color
        return message
    
    def _get_node_type_color_key(self, node_type: str) -> str:
        """
        Get the color key for a specific node type.
        
        Maps node types to their corresponding color configuration keys:
        - 'agent' -> 'agent_node'
        - 'router' -> 'router_node'  
        - 'parallel' -> 'parallel_node'
        - 'miscellaneous' -> 'miscellaneous_node'
        
        Args:
            node_type: Node type string ('agent', 'router', 'parallel', 'miscellaneous')
            
        Returns:
            Color key string for use with LoggingConfig.apply_color()
        """
        node_type_lower = node_type.lower().strip()
        
        # Map node types to color keys
        node_color_map = {
            'agent': 'agent_node',
            'router': 'router_node', 
            'parallel': 'parallel_node',
            'miscellaneous': 'miscellaneous_node'
        }
        
        return node_color_map.get(node_type_lower, 'info')
    
    def _get_event_type_color_key(self, event_type: str) -> str:
        """
        Get the color key for a specific event type.
        
        Maps event types to their corresponding color configuration keys:
        - 'trace' events -> 'trace_event'
        - 'edge' events -> 'edge_event'
        - 'error' events -> 'error_event'
        
        Args:
            event_type: Event type string ('trace', 'edge', 'error', etc.)
            
        Returns:
            Color key string for use with LoggingConfig.apply_color()
        """
        event_type_lower = event_type.lower().strip()
        
        # Map event types to color keys
        event_color_map = {
            'trace': 'trace_event',
            'edge': 'edge_event', 
            'error': 'error_event'
        }
        
        return event_color_map.get(event_type_lower, 'info')
    
    def _format_verbose_message(self, record: logging.LogRecord) -> str:
        """
        Format a message with enhanced verbose mode information.
        
        This method adds debugging information, metadata, and enhanced
        formatting for verbose mode (Requirements 4.2, 4.3).
        
        Args:
            record: LogRecord instance to format
            
        Returns:
            Enhanced formatted message for verbose mode
        """
        # Get base formatted message
        formatted_message = super().format(record)
        
        # Add debugging information if available (Requirements 4.3)
        if hasattr(record, 'verbose_data') and record.verbose_data:
            verbose_data = record.verbose_data
            
            # Add debugging context for verbose mode
            debug_info = []
            
            # Add trace context
            if 'trace_id' in verbose_data:
                trace_id = verbose_data['trace_id']
                short_trace_id = trace_id[:8] + "..." if len(trace_id) > 8 else trace_id
                debug_info.append(f"trace:{short_trace_id}")
            
            # Add node context
            if 'node_id' in verbose_data:
                node_id = verbose_data['node_id']
                short_node_id = node_id[:8] + "..." if len(node_id) > 8 else node_id
                debug_info.append(f"node:{short_node_id}")
            
            # Add workflow context
            if 'workflow_id' in verbose_data:
                workflow_id = verbose_data['workflow_id']
                debug_info.append(f"workflow:{workflow_id}")
            
            # Add parent context for hierarchical traces
            if 'parent_trace_id' in verbose_data:
                parent_id = verbose_data['parent_trace_id']
                short_parent_id = parent_id[:8] + "..." if len(parent_id) > 8 else parent_id
                debug_info.append(f"parent:{short_parent_id}")
            
            # Add performance information
            if 'duration_ms' in verbose_data:
                duration = verbose_data['duration_ms']
                debug_info.append(f"duration:{duration}ms")
            
            # Add status information
            if 'status' in verbose_data:
                status = verbose_data['status']
                debug_info.append(f"status:{status}")
            
            # Add error information
            if 'error_type' in verbose_data:
                error_type = verbose_data['error_type']
                debug_info.append(f"error:{error_type}")
            
            # Append debug information to message
            if debug_info:
                debug_str = " | ".join(debug_info)
                formatted_message = f"{formatted_message} | {debug_str}"
        
        return formatted_message
    
    def formatTime(self, record: logging.LogRecord, datefmt: Optional[str] = None) -> str:
        """
        Format the timestamp for verbose logging.
        
        Uses ISO format with milliseconds for precise timing information
        when verbose logging is enabled (Requirements 4.2, 4.3).
        
        Args:
            record: LogRecord instance
            datefmt: Optional date format string (ignored, uses ISO format)
            
        Returns:
            Formatted timestamp string
        """
        if self.config.level == LoggingLevel.VERBOSE and self.config.show_timestamps:
            # Use high-precision timestamp for verbose mode debugging (Requirements 4.3)
            dt = datetime.fromtimestamp(record.created)
            return dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]  # Millisecond precision
        else:
            # Use standard timestamp format for other levels
            return super().formatTime(record, datefmt)


def create_colored_formatter(config: Optional[LoggingConfig] = None) -> ColoredFormatter:
    """
    Factory function to create a ColoredFormatter instance.
    
    This function provides a convenient way to create formatters with
    proper configuration handling and validation.
    
    Args:
        config: Optional LoggingConfig instance. If None, uses global config.
        
    Returns:
        ColoredFormatter instance ready for use with logging handlers
        
    Example:
        >>> formatter = create_colored_formatter()
        >>> handler = logging.StreamHandler()
        >>> handler.setFormatter(formatter)
        >>> logger.addHandler(handler)
    """
    return ColoredFormatter(config)


def supports_color() -> bool:
    """
    Check if the current environment supports ANSI colors.
    
    This function performs comprehensive environment detection:
    - Checks if stdout is a TTY
    - Examines TERM and COLORTERM environment variables
    - Respects NO_COLOR standard (https://no-color.org/)
    - Handles common CI/CD environments
    
    Returns:
        True if ANSI colors are supported, False otherwise
    """
    # Check if we're in a terminal
    if not hasattr(sys.stdout, 'isatty') or not sys.stdout.isatty():
        return False
    
    # Respect NO_COLOR environment variable (https://no-color.org/)
    if os.environ.get('NO_COLOR'):
        return False
    
    # Check for explicit color support
    if os.environ.get('FORCE_COLOR'):
        return True
    
    # Check TERM environment variable
    term = os.environ.get('TERM', '').lower()
    if term in ['dumb', 'unknown']:
        return False
    
    # Common terminals that support color
    color_terms = [
        'xterm', 'xterm-color', 'xterm-256color', 'screen', 'screen-256color',
        'tmux', 'tmux-256color', 'linux', 'cygwin', 'ansi'
    ]
    
    if any(term.startswith(ct) for ct in color_terms):
        return True
    
    # Check COLORTERM environment variable
    colorterm = os.environ.get('COLORTERM', '').lower()
    if colorterm in ['truecolor', '24bit', 'yes', '1']:
        return True
    
    # Check for common CI environments that support color
    ci_with_color = [
        'GITHUB_ACTIONS', 'GITLAB_CI', 'BUILDKITE', 'CIRCLECI'
    ]
    if any(os.environ.get(var) for var in ci_with_color):
        return True
    
    # Default to True for most modern terminals
    return True


def strip_ansi_codes(text: str) -> str:
    """
    Remove ANSI color codes from text.
    
    This function strips all ANSI escape sequences from a string,
    useful for logging to files or non-terminal outputs.
    
    Args:
        text: Text potentially containing ANSI codes
        
    Returns:
        Text with all ANSI codes removed
        
    Example:
        >>> colored_text = "\\033[32mHello\\033[0m World"
        >>> strip_ansi_codes(colored_text)
        'Hello World'
    """
    import re
    
    # ANSI escape sequence pattern
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)