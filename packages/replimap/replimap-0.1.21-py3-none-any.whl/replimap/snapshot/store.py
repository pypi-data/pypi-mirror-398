"""
Snapshot storage management.

Handles saving, loading, listing, and deleting infrastructure snapshots.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from replimap.snapshot.models import InfraSnapshot

logger = logging.getLogger(__name__)


class SnapshotStore:
    """
    Manages snapshot storage.

    Default location: ~/.replimap/snapshots/

    The store maintains an index file for quick lookups and supports
    multiple snapshots with the same name (keeping track of the latest).

    Usage:
        store = SnapshotStore()
        store.save(snapshot)
        snapshot = store.load("my-snapshot")
        snapshots = store.list()
    """

    DEFAULT_DIR = Path.home() / ".replimap" / "snapshots"

    def __init__(self, base_dir: Path | None = None) -> None:
        """
        Initialize the snapshot store.

        Args:
            base_dir: Custom base directory (default: ~/.replimap/snapshots/)
        """
        self.base_dir = base_dir or self.DEFAULT_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._index_file = self.base_dir / "index.json"

    def save(self, snapshot: InfraSnapshot) -> Path:
        """
        Save a snapshot.

        Generates a unique filename based on name and timestamp,
        and updates the index for quick lookups.

        Args:
            snapshot: The InfraSnapshot to save

        Returns:
            Path to the saved snapshot file
        """
        # Generate safe filename
        safe_name = self._sanitize_name(snapshot.name)
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_name}_{timestamp}.json"

        filepath = self.base_dir / filename
        snapshot.save(filepath)

        # Update index
        self._update_index(snapshot.name, filepath, snapshot)

        logger.info(f"Saved snapshot: {filepath}")
        return filepath

    def load(self, name: str) -> InfraSnapshot | None:
        """
        Load a snapshot by name or path.

        If multiple snapshots have the same name, returns the most recent.
        Also accepts a direct file path.

        Args:
            name: Snapshot name or file path

        Returns:
            InfraSnapshot if found, None otherwise
        """
        # First check if it's a direct path
        path = Path(name)
        if path.exists() and path.is_file():
            try:
                return InfraSnapshot.load(path)
            except Exception as e:
                logger.error(f"Failed to load snapshot from path: {e}")
                return None

        # Check the index
        index = self._load_index()

        if name not in index:
            # Try to find by partial match
            for indexed_name in index:
                if name.lower() in indexed_name.lower():
                    name = indexed_name
                    break
            else:
                return None

        filepath = Path(index[name]["latest_path"])
        if not filepath.exists():
            logger.warning(f"Snapshot file not found: {filepath}")
            return None

        try:
            return InfraSnapshot.load(filepath)
        except Exception as e:
            logger.error(f"Failed to load snapshot: {e}")
            return None

    def list(self, region: str | None = None) -> list[dict]:
        """
        List all saved snapshots.

        Args:
            region: Optional filter by region

        Returns:
            List of snapshot metadata dictionaries
        """
        index = self._load_index()
        snapshots = []

        for name, meta in index.items():
            if region and meta.get("region") != region:
                continue

            snapshots.append(
                {
                    "name": name,
                    "created_at": meta.get("created_at"),
                    "region": meta.get("region"),
                    "resource_count": meta.get("resource_count", 0),
                    "path": meta.get("latest_path"),
                    "vpc_id": meta.get("vpc_id"),
                }
            )

        # Sort by date descending (newest first)
        snapshots.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        return snapshots

    def delete(self, name: str) -> bool:
        """
        Delete a snapshot.

        Args:
            name: Snapshot name to delete

        Returns:
            True if deleted, False if not found
        """
        index = self._load_index()

        if name not in index:
            return False

        filepath = Path(index[name]["latest_path"])
        if filepath.exists():
            try:
                filepath.unlink()
                logger.info(f"Deleted snapshot file: {filepath}")
            except Exception as e:
                logger.error(f"Failed to delete snapshot file: {e}")

        del index[name]
        self._save_index(index)

        return True

    def exists(self, name: str) -> bool:
        """Check if a snapshot exists."""
        index = self._load_index()
        return name in index

    def get_metadata(self, name: str) -> dict | None:
        """Get metadata for a snapshot without loading it."""
        index = self._load_index()
        return index.get(name)

    def _sanitize_name(self, name: str) -> str:
        """Sanitize a snapshot name for use as filename."""
        # Replace spaces and special characters
        safe = ""
        for char in name:
            if char.isalnum() or char in "-_":
                safe += char
            elif char == " ":
                safe += "_"
        return safe or "snapshot"

    def _load_index(self) -> dict:
        """Load the snapshot index."""
        if not self._index_file.exists():
            return {}
        try:
            return json.loads(self._index_file.read_text())
        except Exception as e:
            logger.warning(f"Failed to load snapshot index: {e}")
            return {}

    def _save_index(self, index: dict) -> None:
        """Save the snapshot index."""
        try:
            self._index_file.write_text(json.dumps(index, indent=2))
        except Exception as e:
            logger.error(f"Failed to save snapshot index: {e}")

    def _update_index(
        self,
        name: str,
        filepath: Path,
        snapshot: InfraSnapshot,
    ) -> None:
        """Update index with new snapshot."""
        index = self._load_index()

        index[name] = {
            "latest_path": str(filepath),
            "created_at": snapshot.created_at,
            "region": snapshot.region,
            "resource_count": snapshot.resource_count,
            "vpc_id": snapshot.vpc_id,
            "profile": snapshot.profile,
        }

        self._save_index(index)

    def cleanup_old(self, max_age_days: int = 90) -> int:
        """
        Remove snapshots older than max_age_days.

        Args:
            max_age_days: Maximum age in days

        Returns:
            Number of snapshots deleted
        """
        index = self._load_index()
        cutoff = datetime.now(UTC).timestamp() - (max_age_days * 86400)
        deleted = 0

        to_delete = []
        for name, meta in index.items():
            try:
                created = datetime.fromisoformat(
                    meta.get("created_at", "").replace("Z", "+00:00")
                )
                if created.timestamp() < cutoff:
                    to_delete.append(name)
            except Exception:
                # Skip snapshots with invalid metadata
                logger.debug(f"Skipping snapshot with invalid metadata: {name}")

        for name in to_delete:
            if self.delete(name):
                deleted += 1

        return deleted
