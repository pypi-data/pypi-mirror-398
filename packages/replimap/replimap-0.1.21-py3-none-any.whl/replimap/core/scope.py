"""
Scope Engine for RepliMap.

Determine the appropriate scope for each resource:
- MANAGED: Generate resource + import/moved blocks
- READ_ONLY: Generate data source only
- SKIP: Don't generate anything

The Seven Laws of Sovereign Code:
7. Know Your Boundaries - Manage what you own, reference what you don't.

CRITICAL SAFETY FEATURE: Not everything you find is yours to manage!

The Ownership Trap:
1. RepliMap scans and finds Default VPC (vpc-12345, IsDefault=true)
2. Generates: resource "aws_vpc" "default_vpc_a1b2" { ... }
3. User runs terraform apply → Success, now "managing" Default VPC
4. User decides to clean up unused resources
5. Accidentally deletes the default VPC block from code
6. terraform apply → "Destroy aws_vpc.default_vpc_a1b2"
7. DISASTER: Default VPC destroyed, all default resources broken!

The Rule: If you didn't create it, don't try to manage it.

The "Pragmatic Sovereign" Principle:
- Defaults, Not Absolutes - All safety rules should have escape hatches
- Users can explicitly override via .replimap.yaml if they need to
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from replimap.core.config import RepliMapConfig
    from replimap.core.models import ResourceNode

logger = logging.getLogger(__name__)


class ResourceScope(Enum):
    """How a resource should be handled."""

    MANAGED = "managed"  # Generate resource + import/moved
    READ_ONLY = "read_only"  # Generate data source only
    SKIP = "skip"  # Don't generate anything


@dataclass
class ScopeResult:
    """Result of scope determination for a resource."""

    scope: ResourceScope
    reason: str
    rule_name: str | None = None

    @property
    def is_managed(self) -> bool:
        """Check if resource should be managed."""
        return self.scope == ResourceScope.MANAGED

    @property
    def is_read_only(self) -> bool:
        """Check if resource is read-only."""
        return self.scope == ResourceScope.READ_ONLY

    @property
    def is_skip(self) -> bool:
        """Check if resource should be skipped."""
        return self.scope == ResourceScope.SKIP


@dataclass
class ScopeRule:
    """A rule for determining resource scope."""

    name: str
    description: str
    matcher: Callable[[ResourceNode], bool]
    scope: ResourceScope
    overridable: bool = True  # Can user override this rule?
    priority: int = 0  # Higher priority rules are checked first


class ScopeEngine:
    """
    Determine the appropriate scope for each resource.

    This is a SAFETY feature with an ESCAPE HATCH.
    Default resources are READ_ONLY by default, but users
    can explicitly choose to manage them via configuration.

    Usage:
        engine = ScopeEngine(config)
        scope = engine.determine_scope(resource)

        if scope == ResourceScope.MANAGED:
            # Generate resource block + import
        elif scope == ResourceScope.READ_ONLY:
            # Generate data source only
        else:
            # Skip this resource
    """

    def __init__(self, config: RepliMapConfig | None = None) -> None:
        """
        Initialize the scope engine.

        Args:
            config: User configuration (optional)
        """
        self.config = config
        self.rules: list[ScopeRule] = []

        # Build rules in priority order
        self._build_core_rules()

        # Apply user overrides
        if config:
            self._apply_user_overrides()
            self._load_user_rules()

    def _build_core_rules(self) -> None:
        """Build the core safety rules."""
        # Default VPC
        self.rules.append(
            ScopeRule(
                name="default_vpc",
                description="AWS Default VPCs should not be managed (by default)",
                matcher=lambda r: (
                    str(r.resource_type) == "aws_vpc"
                    and r.config.get("is_default") is True
                ),
                scope=ResourceScope.READ_ONLY,
                overridable=True,
                priority=100,
            )
        )

        # Default Security Group
        self.rules.append(
            ScopeRule(
                name="default_security_group",
                description="Default Security Groups cannot be deleted",
                matcher=lambda r: (
                    str(r.resource_type) == "aws_security_group"
                    and r.config.get("name") == "default"
                ),
                scope=ResourceScope.READ_ONLY,
                overridable=True,
                priority=100,
            )
        )

        # Default Network ACL
        self.rules.append(
            ScopeRule(
                name="default_network_acl",
                description="Default NACLs cannot be deleted",
                matcher=lambda r: (
                    str(r.resource_type) == "aws_network_acl"
                    and r.config.get("is_default") is True
                ),
                scope=ResourceScope.READ_ONLY,
                overridable=True,
                priority=100,
            )
        )

        # Main Route Table
        self.rules.append(
            ScopeRule(
                name="default_route_table",
                description="Main route tables should be referenced, not managed",
                matcher=lambda r: (
                    str(r.resource_type) == "aws_route_table"
                    and (
                        r.config.get("is_main") is True
                        or "main" in str(r.tags.get("Name", "")).lower()
                    )
                ),
                scope=ResourceScope.READ_ONLY,
                overridable=True,
                priority=100,
            )
        )

        # AWS-managed KMS keys
        self.rules.append(
            ScopeRule(
                name="aws_managed_kms",
                description="AWS-managed KMS keys should not be managed",
                matcher=lambda r: (
                    str(r.resource_type) == "aws_kms_key"
                    and (
                        r.config.get("key_manager") == "AWS"
                        or str(r.id).startswith("alias/aws/")
                    )
                ),
                scope=ResourceScope.READ_ONLY,
                overridable=False,  # Cannot override - AWS managed
                priority=200,
            )
        )

    def _apply_user_overrides(self) -> None:
        """
        Apply user overrides from .replimap.yaml.

        THE ESCAPE HATCH: Users can explicitly choose to manage
        default resources if they need to.
        """
        if not self.config:
            return

        # Check for override of each default rule
        for rule in self.rules:
            if not rule.overridable:
                continue

            should_manage = self.config.is_default_managed(rule.name)

            if should_manage:
                # User explicitly wants to manage this resource type
                logger.warning(
                    f"⚠️ User override: {rule.name} will be MANAGED instead of READ_ONLY. "
                    f"This resource can now be destroyed by Terraform!"
                )
                # Change rule scope to MANAGED
                rule.scope = ResourceScope.MANAGED

    def _load_user_rules(self) -> None:
        """Load additional user-defined scope rules."""
        if not self.config:
            return

        # Load force_manage patterns (highest priority)
        for pattern in self.config.get_force_manage_patterns():
            rule = self._parse_pattern_rule(pattern, ResourceScope.MANAGED)
            if rule:
                rule.priority = 300  # Override everything
                self.rules.append(rule)

        # Load read_only patterns
        for pattern in self.config.get_read_only_patterns():
            rule = self._parse_pattern_rule(pattern, ResourceScope.READ_ONLY)
            if rule:
                rule.priority = 50
                self.rules.append(rule)

        # Load skip patterns
        for pattern in self.config.get_skip_patterns():
            rule = self._parse_pattern_rule(pattern, ResourceScope.SKIP)
            if rule:
                rule.priority = 50
                self.rules.append(rule)

        # Sort by priority (descending)
        self.rules.sort(key=lambda r: -r.priority)

    def _parse_pattern_rule(
        self,
        pattern: str,
        scope: ResourceScope,
    ) -> ScopeRule | None:
        """
        Parse a pattern string into a ScopeRule.

        Patterns:
        - tag:Key=Value  -> Match resources with specific tag
        - id:resource-id -> Match specific resource ID
        - id_prefix:prefix -> Match resources with ID prefix
        - type:aws_type -> Match specific resource type

        Args:
            pattern: Pattern string
            scope: Scope to apply

        Returns:
            ScopeRule or None if pattern is invalid
        """
        try:
            if pattern.startswith("tag:"):
                tag_part = pattern[4:]
                if "=" not in tag_part:
                    logger.warning(f"Invalid tag pattern: {pattern}")
                    return None

                key, value = tag_part.split("=", 1)

                return ScopeRule(
                    name=f"user_tag_{key}",
                    description=f"User rule: tag {key}={value}",
                    matcher=lambda r, k=key, v=value: r.tags.get(k) == v,
                    scope=scope,
                )

            elif pattern.startswith("id:"):
                resource_id = pattern[3:]

                return ScopeRule(
                    name=f"user_id_{resource_id[:8]}",
                    description=f"User rule: specific resource {resource_id}",
                    matcher=lambda r, rid=resource_id: r.id == rid,
                    scope=scope,
                )

            elif pattern.startswith("id_prefix:"):
                prefix = pattern[10:]

                return ScopeRule(
                    name=f"user_prefix_{prefix}",
                    description=f"User rule: ID prefix {prefix}",
                    matcher=lambda r, p=prefix: r.id.startswith(p),
                    scope=scope,
                )

            elif pattern.startswith("type:"):
                resource_type = pattern[5:]

                return ScopeRule(
                    name=f"user_type_{resource_type}",
                    description=f"User rule: resource type {resource_type}",
                    matcher=lambda r, t=resource_type: str(r.resource_type) == t,
                    scope=scope,
                )

            else:
                logger.warning(f"Unknown scope pattern format: {pattern}")
                return None

        except Exception as e:
            logger.warning(f"Failed to parse scope pattern '{pattern}': {e}")
            return None

    def determine_scope(self, resource: ResourceNode) -> ScopeResult:
        """
        Determine the scope for a resource.

        Checks rules in priority order and returns the first match.

        Args:
            resource: ResourceNode to check

        Returns:
            ScopeResult with scope, reason, and rule name
        """
        for rule in self.rules:
            try:
                if rule.matcher(resource):
                    logger.debug(
                        f"Resource {resource.id} matched rule '{rule.name}' -> {rule.scope}"
                    )
                    return ScopeResult(
                        scope=rule.scope,
                        reason=rule.description,
                        rule_name=rule.name,
                    )
            except Exception as e:
                logger.warning(f"Error checking rule {rule.name}: {e}")
                continue

        # Default: MANAGED
        return ScopeResult(
            scope=ResourceScope.MANAGED,
            reason="Default: user-created resource",
            rule_name=None,
        )

    def classify_resources(
        self,
        resources: list[ResourceNode],
    ) -> dict[str, list[ResourceNode]]:
        """
        Classify all resources by scope.

        Args:
            resources: List of ResourceNode objects

        Returns:
            Dictionary mapping scope to list of resources
        """
        classified: dict[str, list[ResourceNode]] = {
            "managed": [],
            "read_only": [],
            "skip": [],
        }

        for resource in resources:
            result = self.determine_scope(resource)
            classified[result.scope.value].append(resource)

        # Log summary
        logger.info(
            f"Resource classification: "
            f"{len(classified['managed'])} managed, "
            f"{len(classified['read_only'])} read-only, "
            f"{len(classified['skip'])} skipped"
        )

        return classified

    def get_scope_reason(self, resource: ResourceNode) -> str:
        """
        Get human-readable reason why resource has its scope.

        Args:
            resource: ResourceNode to check

        Returns:
            Reason string
        """
        result = self.determine_scope(resource)
        return result.reason


class DataSourceRenderer:
    """
    Render resources as Terraform data sources.

    For READ_ONLY resources, we generate data sources instead of
    resource blocks. This allows referencing without managing.
    """

    # Mapping of resource types to their data source filter attribute
    FILTER_ATTRIBUTES: dict[str, str] = {
        "aws_vpc": "vpc-id",
        "aws_subnet": "subnet-id",
        "aws_security_group": "group-id",
        "aws_instance": "instance-id",
        "aws_db_instance": "db-instance-id",
        "aws_route_table": "route-table-id",
        "aws_internet_gateway": "internet-gateway-id",
        "aws_nat_gateway": "nat-gateway-id",
        "aws_ebs_volume": "volume-id",
    }

    def __init__(self, scope_engine: ScopeEngine | None = None) -> None:
        """
        Initialize the data source renderer.

        Args:
            scope_engine: Scope engine for determining scope reasons
        """
        self.scope_engine = scope_engine or ScopeEngine()

    def render_data_sources(
        self,
        resources: list[ResourceNode],
    ) -> str:
        """
        Render resources as data sources.

        Args:
            resources: List of READ_ONLY resources

        Returns:
            HCL content for data.tf
        """
        if not resources:
            return ""

        lines = [
            "# ═══════════════════════════════════════════════════════════════════════════════",
            "# Auto-generated by RepliMap",
            "# These are READ-ONLY data sources - they reference existing resources",
            "# that should NOT be managed by this Terraform configuration.",
            "# ═══════════════════════════════════════════════════════════════════════════════",
            "#",
            "# WARNING: Do not convert these to resource blocks!",
            "# These resources are either AWS defaults, shared infrastructure,",
            "# or managed by another team/state.",
            "#",
            "# To override this behavior, add to .replimap.yaml:",
            "#   scope:",
            "#     manage_defaults:",
            "#       default_vpc: true  # Example",
            "#",
            "# ═══════════════════════════════════════════════════════════════════════════════",
            "",
        ]

        for resource in resources:
            reason = self.scope_engine.get_scope_reason(resource)
            resource_type = str(resource.resource_type)
            filter_name = self.FILTER_ATTRIBUTES.get(resource_type, "id")

            lines.extend(
                [
                    f"# {resource_type}: {resource.id}",
                    f"# Reason: {reason}",
                    f'data "{resource_type}" "{resource.terraform_name}" {{',
                ]
            )

            # Add filter block
            lines.append("  filter {")
            lines.append(f'    name   = "{filter_name}"')
            lines.append(f'    values = ["{resource.id}"]')
            lines.append("  }")

            # Add tags filter for better specificity
            if resource.tags:
                name_tag = resource.tags.get("Name")
                if name_tag:
                    lines.append("")
                    lines.append("  filter {")
                    lines.append('    name   = "tag:Name"')
                    lines.append(f'    values = ["{name_tag}"]')
                    lines.append("  }")

            lines.extend(
                [
                    "}",
                    "",
                ]
            )

        return "\n".join(lines)

    def render_data_sources_file(
        self,
        resources: list[ResourceNode],
        output_path: Path,
    ) -> None:
        """
        Write data sources to file.

        Args:
            resources: List of READ_ONLY resources
            output_path: Path to write data.tf
        """
        from pathlib import Path

        content = self.render_data_sources(resources)
        if content:
            Path(output_path).write_text(content)
            logger.info(f"Wrote data.tf: {len(resources)} data sources")
