"""
Async Scanner Base for RepliMap.

Provides async scanning capabilities using aiobotocore for improved
performance when scanning large AWS environments.
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any, ClassVar

from aiobotocore.session import get_session
from botocore.exceptions import ClientError

if TYPE_CHECKING:
    from replimap.core import GraphEngine


logger = logging.getLogger(__name__)


class AsyncScannerError(Exception):
    """Base exception for async scanner errors."""

    pass


class AsyncPermissionError(AsyncScannerError):
    """Raised when AWS permissions are insufficient."""

    pass


class AsyncBaseScanner(ABC):
    """
    Abstract base class for async AWS resource scanners.

    Uses aiobotocore for async AWS API calls, enabling concurrent
    scanning of multiple resource types for improved performance.
    """

    resource_types: ClassVar[list[str]] = []

    def __init__(self, region: str, profile: str | None = None) -> None:
        """
        Initialize the async scanner.

        Args:
            region: AWS region to scan
            profile: AWS profile name (optional)
        """
        self.region = region
        self.profile = profile
        self._session = get_session()

    @asynccontextmanager
    async def get_client(self, service_name: str) -> AsyncIterator[Any]:
        """
        Get an async boto3 client for the specified service.

        Args:
            service_name: AWS service name (e.g., 'ec2', 's3')

        Yields:
            Configured aiobotocore client
        """
        async with self._session.create_client(
            service_name,
            region_name=self.region,
        ) as client:
            yield client

    @abstractmethod
    async def scan(self, graph: GraphEngine) -> None:
        """
        Scan AWS resources asynchronously and add them to the graph.

        Args:
            graph: The GraphEngine to populate

        Raises:
            AsyncScannerError: If scanning fails
            AsyncPermissionError: If AWS permissions are insufficient
        """
        pass

    def _extract_tags(self, tag_list: list[dict] | None) -> dict[str, str]:
        """
        Convert AWS tag list to dictionary.

        Args:
            tag_list: AWS tag list or None

        Returns:
            Dictionary of tag key-value pairs
        """
        if not tag_list:
            return {}
        return {tag["Key"]: tag["Value"] for tag in tag_list}

    async def _handle_aws_error(self, error: ClientError, operation: str) -> None:
        """
        Handle AWS API errors with appropriate logging and exceptions.

        Args:
            error: The boto3 ClientError
            operation: Description of the operation that failed

        Raises:
            AsyncPermissionError: If the error is access-related
            AsyncScannerError: For other AWS errors
        """
        error_code = error.response.get("Error", {}).get("Code", "Unknown")
        error_message = error.response.get("Error", {}).get("Message", str(error))

        if error_code in (
            "AccessDenied",
            "UnauthorizedAccess",
            "AccessDeniedException",
        ):
            logger.error(f"Permission denied: {operation} - {error_message}")
            raise AsyncPermissionError(
                f"Insufficient permissions for {operation}: {error_message}"
            )

        logger.error(f"AWS error during {operation}: {error_code} - {error_message}")
        raise AsyncScannerError(f"AWS error during {operation}: {error_message}")


class AsyncScannerRegistry:
    """
    Registry for async scanners.

    Enables concurrent execution of multiple scanners for improved performance.
    """

    _scanners: ClassVar[list[type[AsyncBaseScanner]]] = []

    @classmethod
    def register(cls, scanner_class: type[AsyncBaseScanner]) -> type[AsyncBaseScanner]:
        """
        Register an async scanner class.

        Args:
            scanner_class: The scanner class to register

        Returns:
            The same scanner class (for decorator use)
        """
        if scanner_class not in cls._scanners:
            cls._scanners.append(scanner_class)
            logger.debug(f"Registered async scanner: {scanner_class.__name__}")
        return scanner_class

    @classmethod
    def get_all(cls) -> list[type[AsyncBaseScanner]]:
        """Get all registered async scanner classes."""
        return cls._scanners.copy()

    @classmethod
    def clear(cls) -> None:
        """Clear all registered scanners (useful for testing)."""
        cls._scanners.clear()


async def run_all_async_scanners(
    region: str,
    graph: GraphEngine,
    profile: str | None = None,
    concurrency: int = 4,
) -> dict[str, Exception | None]:
    """
    Run all registered async scanners concurrently.

    Args:
        region: AWS region to scan
        graph: The GraphEngine to populate
        profile: AWS profile name (optional)
        concurrency: Maximum number of concurrent scanners

    Returns:
        Dictionary mapping scanner names to exceptions (None if successful)
    """
    results: dict[str, Exception | None] = {}
    semaphore = asyncio.Semaphore(concurrency)

    async def run_scanner(scanner_class: type[AsyncBaseScanner]) -> None:
        scanner_name = scanner_class.__name__
        async with semaphore:
            logger.info(f"Running async {scanner_name}...")
            try:
                scanner = scanner_class(region, profile)
                await scanner.scan(graph)
                results[scanner_name] = None
                logger.info(f"{scanner_name} completed successfully")
            except Exception as e:
                results[scanner_name] = e
                logger.error(f"{scanner_name} failed: {e}")

    # Run all scanners concurrently
    await asyncio.gather(
        *[run_scanner(sc) for sc in AsyncScannerRegistry.get_all()],
        return_exceptions=True,
    )

    return results
