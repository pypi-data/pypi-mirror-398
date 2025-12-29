"""
Retry logic for AWS API calls.

This module provides retry decorators that coordinate with boto3's
internal retry mechanism to prevent "retry storms".

IMPORTANT: This decorator is for functions that RETURN data,
NOT for async generators that YIELD data. Applying retry to generators
will cause data duplication on retry.
"""

from __future__ import annotations

import asyncio
import logging
import os
import random
import time
from functools import wraps
from typing import TYPE_CHECKING, Any

from botocore.exceptions import ClientError

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)

# Retry configuration (environment-overridable)
MAX_RETRIES = int(os.environ.get("REPLIMAP_MAX_RETRIES", "5"))
BASE_DELAY = float(os.environ.get("REPLIMAP_RETRY_DELAY", "1.0"))
MAX_DELAY = float(os.environ.get("REPLIMAP_MAX_DELAY", "30.0"))

# Errors that should trigger a retry (transient/throttling)
RETRYABLE_ERRORS = frozenset(
    [
        "Throttling",
        "ThrottlingException",
        "RequestLimitExceeded",
        "TooManyRequestsException",
        "ProvisionedThroughputExceededException",
        "ServiceUnavailable",
        "InternalError",
        "RequestTimeout",
        "RequestTimeoutException",
    ]
)

# Errors that should NOT be retried (permanent failures)
FATAL_ERRORS = frozenset(
    [
        "AccessDenied",
        "AccessDeniedException",
        "UnauthorizedAccess",
        "InvalidClientTokenId",
        "ExpiredToken",
        "ExpiredTokenException",
        "ValidationException",
        "InvalidParameterValue",
        "InvalidParameterException",
        "MalformedQueryString",
        "MissingParameter",
        "UnrecognizedClientException",
    ]
)


def with_retry(
    max_retries: int = MAX_RETRIES,
    base_delay: float = BASE_DELAY,
    max_delay: float = MAX_DELAY,
    retryable_errors: frozenset[str] = RETRYABLE_ERRORS,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator for retrying AWS API calls with exponential backoff.

    This decorator handles AWS rate limiting and transient errors by:
    1. Catching ClientError exceptions
    2. Checking if the error code is retryable
    3. Applying exponential backoff with jitter
    4. Failing immediately on fatal errors (no retry)

    IMPORTANT: This replaces boto3's internal retry mechanism.
    Clients MUST be created with BOTO_CONFIG to disable internal retries.

    WARNING: Do NOT use on async generators (functions with `yield`).
    Apply to page-fetching helpers instead.

    Args:
        max_retries: Maximum number of retry attempts (default: 5)
        base_delay: Initial delay in seconds (default: 1.0)
        max_delay: Maximum delay between retries (default: 30.0)
        retryable_errors: Set of AWS error codes that should trigger retry

    Returns:
        Decorated function with retry logic
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except ClientError as e:
                    error_code = e.response.get("Error", {}).get("Code", "")

                    # Fatal errors - don't retry, fail immediately
                    if error_code in FATAL_ERRORS:
                        logger.debug(
                            f"Fatal error {error_code} in {func.__name__}, not retrying"
                        )
                        raise

                    # Non-retryable - fail immediately
                    if error_code not in retryable_errors:
                        logger.debug(
                            f"Non-retryable error {error_code} in {func.__name__}"
                        )
                        raise

                    last_exception = e

                    if attempt == max_retries:
                        logger.error(
                            f"Max retries ({max_retries}) exceeded for {func.__name__}"
                        )
                        raise

                    # Exponential backoff with jitter
                    delay = min(base_delay * (2**attempt), max_delay)
                    jitter = random.uniform(0, delay * 0.1)  # noqa: S311
                    sleep_time = delay + jitter

                    logger.warning(
                        f"Rate limited ({error_code}), retrying {func.__name__} "
                        f"in {sleep_time:.1f}s (attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(sleep_time)

            # Should not reach here, but just in case
            if last_exception:
                raise last_exception
            return None

        return wrapper

    return decorator


def async_retry(
    max_retries: int = MAX_RETRIES,
    base_delay: float = BASE_DELAY,
    max_delay: float = MAX_DELAY,
    retryable_errors: frozenset[str] = RETRYABLE_ERRORS,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Async decorator for retrying AWS API calls with exponential backoff.

    This is the async version of with_retry, using asyncio.sleep instead
    of time.sleep.

    IMPORTANT: This replaces boto3's internal retry mechanism.
    Clients MUST be created with proper config to disable internal retries.

    WARNING: Do NOT use on async generators (functions with `yield`).
    Apply to page-fetching helpers instead.

    Args:
        max_retries: Maximum number of retry attempts (default: 5)
        base_delay: Initial delay in seconds (default: 1.0)
        max_delay: Maximum delay between retries (default: 30.0)
        retryable_errors: Set of AWS error codes that should trigger retry

    Returns:
        Decorated async function with retry logic
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except ClientError as e:
                    error_code = e.response.get("Error", {}).get("Code", "")

                    # Fatal errors - don't retry, fail immediately
                    if error_code in FATAL_ERRORS:
                        logger.debug(
                            f"Fatal error {error_code} in {func.__name__}, not retrying"
                        )
                        raise

                    # Non-retryable - fail immediately
                    if error_code not in retryable_errors:
                        logger.debug(
                            f"Non-retryable error {error_code} in {func.__name__}"
                        )
                        raise

                    last_exception = e

                    if attempt == max_retries:
                        logger.error(
                            f"Max retries ({max_retries}) exceeded for {func.__name__}"
                        )
                        raise

                    # Exponential backoff with jitter
                    delay = min(base_delay * (2**attempt), max_delay)
                    jitter = random.uniform(0, delay * 0.1)  # noqa: S311
                    sleep_time = delay + jitter

                    logger.warning(
                        f"Rate limited ({error_code}), retrying {func.__name__} "
                        f"in {sleep_time:.1f}s (attempt {attempt + 1}/{max_retries})"
                    )
                    await asyncio.sleep(sleep_time)

            # Should not reach here, but just in case
            if last_exception:
                raise last_exception
            return None

        return wrapper

    return decorator
