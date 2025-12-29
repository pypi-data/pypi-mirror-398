"""
Base Scanner for RepliMap.

All resource scanners inherit from BaseScanner and implement the scan() method
to extract resources from AWS and add them to the graph.

Key Improvements:
- Uses BOTO_CONFIG to disable boto3 internal retries (prevents retry storm)
- Uses with_retry decorator for coordinated retry logic
- Supports circuit breaker pattern for resilient scanning
- Sanitizes sensitive data before adding to graph
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TYPE_CHECKING, Any, ClassVar

import boto3
from botocore.exceptions import ClientError

from replimap.core.aws_config import BOTO_CONFIG
from replimap.core.retry import (
    with_retry,  # noqa: F401 - Re-export for backward compatibility
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from replimap.core import GraphEngine


logger = logging.getLogger(__name__)

# Configuration for parallel scanning
MAX_SCANNER_WORKERS = int(os.environ.get("REPLIMAP_MAX_WORKERS", "4"))

# NOTE: Retry configuration is now in replimap.core.retry
# The with_retry decorator is re-exported above for backward compatibility


# Intra-scanner parallelization config
INTRA_SCANNER_WORKERS = int(os.environ.get("REPLIMAP_INTRA_SCANNER_WORKERS", "8"))


def parallel_process_items(
    items: list[Any],
    processor: Callable[[Any], Any],
    max_workers: int | None = None,
    description: str = "items",
) -> tuple[list[Any], list[tuple[Any, Exception]]]:
    """
    Process a list of items in parallel.

    Useful for intra-scanner parallelization (e.g., processing S3 buckets).

    Args:
        items: List of items to process
        processor: Function to process each item
        max_workers: Maximum parallel workers (default: REPLIMAP_INTRA_SCANNER_WORKERS)
        description: Description for logging

    Returns:
        Tuple of (successful_results, failed_items_with_errors)
    """
    if not items:
        return [], []

    workers = max_workers or INTRA_SCANNER_WORKERS
    results: list[Any] = []
    failures: list[tuple[Any, Exception]] = []

    # For small batches, process sequentially
    if len(items) <= 2 or workers <= 1:
        for item in items:
            try:
                result = processor(item)
                if result is not None:
                    results.append(result)
            except Exception as e:
                failures.append((item, e))
                logger.warning(f"Failed to process {description} item: {e}")
        return results, failures

    # Process in parallel
    with ThreadPoolExecutor(max_workers=min(workers, len(items))) as executor:
        future_to_item = {executor.submit(processor, item): item for item in items}

        for future in as_completed(future_to_item):
            item = future_to_item[future]
            try:
                result = future.result()
                if result is not None:
                    results.append(result)
            except Exception as e:
                failures.append((item, e))
                logger.warning(f"Failed to process {description} item: {e}")

    if failures:
        logger.warning(
            f"Parallel processing: {len(results)} succeeded, {len(failures)} failed"
        )

    return results, failures


class ScannerError(Exception):
    """Base exception for scanner errors."""

    pass


class AWSPermissionError(ScannerError):
    """Raised when AWS permissions are insufficient."""

    pass


# Backward compatibility alias (avoid shadowing built-in PermissionError)
PermissionDeniedError = AWSPermissionError


class BaseScanner(ABC):
    """
    Abstract base class for AWS resource scanners.

    Each scanner is responsible for:
    1. Calling AWS APIs to retrieve resources
    2. Converting AWS responses to ResourceNodes
    3. Adding nodes and dependencies to the graph

    Subclasses must implement:
    - resource_types: List of Terraform resource types this scanner handles
    - scan(): The main scanning logic

    Optionally set:
    - depends_on_types: Resource types that must be scanned first
    """

    # Terraform resource types this scanner handles
    resource_types: ClassVar[list[str]] = []

    # Resource types this scanner depends on (must be scanned first)
    # Scanners with dependencies run in phase 2, after phase 1 completes
    depends_on_types: ClassVar[list[str]] = []

    def __init__(self, session: boto3.Session, region: str) -> None:
        """
        Initialize the scanner with AWS credentials.

        Args:
            session: Configured boto3 session
            region: AWS region to scan
        """
        self.session = session
        self.region = region
        self._clients: dict[str, object] = {}

    def get_client(self, service_name: str) -> object:
        """
        Get or create a boto3 client for the specified service.

        Clients are cached for reuse within the scanner.
        All clients are created with BOTO_CONFIG which:
        - Disables boto3 internal retries (we handle retries ourselves)
        - Sets connection and read timeouts
        - Uses signature v4

        Args:
            service_name: AWS service name (e.g., 'ec2', 's3')

        Returns:
            Configured boto3 client
        """
        if service_name not in self._clients:
            self._clients[service_name] = self.session.client(
                service_name,
                region_name=self.region,
                config=BOTO_CONFIG,  # CRITICAL: Prevents retry storm
            )
        return self._clients[service_name]

    @abstractmethod
    def scan(self, graph: GraphEngine) -> None:
        """
        Scan AWS resources and add them to the graph.

        This method should:
        1. Call AWS APIs to list resources
        2. Create ResourceNode instances for each resource
        3. Add nodes to the graph
        4. Establish dependency edges

        Args:
            graph: The GraphEngine to populate

        Raises:
            ScannerError: If scanning fails
            AWSPermissionError: If AWS permissions are insufficient
        """
        pass

    def _extract_tags(self, tag_list: list[dict] | None) -> dict[str, str]:
        """
        Convert AWS tag list to dictionary.

        AWS returns tags as [{"Key": "Name", "Value": "my-resource"}, ...].
        This converts to {"Name": "my-resource", ...}.

        Args:
            tag_list: AWS tag list or None

        Returns:
            Dictionary of tag key-value pairs
        """
        if not tag_list:
            return {}
        return {tag["Key"]: tag["Value"] for tag in tag_list}

    def _handle_aws_error(self, error: ClientError, operation: str) -> None:
        """
        Handle AWS API errors with appropriate logging and exceptions.

        Args:
            error: The boto3 ClientError
            operation: Description of the operation that failed

        Raises:
            AWSPermissionError: If the error is access-related
            ScannerError: For other AWS errors
        """
        error_code = error.response.get("Error", {}).get("Code", "Unknown")
        error_message = error.response.get("Error", {}).get("Message", str(error))

        if error_code in (
            "AccessDenied",
            "UnauthorizedAccess",
            "AccessDeniedException",
        ):
            logger.error(f"Permission denied: {operation} - {error_message}")
            raise AWSPermissionError(
                f"Insufficient permissions for {operation}: {error_message}"
            )

        logger.error(f"AWS error during {operation}: {error_code} - {error_message}")
        raise ScannerError(f"AWS error during {operation}: {error_message}")


class ScannerRegistry:
    """
    Registry for available scanners.

    Provides a central place to register and retrieve scanners,
    enabling dynamic discovery and execution.
    """

    _scanners: ClassVar[list[type[BaseScanner]]] = []

    @classmethod
    def register(cls, scanner_class: type[BaseScanner]) -> type[BaseScanner]:
        """
        Register a scanner class.

        Can be used as a decorator:
            @ScannerRegistry.register
            class MyScanner(BaseScanner):
                ...

        Args:
            scanner_class: The scanner class to register

        Returns:
            The same scanner class (for decorator use)
        """
        if scanner_class not in cls._scanners:
            cls._scanners.append(scanner_class)
            logger.debug(f"Registered scanner: {scanner_class.__name__}")
        return scanner_class

    @classmethod
    def get_all(cls) -> list[type[BaseScanner]]:
        """Get all registered scanner classes."""
        return cls._scanners.copy()

    @classmethod
    def get_for_type(cls, resource_type: str) -> type[BaseScanner] | None:
        """
        Get the scanner that handles a specific resource type.

        Args:
            resource_type: Terraform resource type (e.g., 'aws_vpc')

        Returns:
            Scanner class if found, None otherwise
        """
        for scanner_class in cls._scanners:
            if resource_type in scanner_class.resource_types:
                return scanner_class
        return None

    @classmethod
    def clear(cls) -> None:
        """Clear all registered scanners (useful for testing)."""
        cls._scanners.clear()


def _compute_scanner_phases(
    scanner_classes: list[type[BaseScanner]],
) -> list[list[type[BaseScanner]]]:
    """
    Compute execution phases for scanners based on dependency graph.

    Uses topological sorting to determine the correct order, grouping
    scanners into phases where all scanners in a phase can run in parallel.

    Algorithm:
    1. Build resource_type -> scanner mapping
    2. Build scanner dependency graph (scanner A depends on scanner B if
       A.depends_on_types includes any type produced by B)
    3. Topologically sort and group into levels

    Args:
        scanner_classes: List of scanner classes to organize

    Returns:
        List of phases, where each phase is a list of scanner classes
        that can run in parallel
    """
    if not scanner_classes:
        return []

    # Build resource_type -> scanner mapping
    type_to_scanner: dict[str, type[BaseScanner]] = {}
    for sc in scanner_classes:
        for resource_type in sc.resource_types:
            type_to_scanner[resource_type] = sc

    # Build scanner dependency graph (adjacency list: scanner -> scanners it depends on)
    scanner_deps: dict[type[BaseScanner], set[type[BaseScanner]]] = {
        sc: set() for sc in scanner_classes
    }

    for sc in scanner_classes:
        for dep_type in sc.depends_on_types:
            if dep_type in type_to_scanner:
                provider = type_to_scanner[dep_type]
                if provider != sc:  # Avoid self-dependency
                    scanner_deps[sc].add(provider)

    # Compute in-degree: for each scanner, count the number of dependencies it has
    in_degree: dict[type[BaseScanner], int] = {
        sc: len(scanner_deps[sc]) for sc in scanner_classes
    }

    # Kahn's algorithm for topological sort with level grouping
    phases: list[list[type[BaseScanner]]] = []
    remaining = set(scanner_classes)

    while remaining:
        # Find all scanners with in-degree 0 (no unprocessed dependencies)
        ready = [sc for sc in remaining if in_degree[sc] == 0]

        if not ready:
            # Cycle detected - fall back to running remaining scanners together
            logger.warning(
                f"Dependency cycle detected among scanners: {[s.__name__ for s in remaining]}"
            )
            phases.append(list(remaining))
            break

        phases.append(ready)

        # Remove processed scanners and update in-degrees
        for sc in ready:
            remaining.remove(sc)
            # Decrease in-degree of scanners that depended on this one
            for other in remaining:
                if sc in scanner_deps[other]:
                    scanner_deps[other].remove(sc)
                    in_degree[other] -= 1

    return phases


def run_all_scanners(
    session: boto3.Session,
    region: str,
    graph: GraphEngine,
    parallel: bool = True,
    max_workers: int | None = None,
) -> dict[str, Exception | None]:
    """
    Run all registered scanners.

    Scanners are executed in phases determined by their dependency graph:
    - Scanners with no dependencies run first
    - Scanners depending on those run next, and so on
    - Scanners within each phase run in parallel

    This ensures scanners that query the graph for resources populated by
    other scanners will find those resources (handles transitive dependencies).

    Args:
        session: Configured boto3 session
        region: AWS region to scan
        graph: The GraphEngine to populate
        parallel: If True, run scanners in parallel (default: True)
        max_workers: Maximum parallel workers (default: REPLIMAP_MAX_WORKERS or 4)

    Returns:
        Dictionary mapping scanner names to exceptions (None if successful)
    """
    results: dict[str, Exception | None] = {}
    scanner_classes = ScannerRegistry.get_all()

    if not scanner_classes:
        return results

    # Compute phases based on dependency graph
    phases = _compute_scanner_phases(scanner_classes)
    workers = max_workers or MAX_SCANNER_WORKERS

    for i, phase_scanners in enumerate(phases, 1):
        if not phase_scanners:
            continue

        scanner_names = [sc.__name__ for sc in phase_scanners]
        logger.debug(
            f"Phase {i}: Running {len(phase_scanners)} scanners: {scanner_names}"
        )

        if parallel and workers > 1 and len(phase_scanners) > 1:
            phase_results = _run_scanners_parallel(
                session, region, graph, phase_scanners, workers
            )
        else:
            phase_results = _run_scanners_sequential(
                session, region, graph, phase_scanners
            )

        results.update(phase_results)

    return results


def _run_scanners_sequential(
    session: boto3.Session,
    region: str,
    graph: GraphEngine,
    scanner_classes: list[type[BaseScanner]],
) -> dict[str, Exception | None]:
    """Run scanners sequentially."""
    results: dict[str, Exception | None] = {}

    for scanner_class in scanner_classes:
        scanner_name = scanner_class.__name__
        logger.info(f"Running {scanner_name}...")

        try:
            scanner = scanner_class(session, region)
            scanner.scan(graph)
            results[scanner_name] = None
            logger.info(f"{scanner_name} completed successfully")
        except Exception as e:
            results[scanner_name] = e
            logger.error(f"{scanner_name} failed: {e}")

    return results


def _run_scanners_parallel(
    session: boto3.Session,
    region: str,
    graph: GraphEngine,
    scanner_classes: list[type[BaseScanner]],
    max_workers: int,
) -> dict[str, Exception | None]:
    """Run scanners in parallel using ThreadPoolExecutor."""
    results: dict[str, Exception | None] = {}

    def run_single_scanner(
        scanner_class: type[BaseScanner],
    ) -> tuple[str, Exception | None]:
        scanner_name = scanner_class.__name__
        logger.info(f"Running {scanner_name}...")
        try:
            scanner = scanner_class(session, region)
            scanner.scan(graph)
            logger.info(f"{scanner_name} completed successfully")
            return (scanner_name, None)
        except Exception as e:
            logger.error(f"{scanner_name} failed: {e}")
            return (scanner_name, e)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(run_single_scanner, sc): sc for sc in scanner_classes
        }

        for future in as_completed(futures):
            scanner_name, error = future.result()
            results[scanner_name] = error

    return results
