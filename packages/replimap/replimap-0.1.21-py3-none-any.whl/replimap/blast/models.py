"""
Blast Radius data models.

Models for representing impact analysis results when a resource
is deleted or modified.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ImpactLevel(str, Enum):
    """Impact severity levels."""

    CRITICAL = "CRITICAL"  # Core infrastructure (VPC, main DB)
    HIGH = "HIGH"  # Production services
    MEDIUM = "MEDIUM"  # Supporting resources
    LOW = "LOW"  # Peripheral resources
    NONE = "NONE"  # No downstream impact

    def __str__(self) -> str:
        return self.value


class DependencyType(str, Enum):
    """Types of resource dependencies."""

    HARD = "HARD"  # Will break if deleted (e.g., SG -> EC2)
    SOFT = "SOFT"  # May degrade (e.g., CloudWatch -> EC2)
    REFERENCE = "REFERENCE"  # Just references (e.g., tags)

    def __str__(self) -> str:
        return self.value


@dataclass
class BlastNode:
    """A resource in the blast radius analysis."""

    id: str
    type: str  # aws_instance, aws_security_group, etc.
    name: str
    arn: str | None = None
    region: str = ""

    # Blast metadata
    impact_level: ImpactLevel = ImpactLevel.MEDIUM
    impact_score: int = 0  # 0-100
    depth: int = 0  # Distance from blast center

    # Dependencies
    depends_on: list[str] = field(default_factory=list)  # Resources this depends on
    depended_by: list[str] = field(
        default_factory=list
    )  # Resources that depend on this

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
class BlastZone:
    """A group of resources at the same impact distance."""

    depth: int  # 0 = blast center, 1 = direct deps, etc.
    resources: list[BlastNode] = field(default_factory=list)
    total_impact_score: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "depth": self.depth,
            "resources": [r.id for r in self.resources],
            "resource_count": len(self.resources),
            "total_impact_score": self.total_impact_score,
        }


@dataclass
class BlastRadiusResult:
    """Complete blast radius analysis result."""

    # The resource being analyzed
    center_resource: BlastNode

    # Impact zones (organized by depth)
    zones: list[BlastZone] = field(default_factory=list)

    # All affected resources
    affected_resources: list[BlastNode] = field(default_factory=list)

    # Dependency edges
    edges: list[DependencyEdge] = field(default_factory=list)

    # Summary
    total_affected: int = 0
    max_depth: int = 0
    overall_impact: ImpactLevel = ImpactLevel.MEDIUM
    overall_score: int = 0  # 0-100

    # Safe deletion order (if applicable)
    safe_deletion_order: list[str] = field(default_factory=list)

    # Warnings
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON output."""
        return {
            "center": {
                "id": self.center_resource.id,
                "type": self.center_resource.type,
                "name": self.center_resource.name,
            },
            "summary": {
                "total_affected": self.total_affected,
                "max_depth": self.max_depth,
                "overall_impact": self.overall_impact.value,
                "overall_score": self.overall_score,
            },
            "zones": [z.to_dict() for z in self.zones],
            "affected_resources": [r.to_dict() for r in self.affected_resources],
            "edges": [e.to_dict() for e in self.edges],
            "safe_deletion_order": self.safe_deletion_order,
            "warnings": self.warnings,
        }
