"""
Dependency Explorer data models.

Models for representing dependency analysis results when exploring
what resources may be affected if a resource is modified or deleted.

IMPORTANT DISCLAIMER:
This analysis is based on AWS API metadata ONLY. Application-level
dependencies (hardcoded IPs, DNS, config files) CANNOT be detected.
Always validate all dependencies before making infrastructure changes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ImpactLevel(str, Enum):
    """
    Estimated impact severity levels.

    Note: These are ESTIMATES based on resource type and AWS API metadata.
    Actual impact may differ based on application-level dependencies.
    """

    CRITICAL = "CRITICAL"  # Core infrastructure (VPC, main DB)
    HIGH = "HIGH"  # Production services
    MEDIUM = "MEDIUM"  # Supporting resources
    LOW = "LOW"  # Peripheral resources
    NONE = "NONE"  # No downstream impact detected
    UNKNOWN = "UNKNOWN"  # Cannot determine impact level

    def __str__(self) -> str:
        return self.value


class DependencyType(str, Enum):
    """Types of resource dependencies detected via AWS API."""

    HARD = "HARD"  # AWS API indicates direct dependency (e.g., SG -> EC2)
    SOFT = "SOFT"  # May degrade functionality (e.g., CloudWatch -> EC2)
    REFERENCE = "REFERENCE"  # References resource (e.g., tags)

    def __str__(self) -> str:
        return self.value


@dataclass
class ResourceNode:
    """A resource in the dependency exploration analysis."""

    id: str
    type: str  # aws_instance, aws_security_group, etc.
    name: str
    arn: str | None = None
    region: str = ""

    # Impact metadata (estimates only)
    impact_level: ImpactLevel = ImpactLevel.UNKNOWN
    impact_score: int = 0  # 0-100 (estimate)
    depth: int = 0  # Distance from center resource

    # Dependencies (detected via AWS API only)
    depends_on: list[str] = field(default_factory=list)
    depended_by: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "arn": self.arn,
            "region": self.region,
            "impact_level": self.impact_level.value,
            "impact_score": self.impact_score,
            "depth": self.depth,
            "depends_on": self.depends_on,
            "depended_by": self.depended_by,
        }


# Alias for backward compatibility
BlastNode = ResourceNode


@dataclass
class DependencyEdge:
    """An edge representing a dependency between resources."""

    source_id: str  # Dependent resource
    target_id: str  # Resource being depended on
    dependency_type: DependencyType = DependencyType.HARD
    attribute: str = ""  # Which attribute creates the dependency
    description: str = ""  # Human-readable description

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "dependency_type": self.dependency_type.value,
            "attribute": self.attribute,
            "description": self.description,
        }


@dataclass
class DependencyZone:
    """A group of resources at the same depth from the center."""

    depth: int  # 0 = center resource, 1 = direct deps, etc.
    resources: list[ResourceNode] = field(default_factory=list)
    total_impact_score: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "depth": self.depth,
            "resources": [r.id for r in self.resources],
            "resource_count": len(self.resources),
            "total_impact_score": self.total_impact_score,
        }


# Alias for backward compatibility
BlastZone = DependencyZone


# Standard disclaimer text
DISCLAIMER_SHORT = (
    "Based on AWS API metadata only. "
    "Application-level dependencies (hardcoded IPs, DNS, config) NOT detected."
)

DISCLAIMER_FULL = """
IMPORTANT DISCLAIMER

This analysis is based on AWS API metadata ONLY.

The following dependencies CANNOT be detected:
• Hardcoded IP addresses in application code
• DNS-based service discovery
• Configuration files referencing other resources
• Application-level dependencies
• Cross-account references
• External service integrations

ALWAYS review application logs, code, and configuration
before making any infrastructure changes.

RepliMap provides suggestions only. You are responsible
for validating all dependencies before making changes.
"""

# Standard limitations list
STANDARD_LIMITATIONS = [
    "Application-level dependencies not detected",
    "Hardcoded IPs/hostnames not detected",
    "DNS-based references not detected",
    "Cross-account dependencies not detected",
    "Configuration file references not detected",
    "External service integrations not detected",
]


@dataclass
class DependencyExplorerResult:
    """
    Complete dependency exploration result.

    IMPORTANT: This analysis is based on AWS API metadata only.
    Application-level dependencies cannot be detected.
    """

    # The resource being analyzed
    center_resource: ResourceNode

    # Impact zones (organized by depth)
    zones: list[DependencyZone] = field(default_factory=list)

    # All affected resources (detected via AWS API)
    affected_resources: list[ResourceNode] = field(default_factory=list)

    # Dependency edges
    edges: list[DependencyEdge] = field(default_factory=list)

    # Summary
    total_affected: int = 0
    max_depth: int = 0

    # Renamed from "overall_impact" - be more cautious
    estimated_impact: ImpactLevel = ImpactLevel.UNKNOWN
    estimated_score: int = 0  # 0-100

    # Renamed from "safe_deletion_order" - no guarantees
    suggested_review_order: list[str] = field(default_factory=list)

    # Warnings - always include disclaimer
    warnings: list[str] = field(default_factory=list)

    # Explicit limitations - always populated
    limitations: list[str] = field(default_factory=lambda: list(STANDARD_LIMITATIONS))

    # Disclaimer text for display
    disclaimer: str = field(default_factory=lambda: DISCLAIMER_FULL.strip())

    def __post_init__(self) -> None:
        """Ensure disclaimer warning is always present."""
        main_warning = (
            "This analysis is based on AWS API metadata only. "
            "Application-level dependencies cannot be detected."
        )
        if not any(main_warning in str(w) for w in self.warnings):
            self.warnings.insert(0, main_warning)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON output."""
        return {
            "disclaimer": self.disclaimer,
            "limitations": self.limitations,
            "center": {
                "id": self.center_resource.id,
                "type": self.center_resource.type,
                "name": self.center_resource.name,
            },
            "summary": {
                "total_affected": self.total_affected,
                "max_depth": self.max_depth,
                "estimated_impact": self.estimated_impact.value,
                "estimated_score": self.estimated_score,
                "note": "Impact levels are estimates based on AWS API metadata only",
            },
            "zones": [z.to_dict() for z in self.zones],
            "affected_resources": [r.to_dict() for r in self.affected_resources],
            "edges": [e.to_dict() for e in self.edges],
            "suggested_review_order": self.suggested_review_order,
            "warnings": self.warnings,
        }


# Alias for backward compatibility
BlastRadiusResult = DependencyExplorerResult
