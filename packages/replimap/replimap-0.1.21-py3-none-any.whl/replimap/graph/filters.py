"""
Graph Filter configuration for resource visibility.

Defines which resource types to show/hide in graph visualizations.
By default, noisy resources (SG rules, routes) are hidden to improve
graph readability.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from replimap.core.models import ResourceNode


class ResourceVisibility(str, Enum):
    """Visibility level for resource types."""

    CORE = "CORE"  # Always shown: VPC, Subnet, EC2, RDS, etc.
    SECURITY = "SECURITY"  # Security resources: SG, IAM, KMS
    NETWORK_DETAIL = "NETWORK_DETAIL"  # Route tables, routes, NAT
    NOISY = "NOISY"  # Hidden by default: SG rules, individual routes

    def __str__(self) -> str:
        return self.value


# Classification of resource types by visibility level
RESOURCE_VISIBILITY: dict[str, ResourceVisibility] = {
    # Core resources - always shown
    "aws_vpc": ResourceVisibility.CORE,
    "aws_subnet": ResourceVisibility.CORE,
    "aws_instance": ResourceVisibility.CORE,
    "aws_db_instance": ResourceVisibility.CORE,
    "aws_s3_bucket": ResourceVisibility.CORE,
    "aws_lb": ResourceVisibility.CORE,
    "aws_lb_target_group": ResourceVisibility.CORE,
    "aws_elasticache_cluster": ResourceVisibility.CORE,
    "aws_lambda_function": ResourceVisibility.CORE,
    "aws_autoscaling_group": ResourceVisibility.CORE,
    "aws_launch_template": ResourceVisibility.CORE,
    "aws_sqs_queue": ResourceVisibility.CORE,
    "aws_sns_topic": ResourceVisibility.CORE,
    "aws_ebs_volume": ResourceVisibility.CORE,
    "aws_db_subnet_group": ResourceVisibility.CORE,
    "aws_elasticache_subnet_group": ResourceVisibility.CORE,
    # Security resources - shown with --security flag
    "aws_security_group": ResourceVisibility.SECURITY,
    "aws_iam_role": ResourceVisibility.SECURITY,
    "aws_kms_key": ResourceVisibility.SECURITY,
    "aws_s3_bucket_policy": ResourceVisibility.SECURITY,
    # Network detail - shown with --routes or --all
    "aws_route_table": ResourceVisibility.NETWORK_DETAIL,
    "aws_nat_gateway": ResourceVisibility.NETWORK_DETAIL,
    "aws_internet_gateway": ResourceVisibility.NETWORK_DETAIL,
    "aws_vpc_endpoint": ResourceVisibility.NETWORK_DETAIL,
    "aws_eip": ResourceVisibility.NETWORK_DETAIL,
    "aws_lb_listener": ResourceVisibility.NETWORK_DETAIL,
    # Noisy resources - hidden by default, shown with specific flags
    "aws_route": ResourceVisibility.NOISY,
    "aws_security_group_rule": ResourceVisibility.NOISY,
    "aws_db_parameter_group": ResourceVisibility.NOISY,
}


# Noisy resource types (hidden by default)
NOISY_RESOURCE_TYPES: set[str] = {
    "aws_security_group_rule",
    "aws_route",
    "aws_db_parameter_group",
}

# Security group rules - shown with --sg-rules flag
SG_RULE_TYPES: set[str] = {
    "aws_security_group_rule",
}

# Route-related resources - shown with --routes flag
ROUTE_TYPES: set[str] = {
    "aws_route",
    "aws_route_table",
    "aws_route_table_association",
}


@dataclass
class GraphFilter:
    """
    Configuration for filtering graph resources.

    Controls which resource types are visible in visualizations.
    By default, noisy resources (SG rules, routes) are hidden.

    Attributes:
        show_all: Show all resources including noisy ones
        show_sg_rules: Show security group rules
        show_routes: Show routes and route tables
        show_security: Show security resources (SG, IAM, KMS)
        hide_types: Additional resource types to hide
        show_types: Additional resource types to show (overrides hide)
    """

    show_all: bool = False
    show_sg_rules: bool = False
    show_routes: bool = False
    show_security: bool = True  # Security resources shown by default
    hide_types: set[str] = field(default_factory=set)
    show_types: set[str] = field(default_factory=set)

    @classmethod
    def default(cls) -> GraphFilter:
        """Create default filter (hides noisy resources)."""
        return cls()

    @classmethod
    def show_everything(cls) -> GraphFilter:
        """Create filter that shows all resources."""
        return cls(show_all=True)

    @classmethod
    def security_focused(cls) -> GraphFilter:
        """Create filter focused on security resources."""
        return cls(
            show_security=True,
            show_sg_rules=True,
        )

    def should_show(self, resource: ResourceNode) -> bool:
        """
        Determine if a resource should be shown.

        Args:
            resource: The resource to check

        Returns:
            True if the resource should be shown
        """
        resource_type = str(resource.resource_type)
        return self.should_show_type(resource_type)

    def should_show_type(self, resource_type: str) -> bool:
        """
        Determine if a resource type should be shown.

        Args:
            resource_type: The Terraform resource type string

        Returns:
            True if resources of this type should be shown
        """
        # Explicit show_types always takes precedence
        if resource_type in self.show_types:
            return True

        # Explicit hide_types hides resources
        if resource_type in self.hide_types:
            return False

        # Show all flag overrides defaults
        if self.show_all:
            return True

        # Check specific flags
        if resource_type in SG_RULE_TYPES:
            return self.show_sg_rules

        if resource_type in ROUTE_TYPES:
            return self.show_routes

        # Get visibility level for this type
        visibility = RESOURCE_VISIBILITY.get(resource_type, ResourceVisibility.CORE)

        # Core resources always shown
        if visibility == ResourceVisibility.CORE:
            return True

        # Security resources shown based on flag
        if visibility == ResourceVisibility.SECURITY:
            return self.show_security

        # Network detail shown with routes flag
        if visibility == ResourceVisibility.NETWORK_DETAIL:
            return self.show_routes

        # Noisy resources hidden by default
        if visibility == ResourceVisibility.NOISY:
            return False

        # Default: show
        return True

    def filter_resources(self, resources: list[ResourceNode]) -> list[ResourceNode]:
        """
        Filter a list of resources.

        Args:
            resources: List of resources to filter

        Returns:
            Filtered list containing only visible resources
        """
        return [r for r in resources if self.should_show(r)]

    def get_hidden_count(self, resources: list[ResourceNode]) -> dict[str, int]:
        """
        Count hidden resources by type.

        Args:
            resources: List of resources to analyze

        Returns:
            Dictionary mapping resource type to hidden count
        """
        hidden: dict[str, int] = {}
        for resource in resources:
            if not self.should_show(resource):
                resource_type = str(resource.resource_type)
                hidden[resource_type] = hidden.get(resource_type, 0) + 1
        return hidden

    def get_summary(self) -> str:
        """Get human-readable summary of filter settings."""
        if self.show_all:
            return "Showing all resources"

        parts = ["Showing: core resources"]

        if self.show_security:
            parts.append("security groups")
        if self.show_sg_rules:
            parts.append("SG rules")
        if self.show_routes:
            parts.append("routes")

        hidden_parts = []
        if not self.show_sg_rules:
            hidden_parts.append("SG rules")
        if not self.show_routes:
            hidden_parts.append("routes")

        result = ", ".join(parts)
        if hidden_parts:
            result += f" | Hidden: {', '.join(hidden_parts)}"

        return result

    def to_dict(self) -> dict[str, bool | list[str]]:
        """Convert to dictionary for serialization."""
        return {
            "show_all": self.show_all,
            "show_sg_rules": self.show_sg_rules,
            "show_routes": self.show_routes,
            "show_security": self.show_security,
            "hide_types": list(self.hide_types),
            "show_types": list(self.show_types),
        }

    @classmethod
    def from_dict(cls, data: dict) -> GraphFilter:
        """Create from dictionary."""
        return cls(
            show_all=data.get("show_all", False),
            show_sg_rules=data.get("show_sg_rules", False),
            show_routes=data.get("show_routes", False),
            show_security=data.get("show_security", True),
            hide_types=set(data.get("hide_types", [])),
            show_types=set(data.get("show_types", [])),
        )
