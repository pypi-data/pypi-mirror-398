"""
Snapshot data models.

Core data structures for infrastructure snapshots and change tracking.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from replimap import __version__


@dataclass
class ResourceSnapshot:
    """
    Snapshot of a single AWS resource.

    Captures the complete configuration of a resource at a point in time.

    Attributes:
        id: AWS resource ID (e.g., 'vpc-12345')
        type: Terraform resource type (e.g., 'aws_vpc')
        arn: Full AWS ARN if available
        name: Resource name from tags or ID
        region: AWS region
        config: Full configuration at snapshot time
        config_hash: Computed hash for quick comparison
        tags: Resource tags
    """

    id: str
    type: str
    arn: str | None = None
    name: str | None = None
    region: str = ""
    config: dict[str, Any] = field(default_factory=dict)
    config_hash: str = ""
    tags: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Compute config hash if not provided."""
        if not self.config_hash and self.config:
            self.config_hash = self._compute_hash(self.config)

    @staticmethod
    def _compute_hash(config: dict[str, Any]) -> str:
        """
        Compute deterministic hash of config.

        Uses SHA-256 with sorted keys for consistency.
        """
        serialized = json.dumps(config, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        """Convert to serializable dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ResourceSnapshot:
        """Create from dictionary."""
        return cls(**data)


@dataclass
class InfraSnapshot:
    """
    Complete infrastructure snapshot.

    Captures all resources in a region/VPC at a point in time.

    Attributes:
        name: User-provided snapshot name
        created_at: ISO timestamp of snapshot creation
        region: AWS region
        vpc_id: VPC ID if scoped
        profile: AWS profile used
        resources: List of resource snapshots
        resource_count: Total resources
        version: Snapshot format version
        replimap_version: RepliMap version used
    """

    name: str
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    region: str = ""
    vpc_id: str | None = None
    profile: str = "default"
    resources: list[ResourceSnapshot] = field(default_factory=list)
    resource_count: int = 0
    version: str = "1.0"
    replimap_version: str = field(default_factory=lambda: __version__)

    def __post_init__(self) -> None:
        """Update resource count."""
        self.resource_count = len(self.resources)

    def to_dict(self) -> dict[str, Any]:
        """Convert to serializable dictionary."""
        return {
            "name": self.name,
            "created_at": self.created_at,
            "region": self.region,
            "vpc_id": self.vpc_id,
            "profile": self.profile,
            "resource_count": self.resource_count,
            "version": self.version,
            "replimap_version": self.replimap_version,
            "resources": [r.to_dict() for r in self.resources],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> InfraSnapshot:
        """Create from dictionary."""
        resources = [ResourceSnapshot.from_dict(r) for r in data.pop("resources", [])]
        return cls(resources=resources, **data)

    def save(self, path: Path) -> None:
        """Save snapshot to file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2, default=str))

    @classmethod
    def load(cls, path: Path) -> InfraSnapshot:
        """Load snapshot from file."""
        data = json.loads(path.read_text())
        return cls.from_dict(data)

    def get_resource(self, resource_id: str) -> ResourceSnapshot | None:
        """Get resource by ID."""
        for r in self.resources:
            if r.id == resource_id:
                return r
        return None

    def get_resources_by_type(self, resource_type: str) -> list[ResourceSnapshot]:
        """Get all resources of a specific type."""
        return [r for r in self.resources if r.type == resource_type]

    def resource_types(self) -> dict[str, int]:
        """Get count of resources by type."""
        counts: dict[str, int] = {}
        for r in self.resources:
            counts[r.type] = counts.get(r.type, 0) + 1
        return counts


@dataclass
class ResourceChange:
    """
    A single resource change between snapshots.

    Represents an added, removed, or modified resource.

    Attributes:
        resource_id: AWS resource ID
        resource_type: Terraform resource type
        resource_name: Human-readable name
        change_type: One of 'added', 'removed', 'modified', 'unchanged'
        changed_attributes: List of modified attribute paths
        before: Old values for changed attributes
        after: New values for changed attributes
        severity: Impact severity (low, medium, high, critical)
    """

    resource_id: str
    resource_type: str
    resource_name: str | None = None
    change_type: str = "modified"  # added, removed, modified, unchanged
    changed_attributes: list[str] = field(default_factory=list)
    before: dict[str, Any] = field(default_factory=dict)
    after: dict[str, Any] = field(default_factory=dict)
    severity: str = "low"  # low, medium, high, critical

    def to_dict(self) -> dict[str, Any]:
        """Convert to serializable dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ResourceChange:
        """Create from dictionary."""
        return cls(**data)

    @property
    def is_security_relevant(self) -> bool:
        """Check if change is security-relevant."""
        security_attrs = [
            "ingress",
            "egress",
            "policy",
            "acl",
            "security_groups",
            "iam",
            "public",
            "encrypted",
            "kms",
            "password",
        ]
        for attr in self.changed_attributes:
            attr_lower = attr.lower()
            if any(sec in attr_lower for sec in security_attrs):
                return True
        return False


@dataclass
class SnapshotDiff:
    """
    Difference between two infrastructure snapshots.

    Provides a complete change analysis between baseline and current state.

    Attributes:
        baseline_name: Name of baseline snapshot
        baseline_date: Timestamp of baseline
        current_name: Name of current snapshot
        current_date: Timestamp of current
        total_added: Count of added resources
        total_removed: Count of removed resources
        total_modified: Count of modified resources
        total_unchanged: Count of unchanged resources
        changes: List of all changes
        by_type: Changes grouped by resource type
        critical_changes: High/critical severity changes
    """

    baseline_name: str
    baseline_date: str
    current_name: str
    current_date: str
    total_added: int = 0
    total_removed: int = 0
    total_modified: int = 0
    total_unchanged: int = 0
    changes: list[ResourceChange] = field(default_factory=list)
    by_type: dict[str, dict[str, int]] = field(default_factory=dict)
    critical_changes: list[ResourceChange] = field(default_factory=list)

    @property
    def total_changes(self) -> int:
        """Total number of changes (added + removed + modified)."""
        return self.total_added + self.total_removed + self.total_modified

    @property
    def has_changes(self) -> bool:
        """Check if there are any changes."""
        return self.total_changes > 0

    @property
    def has_critical_changes(self) -> bool:
        """Check if there are critical/high severity changes."""
        return len(self.critical_changes) > 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to serializable dictionary."""
        return {
            "baseline": {
                "name": self.baseline_name,
                "date": self.baseline_date,
            },
            "current": {
                "name": self.current_name,
                "date": self.current_date,
            },
            "summary": {
                "added": self.total_added,
                "removed": self.total_removed,
                "modified": self.total_modified,
                "unchanged": self.total_unchanged,
                "total_changes": self.total_changes,
            },
            "changes": [c.to_dict() for c in self.changes],
            "by_type": self.by_type,
            "critical_changes": [c.to_dict() for c in self.critical_changes],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SnapshotDiff:
        """Create from dictionary."""
        changes = [ResourceChange.from_dict(c) for c in data.get("changes", [])]
        critical_changes = [
            ResourceChange.from_dict(c) for c in data.get("critical_changes", [])
        ]
        return cls(
            baseline_name=data["baseline"]["name"],
            baseline_date=data["baseline"]["date"],
            current_name=data["current"]["name"],
            current_date=data["current"]["date"],
            total_added=data["summary"]["added"],
            total_removed=data["summary"]["removed"],
            total_modified=data["summary"]["modified"],
            total_unchanged=data["summary"]["unchanged"],
            changes=changes,
            by_type=data.get("by_type", {}),
            critical_changes=critical_changes,
        )

    def get_changes_by_type(self, change_type: str) -> list[ResourceChange]:
        """Get changes of a specific type (added, removed, modified)."""
        return [c for c in self.changes if c.change_type == change_type]

    def get_changes_by_severity(self, severity: str) -> list[ResourceChange]:
        """Get changes of a specific severity."""
        return [c for c in self.changes if c.severity == severity]

    def summary_text(self) -> str:
        """Generate a text summary of the diff."""
        lines = [
            f"Snapshot Diff: {self.baseline_name} → {self.current_name}",
            f"Baseline: {self.baseline_date}",
            f"Current: {self.current_date}",
            "",
            f"Added: {self.total_added}",
            f"Removed: {self.total_removed}",
            f"Modified: {self.total_modified}",
            f"Unchanged: {self.total_unchanged}",
        ]

        if self.critical_changes:
            lines.append("")
            lines.append(f"Critical/High Changes: {len(self.critical_changes)}")

        return "\n".join(lines)
