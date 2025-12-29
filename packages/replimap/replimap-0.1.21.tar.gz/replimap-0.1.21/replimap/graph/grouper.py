"""
Resource Grouper for graph simplification.

Collapses large collections of similar resources into single nodes
to improve graph readability. For example, 50 EC2 instances in a
subnet can be shown as "50 EC2 instances" instead of 50 separate nodes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from replimap.core.models import ResourceNode


class GroupingStrategy(str, Enum):
    """Strategy for grouping resources."""

    NONE = "NONE"  # No grouping - show all individual resources
    BY_SUBNET = "BY_SUBNET"  # Group by subnet
    BY_TYPE = "BY_TYPE"  # Group by resource type
    BY_VPC = "BY_VPC"  # Group by VPC

    def __str__(self) -> str:
        return self.value


# Default collapse threshold - groups larger than this are collapsed
DEFAULT_COLLAPSE_THRESHOLD = 5


@dataclass
class ResourceGroup:
    """
    A group of similar resources collapsed into a single node.

    Represents multiple resources of the same type within a scope
    (e.g., all EC2 instances in a subnet).

    Attributes:
        group_id: Unique identifier for the group
        resource_type: Type of resources in the group
        count: Number of resources in the group
        scope_id: ID of containing resource (subnet, VPC, etc.)
        scope_type: Type of containing resource
        member_ids: IDs of individual resources in the group
        label: Display label for the group
        properties: Aggregated properties for display
    """

    group_id: str
    resource_type: str
    count: int
    scope_id: str | None = None
    scope_type: str | None = None
    member_ids: list[str] = field(default_factory=list)
    label: str = ""
    properties: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Generate default label if not provided."""
        if not self.label:
            type_name = self._friendly_type_name()
            self.label = f"{self.count} {type_name}"

    def _friendly_type_name(self) -> str:
        """Convert resource type to friendly name."""
        type_map = {
            "aws_instance": "EC2 instances",
            "aws_security_group": "security groups",
            "aws_security_group_rule": "SG rules",
            "aws_route": "routes",
            "aws_ebs_volume": "EBS volumes",
            "aws_db_instance": "RDS instances",
            "aws_lambda_function": "Lambda functions",
            "aws_lb_target_group": "target groups",
            "aws_sqs_queue": "SQS queues",
            "aws_sns_topic": "SNS topics",
        }
        friendly = type_map.get(self.resource_type)
        if friendly:
            return friendly

        # Generic conversion: aws_foo_bar -> foo bars
        name = self.resource_type.replace("aws_", "").replace("_", " ")
        if self.count != 1:
            name += "s"
        return name

    @property
    def is_collapsed(self) -> bool:
        """Check if this group is collapsed (multiple resources)."""
        return self.count > 1

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "group_id": self.group_id,
            "resource_type": self.resource_type,
            "count": self.count,
            "scope_id": self.scope_id,
            "scope_type": self.scope_type,
            "member_ids": self.member_ids,
            "label": self.label,
            "properties": self.properties,
            "is_collapsed": self.is_collapsed,
        }


@dataclass
class GroupingConfig:
    """
    Configuration for resource grouping.

    Controls how resources are grouped and collapsed.

    Attributes:
        enabled: Enable grouping (default True)
        strategy: Grouping strategy to use
        collapse_threshold: Min count to collapse (default 5)
        collapse_types: Resource types to collapse
        never_collapse: Resource types to never collapse
    """

    enabled: bool = True
    strategy: GroupingStrategy = GroupingStrategy.BY_SUBNET
    collapse_threshold: int = DEFAULT_COLLAPSE_THRESHOLD
    collapse_types: set[str] = field(
        default_factory=lambda: {
            "aws_instance",
            "aws_security_group_rule",
            "aws_route",
            "aws_ebs_volume",
            "aws_lb_target_group",
        }
    )
    never_collapse: set[str] = field(
        default_factory=lambda: {
            "aws_vpc",
            "aws_subnet",
            "aws_db_instance",
            "aws_lb",
            "aws_nat_gateway",
            "aws_internet_gateway",
        }
    )

    @classmethod
    def disabled(cls) -> GroupingConfig:
        """Create config with grouping disabled."""
        return cls(enabled=False)

    @classmethod
    def aggressive(cls) -> GroupingConfig:
        """Create config with aggressive grouping (threshold=3)."""
        return cls(collapse_threshold=3)

    def should_collapse(self, resource_type: str, count: int) -> bool:
        """
        Determine if resources should be collapsed.

        Args:
            resource_type: Type of resource
            count: Number of resources

        Returns:
            True if resources should be collapsed
        """
        if not self.enabled:
            return False

        if resource_type in self.never_collapse:
            return False

        if resource_type in self.collapse_types:
            return count >= self.collapse_threshold

        # Default: collapse if count is very high
        return count >= self.collapse_threshold * 2


class ResourceGrouper:
    """
    Groups similar resources for graph simplification.

    Takes a list of resources and returns a combination of
    individual resources and collapsed groups based on the
    grouping configuration.
    """

    def __init__(self, config: GroupingConfig | None = None) -> None:
        """
        Initialize the grouper.

        Args:
            config: Grouping configuration (default creates GroupingConfig())
        """
        self.config = config or GroupingConfig()

    def group_resources(
        self,
        resources: list[ResourceNode],
    ) -> tuple[list[ResourceNode], list[ResourceGroup]]:
        """
        Group resources according to configuration.

        Args:
            resources: List of resources to group

        Returns:
            Tuple of (ungrouped resources, resource groups)
        """
        if not self.config.enabled:
            return resources, []

        if self.config.strategy == GroupingStrategy.BY_SUBNET:
            return self._group_by_subnet(resources)
        elif self.config.strategy == GroupingStrategy.BY_TYPE:
            return self._group_by_type(resources)
        elif self.config.strategy == GroupingStrategy.BY_VPC:
            return self._group_by_vpc(resources)
        else:
            return resources, []

    def _group_by_subnet(
        self,
        resources: list[ResourceNode],
    ) -> tuple[list[ResourceNode], list[ResourceGroup]]:
        """Group resources by their containing subnet."""
        # Group resources by (resource_type, subnet_id)
        type_subnet_groups: dict[tuple[str, str | None], list[ResourceNode]] = {}

        for resource in resources:
            resource_type = str(resource.resource_type)
            subnet_id = resource.config.get("subnet_id") or resource.config.get(
                "subnet_ids", [None]
            )
            if isinstance(subnet_id, list):
                subnet_id = subnet_id[0] if subnet_id else None

            key = (resource_type, subnet_id)
            if key not in type_subnet_groups:
                type_subnet_groups[key] = []
            type_subnet_groups[key].append(resource)

        return self._apply_grouping(type_subnet_groups, "aws_subnet")

    def _group_by_type(
        self,
        resources: list[ResourceNode],
    ) -> tuple[list[ResourceNode], list[ResourceGroup]]:
        """Group resources by type only (global)."""
        type_groups: dict[tuple[str, str | None], list[ResourceNode]] = {}

        for resource in resources:
            resource_type = str(resource.resource_type)
            key = (resource_type, None)
            if key not in type_groups:
                type_groups[key] = []
            type_groups[key].append(resource)

        return self._apply_grouping(type_groups, None)

    def _group_by_vpc(
        self,
        resources: list[ResourceNode],
    ) -> tuple[list[ResourceNode], list[ResourceGroup]]:
        """Group resources by their containing VPC."""
        type_vpc_groups: dict[tuple[str, str | None], list[ResourceNode]] = {}

        for resource in resources:
            resource_type = str(resource.resource_type)
            vpc_id = resource.config.get("vpc_id")

            key = (resource_type, vpc_id)
            if key not in type_vpc_groups:
                type_vpc_groups[key] = []
            type_vpc_groups[key].append(resource)

        return self._apply_grouping(type_vpc_groups, "aws_vpc")

    def _apply_grouping(
        self,
        grouped: dict[tuple[str, str | None], list[ResourceNode]],
        scope_type: str | None,
    ) -> tuple[list[ResourceNode], list[ResourceGroup]]:
        """
        Apply grouping configuration to grouped resources.

        Args:
            grouped: Dict of (type, scope_id) -> resources
            scope_type: Type of scope (subnet, vpc, etc.)

        Returns:
            Tuple of (ungrouped resources, resource groups)
        """
        ungrouped: list[ResourceNode] = []
        groups: list[ResourceGroup] = []

        for (resource_type, scope_id), resource_list in grouped.items():
            count = len(resource_list)

            if self.config.should_collapse(resource_type, count):
                # Create collapsed group
                group = ResourceGroup(
                    group_id=self._generate_group_id(resource_type, scope_id),
                    resource_type=resource_type,
                    count=count,
                    scope_id=scope_id,
                    scope_type=scope_type,
                    member_ids=[r.id for r in resource_list],
                    properties=self._aggregate_properties(resource_list),
                )
                groups.append(group)
            else:
                # Keep individual resources
                ungrouped.extend(resource_list)

        return ungrouped, groups

    def _generate_group_id(
        self,
        resource_type: str,
        scope_id: str | None,
    ) -> str:
        """Generate unique ID for a resource group."""
        type_short = resource_type.replace("aws_", "")
        if scope_id:
            return f"group_{type_short}_{scope_id}"
        return f"group_{type_short}_global"

    def _aggregate_properties(
        self,
        resources: list[ResourceNode],
    ) -> dict[str, Any]:
        """Aggregate properties from resources for group summary."""
        if not resources:
            return {}

        properties: dict[str, Any] = {
            "count": len(resources),
            "ids": [r.id for r in resources[:5]],  # First 5 IDs
        }

        # Aggregate instance types if applicable
        instance_types: dict[str, int] = {}
        for r in resources:
            inst_type = r.config.get("instance_type")
            if inst_type:
                instance_types[inst_type] = instance_types.get(inst_type, 0) + 1

        if instance_types:
            properties["instance_types"] = instance_types

        # Count unique tags
        all_tags: set[str] = set()
        for r in resources:
            all_tags.update(r.tags.keys())
        if all_tags:
            properties["unique_tags"] = list(all_tags)[:10]

        return properties

    def get_grouping_summary(
        self,
        resources: list[ResourceNode],
        groups: list[ResourceGroup],
    ) -> dict[str, Any]:
        """
        Get summary of grouping results.

        Args:
            resources: Ungrouped resources
            groups: Created groups

        Returns:
            Summary dictionary
        """
        total_original = len(resources) + sum(g.count for g in groups)
        total_after = len(resources) + len(groups)
        reduction = total_original - total_after if total_original > 0 else 0

        return {
            "original_count": total_original,
            "after_grouping": total_after,
            "reduction": reduction,
            "reduction_percent": (
                round(reduction / total_original * 100, 1) if total_original > 0 else 0
            ),
            "ungrouped_count": len(resources),
            "group_count": len(groups),
            "groups": [
                {"type": g.resource_type, "count": g.count, "label": g.label}
                for g in groups
            ],
        }
