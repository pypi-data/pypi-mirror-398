"""
Graph-Based Selection Engine for RepliMap.

This module implements a sophisticated resource selection system based on
graph traversal rather than simple filtering. It supports:

- Multiple selection modes (VPC scope, entry point, tag-based)
- Intelligent boundary handling (network, identity, global resources)
- Context-aware clone vs reference decisions
- Dependency integrity enforcement

The key insight is that users think in terms of "entry points" and want
to automatically include all related resources, not manually specify filters.
"""

from __future__ import annotations

import fnmatch
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

from .models import ResourceNode, ResourceType

if TYPE_CHECKING:
    from .graph_engine import GraphEngine

logger = logging.getLogger(__name__)


# =============================================================================
# Enums
# =============================================================================


class SelectionMode(Enum):
    """Resource selection mode."""

    ALL = "all"  # All resources
    VPC_SCOPE = "vpc"  # VPC-scoped selection
    ENTRY_POINT = "entry"  # Entry point traversal
    TAG_BASED = "tag"  # Tag-based selection


class DependencyDirection(Enum):
    """Dependency traversal direction."""

    UPSTREAM = "upstream"  # What I depend on (EC2 -> Subnet -> VPC)
    DOWNSTREAM = "downstream"  # What depends on me (VPC -> Subnet -> EC2)
    BOTH = "both"  # Bidirectional


class BoundaryAction(Enum):
    """How to handle boundary resources."""

    TRAVERSE = "traverse"  # Continue traversing
    DATA_SOURCE = "data_source"  # Generate data source reference
    VARIABLE = "variable"  # Generate variable placeholder
    EXCLUDE = "exclude"  # Completely exclude


class CloneAction(Enum):
    """What to do with a resource."""

    CLONE = "clone"  # Create new resource
    REFERENCE = "reference"  # Use data source
    VARIABLE = "variable"  # Use variable
    SKIP = "skip"  # Skip entirely


class CloneMode(Enum):
    """Clone mode preset."""

    ISOLATED = "isolated"  # Fully isolated environment (clone most)
    SHARED = "shared"  # Share infrastructure (reference more)
    MINIMAL = "minimal"  # Minimal clone


# =============================================================================
# Configuration Classes
# =============================================================================


@dataclass
class BoundaryConfig:
    """
    Configuration for handling resource boundaries.

    Boundaries are resources where traversal should stop or change behavior.
    This prevents "topology explosion" when traversing interconnected resources.
    """

    # Network boundaries: Stop traversal, generate data source
    network_boundaries: set[str] = field(
        default_factory=lambda: {
            "aws_ec2_transit_gateway",
            "aws_ec2_transit_gateway_attachment",
            "aws_vpc_peering_connection",
            "aws_vpn_connection",
            "aws_dx_connection",
            "aws_customer_gateway",
        }
    )

    # Identity boundaries: Default to variable, can override to clone
    identity_boundaries: set[str] = field(
        default_factory=lambda: {
            "aws_iam_role",
            "aws_iam_policy",
            "aws_iam_instance_profile",
        }
    )

    # Global resources: Exclude entirely (not region-specific)
    global_resources: set[str] = field(
        default_factory=lambda: {
            "aws_route53_zone",
            "aws_route53_record",
            "aws_cloudfront_distribution",
            "aws_acm_certificate",
            "aws_iam_user",
            "aws_iam_group",
            "aws_waf_web_acl",
        }
    )

    # Shared service boundaries: Default to reference
    shared_services: set[str] = field(
        default_factory=lambda: {
            "aws_directory_service_directory",
            "aws_elasticsearch_domain",
            "aws_msk_cluster",
        }
    )

    # User overrides: Resource type -> action
    user_overrides: dict[str, BoundaryAction] = field(default_factory=dict)

    def get_action(self, resource_type: str) -> BoundaryAction:
        """Get the boundary action for a resource type."""
        # Normalize type name
        if not resource_type.startswith("aws_"):
            resource_type = f"aws_{resource_type}"

        # User overrides take precedence
        if resource_type in self.user_overrides:
            return self.user_overrides[resource_type]

        if resource_type in self.global_resources:
            return BoundaryAction.EXCLUDE

        if resource_type in self.network_boundaries:
            return BoundaryAction.DATA_SOURCE

        if resource_type in self.identity_boundaries:
            return BoundaryAction.VARIABLE

        if resource_type in self.shared_services:
            return BoundaryAction.DATA_SOURCE

        return BoundaryAction.TRAVERSE


@dataclass
class TargetContext:
    """
    Context about the target environment for clone decisions.

    This helps the engine decide whether to clone or reference resources
    based on the relationship between source and target environments.
    """

    # Environment relationship
    same_account: bool = True
    same_region: bool = True
    same_vpc: bool = False  # Usually staging is a new VPC

    # Target identifiers (for reference generation)
    target_vpc_id: str | None = None
    target_account_id: str | None = None
    target_region: str | None = None

    # Clone mode preset
    clone_mode: CloneMode = CloneMode.ISOLATED

    # Environment naming (for renaming transformations)
    source_env: str = "prod"
    target_env: str = "staging"


@dataclass
class SelectionStrategy:
    """
    Complete resource selection strategy.

    This is the main configuration object that controls how resources
    are selected, how boundaries are handled, and what actions to take.
    """

    # === Selection Mode ===
    mode: SelectionMode = SelectionMode.ALL

    # === VPC Scope Selection ===
    vpc_ids: list[str] = field(default_factory=list)
    vpc_names: list[str] = field(default_factory=list)

    # === Entry Point Selection ===
    entry_points: list[str] = field(default_factory=list)  # Resource IDs
    entry_point_types: list[str] = field(default_factory=list)  # Resource types
    entry_point_tags: dict[str, str] = field(default_factory=dict)  # Tag filters
    entry_point_names: list[str] = field(default_factory=list)  # Name patterns

    # === Traversal Options ===
    direction: DependencyDirection = DependencyDirection.UPSTREAM
    max_depth: int = 15  # Prevent infinite traversal

    # === Include/Exclude Filters ===
    include_types: set[str] = field(default_factory=set)
    exclude_types: set[str] = field(default_factory=set)
    exclude_patterns: list[str] = field(default_factory=list)  # Name patterns
    exclude_tags: dict[str, str] = field(default_factory=dict)

    # === Special Options ===
    include_shared_resources: bool = True
    include_aws_managed: bool = False  # default SG, etc.

    # === Boundary and Clone Config ===
    boundary_config: BoundaryConfig = field(default_factory=BoundaryConfig)
    target_context: TargetContext = field(default_factory=TargetContext)

    def is_empty(self) -> bool:
        """Check if this is an empty/default strategy."""
        return (
            self.mode == SelectionMode.ALL
            and not self.vpc_ids
            and not self.vpc_names
            and not self.entry_points
            and not self.entry_point_types
            and not self.entry_point_tags
            and not self.entry_point_names
            and not self.include_types
            and not self.exclude_types
            and not self.exclude_patterns
            and not self.exclude_tags
        )

    def describe(self) -> str:
        """Human-readable description of the strategy."""
        parts = []

        if self.mode == SelectionMode.VPC_SCOPE:
            if self.vpc_ids:
                parts.append(f"VPC: {', '.join(self.vpc_ids)}")
            if self.vpc_names:
                parts.append(f"VPC names: {', '.join(self.vpc_names)}")

        elif self.mode == SelectionMode.ENTRY_POINT:
            if self.entry_points:
                parts.append(f"Entry points: {', '.join(self.entry_points[:3])}")
            if self.entry_point_types:
                parts.append(f"Entry types: {', '.join(self.entry_point_types)}")
            if self.entry_point_tags:
                tags = [f"{k}={v}" for k, v in self.entry_point_tags.items()]
                parts.append(f"Entry tags: {', '.join(tags)}")

        elif self.mode == SelectionMode.TAG_BASED:
            if self.entry_point_tags:
                tags = [f"{k}={v}" for k, v in self.entry_point_tags.items()]
                parts.append(f"Tags: {', '.join(tags)}")

        if self.exclude_types:
            parts.append(f"Exclude types: {', '.join(self.exclude_types)}")

        if self.exclude_patterns:
            parts.append(f"Exclude patterns: {', '.join(self.exclude_patterns)}")

        return "; ".join(parts) if parts else "No selection criteria"

    @classmethod
    def from_cli_args(
        cls,
        scope: str | None = None,
        entry: str | None = None,
        tag: list[str] | None = None,
        exclude_types: str | None = None,
        exclude_patterns: str | None = None,
        clone_mode: str | None = None,
        direction: str | None = None,
    ) -> SelectionStrategy:
        """
        Create strategy from CLI arguments.

        CLI Syntax:
            --scope vpc:vpc-12345
            --scope vpc-name:Production*
            --entry alb:my-app-alb
            --entry tag:Application=MyApp
            --tag Environment=Production
        """
        strategy = cls()

        # Parse --scope
        if scope:
            if scope.startswith("vpc:"):
                strategy.mode = SelectionMode.VPC_SCOPE
                vpc_value = scope[4:]
                strategy.vpc_ids = [v.strip() for v in vpc_value.split(",")]
            elif scope.startswith("vpc-name:"):
                strategy.mode = SelectionMode.VPC_SCOPE
                vpc_name = scope[9:]
                strategy.vpc_names = [v.strip() for v in vpc_name.split(",")]
            else:
                # Assume it's a VPC ID if it starts with vpc-
                if scope.startswith("vpc-"):
                    strategy.mode = SelectionMode.VPC_SCOPE
                    strategy.vpc_ids = [scope]

        # Parse --entry
        if entry:
            strategy.mode = SelectionMode.ENTRY_POINT
            if entry.startswith("tag:"):
                # Entry by tag: tag:Key=Value
                tag_spec = entry[4:]
                if "=" in tag_spec:
                    key, value = tag_spec.split("=", 1)
                    strategy.entry_point_tags[key] = value
            elif ":" in entry:
                # Entry by type:name pattern
                entry_type, entry_pattern = entry.split(":", 1)
                strategy.entry_point_types.append(entry_type)
                strategy.entry_point_names.append(entry_pattern)
            else:
                # Assume it's a resource ID
                strategy.entry_points.append(entry)

        # Parse --tag (for tag-based selection)
        if tag:
            if strategy.mode == SelectionMode.ALL:
                strategy.mode = SelectionMode.TAG_BASED
            for tag_spec in tag:
                if "=" in tag_spec:
                    key, value = tag_spec.split("=", 1)
                    strategy.entry_point_tags[key] = value

        # Parse --exclude-types
        if exclude_types:
            strategy.exclude_types = {
                t.strip().lower() for t in exclude_types.split(",")
            }

        # Parse --exclude-patterns
        if exclude_patterns:
            strategy.exclude_patterns = [p.strip() for p in exclude_patterns.split(",")]

        # Parse --clone-mode
        if clone_mode:
            try:
                strategy.target_context.clone_mode = CloneMode(clone_mode.lower())
            except ValueError:
                pass

        # Parse --direction
        if direction:
            try:
                strategy.direction = DependencyDirection(direction.lower())
            except ValueError:
                pass

        return strategy

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SelectionStrategy:
        """Create strategy from a dictionary (e.g., YAML config)."""
        strategy = cls()

        # Selection mode
        if "mode" in data:
            strategy.mode = SelectionMode(data["mode"])

        # VPC scope
        if "vpc_ids" in data:
            strategy.vpc_ids = data["vpc_ids"]
        if "vpc_names" in data:
            strategy.vpc_names = data["vpc_names"]

        # Entry points
        if "entry_points" in data:
            for entry in data["entry_points"]:
                if isinstance(entry, str):
                    strategy.entry_points.append(entry)
                elif isinstance(entry, dict):
                    if "id" in entry:
                        strategy.entry_points.append(entry["id"])
                    if "type" in entry:
                        strategy.entry_point_types.append(entry["type"])
                    if "tag" in entry:
                        key, value = entry["tag"].split("=", 1)
                        strategy.entry_point_tags[key] = value
                    if "name" in entry:
                        strategy.entry_point_names.append(entry["name"])

        # Traversal
        if "direction" in data:
            strategy.direction = DependencyDirection(data["direction"])
        if "max_depth" in data:
            strategy.max_depth = data["max_depth"]

        # Filters
        if "include_types" in data:
            strategy.include_types = set(data["include_types"])
        if "exclude" in data:
            exclude = data["exclude"]
            if "types" in exclude:
                strategy.exclude_types = set(exclude["types"])
            if "patterns" in exclude:
                strategy.exclude_patterns = exclude["patterns"]
            if "tags" in exclude:
                strategy.exclude_tags = exclude["tags"]

        # Boundary config
        if "boundaries" in data:
            boundary_data = data["boundaries"]
            if "user_overrides" in boundary_data:
                for rtype, action in boundary_data["user_overrides"].items():
                    strategy.boundary_config.user_overrides[rtype] = BoundaryAction(
                        action
                    )

        # Target context
        if "target" in data:
            target_data = data["target"]
            ctx = strategy.target_context
            if "same_account" in target_data:
                ctx.same_account = target_data["same_account"]
            if "same_region" in target_data:
                ctx.same_region = target_data["same_region"]
            if "same_vpc" in target_data:
                ctx.same_vpc = target_data["same_vpc"]
            if "clone_mode" in target_data:
                ctx.clone_mode = CloneMode(target_data["clone_mode"])
            if "source_env" in target_data:
                ctx.source_env = target_data["source_env"]
            if "target_env" in target_data:
                ctx.target_env = target_data["target_env"]

        return strategy


# =============================================================================
# Selection Result
# =============================================================================


@dataclass
class SelectionResult:
    """Result of a selection operation."""

    # Resources to clone (create new)
    to_clone: list[ResourceNode] = field(default_factory=list)

    # Resources to reference (data source)
    data_sources: list[ResourceNode] = field(default_factory=list)

    # Resources requiring variables
    variables: list[ResourceNode] = field(default_factory=list)

    # Resources excluded from output
    excluded: list[ResourceNode] = field(default_factory=list)

    # Metadata
    entry_points_found: list[str] = field(default_factory=list)
    traversal_depth_reached: int = 0

    @property
    def total_selected(self) -> int:
        """Total resources that will produce output."""
        return len(self.to_clone) + len(self.data_sources) + len(self.variables)

    def summary(self) -> dict[str, Any]:
        """Get summary statistics."""
        return {
            "clone": len(self.to_clone),
            "reference": len(self.data_sources),
            "variable": len(self.variables),
            "excluded": len(self.excluded),
            "total": self.total_selected,
            "entry_points": len(self.entry_points_found),
            "max_depth": self.traversal_depth_reached,
        }

    def get_all_selected(self) -> list[ResourceNode]:
        """Get all selected resources (for building subgraph)."""
        return self.to_clone + self.data_sources + self.variables


# =============================================================================
# Clone Decision Engine
# =============================================================================


class CloneDecisionEngine:
    """
    Decides whether to clone or reference each resource.

    The decision depends on:
    - Resource type characteristics
    - Target environment context
    - Clone mode preset
    - Whether the resource is shared
    """

    # Decision matrix: resource_type -> (same_vpc, new_vpc_same_account, cross_account)
    DECISION_MATRIX: dict[str, tuple[str, str, str]] = {
        # Network - must clone for new VPC
        "aws_vpc": ("N/A", "CLONE", "CLONE"),
        "aws_subnet": ("REF", "CLONE", "CLONE"),
        "aws_security_group": ("REF", "CLONE", "CLONE"),
        "aws_route_table": ("REF", "CLONE", "CLONE"),
        "aws_internet_gateway": ("REF", "CLONE", "CLONE"),
        "aws_nat_gateway": ("REF", "CLONE", "CLONE"),
        "aws_vpc_endpoint": ("REF", "CLONE", "CLONE"),
        # Compute - always clone
        "aws_instance": ("CLONE", "CLONE", "CLONE"),
        "aws_launch_template": ("CLONE", "CLONE", "CLONE"),
        "aws_autoscaling_group": ("CLONE", "CLONE", "CLONE"),
        # Load balancing
        "aws_lb": ("CLONE", "CLONE", "CLONE"),
        "aws_lb_listener": ("CLONE", "CLONE", "CLONE"),
        "aws_lb_target_group": ("CLONE", "CLONE", "CLONE"),
        # Database
        "aws_db_instance": ("CLONE", "CLONE", "CLONE"),
        "aws_db_subnet_group": ("REF", "CLONE", "CLONE"),
        "aws_db_parameter_group": ("REF", "CLONE", "CLONE"),
        "aws_elasticache_cluster": ("CLONE", "CLONE", "CLONE"),
        "aws_elasticache_subnet_group": ("REF", "CLONE", "CLONE"),
        # Storage
        "aws_s3_bucket": ("CLONE", "CLONE", "CLONE"),
        "aws_s3_bucket_policy": ("CLONE", "CLONE", "CLONE"),
        "aws_ebs_volume": ("CLONE", "CLONE", "CLONE"),
        # Messaging
        "aws_sqs_queue": ("CLONE", "CLONE", "CLONE"),
        "aws_sns_topic": ("CLONE", "CLONE", "CLONE"),
        # IAM - reference in same account, clone cross-account
        "aws_iam_role": ("REF", "REF", "CLONE"),
        "aws_iam_policy": ("REF", "REF", "CLONE"),
        "aws_iam_instance_profile": ("REF", "REF", "CLONE"),
        # KMS - typically reference
        "aws_kms_key": ("REF", "REF", "CLONE"),
        "aws_kms_alias": ("REF", "REF", "CLONE"),
    }

    def __init__(self, context: TargetContext):
        """Initialize with target context."""
        self.context = context

    def decide(self, resource: ResourceNode) -> CloneAction:
        """Decide what action to take for a resource."""
        resource_type = resource.resource_type.value

        # Check decision matrix
        if resource_type in self.DECISION_MATRIX:
            matrix_row = self.DECISION_MATRIX[resource_type]

            if self.context.same_vpc:
                decision = matrix_row[0]
            elif self.context.same_account and not self.context.same_vpc:
                decision = matrix_row[1]
            else:  # cross_account
                decision = matrix_row[2]

            if decision == "CLONE":
                return CloneAction.CLONE
            elif decision == "REF":
                return CloneAction.REFERENCE
            elif decision == "N/A":
                return CloneAction.SKIP

        # Check for shared resources in SHARED mode
        if self.context.clone_mode == CloneMode.SHARED:
            if self._is_shared_resource(resource):
                return CloneAction.REFERENCE

        # Check for AWS-managed resources
        if self._is_aws_managed(resource):
            return CloneAction.REFERENCE

        # Default: clone
        return CloneAction.CLONE

    def _is_shared_resource(self, resource: ResourceNode) -> bool:
        """Check if a resource appears to be shared infrastructure."""
        name = (resource.original_name or resource.id).lower()

        # Name patterns that suggest shared resources
        shared_keywords = ["shared", "common", "base", "default", "global", "central"]
        if any(kw in name for kw in shared_keywords):
            return True

        # Check for explicit shared tag
        if resource.tags.get("Shared", "").lower() in ("true", "yes", "1"):
            return True

        return False

    def _is_aws_managed(self, resource: ResourceNode) -> bool:
        """Check if a resource is AWS-managed."""
        name = (resource.original_name or resource.id).lower()

        # Default resources
        if name.startswith("default"):
            return True

        # AWS-managed tags
        for tag_key in resource.tags:
            if tag_key.startswith("aws:"):
                return True

        return False


# =============================================================================
# Graph Selector
# =============================================================================


class GraphSelector:
    """
    Graph-based resource selector.

    Traverses the resource dependency graph starting from entry points
    or within a specified scope, collecting related resources while
    respecting boundaries.
    """

    def __init__(self, graph: GraphEngine, strategy: SelectionStrategy):
        """Initialize selector with graph and strategy."""
        self.graph = graph
        self.strategy = strategy
        self.boundary_config = strategy.boundary_config
        self.decision_engine = CloneDecisionEngine(strategy.target_context)

        # Traversal state
        self._selected: set[str] = set()
        self._visited: set[str] = set()
        self._boundary_resources: dict[str, BoundaryAction] = {}
        self._max_depth_reached = 0

    def select(self) -> SelectionResult:
        """Execute selection and return result."""
        # Reset state
        self._selected.clear()
        self._visited.clear()
        self._boundary_resources.clear()
        self._max_depth_reached = 0

        # Execute selection based on mode
        if self.strategy.mode == SelectionMode.ALL:
            entry_points = self._select_all()
        elif self.strategy.mode == SelectionMode.VPC_SCOPE:
            entry_points = self._select_by_vpc()
        elif self.strategy.mode == SelectionMode.ENTRY_POINT:
            entry_points = self._select_by_entry_points()
        elif self.strategy.mode == SelectionMode.TAG_BASED:
            entry_points = self._select_by_tags()
        else:
            entry_points = []

        # Resolve dependencies to ensure integrity
        self._resolve_dependencies()

        # Build result with clone decisions
        result = self._build_result(entry_points)

        return result

    def _select_all(self) -> list[str]:
        """Select all resources (with filters applied)."""
        entry_points = []
        for resource in self.graph.get_all_resources():
            if self._should_include(resource):
                self._selected.add(resource.id)
                entry_points.append(resource.id)
        return entry_points

    def _select_by_vpc(self) -> list[str]:
        """Select resources within VPC scope."""
        # Find target VPCs
        target_vpc_ids = set(self.strategy.vpc_ids)

        # Add VPCs matching name patterns
        for vpc_name in self.strategy.vpc_names:
            for resource in self.graph.get_resources_by_type(ResourceType.VPC):
                name = resource.original_name or resource.id
                if fnmatch.fnmatch(name.lower(), vpc_name.lower()):
                    target_vpc_ids.add(resource.id)

        if not target_vpc_ids:
            logger.warning("No VPCs found matching selection criteria")
            return []

        # Select VPCs and traverse downstream
        entry_points = list(target_vpc_ids)
        for vpc_id in target_vpc_ids:
            self._traverse(
                resource_id=vpc_id,
                direction=DependencyDirection.DOWNSTREAM,
                depth=0,
            )

        return entry_points

    def _select_by_entry_points(self) -> list[str]:
        """Select resources starting from entry points."""
        entry_points: list[str] = []

        # Direct resource IDs
        for resource_id in self.strategy.entry_points:
            if self.graph.get_resource(resource_id):
                entry_points.append(resource_id)

        # Resources matching type and name patterns
        for i, entry_type in enumerate(self.strategy.entry_point_types):
            name_pattern = (
                self.strategy.entry_point_names[i]
                if i < len(self.strategy.entry_point_names)
                else "*"
            )

            for resource in self.graph.get_all_resources():
                type_name = resource.resource_type.value.replace("aws_", "")
                if entry_type.lower() in (type_name, resource.resource_type.value):
                    name = resource.original_name or resource.id
                    if fnmatch.fnmatch(name.lower(), name_pattern.lower()):
                        entry_points.append(resource.id)

        # Resources matching tags
        if self.strategy.entry_point_tags:
            for resource in self.graph.get_all_resources():
                if self._matches_tags(resource, self.strategy.entry_point_tags):
                    entry_points.append(resource.id)

        # Traverse from entry points
        for entry_id in entry_points:
            self._traverse(
                resource_id=entry_id,
                direction=self.strategy.direction,
                depth=0,
            )

        return entry_points

    def _select_by_tags(self) -> list[str]:
        """Select resources by tags and traverse their dependencies."""
        entry_points: list[str] = []

        # Find all resources with matching tags
        for resource in self.graph.get_all_resources():
            if self._matches_tags(resource, self.strategy.entry_point_tags):
                entry_points.append(resource.id)

        # Traverse upstream from each tagged resource
        for entry_id in entry_points:
            self._traverse(
                resource_id=entry_id,
                direction=DependencyDirection.UPSTREAM,
                depth=0,
            )

        return entry_points

    def _traverse(
        self,
        resource_id: str,
        direction: DependencyDirection,
        depth: int,
    ) -> None:
        """Recursively traverse dependencies."""
        # Track max depth
        if depth > self._max_depth_reached:
            self._max_depth_reached = depth

        # Prevent infinite recursion
        if depth > self.strategy.max_depth:
            return

        # Prevent revisiting
        if resource_id in self._visited:
            return
        self._visited.add(resource_id)

        # Get resource
        resource = self.graph.get_resource(resource_id)
        if not resource:
            return

        # Check boundary
        boundary_action = self.boundary_config.get_action(resource.resource_type.value)

        if boundary_action == BoundaryAction.EXCLUDE:
            return

        if boundary_action in (BoundaryAction.DATA_SOURCE, BoundaryAction.VARIABLE):
            # Add as boundary resource but don't traverse further
            self._selected.add(resource_id)
            self._boundary_resources[resource_id] = boundary_action
            return

        # Apply filters
        if not self._should_include(resource):
            return

        # Add to selection
        self._selected.add(resource_id)

        # Traverse in specified direction
        if direction in (DependencyDirection.UPSTREAM, DependencyDirection.BOTH):
            for dep in self.graph.get_dependencies(resource_id):
                self._traverse(dep.id, direction, depth + 1)

        if direction in (DependencyDirection.DOWNSTREAM, DependencyDirection.BOTH):
            for dep in self.graph.get_dependents(resource_id):
                self._traverse(dep.id, direction, depth + 1)

    def _should_include(self, resource: ResourceNode) -> bool:
        """Check if resource passes all filter criteria."""
        resource_type = resource.resource_type.value
        type_short = resource_type.replace("aws_", "")

        # Include types filter
        if self.strategy.include_types:
            if (
                resource_type not in self.strategy.include_types
                and type_short not in self.strategy.include_types
            ):
                return False

        # Exclude types filter
        if self.strategy.exclude_types:
            if (
                resource_type in self.strategy.exclude_types
                or type_short in self.strategy.exclude_types
            ):
                return False

        # Exclude patterns filter
        name = resource.original_name or resource.id
        for pattern in self.strategy.exclude_patterns:
            if fnmatch.fnmatch(name.lower(), pattern.lower()):
                return False

        # Exclude tags filter
        if self.strategy.exclude_tags:
            for tag_key, tag_value in self.strategy.exclude_tags.items():
                if resource.tags.get(tag_key) == tag_value:
                    return False

        # AWS managed resources
        if not self.strategy.include_aws_managed:
            if self._is_aws_managed(resource):
                return False

        return True

    def _matches_tags(self, resource: ResourceNode, tags: dict[str, str]) -> bool:
        """Check if resource matches all specified tags."""
        for key, value in tags.items():
            resource_value = resource.tags.get(key)
            if resource_value is None:
                return False
            if value != "*" and resource_value != value:
                # Support wildcard in value
                if not fnmatch.fnmatch(resource_value, value):
                    return False
        return True

    def _is_aws_managed(self, resource: ResourceNode) -> bool:
        """Check if resource is AWS-managed."""
        name = (resource.original_name or resource.id).lower()
        if name.startswith("default"):
            return True
        return False

    def _resolve_dependencies(self) -> None:
        """Ensure all required dependencies are included."""
        # Iterate until no new dependencies are added
        added = True
        while added:
            added = False
            for resource_id in list(self._selected):
                resource = self.graph.get_resource(resource_id)
                if not resource:
                    continue

                # Get required dependencies
                for dep in self.graph.get_dependencies(resource_id):
                    if dep.id not in self._selected:
                        # Check boundary
                        action = self.boundary_config.get_action(
                            dep.resource_type.value
                        )

                        if action == BoundaryAction.EXCLUDE:
                            continue

                        if action in (
                            BoundaryAction.DATA_SOURCE,
                            BoundaryAction.VARIABLE,
                        ):
                            self._boundary_resources[dep.id] = action

                        self._selected.add(dep.id)
                        added = True

    def _build_result(self, entry_points: list[str]) -> SelectionResult:
        """Build selection result with clone decisions."""
        result = SelectionResult()
        result.entry_points_found = entry_points
        result.traversal_depth_reached = self._max_depth_reached

        for resource_id in self._selected:
            resource = self.graph.get_resource(resource_id)
            if not resource:
                continue

            # Check if it's a boundary resource
            if resource_id in self._boundary_resources:
                action = self._boundary_resources[resource_id]
                if action == BoundaryAction.DATA_SOURCE:
                    result.data_sources.append(resource)
                elif action == BoundaryAction.VARIABLE:
                    result.variables.append(resource)
                continue

            # Use decision engine
            clone_action = self.decision_engine.decide(resource)

            if clone_action == CloneAction.CLONE:
                result.to_clone.append(resource)
            elif clone_action == CloneAction.REFERENCE:
                result.data_sources.append(resource)
            elif clone_action == CloneAction.VARIABLE:
                result.variables.append(resource)
            elif clone_action == CloneAction.SKIP:
                result.excluded.append(resource)

        return result


# =============================================================================
# Helper Functions
# =============================================================================


def apply_selection(
    graph: GraphEngine,
    strategy: SelectionStrategy,
) -> SelectionResult:
    """
    Apply selection strategy to a graph.

    This is the main entry point for the selection engine.

    Args:
        graph: The resource graph to select from
        strategy: Selection strategy to apply

    Returns:
        SelectionResult with categorized resources
    """
    selector = GraphSelector(graph, strategy)
    return selector.select()


def build_subgraph_from_selection(
    graph: GraphEngine,
    result: SelectionResult,
) -> GraphEngine:
    """
    Create a subgraph containing only selected resources.

    Args:
        graph: Original graph
        result: Selection result

    Returns:
        New GraphEngine with selected resources
    """
    selected_ids = [r.id for r in result.get_all_selected()]
    return graph.get_subgraph(selected_ids)
