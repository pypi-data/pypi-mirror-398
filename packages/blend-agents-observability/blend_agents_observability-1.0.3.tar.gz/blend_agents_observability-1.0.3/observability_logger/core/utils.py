"""
Utility functions for observability logger.
"""

import time
import uuid
import logging

logger = logging.getLogger(__name__)


def generate_id(prefix: str = "") -> str:
    """
    Generate a unique identifier.

    Uses UUID4 for globally unique IDs. Optionally adds a prefix
    for better readability in logs.

    Args:
        prefix: Optional prefix for the ID (e.g., "node_", "edge_")

    Returns:
        Unique identifier string

    Example:
        >>> generate_id("node")
        'node_a1b2c3d4-e5f6-7890-abcd-ef1234567890'
    """
    unique_id = str(uuid.uuid4())
    return f"{prefix}{unique_id}" if prefix else unique_id


def get_current_timestamp_ms() -> int:
    """
    Get current Unix timestamp in milliseconds.

    Returns:
        Current timestamp as integer milliseconds since epoch

    Example:
        >>> get_current_timestamp_ms()
        1700000000000
    """
    return int(time.time() * 1000)



