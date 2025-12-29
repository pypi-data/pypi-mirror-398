"""Data models for drift detection."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class DriftType(str, Enum):
    """Type of drift detected."""

    ADDED = "added"  # Resource exists in AWS but not in TF
    REMOVED = "removed"  # Resource in TF but deleted from AWS
    MODIFIED = "modified"  # Resource exists in both but attributes differ
    UNCHANGED = "unchanged"  # No drift


class DriftSeverity(str, Enum):
    """Severity of the drift."""

    CRITICAL = "critical"  # Security-related changes (SG, IAM)
    HIGH = "high"  # Production-impacting changes
    MEDIUM = "medium"  # Configuration changes
    LOW = "low"  # Cosmetic changes (tags)
    INFO = "info"  # Informational only


@dataclass
class AttributeDiff:
    """A single attribute difference."""

    attribute: str
    expected: Any  # Value from TF state
    actual: Any  # Value from AWS
    severity: DriftSeverity = DriftSeverity.MEDIUM

    def __str__(self) -> str:
        return f"{self.attribute}: {self.expected!r} → {self.actual!r}"


@dataclass
class ResourceDrift:
    """Drift information for a single resource."""

    resource_type: str  # e.g., "aws_security_group"
    resource_id: str  # e.g., "sg-abc123"
    resource_name: str  # e.g., "web-sg" (TF resource name)
    drift_type: DriftType
    diffs: list[AttributeDiff] = field(default_factory=list)
    severity: DriftSeverity = DriftSeverity.MEDIUM

    # Metadata
    tf_address: str = ""  # e.g., "aws_security_group.web"
    last_modified: datetime | None = None
    modifier: str | None = None  # From CloudTrail if available

    @property
    def is_drifted(self) -> bool:
        return self.drift_type != DriftType.UNCHANGED

    @property
    def diff_count(self) -> int:
        return len(self.diffs)


@dataclass
class DriftReport:
    """Complete drift detection report."""

    # Summary
    total_resources: int = 0
    drifted_resources: int = 0
    added_resources: int = 0
    removed_resources: int = 0
    modified_resources: int = 0

    # Details
    drifts: list[ResourceDrift] = field(default_factory=list)

    # Metadata
    state_file: str = ""
    region: str = ""
    scanned_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    scan_duration_seconds: float = 0.0

    @property
    def has_drift(self) -> bool:
        return self.drifted_resources > 0

    @property
    def critical_drifts(self) -> list[ResourceDrift]:
        return [d for d in self.drifts if d.severity == DriftSeverity.CRITICAL]

    @property
    def high_drifts(self) -> list[ResourceDrift]:
        return [d for d in self.drifts if d.severity == DriftSeverity.HIGH]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "summary": {
                "total_resources": self.total_resources,
                "drifted_resources": self.drifted_resources,
                "added_resources": self.added_resources,
                "removed_resources": self.removed_resources,
                "modified_resources": self.modified_resources,
                "has_drift": self.has_drift,
            },
            "drifts": [
                {
                    "type": d.drift_type.value,
                    "severity": d.severity.value,
                    "resource_type": d.resource_type,
                    "resource_id": d.resource_id,
                    "resource_name": d.resource_name,
                    "tf_address": d.tf_address,
                    "diffs": [
                        {
                            "attribute": diff.attribute,
                            "expected": diff.expected,
                            "actual": diff.actual,
                            "severity": diff.severity.value,
                        }
                        for diff in d.diffs
                    ],
                }
                for d in self.drifts
                if d.is_drifted
            ],
            "metadata": {
                "state_file": self.state_file,
                "region": self.region,
                "scanned_at": self.scanned_at.isoformat(),
                "scan_duration_seconds": self.scan_duration_seconds,
            },
        }
