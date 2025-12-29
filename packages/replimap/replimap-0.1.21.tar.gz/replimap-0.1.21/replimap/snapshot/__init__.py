"""
RepliMap Snapshot Module.

Provides infrastructure snapshot capabilities for change tracking
without requiring Terraform state files.

Usage:
    # Save a snapshot
    replimap snapshot save -r us-east-1 -n "before-migration"

    # Compare to current state
    replimap snapshot diff -r us-east-1 -b "before-migration"

Value Proposition:
- Works for ALL AWS users, not just Terraform users
- Perfect for SOC2 CC7.1 (Change Management) evidence
- Catches "shadow changes" made via Console
"""

from replimap.snapshot.differ import SnapshotDiffer
from replimap.snapshot.models import (
    InfraSnapshot,
    ResourceChange,
    ResourceSnapshot,
    SnapshotDiff,
)
from replimap.snapshot.reporter import SnapshotReporter
from replimap.snapshot.store import SnapshotStore

__all__ = [
    "InfraSnapshot",
    "ResourceChange",
    "ResourceSnapshot",
    "SnapshotDiff",
    "SnapshotDiffer",
    "SnapshotReporter",
    "SnapshotStore",
]
