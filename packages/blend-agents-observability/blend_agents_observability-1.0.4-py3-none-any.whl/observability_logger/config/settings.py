"""
Configuration management for observability logger.

This module handles:
- AWS credentials via boto3 credential chain
- Environment variable loading with defaults
- Configuration validation

Note on cross-account access:
- The library does not perform STS AssumeRole directly.
- If you need to publish to a Kinesis stream in another AWS account, run your
  application with credentials that already assume into (or are issued for) the
  target account (e.g., using an `AWS_PROFILE` with `role_arn` configured).
"""

import os
import logging
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ObservabilityConfig:
    """
    Configuration for the observability logger.

    This dataclass holds all configuration needed for the observability logger
    to connect to AWS services and emit events.

    Attributes:
        aws_region: AWS region for Kinesis (default: us-east-1)
        kinesis_stream_arn: ARN of the Kinesis stream to emit events to
        log_level: Logging level for the library (default: WARNING)
        enable_validation: Whether to enable Pydantic validation (default: True)

    Environment Variables:
        - KINESIS_STREAM_ARN: Required. ARN of the Kinesis stream
        - AWS_REGION: Optional. AWS region (default: us-east-1)
        - OBSERVABILITY_LOG_LEVEL: Optional. Log level (default: WARNING)
        - OBSERVABILITY_ENABLE_VALIDATION: Optional. Enable validation (default: true)

    Example:
        >>> # Configuration is loaded automatically from environment
        >>> config = get_config()
        >>> print(config.kinesis_stream_arn)
        'arn:aws:kinesis:us-east-1:123456789012:stream/my-kinesis-stream'
    """

    # AWS Configuration
    aws_region: str
    kinesis_stream_arn: str

    # Optional Configuration
    log_level: str = "WARNING"
    enable_validation: bool = True

    @classmethod
    def from_environment(cls) -> 'ObservabilityConfig':
        """
        Load configuration from environment variables.

        Required Environment Variables:
        - KINESIS_STREAM_ARN: ARN of the Kinesis stream

        Optional Environment Variables:
        - AWS_REGION: AWS region (default: us-east-1)
        - OBSERVABILITY_LOG_LEVEL: Logging level (default: WARNING)
        - OBSERVABILITY_ENABLE_VALIDATION: Enable schema validation (default: true)

        Returns:
            ObservabilityConfig instance

        Note:
            If KINESIS_STREAM_ARN is not provided, the library will log a warning
            and continue with a placeholder ARN. Events will not be sent to Kinesis
            but the application flow will not be interrupted.
        """
        kinesis_stream_arn = os.environ.get('KINESIS_STREAM_ARN')
        if not kinesis_stream_arn:
            logger.warning(
                "⚠️  KINESIS_STREAM_ARN environment variable not found. "
                "Observability events will not be sent to Kinesis. "
                "Set KINESIS_STREAM_ARN to enable event emission."
            )
            # Use a placeholder ARN to prevent crashes
            kinesis_stream_arn = "arn:aws:kinesis:us-east-1:000000000000:stream/placeholder-stream"

        aws_region = os.environ.get('AWS_REGION', 'us-east-1')
        log_level = os.environ.get('OBSERVABILITY_LOG_LEVEL', 'WARNING')
        enable_validation = os.environ.get('OBSERVABILITY_ENABLE_VALIDATION', 'true').lower() == 'true'

        return cls(
            aws_region=aws_region,
            kinesis_stream_arn=kinesis_stream_arn,
            log_level=log_level,
            enable_validation=enable_validation
        )

    def validate(self) -> None:
        """
        Validate configuration values.

        Note:
            This method will not raise exceptions for missing KINESIS_STREAM_ARN
            to prevent interrupting application flow. Instead, it logs warnings.
        """
        if not self.kinesis_stream_arn or self.kinesis_stream_arn.startswith("arn:aws:kinesis:us-east-1:000000000000"):
            logger.warning(
                "⚠️  Invalid or placeholder Kinesis stream ARN detected. "
                "Events will not be sent to Kinesis."
            )

        if not self.aws_region:
            logger.error("❌ aws_region cannot be empty")

        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.log_level.upper() not in valid_log_levels:
            logger.warning(
                f"⚠️  Invalid log_level '{self.log_level}'. "
                f"Must be one of: {', '.join(valid_log_levels)}. Using WARNING as default."
            )
            self.log_level = 'WARNING'

    def is_kinesis_configured(self) -> bool:
        """
        Check if Kinesis is properly configured.
        
        Returns:
            True if Kinesis stream ARN is valid, False otherwise.
        """
        return bool(
            self.kinesis_stream_arn and 
            not self.kinesis_stream_arn.startswith("arn:aws:kinesis:us-east-1:000000000000")
        )


# Global configuration instance (lazy-loaded)
_config: Optional[ObservabilityConfig] = None


def get_config() -> ObservabilityConfig:
    """
    Get the global ObservabilityConfig singleton instance.

    The configuration is loaded lazily on first access from environment
    variables and validated. Subsequent calls return the cached instance.

    Returns:
        ObservabilityConfig: The global configuration instance

    Raises:
        ValueError: If required environment variables are missing or invalid

    Note:
        This function is called internally by KinesisEmitter on initialization.
        Users typically don't need to call this directly.
    """
    global _config
    if _config is None:
        _config = ObservabilityConfig.from_environment()
        _config.validate()
    return _config


def reset_config() -> None:
    """Reset the global configuration instance (used for testing)."""
    global _config
    _config = None
