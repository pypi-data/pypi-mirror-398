"""
AWS Client Configuration for RepliMap.

This module provides standardized botocore.Config settings for all
AWS API clients to ensure:
1. Consistent timeout behavior
2. Coordinated retry behavior with our custom retry decorator
3. Proper error handling

IMPORTANT: All boto3 clients MUST use BOTO_CONFIG to prevent
"retry storm" behavior where boto3 internal retries compound
with our custom retry decorator.
"""

from __future__ import annotations

import os

from botocore.config import Config

# Timeout configuration (seconds)
CONNECT_TIMEOUT = int(os.environ.get("REPLIMAP_CONNECT_TIMEOUT", "10"))
READ_TIMEOUT = int(os.environ.get("REPLIMAP_READ_TIMEOUT", "30"))

# Disable boto3 internal retries - we handle retries ourselves
# This prevents "retry storm" where boto3 retries 5x and our decorator
# retries 5x, resulting in up to 25 attempts
BOTO_CONFIG = Config(
    retries={
        "mode": "standard",
        "max_attempts": 1,  # Disable boto3 retries, we handle it ourselves
    },
    connect_timeout=CONNECT_TIMEOUT,
    read_timeout=READ_TIMEOUT,
    # Use signature version 4 for all regions
    signature_version="v4",
)


def get_boto_config(
    connect_timeout: int | None = None,
    read_timeout: int | None = None,
    max_pool_connections: int | None = None,
) -> Config:
    """
    Get a customized botocore Config.

    Use this when you need different timeout values than the defaults,
    but still want to maintain the retry coordination.

    Args:
        connect_timeout: Connection timeout in seconds (default: 10)
        read_timeout: Read timeout in seconds (default: 30)
        max_pool_connections: Max connections in the pool (default: 10)

    Returns:
        Configured botocore.Config instance
    """
    config_dict = {
        "retries": {
            "mode": "standard",
            "max_attempts": 1,
        },
        "connect_timeout": connect_timeout or CONNECT_TIMEOUT,
        "read_timeout": read_timeout or READ_TIMEOUT,
        "signature_version": "v4",
    }

    if max_pool_connections is not None:
        config_dict["max_pool_connections"] = max_pool_connections

    return Config(**config_dict)
