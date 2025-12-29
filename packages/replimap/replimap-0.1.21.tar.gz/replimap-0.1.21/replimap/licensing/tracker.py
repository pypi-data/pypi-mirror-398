"""
Usage Tracking for RepliMap.

Tracks feature usage, scan counts, and resource metrics for
license compliance and analytics.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def ensure_utc(dt: datetime) -> datetime:
    """
    Ensure a datetime is timezone-aware (UTC).

    Handles both naive and aware datetimes for compatibility
    with older saved data.

    Args:
        dt: A datetime object (naive or aware)

    Returns:
        A timezone-aware datetime in UTC
    """
    if dt.tzinfo is None:
        # Naive datetime - assume it was UTC
        return dt.replace(tzinfo=UTC)
    return dt


@dataclass
class ScanRecord:
    """Record of a single scan operation."""

    scan_id: str
    timestamp: datetime
    region: str
    resource_count: int
    resource_types: dict[str, int]
    duration_seconds: float
    profile: str | None = None
    success: bool = True
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "scan_id": self.scan_id,
            "timestamp": self.timestamp.isoformat(),
            "region": self.region,
            "resource_count": self.resource_count,
            "resource_types": self.resource_types,
            "duration_seconds": self.duration_seconds,
            "profile": self.profile,
            "success": self.success,
            "error_message": self.error_message,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ScanRecord:
        """Create from dictionary."""
        # Ensure timestamp is timezone-aware for comparison compatibility
        timestamp = ensure_utc(datetime.fromisoformat(data["timestamp"]))
        return cls(
            scan_id=data["scan_id"],
            timestamp=timestamp,
            region=data["region"],
            resource_count=data["resource_count"],
            resource_types=data["resource_types"],
            duration_seconds=data["duration_seconds"],
            profile=data.get("profile"),
            success=data.get("success", True),
            error_message=data.get("error_message"),
        )


@dataclass
class UsageStats:
    """Aggregated usage statistics."""

    total_scans: int = 0
    total_resources_scanned: int = 0
    scans_this_month: int = 0
    resources_this_month: int = 0
    unique_regions: set[str] = field(default_factory=set)
    unique_accounts: set[str] = field(default_factory=set)
    resource_type_counts: dict[str, int] = field(default_factory=dict)
    last_scan: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_scans": self.total_scans,
            "total_resources_scanned": self.total_resources_scanned,
            "scans_this_month": self.scans_this_month,
            "resources_this_month": self.resources_this_month,
            "unique_regions": list(self.unique_regions),
            "unique_accounts": list(self.unique_accounts),
            "resource_type_counts": self.resource_type_counts,
            "last_scan": self.last_scan.isoformat() if self.last_scan else None,
        }


class UsageTracker:
    """
    Tracks usage metrics for license compliance and analytics.

    Persists usage data locally and can sync with the cloud for
    quota enforcement and analytics.
    """

    def __init__(self, data_dir: Path | None = None) -> None:
        """
        Initialize the usage tracker.

        Args:
            data_dir: Directory for usage data storage
        """
        self.data_dir = data_dir or Path.home() / ".replimap"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._scans: list[ScanRecord] = []
        self._load_history()

    @property
    def usage_file(self) -> Path:
        """Path to the usage history file."""
        return self.data_dir / "usage_history.json"

    def record_scan(
        self,
        scan_id: str,
        region: str,
        resource_count: int,
        resource_types: dict[str, int],
        duration_seconds: float,
        profile: str | None = None,
        success: bool = True,
        error_message: str | None = None,
    ) -> ScanRecord:
        """
        Record a scan operation.

        Args:
            scan_id: Unique identifier for the scan
            region: AWS region scanned
            resource_count: Total resources found
            resource_types: Count by resource type
            duration_seconds: Scan duration
            profile: AWS profile used
            success: Whether scan completed successfully
            error_message: Error message if failed

        Returns:
            The created ScanRecord
        """
        record = ScanRecord(
            scan_id=scan_id,
            timestamp=datetime.now(UTC),
            region=region,
            resource_count=resource_count,
            resource_types=resource_types,
            duration_seconds=duration_seconds,
            profile=profile,
            success=success,
            error_message=error_message,
        )

        self._scans.append(record)
        self._save_history()

        logger.debug(f"Recorded scan: {scan_id} ({resource_count} resources)")
        return record

    def get_stats(self) -> UsageStats:
        """
        Get aggregated usage statistics.

        Returns:
            UsageStats with aggregated metrics
        """
        stats = UsageStats()

        current_month = datetime.now(UTC).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )

        for scan in self._scans:
            stats.total_scans += 1
            stats.total_resources_scanned += scan.resource_count
            stats.unique_regions.add(scan.region)

            if scan.profile:
                stats.unique_accounts.add(scan.profile)

            # Update resource type counts
            for rtype, count in scan.resource_types.items():
                stats.resource_type_counts[rtype] = (
                    stats.resource_type_counts.get(rtype, 0) + count
                )

            # Check if this month
            if scan.timestamp >= current_month:
                stats.scans_this_month += 1
                stats.resources_this_month += scan.resource_count

            # Track last scan
            if stats.last_scan is None or scan.timestamp > stats.last_scan:
                stats.last_scan = scan.timestamp

        return stats

    def get_scans_this_month(self) -> int:
        """Get the number of scans performed this month."""
        current_month = datetime.now(UTC).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        return sum(1 for s in self._scans if s.timestamp >= current_month)

    def get_resources_this_month(self) -> int:
        """Get the total resources scanned this month."""
        current_month = datetime.now(UTC).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        return sum(
            s.resource_count for s in self._scans if s.timestamp >= current_month
        )

    def get_recent_scans(self, limit: int = 10) -> list[ScanRecord]:
        """
        Get the most recent scans.

        Args:
            limit: Maximum number of scans to return

        Returns:
            List of recent ScanRecords
        """
        return sorted(
            self._scans,
            key=lambda s: s.timestamp,
            reverse=True,
        )[:limit]

    def check_scan_quota(self, max_scans: int | None) -> bool:
        """
        Check if the scan quota allows another scan.

        Args:
            max_scans: Maximum scans per month (None = unlimited)

        Returns:
            True if another scan is allowed
        """
        if max_scans is None:
            return True
        return self.get_scans_this_month() < max_scans

    def clear_history(self) -> None:
        """Clear all usage history."""
        self._scans = []
        if self.usage_file.exists():
            self.usage_file.unlink()
        logger.info("Usage history cleared")

    def _load_history(self) -> None:
        """Load usage history from disk."""
        if not self.usage_file.exists():
            return

        try:
            data = json.loads(self.usage_file.read_text())
            self._scans = [ScanRecord.from_dict(s) for s in data.get("scans", [])]
            logger.debug(f"Loaded {len(self._scans)} scan records")
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Failed to load usage history: {e}")
            self._scans = []

    def _save_history(self) -> None:
        """Save usage history to disk."""
        # Keep only last 1000 scans to limit file size
        scans_to_save = sorted(
            self._scans,
            key=lambda s: s.timestamp,
            reverse=True,
        )[:1000]

        data = {
            "version": 1,
            "scans": [s.to_dict() for s in scans_to_save],
        }

        self.usage_file.write_text(json.dumps(data, indent=2))

    def export_for_sync(self) -> dict[str, Any]:
        """
        Export usage data for cloud sync.

        Returns:
            Dictionary suitable for API upload
        """
        stats = self.get_stats()
        return {
            "stats": stats.to_dict(),
            "recent_scans": [s.to_dict() for s in self.get_recent_scans(50)],
            "exported_at": datetime.now(UTC).isoformat(),
        }


# Global tracker instance
_tracker: UsageTracker | None = None


def get_usage_tracker() -> UsageTracker:
    """Get the global usage tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = UsageTracker()
    return _tracker


def set_usage_tracker(tracker: UsageTracker) -> None:
    """Set the global usage tracker instance (useful for testing)."""
    global _tracker
    _tracker = tracker
