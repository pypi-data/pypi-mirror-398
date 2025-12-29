"""
Scan Filters for RepliMap.

Provides filtering capabilities for resource scanning to enable
targeted scans and reduce scan time.
"""

from __future__ import annotations

import fnmatch
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from replimap.core.graph_engine import GraphEngine
    from replimap.core.models import ResourceNode

logger = logging.getLogger(__name__)


@dataclass
class ScanFilter:
    """
    Filter configuration for resource scanning.

    Supports filtering by VPC, resource types, tags, and exclusions.
    Filters are ANDed together (resource must match all specified filters).

    Examples:
        # Filter by VPC
        filter = ScanFilter(vpc_ids=["vpc-12345678"])

        # Filter by resource types
        filter = ScanFilter(resource_types=["vpc", "subnet", "ec2"])

        # Filter by tags
        filter = ScanFilter(include_tags={"Environment": "Production"})

        # Exclude resources
        filter = ScanFilter(exclude_types=["sns", "sqs"])
    """

    # Include filters (ANDed)
    vpc_ids: list[str] = field(default_factory=list)
    vpc_names: list[str] = field(default_factory=list)
    resource_types: list[str] = field(default_factory=list)
    include_tags: dict[str, str] = field(default_factory=dict)
    name_patterns: list[str] = field(default_factory=list)

    # Exclude filters (ORed - any match excludes)
    exclude_types: list[str] = field(default_factory=list)
    exclude_tags: dict[str, str] = field(default_factory=dict)
    exclude_patterns: list[str] = field(default_factory=list)

    def is_empty(self) -> bool:
        """Check if no filters are configured."""
        return not any(
            [
                self.vpc_ids,
                self.vpc_names,
                self.resource_types,
                self.include_tags,
                self.name_patterns,
                self.exclude_types,
                self.exclude_tags,
                self.exclude_patterns,
            ]
        )

    def should_include_resource(self, resource: ResourceNode) -> bool:
        """
        Determine if a resource should be included based on filters.

        Args:
            resource: The resource to check

        Returns:
            True if the resource passes all filters
        """
        # Check exclusions first (any match excludes)
        if self._is_excluded(resource):
            return False

        # Check inclusions (all must match)
        return self._matches_inclusions(resource)

    def _is_excluded(self, resource: ResourceNode) -> bool:
        """Check if resource matches any exclusion filter."""
        # Check excluded types
        if self.exclude_types:
            resource_type = resource.resource_type.value
            # Support both full type (aws_vpc) and short type (vpc)
            short_type = resource_type.replace("aws_", "")
            if resource_type in self.exclude_types or short_type in self.exclude_types:
                return True

        # Check excluded tags
        if self.exclude_tags:
            for key, value in self.exclude_tags.items():
                if resource.tags.get(key) == value:
                    return True

        # Check excluded name patterns
        if self.exclude_patterns:
            name = resource.original_name or resource.terraform_name or resource.id
            for pattern in self.exclude_patterns:
                if fnmatch.fnmatch(name.lower(), pattern.lower()):
                    return True

        return False

    def _matches_inclusions(self, resource: ResourceNode) -> bool:
        """Check if resource matches all inclusion filters."""
        # Check resource types
        if self.resource_types:
            resource_type = resource.resource_type.value
            short_type = resource_type.replace("aws_", "")
            if not (
                resource_type in self.resource_types
                or short_type in self.resource_types
            ):
                return False

        # Check VPC IDs (for resources that have vpc_id in config)
        if self.vpc_ids:
            vpc_id = self._get_resource_vpc_id(resource)
            if vpc_id and vpc_id not in self.vpc_ids:
                return False

        # Check VPC names
        if self.vpc_names:
            vpc_name = self._get_resource_vpc_name(resource)
            if vpc_name:
                if not any(
                    fnmatch.fnmatch(vpc_name.lower(), pattern.lower())
                    for pattern in self.vpc_names
                ):
                    return False

        # Check include tags
        if self.include_tags:
            for key, value in self.include_tags.items():
                if value == "*":
                    # Wildcard: just check if tag exists
                    if key not in resource.tags:
                        return False
                elif resource.tags.get(key) != value:
                    return False

        # Check name patterns
        if self.name_patterns:
            name = resource.original_name or resource.terraform_name or resource.id
            if not any(
                fnmatch.fnmatch(name.lower(), pattern.lower())
                for pattern in self.name_patterns
            ):
                return False

        return True

    def _get_resource_vpc_id(self, resource: ResourceNode) -> str | None:
        """Extract VPC ID from resource config."""
        config = resource.config

        # Direct VPC ID
        if "VpcId" in config:
            vpc_id = config["VpcId"]
            return str(vpc_id) if vpc_id is not None else None
        if "vpc_id" in config:
            vpc_id = config["vpc_id"]
            return str(vpc_id) if vpc_id is not None else None

        # For VPC resources, the ID is the resource ID
        if resource.resource_type.value == "aws_vpc":
            return resource.id

        return None

    def _get_resource_vpc_name(self, resource: ResourceNode) -> str | None:
        """Extract VPC name from resource."""
        # For VPC resources, check Name tag
        if resource.resource_type.value == "aws_vpc":
            return resource.tags.get("Name")

        return None

    def get_vpc_filter_for_api(self) -> list[dict] | None:
        """
        Get AWS API filter format for VPC filtering.

        Returns filters suitable for boto3 describe_* calls.
        """
        if not self.vpc_ids:
            return None

        return [{"Name": "vpc-id", "Values": self.vpc_ids}]

    def get_tag_filters_for_api(self) -> list[dict] | None:
        """
        Get AWS API filter format for tag filtering.

        Returns filters suitable for boto3 describe_* calls.
        """
        if not self.include_tags:
            return None

        filters = []
        for key, value in self.include_tags.items():
            if value == "*":
                filters.append({"Name": "tag-key", "Values": [key]})
            else:
                filters.append({"Name": f"tag:{key}", "Values": [value]})

        return filters

    @classmethod
    def from_cli_args(
        cls,
        vpc: str | None = None,
        vpc_name: str | None = None,
        types: str | None = None,
        tags: list[str] | None = None,
        exclude_types: str | None = None,
        exclude_tags: list[str] | None = None,
        name_pattern: str | None = None,
        exclude_pattern: str | None = None,
    ) -> ScanFilter:
        """
        Create a ScanFilter from CLI arguments.

        Args:
            vpc: Comma-separated VPC IDs
            vpc_name: VPC name pattern (supports wildcards)
            types: Comma-separated resource types
            tags: List of "Key=Value" tag filters
            exclude_types: Comma-separated types to exclude
            exclude_tags: List of "Key=Value" tags to exclude
            name_pattern: Resource name pattern (supports wildcards)
            exclude_pattern: Name pattern to exclude

        Returns:
            Configured ScanFilter instance
        """
        filter_obj = cls()

        if vpc:
            filter_obj.vpc_ids = [v.strip() for v in vpc.split(",")]

        if vpc_name:
            filter_obj.vpc_names = [v.strip() for v in vpc_name.split(",")]

        if types:
            filter_obj.resource_types = [t.strip().lower() for t in types.split(",")]

        if tags:
            for tag in tags:
                if "=" in tag:
                    key, value = tag.split("=", 1)
                    filter_obj.include_tags[key.strip()] = value.strip()

        if exclude_types:
            filter_obj.exclude_types = [
                t.strip().lower() for t in exclude_types.split(",")
            ]

        if exclude_tags:
            for tag in exclude_tags:
                if "=" in tag:
                    key, value = tag.split("=", 1)
                    filter_obj.exclude_tags[key.strip()] = value.strip()

        if name_pattern:
            filter_obj.name_patterns = [name_pattern]

        if exclude_pattern:
            filter_obj.exclude_patterns = [exclude_pattern]

        return filter_obj

    def describe(self) -> str:
        """Return a human-readable description of active filters."""
        parts = []

        if self.vpc_ids:
            parts.append(f"VPC: {', '.join(self.vpc_ids)}")
        if self.vpc_names:
            parts.append(f"VPC Name: {', '.join(self.vpc_names)}")
        if self.resource_types:
            parts.append(f"Types: {', '.join(self.resource_types)}")
        if self.include_tags:
            tags = [f"{k}={v}" for k, v in self.include_tags.items()]
            parts.append(f"Tags: {', '.join(tags)}")
        if self.name_patterns:
            parts.append(f"Name: {', '.join(self.name_patterns)}")
        if self.exclude_types:
            parts.append(f"Exclude types: {', '.join(self.exclude_types)}")
        if self.exclude_tags:
            tags = [f"{k}={v}" for k, v in self.exclude_tags.items()]
            parts.append(f"Exclude tags: {', '.join(tags)}")
        if self.exclude_patterns:
            parts.append(f"Exclude names: {', '.join(self.exclude_patterns)}")

        return " | ".join(parts) if parts else "No filters"


def apply_filter_to_graph(
    graph: GraphEngine,
    scan_filter: ScanFilter,
    retain_dependencies: bool = True,
) -> int:
    """
    Apply filter to a graph, removing non-matching resources.

    Args:
        graph: The GraphEngine to filter
        scan_filter: Filter configuration
        retain_dependencies: If True, keep resources that filtered resources depend on

    Returns:
        Number of resources removed
    """
    if scan_filter.is_empty():
        return 0

    # First pass: identify resources to keep
    resources_to_keep = set()
    resources_to_remove = set()

    for resource in graph.get_all_resources():
        if scan_filter.should_include_resource(resource):
            resources_to_keep.add(resource.id)
        else:
            resources_to_remove.add(resource.id)

    # Second pass: if retaining dependencies, add back required dependencies
    if retain_dependencies:
        # Traverse dependencies of kept resources
        dependencies_to_keep: set[str] = set()
        for resource_id in resources_to_keep:
            dep_resource = graph.get_resource(resource_id)
            if dep_resource:
                _collect_dependencies(graph, dep_resource, dependencies_to_keep)

        # Add dependencies back to keep set
        resources_to_keep.update(dependencies_to_keep)
        resources_to_remove -= dependencies_to_keep

    # Remove resources
    removed_count = 0
    for resource_id in resources_to_remove:
        try:
            graph.remove_resource(resource_id)
            removed_count += 1
        except Exception as e:
            logger.warning(f"Failed to remove resource {resource_id}: {e}")

    logger.info(
        f"Filter applied: kept {len(resources_to_keep)} resources, "
        f"removed {removed_count} resources"
    )

    return removed_count


def _collect_dependencies(
    graph: GraphEngine,
    resource: ResourceNode,
    collected: set[str],
) -> None:
    """Recursively collect all dependencies of a resource."""
    for dep_id in resource.dependencies:
        if dep_id not in collected:
            collected.add(dep_id)
            dep_resource = graph.get_resource(dep_id)
            if dep_resource:
                _collect_dependencies(graph, dep_resource, collected)
