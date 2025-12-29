"""
Scan Cache for RepliMap.

Provides caching capabilities for scanned resources to enable
faster incremental scans and reduce AWS API calls.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .models import ResourceNode, ResourceType

if TYPE_CHECKING:
    from .graph_engine import GraphEngine

logger = logging.getLogger(__name__)

# Default cache directory
DEFAULT_CACHE_DIR = Path.home() / ".replimap" / "cache"

# Default TTLs by resource type (in seconds)
# Resources that rarely change have longer TTLs
DEFAULT_TTLS: dict[str, int] = {
    # Infrastructure (rarely changes) - 24 hours
    "aws_vpc": 86400,
    "aws_subnet": 86400,
    "aws_internet_gateway": 86400,
    "aws_nat_gateway": 86400,
    "aws_route_table": 86400,
    "aws_vpc_endpoint": 86400,
    # Database infrastructure - 12 hours
    "aws_db_subnet_group": 43200,
    "aws_db_parameter_group": 43200,
    "aws_elasticache_subnet_group": 43200,
    # S3 (bucket config rarely changes) - 12 hours
    "aws_s3_bucket": 43200,
    "aws_s3_bucket_policy": 43200,
    # Security groups (moderate change frequency) - 4 hours
    "aws_security_group": 14400,
    # Compute (changes frequently) - 1 hour
    "aws_instance": 3600,
    "aws_launch_template": 3600,
    "aws_autoscaling_group": 3600,
    # Load balancers - 2 hours
    "aws_lb": 7200,
    "aws_lb_listener": 7200,
    "aws_lb_target_group": 7200,
    # Database instances - 2 hours
    "aws_db_instance": 7200,
    "aws_elasticache_cluster": 7200,
    # Messaging - 4 hours
    "aws_sqs_queue": 14400,
    "aws_sns_topic": 14400,
    # Storage - 2 hours
    "aws_ebs_volume": 7200,
    # Routes - 6 hours
    "aws_route": 21600,
}

# Default TTL for unknown resource types
DEFAULT_TTL = 3600  # 1 hour


@dataclass
class CacheEntry:
    """
    A single cache entry for a resource.

    Attributes:
        resource: The cached ResourceNode
        cached_at: Unix timestamp when the resource was cached
        ttl: Time-to-live in seconds
    """

    resource: ResourceNode
    cached_at: float
    ttl: int

    def is_expired(self) -> bool:
        """Check if this cache entry has expired."""
        return time.time() > (self.cached_at + self.ttl)

    def to_dict(self) -> dict[str, Any]:
        """Convert to a serializable dictionary."""
        return {
            "resource": self.resource.to_dict(),
            "cached_at": self.cached_at,
            "ttl": self.ttl,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CacheEntry:
        """Create a CacheEntry from a dictionary."""
        return cls(
            resource=ResourceNode.from_dict(data["resource"]),
            cached_at=data["cached_at"],
            ttl=data["ttl"],
        )


@dataclass
class CacheMetadata:
    """
    Metadata about the cache.

    Attributes:
        account_id: AWS account ID
        region: AWS region
        created_at: Unix timestamp when cache was created
        last_updated: Unix timestamp of last update
        resource_count: Number of resources in cache
    """

    account_id: str
    region: str
    created_at: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)
    resource_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to a serializable dictionary."""
        return {
            "account_id": self.account_id,
            "region": self.region,
            "created_at": self.created_at,
            "last_updated": self.last_updated,
            "resource_count": self.resource_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CacheMetadata:
        """Create CacheMetadata from a dictionary."""
        return cls(
            account_id=data["account_id"],
            region=data["region"],
            created_at=data.get("created_at", time.time()),
            last_updated=data.get("last_updated", time.time()),
            resource_count=data.get("resource_count", 0),
        )


class ScanCache:
    """
    Cache for scanned AWS resources.

    Supports:
    - TTL-based expiration per resource type
    - File-based persistence
    - Incremental updates
    - Cache key based on account/region

    Examples:
        # Create cache for a region
        cache = ScanCache(account_id="123456789", region="us-east-1")

        # Check for cached resource
        resource = cache.get("vpc-12345")
        if resource:
            print("Cache hit!")
        else:
            # Scan and cache
            resource = scan_vpc(...)
            cache.put(resource)

        # Save to disk
        cache.save()

        # Load from disk
        cache = ScanCache.load(account_id="123456789", region="us-east-1")
    """

    def __init__(
        self,
        account_id: str,
        region: str,
        cache_dir: Path | str | None = None,
        ttls: dict[str, int] | None = None,
        default_ttl: int = DEFAULT_TTL,
    ) -> None:
        """
        Initialize the scan cache.

        Args:
            account_id: AWS account ID
            region: AWS region
            cache_dir: Directory to store cache files
            ttls: Custom TTLs per resource type
            default_ttl: Default TTL for unknown resource types
        """
        self.account_id = account_id
        self.region = region
        self.cache_dir = Path(cache_dir) if cache_dir else DEFAULT_CACHE_DIR
        self.ttls = {**DEFAULT_TTLS, **(ttls or {})}
        self.default_ttl = default_ttl

        self._entries: dict[str, CacheEntry] = {}
        self._metadata = CacheMetadata(account_id=account_id, region=region)

    def _get_ttl(self, resource_type: str) -> int:
        """Get TTL for a resource type."""
        return self.ttls.get(resource_type, self.default_ttl)

    def _get_cache_key(self) -> str:
        """Generate cache key from account and region."""
        key = f"{self.account_id}-{self.region}"
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    def _get_cache_path(self) -> Path:
        """Get path to cache file."""
        return self.cache_dir / f"scan-{self._get_cache_key()}.json"

    def get(self, resource_id: str) -> ResourceNode | None:
        """
        Get a resource from cache.

        Returns None if not cached or expired.

        Args:
            resource_id: The resource ID to look up

        Returns:
            ResourceNode if found and valid, None otherwise
        """
        entry = self._entries.get(resource_id)
        if entry is None:
            return None

        if entry.is_expired():
            logger.debug(f"Cache expired for {resource_id}")
            del self._entries[resource_id]
            return None

        logger.debug(f"Cache hit for {resource_id}")
        return entry.resource

    def get_by_type(self, resource_type: ResourceType) -> list[ResourceNode]:
        """
        Get all cached resources of a specific type.

        Only returns non-expired entries.

        Args:
            resource_type: The resource type to filter by

        Returns:
            List of ResourceNodes of the specified type
        """
        result = []
        expired = []

        for resource_id, entry in self._entries.items():
            if entry.resource.resource_type == resource_type:
                if entry.is_expired():
                    expired.append(resource_id)
                else:
                    result.append(entry.resource)

        # Clean up expired entries
        for resource_id in expired:
            del self._entries[resource_id]

        return result

    def put(
        self,
        resource: ResourceNode,
        ttl: int | None = None,
    ) -> None:
        """
        Add or update a resource in the cache.

        Args:
            resource: The ResourceNode to cache
            ttl: Optional custom TTL (uses resource type default if not specified)
        """
        resource_ttl = (
            ttl if ttl is not None else self._get_ttl(resource.resource_type.value)
        )
        entry = CacheEntry(
            resource=resource,
            cached_at=time.time(),
            ttl=resource_ttl,
        )
        self._entries[resource.id] = entry
        self._metadata.last_updated = time.time()
        self._metadata.resource_count = len(self._entries)
        logger.debug(f"Cached {resource.id} with TTL {resource_ttl}s")

    def put_many(self, resources: list[ResourceNode]) -> None:
        """
        Add multiple resources to the cache.

        Args:
            resources: List of ResourceNodes to cache
        """
        for resource in resources:
            self.put(resource)

    def invalidate(self, resource_id: str) -> bool:
        """
        Invalidate (remove) a specific resource from cache.

        Args:
            resource_id: The resource ID to invalidate

        Returns:
            True if the resource was in cache, False otherwise
        """
        if resource_id in self._entries:
            del self._entries[resource_id]
            self._metadata.resource_count = len(self._entries)
            logger.debug(f"Invalidated cache for {resource_id}")
            return True
        return False

    def invalidate_type(self, resource_type: ResourceType) -> int:
        """
        Invalidate all resources of a specific type.

        Args:
            resource_type: The resource type to invalidate

        Returns:
            Number of resources invalidated
        """
        to_remove = [
            rid
            for rid, entry in self._entries.items()
            if entry.resource.resource_type == resource_type
        ]
        for resource_id in to_remove:
            del self._entries[resource_id]

        self._metadata.resource_count = len(self._entries)
        logger.debug(f"Invalidated {len(to_remove)} {resource_type.value} resources")
        return len(to_remove)

    def clear(self) -> None:
        """Clear all cached entries."""
        self._entries.clear()
        self._metadata.resource_count = 0
        logger.debug("Cache cleared")

    def prune_expired(self) -> int:
        """
        Remove all expired entries from cache.

        Returns:
            Number of entries removed
        """
        expired = [rid for rid, entry in self._entries.items() if entry.is_expired()]
        for resource_id in expired:
            del self._entries[resource_id]

        self._metadata.resource_count = len(self._entries)
        if expired:
            logger.debug(f"Pruned {len(expired)} expired cache entries")
        return len(expired)

    def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        self.prune_expired()

        type_counts: dict[str, int] = {}
        for entry in self._entries.values():
            type_name = entry.resource.resource_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

        return {
            "account_id": self.account_id,
            "region": self.region,
            "total_resources": len(self._entries),
            "by_type": type_counts,
            "created_at": self._metadata.created_at,
            "last_updated": self._metadata.last_updated,
        }

    def save(self) -> Path:
        """
        Save cache to disk.

        Returns:
            Path to the saved cache file
        """
        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Prune before saving
        self.prune_expired()

        cache_data = {
            "version": 1,
            "metadata": self._metadata.to_dict(),
            "entries": {rid: entry.to_dict() for rid, entry in self._entries.items()},
        }

        cache_path = self._get_cache_path()
        with open(cache_path, "w") as f:
            json.dump(cache_data, f, indent=2)
        # Set restrictive permissions on cache file (contains resource metadata)
        os.chmod(cache_path, 0o600)

        logger.info(f"Saved cache to {cache_path} ({len(self._entries)} resources)")
        return cache_path

    @classmethod
    def load(
        cls,
        account_id: str,
        region: str,
        cache_dir: Path | str | None = None,
        ttls: dict[str, int] | None = None,
    ) -> ScanCache:
        """
        Load cache from disk.

        Creates a new empty cache if file doesn't exist.

        Args:
            account_id: AWS account ID
            region: AWS region
            cache_dir: Directory containing cache files
            ttls: Custom TTLs per resource type

        Returns:
            Loaded ScanCache instance
        """
        cache = cls(
            account_id=account_id,
            region=region,
            cache_dir=cache_dir,
            ttls=ttls,
        )

        cache_path = cache._get_cache_path()
        if not cache_path.exists():
            logger.debug(f"No cache file found at {cache_path}")
            return cache

        try:
            with open(cache_path) as f:
                cache_data = json.load(f)

            # Verify version
            version = cache_data.get("version", 0)
            if version != 1:
                logger.warning(f"Unknown cache version {version}, starting fresh")
                return cache

            # Load metadata
            if "metadata" in cache_data:
                cache._metadata = CacheMetadata.from_dict(cache_data["metadata"])

            # Load entries
            for rid, entry_data in cache_data.get("entries", {}).items():
                try:
                    entry = CacheEntry.from_dict(entry_data)
                    if not entry.is_expired():
                        cache._entries[rid] = entry
                except Exception as e:
                    logger.warning(f"Failed to load cache entry {rid}: {e}")

            logger.info(
                f"Loaded cache from {cache_path} "
                f"({len(cache._entries)} valid resources)"
            )

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse cache file: {e}")
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")

        return cache

    @classmethod
    def delete_cache(
        cls,
        account_id: str,
        region: str,
        cache_dir: Path | str | None = None,
    ) -> bool:
        """
        Delete cache file for an account/region.

        Args:
            account_id: AWS account ID
            region: AWS region
            cache_dir: Directory containing cache files

        Returns:
            True if cache was deleted, False if it didn't exist
        """
        cache = cls(account_id=account_id, region=region, cache_dir=cache_dir)
        cache_path = cache._get_cache_path()

        if cache_path.exists():
            os.remove(cache_path)
            logger.info(f"Deleted cache at {cache_path}")
            return True
        return False


def populate_graph_from_cache(
    cache: ScanCache,
    graph: GraphEngine,
    resource_types: list[ResourceType] | None = None,
) -> int:
    """
    Populate a graph with cached resources.

    Args:
        cache: The ScanCache to read from
        graph: The GraphEngine to populate
        resource_types: Optional list of types to load (loads all if None)

    Returns:
        Number of resources added to the graph
    """
    count = 0
    cache.prune_expired()

    for entry in cache._entries.values():
        if resource_types and entry.resource.resource_type not in resource_types:
            continue
        graph.add_resource(entry.resource)
        count += 1

    logger.info(f"Populated graph with {count} resources from cache")
    return count


def update_cache_from_graph(
    cache: ScanCache,
    graph: GraphEngine,
    resource_types: list[ResourceType] | None = None,
) -> int:
    """
    Update cache with resources from a graph.

    Args:
        cache: The ScanCache to update
        graph: The GraphEngine to read from
        resource_types: Optional list of types to cache (caches all if None)

    Returns:
        Number of resources added to cache
    """
    count = 0
    for resource in graph.get_all_resources():
        if resource_types and resource.resource_type not in resource_types:
            continue
        cache.put(resource)
        count += 1

    logger.info(f"Updated cache with {count} resources from graph")
    return count


def get_uncached_resource_types(
    cache: ScanCache,
    all_types: list[ResourceType],
    min_count: int = 1,
) -> list[ResourceType]:
    """
    Determine which resource types need to be scanned.

    Returns types that either aren't in cache or have fewer than min_count entries.

    Args:
        cache: The ScanCache to check
        all_types: List of all resource types to consider
        min_count: Minimum number of resources to consider type cached

    Returns:
        List of resource types that need scanning
    """
    cache.prune_expired()
    stats = cache.get_stats()
    type_counts = stats.get("by_type", {})

    uncached = []
    for resource_type in all_types:
        count = type_counts.get(resource_type.value, 0)
        if count < min_count:
            uncached.append(resource_type)

    return uncached
