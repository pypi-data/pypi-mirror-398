"""
Logging configuration for enhanced observability logging strategy.

This module provides:
- LoggingLevel enum with validation
- LoggingConfig dataclass with environment variable support
- ANSI color configuration for different node types
"""

import os
import logging
from enum import Enum
from typing import Dict, Optional, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class LoggingLevel(Enum):
    """
    Enumeration of available logging levels for observability output.
    
    SILENT: No logging output to console
    DISCRETE: Only principal events (node creation, trace completion)
    VERBOSE: Detailed information including metadata, timestamps, debugging info
    """
    SILENT = "silent"
    DISCRETE = "discrete"
    VERBOSE = "verbose"

    @classmethod
    def from_string(cls, value: str) -> 'LoggingLevel':
        """
        Convert string to LoggingLevel enum with validation.
        
        Args:
            value: String representation of logging level
            
        Returns:
            LoggingLevel enum value
            
        Raises:
            ValueError: If the value is not a valid logging level
        """
        if not isinstance(value, str):
            raise ValueError(f"Logging level must be a string, got {type(value)}")
        
        value_lower = value.lower().strip()
        for level in cls:
            if level.value == value_lower:
                return level
        
        valid_levels = [level.value for level in cls]
        raise ValueError(
            f"Invalid logging level '{value}'. "
            f"Must be one of: {', '.join(valid_levels)}"
        )

    def __str__(self) -> str:
        return self.value


# ANSI color codes for terminal output
class ANSIColors:
    """ANSI color codes for terminal formatting."""
    
    # Reset
    RESET = "\033[0m"
    
    # Node type colors
    MISCELLANEOUS_NODE = "\033[36m"  # Cyan
    PARALLEL_NODE = "\033[33m"       # Yellow
    ROUTER_NODE = "\033[35m"         # Magenta
    AGENT_NODE = "\033[32m"          # Green
    
    # Event type colors
    TRACE_EVENT = "\033[34m"         # Blue
    EDGE_EVENT = "\033[37m"          # White
    ERROR_EVENT = "\033[31m"         # Red
    
    # Status colors
    SUCCESS = "\033[92m"             # Bright Green
    WARNING = "\033[93m"             # Bright Yellow
    INFO = "\033[94m"                # Bright Blue
    
    # Text formatting
    BOLD = "\033[1m"
    DIM = "\033[2m"


@dataclass
class LoggingConfig:
    """
    Configuration for enhanced observability logging.
    
    This dataclass manages logging level, color configuration, and display options
    for the observability system. It supports both environment variable and
    programmatic configuration with validation and fallback mechanisms.
    
    Attributes:
        level: Logging verbosity level
        colors: Dictionary mapping event types to ANSI color codes
        show_timestamps: Whether to include timestamps in verbose mode
        show_metadata: Whether to include metadata in verbose mode
        use_colors: Whether to use ANSI colors (auto-detected for terminals)
    """
    
    level: LoggingLevel = LoggingLevel.DISCRETE
    colors: Dict[str, str] = field(default_factory=dict)
    show_timestamps: bool = True
    show_metadata: bool = True
    use_colors: bool = True
    
    # Internal field to store environment loading warnings
    _environment_warnings: list = field(default_factory=list, init=False, repr=False)

    def __post_init__(self):
        """Initialize default colors if not provided."""
        if not self.colors:
            self.colors = self._get_default_colors()
        
        # Auto-detect color support if not explicitly set
        if self.use_colors and not self._supports_color():
            self.use_colors = False

    @classmethod
    def from_environment(cls) -> 'LoggingConfig':
        """
        Load configuration from environment variables with validation and fallback.
        
        Environment Variables:
        - OBSERVABILITY_LOGGING_LEVEL: Logging level (silent/discrete/verbose)
        - OBSERVABILITY_SHOW_TIMESTAMPS: Show timestamps in verbose mode (true/false)
        - OBSERVABILITY_SHOW_METADATA: Show metadata in verbose mode (true/false)
        - OBSERVABILITY_USE_COLORS: Use ANSI colors (true/false)
        - OBSERVABILITY_COLOR_*: Custom color configuration (e.g., OBSERVABILITY_COLOR_AGENT_NODE)
        
        Returns:
            LoggingConfig instance with environment-based configuration
        """
        warnings_issued = []
        
        # Load logging level with validation and fallback (Requirements 6.3, 6.4)
        level_str = os.environ.get('OBSERVABILITY_LOGGING_LEVEL', 'discrete')
        try:
            level = LoggingLevel.from_string(level_str)
        except ValueError as e:
            warning_msg = f"Invalid OBSERVABILITY_LOGGING_LEVEL '{level_str}': {e}. Using default 'discrete'."
            logger.warning(warning_msg)
            warnings_issued.append(warning_msg)
            level = LoggingLevel.DISCRETE
        
        # Load boolean options with validation and fallback (Requirements 6.4)
        show_timestamps = cls._parse_boolean_env_var(
            'OBSERVABILITY_SHOW_TIMESTAMPS', 'true', warnings_issued
        )
        show_metadata = cls._parse_boolean_env_var(
            'OBSERVABILITY_SHOW_METADATA', 'true', warnings_issued
        )
        use_colors = cls._parse_boolean_env_var(
            'OBSERVABILITY_USE_COLORS', 'true', warnings_issued
        )
        
        # Load custom colors with validation (Requirements 6.5)
        colors = cls._load_custom_colors_from_env(warnings_issued)
        
        config = cls(
            level=level,
            colors=colors,
            show_timestamps=show_timestamps,
            show_metadata=show_metadata,
            use_colors=use_colors
        )
        
        # Store warnings for later access
        config._environment_warnings = warnings_issued
        
        return config

    @staticmethod
    def _parse_boolean_env_var(
        var_name: str, 
        default_value: str, 
        warnings_list: list
    ) -> bool:
        """
        Parse boolean environment variable with validation and fallback.
        
        Args:
            var_name: Environment variable name
            default_value: Default value if not set or invalid
            warnings_list: List to append warnings to
            
        Returns:
            Boolean value from environment or default
        """
        value_str = os.environ.get(var_name, default_value).lower().strip()
        
        # Valid boolean representations
        true_values = {'true', '1', 'yes', 'on', 'enabled'}
        false_values = {'false', '0', 'no', 'off', 'disabled'}
        
        if value_str in true_values:
            return True
        elif value_str in false_values:
            return False
        else:
            # Invalid value - use default and warn (Requirements 6.4)
            default_bool = default_value.lower() in true_values
            warning_msg = (
                f"Invalid {var_name} value '{value_str}'. "
                f"Expected true/false, yes/no, 1/0, on/off, or enabled/disabled. "
                f"Using default '{default_value}'."
            )
            logger.warning(warning_msg)
            warnings_list.append(warning_msg)
            return default_bool

    @staticmethod
    def _load_custom_colors_from_env(warnings_list: list) -> Dict[str, str]:
        """
        Load custom color configuration from environment variables with validation.
        
        Args:
            warnings_list: List to append warnings to
            
        Returns:
            Dictionary of custom color configurations
        """
        colors = {}
        color_prefix = 'OBSERVABILITY_COLOR_'
        
        # Valid color keys that can be customized (Requirements 6.5)
        valid_color_keys = {
            'miscellaneous_node', 'parallel_node', 'router_node', 'agent_node',
            'trace_event', 'edge_event', 'error_event',
            'success', 'warning', 'info', 'bold', 'dim', 'reset'
        }
        
        for key, value in os.environ.items():
            if key.startswith(color_prefix):
                color_key = key[len(color_prefix):].lower()
                
                # Validate color key (Requirements 6.5)
                if color_key not in valid_color_keys:
                    warning_msg = (
                        f"Unknown color key '{color_key}' in {key}. "
                        f"Valid keys: {', '.join(sorted(valid_color_keys))}. Ignoring."
                    )
                    logger.warning(warning_msg)
                    warnings_list.append(warning_msg)
                    continue
                
                # Validate ANSI color code format (Requirements 6.5)
                if not LoggingConfig._is_valid_ansi_color(value):
                    warning_msg = (
                        f"Invalid ANSI color code '{value}' for {key}. "
                        f"Expected format: \\033[<code>m (e.g., \\033[32m for green). Ignoring."
                    )
                    logger.warning(warning_msg)
                    warnings_list.append(warning_msg)
                    continue
                
                colors[color_key] = value
        
        return colors

    def _get_default_colors(self) -> Dict[str, str]:
        """Get default ANSI color configuration."""
        return {
            'miscellaneous_node': ANSIColors.MISCELLANEOUS_NODE,
            'parallel_node': ANSIColors.PARALLEL_NODE,
            'router_node': ANSIColors.ROUTER_NODE,
            'agent_node': ANSIColors.AGENT_NODE,
            'trace_event': ANSIColors.TRACE_EVENT,
            'edge_event': ANSIColors.EDGE_EVENT,
            'error_event': ANSIColors.ERROR_EVENT,
            'success': ANSIColors.SUCCESS,
            'warning': ANSIColors.WARNING,
            'info': ANSIColors.INFO,
            'bold': ANSIColors.BOLD,
            'dim': ANSIColors.DIM,
            'reset': ANSIColors.RESET
        }

    def _supports_color(self) -> bool:
        """
        Detect if the current environment supports ANSI colors.
        
        Returns:
            True if colors are supported, False otherwise
        """
        # Check if we're in a terminal
        if not hasattr(os.sys.stdout, 'isatty') or not os.sys.stdout.isatty():
            return False
        
        # Check environment variables that indicate color support
        term = os.environ.get('TERM', '').lower()
        colorterm = os.environ.get('COLORTERM', '').lower()
        
        # Common terminals that support color
        color_terms = ['xterm', 'xterm-color', 'xterm-256color', 'screen', 'linux', 'cygwin']
        
        if any(term.startswith(ct) for ct in color_terms):
            return True
        
        if colorterm in ['truecolor', '24bit']:
            return True
        
        # Check for NO_COLOR environment variable (https://no-color.org/)
        if os.environ.get('NO_COLOR'):
            return False
        
        # Default to True for most modern terminals
        return True

    def validate(self) -> None:
        """
        Validate configuration values with comprehensive checks.
        
        Raises:
            ValueError: If configuration contains invalid values (Requirements 6.3)
        """
        # Validate logging level (Requirements 6.3)
        if not isinstance(self.level, LoggingLevel):
            raise ValueError(f"level must be a LoggingLevel enum, got {type(self.level)}")
        
        # Validate colors dictionary (Requirements 6.3, 6.5)
        if not isinstance(self.colors, dict):
            raise ValueError(f"colors must be a dictionary, got {type(self.colors)}")
        
        # Validate each color value in the dictionary
        for color_key, color_value in self.colors.items():
            if not isinstance(color_key, str):
                raise ValueError(f"color key must be a string, got {type(color_key)} for key {color_key}")
            
            if not isinstance(color_value, str):
                raise ValueError(f"color value must be a string, got {type(color_value)} for key {color_key}")
            
            # Validate ANSI color format if not empty
            if color_value and not self._is_valid_ansi_color(color_value):
                raise ValueError(f"invalid ANSI color code '{color_value}' for key '{color_key}'")
        
        # Validate boolean options (Requirements 6.3)
        if not isinstance(self.show_timestamps, bool):
            raise ValueError(f"show_timestamps must be a boolean, got {type(self.show_timestamps)}")
        
        if not isinstance(self.show_metadata, bool):
            raise ValueError(f"show_metadata must be a boolean, got {type(self.show_metadata)}")
        
        if not isinstance(self.use_colors, bool):
            raise ValueError(f"use_colors must be a boolean, got {type(self.use_colors)}")

    @staticmethod
    def _is_valid_ansi_color(color_code: str) -> bool:
        """
        Validate ANSI color code format.
        
        Args:
            color_code: ANSI color code string to validate
            
        Returns:
            True if valid ANSI color code, False otherwise
        """
        if not color_code:
            return True  # Empty string is valid (no color)
        
        # Basic ANSI color code pattern: \033[<numbers>m or \x1b[<numbers>m
        import re
        ansi_pattern = r'^(\033\[|\x1b\[)[0-9;]*m$'
        
        return bool(re.match(ansi_pattern, color_code))

    def validate_and_fallback(self) -> list:
        """
        Validate configuration and return list of fallback actions taken.
        
        This method performs validation and automatically applies fallbacks
        for invalid configurations instead of raising exceptions.
        
        Returns:
            List of warning messages about fallbacks applied (Requirements 6.4)
        """
        warnings = []
        
        # Validate and fallback logging level
        if not isinstance(self.level, LoggingLevel):
            warnings.append(f"Invalid level type {type(self.level)}, falling back to DISCRETE")
            self.level = LoggingLevel.DISCRETE
        
        # Validate and fallback colors
        if not isinstance(self.colors, dict):
            warnings.append(f"Invalid colors type {type(self.colors)}, falling back to defaults")
            self.colors = self._get_default_colors()
        else:
            # Validate individual color entries
            invalid_colors = []
            for color_key, color_value in list(self.colors.items()):
                if not isinstance(color_key, str) or not isinstance(color_value, str):
                    invalid_colors.append(color_key)
                elif color_value and not self._is_valid_ansi_color(color_value):
                    invalid_colors.append(color_key)
            
            # Remove invalid colors and warn
            for color_key in invalid_colors:
                del self.colors[color_key]
                warnings.append(f"Invalid color configuration for '{color_key}', removed")
            
            # Merge with defaults for missing colors
            default_colors = self._get_default_colors()
            for key, value in default_colors.items():
                if key not in self.colors:
                    self.colors[key] = value
        
        # Validate and fallback boolean options
        if not isinstance(self.show_timestamps, bool):
            warnings.append(f"Invalid show_timestamps type {type(self.show_timestamps)}, falling back to True")
            self.show_timestamps = True
        
        if not isinstance(self.show_metadata, bool):
            warnings.append(f"Invalid show_metadata type {type(self.show_metadata)}, falling back to True")
            self.show_metadata = True
        
        if not isinstance(self.use_colors, bool):
            warnings.append(f"Invalid use_colors type {type(self.use_colors)}, falling back to True")
            self.use_colors = True
        
        return warnings

    def get_color(self, color_key: str) -> str:
        """
        Get ANSI color code for a specific color key.
        
        Args:
            color_key: Key for the color (e.g., 'agent_node', 'trace_event')
            
        Returns:
            ANSI color code string, or empty string if colors disabled
        """
        if not self.use_colors:
            return ""
        
        return self.colors.get(color_key.lower(), "")

    def apply_color(self, text: str, color_key: str) -> str:
        """
        Apply color formatting to text.
        
        Args:
            text: Text to colorize
            color_key: Color key to apply
            
        Returns:
            Colorized text with reset code, or original text if colors disabled
        """
        if not self.use_colors:
            return text
        
        color_code = self.get_color(color_key)
        if not color_code:
            return text
        
        reset_code = self.get_color('reset')
        return f"{color_code}{text}{reset_code}"

    def get_environment_warnings(self) -> list:
        """
        Get warnings issued during environment variable loading.
        
        Returns:
            List of warning messages from environment configuration loading
        """
        return getattr(self, '_environment_warnings', [])

    def has_configuration_issues(self) -> bool:
        """
        Check if there were any configuration issues during loading.
        
        Returns:
            True if warnings were issued during configuration loading
        """
        return len(self.get_environment_warnings()) > 0

    @classmethod
    def create_safe(
        cls,
        level: Optional[LoggingLevel] = None,
        colors: Optional[Dict[str, str]] = None,
        show_timestamps: Optional[bool] = None,
        show_metadata: Optional[bool] = None,
        use_colors: Optional[bool] = None
    ) -> 'LoggingConfig':
        """
        Create a LoggingConfig with validation and fallback for invalid values.
        
        This method creates a configuration instance and automatically applies
        fallbacks for any invalid values instead of raising exceptions.
        
        Args:
            level: Optional logging level
            colors: Optional color configuration
            show_timestamps: Optional timestamp display setting
            show_metadata: Optional metadata display setting
            use_colors: Optional color usage setting
            
        Returns:
            LoggingConfig instance with validated values and fallbacks applied
        """
        # Start with defaults
        config = cls()
        
        # Apply provided values with validation and fallback
        warnings = []
        
        if level is not None:
            if isinstance(level, LoggingLevel):
                config.level = level
            else:
                warnings.append(f"Invalid level type {type(level)}, using default DISCRETE")
        
        if colors is not None:
            if isinstance(colors, dict):
                # Validate each color entry
                valid_colors = {}
                for k, v in colors.items():
                    if isinstance(k, str) and isinstance(v, str):
                        if not v or cls._is_valid_ansi_color(v):
                            valid_colors[k] = v
                        else:
                            warnings.append(f"Invalid ANSI color '{v}' for key '{k}', skipped")
                    else:
                        warnings.append(f"Invalid color entry {k}:{v}, skipped")
                
                # Merge with defaults
                default_colors = config._get_default_colors()
                default_colors.update(valid_colors)
                config.colors = default_colors
            else:
                warnings.append(f"Invalid colors type {type(colors)}, using defaults")
        
        if show_timestamps is not None:
            if isinstance(show_timestamps, bool):
                config.show_timestamps = show_timestamps
            else:
                warnings.append(f"Invalid show_timestamps type {type(show_timestamps)}, using default True")
        
        if show_metadata is not None:
            if isinstance(show_metadata, bool):
                config.show_metadata = show_metadata
            else:
                warnings.append(f"Invalid show_metadata type {type(show_metadata)}, using default True")
        
        if use_colors is not None:
            if isinstance(use_colors, bool):
                config.use_colors = use_colors
            else:
                warnings.append(f"Invalid use_colors type {type(use_colors)}, using default True")
        
        # Store warnings
        config._environment_warnings = warnings
        
        # Log warnings if any
        for warning in warnings:
            logger.warning(f"Configuration fallback: {warning}")
        
        return config


# Global logging configuration instance (lazy-loaded)
_logging_config: Optional[LoggingConfig] = None


def get_logging_config() -> LoggingConfig:
    """
    Get the global LoggingConfig singleton instance with validation and fallback.
    
    The configuration is loaded lazily on first access from environment
    variables with automatic validation and fallback for invalid values.
    Subsequent calls return the cached instance.
    
    Returns:
        LoggingConfig: The global logging configuration instance
    """
    global _logging_config
    if _logging_config is None:
        _logging_config = LoggingConfig.from_environment()
        
        # Apply validation with fallback instead of strict validation (Requirements 6.4)
        fallback_warnings = _logging_config.validate_and_fallback()
        for warning in fallback_warnings:
            logger.warning(f"Configuration validation fallback: {warning}")
    
    return _logging_config


def set_logging_config(config: LoggingConfig) -> None:
    """
    Set the global logging configuration instance with validation and fallback.
    
    Args:
        config: LoggingConfig instance to use globally
    """
    global _logging_config
    
    # Apply validation with fallback instead of strict validation (Requirements 6.4)
    fallback_warnings = config.validate_and_fallback()
    for warning in fallback_warnings:
        logger.warning(f"Configuration validation fallback: {warning}")
    
    _logging_config = config


def create_safe_logging_config(**kwargs) -> LoggingConfig:
    """
    Create a LoggingConfig with safe validation and fallback mechanisms.
    
    This function creates a configuration instance that automatically handles
    invalid values by applying fallbacks instead of raising exceptions.
    
    Args:
        **kwargs: Configuration parameters (level, colors, show_timestamps, etc.)
        
    Returns:
        LoggingConfig instance with validated values and fallbacks applied
    """
    return LoggingConfig.create_safe(**kwargs)


def validate_logging_level(level_value: any) -> tuple:
    """
    Validate a logging level value and provide fallback.
    
    Args:
        level_value: Value to validate as a logging level
        
    Returns:
        Tuple of (LoggingLevel, warning_message or None)
    """
    if isinstance(level_value, LoggingLevel):
        return level_value, None
    
    if isinstance(level_value, str):
        try:
            return LoggingLevel.from_string(level_value), None
        except ValueError as e:
            return LoggingLevel.DISCRETE, f"Invalid logging level '{level_value}': {e}"
    
    return LoggingLevel.DISCRETE, f"Invalid logging level type {type(level_value)}, expected LoggingLevel or string"


def get_configuration_status() -> Dict[str, Any]:
    """
    Get comprehensive status of the current logging configuration.
    
    Returns:
        Dictionary containing configuration status, warnings, and validation info
    """
    config = get_logging_config()
    
    return {
        'level': config.level.value,
        'use_colors': config.use_colors,
        'show_timestamps': config.show_timestamps,
        'show_metadata': config.show_metadata,
        'color_count': len(config.colors),
        'environment_warnings': config.get_environment_warnings(),
        'has_issues': config.has_configuration_issues(),
        'color_support_detected': config._supports_color(),
        'custom_colors_loaded': len([k for k in config.colors.keys() 
                                   if k not in config._get_default_colors()]) > 0
    }


def reset_logging_config() -> None:
    """Reset the global logging configuration instance (used for testing)."""
    global _logging_config
    _logging_config = None