"""
Snapshot comparison engine.

Compares two infrastructure snapshots to identify changes.
"""

from __future__ import annotations

import logging
from typing import Any

from replimap.snapshot.models import (
    InfraSnapshot,
    ResourceChange,
    SnapshotDiff,
)

logger = logging.getLogger(__name__)


# Attributes that indicate high severity changes when modified
HIGH_SEVERITY_ATTRIBUTES: dict[str, list[str]] = {
    "aws_security_group": ["ingress", "egress", "cidr_blocks", "security_groups"],
    "aws_iam_role": ["assume_role_policy", "inline_policy", "managed_policy_arns"],
    "aws_iam_policy": ["policy", "policy_document"],
    "aws_s3_bucket": ["acl", "policy", "public_access_block", "website"],
    "aws_s3_bucket_policy": ["policy"],
    "aws_db_instance": [
        "publicly_accessible",
        "storage_encrypted",
        "iam_database_authentication_enabled",
    ],
    "aws_instance": [
        "security_groups",
        "vpc_security_group_ids",
        "iam_instance_profile",
    ],
    "aws_lb": ["internal", "security_groups"],
    "aws_vpc": ["enable_dns_support", "enable_dns_hostnames"],
    "aws_kms_key": ["policy", "key_rotation_enabled"],
    "aws_elasticache_cluster": [
        "transit_encryption_enabled",
        "at_rest_encryption_enabled",
    ],
}

# Resource types that are critical (changes are always high/critical severity)
CRITICAL_RESOURCE_TYPES: set[str] = {
    "aws_vpc",
    "aws_db_instance",
    "aws_rds_cluster",
    "aws_iam_role",
    "aws_iam_policy",
    "aws_iam_user",
    "aws_kms_key",
}

# Attributes to ignore in comparisons (frequently changing, not meaningful)
DEFAULT_IGNORE_ATTRIBUTES: list[str] = [
    "last_modified",
    "modification_date",
    "create_date",
    "launch_time",
    "created_at",
    "state_transition_reason",
    "status_message",
    "instance_state",
    "availability",
    "latestVersion",
    "ebs_optimized",  # Can change without user action
]


class SnapshotDiffer:
    """
    Compares two infrastructure snapshots to find changes.

    Usage:
        differ = SnapshotDiffer()
        diff = differ.diff(baseline, current)

        print(f"Changes: {diff.total_changes}")
        for change in diff.critical_changes:
            print(f"CRITICAL: {change.resource_id}")
    """

    def __init__(
        self,
        ignore_attributes: list[str] | None = None,
    ) -> None:
        """
        Initialize the differ.

        Args:
            ignore_attributes: Attributes to ignore in comparisons
                (uses DEFAULT_IGNORE_ATTRIBUTES if not provided)
        """
        self.ignore_attributes = set(ignore_attributes or DEFAULT_IGNORE_ATTRIBUTES)

    def diff(
        self,
        baseline: InfraSnapshot,
        current: InfraSnapshot,
    ) -> SnapshotDiff:
        """
        Compare two snapshots.

        Args:
            baseline: The reference snapshot (older)
            current: The current state (newer)

        Returns:
            SnapshotDiff with all changes
        """
        changes: list[ResourceChange] = []
        by_type: dict[str, dict[str, int]] = {}

        # Index resources by ID for quick lookup
        baseline_by_id = {r.id: r for r in baseline.resources}
        current_by_id = {r.id: r for r in current.resources}

        baseline_ids = set(baseline_by_id.keys())
        current_ids = set(current_by_id.keys())

        # Find added resources
        added_ids = current_ids - baseline_ids
        for rid in added_ids:
            resource = current_by_id[rid]
            change = ResourceChange(
                resource_id=rid,
                resource_type=resource.type,
                resource_name=resource.name,
                change_type="added",
                after=resource.config,
                severity=self._assess_severity(resource.type, "added", []),
            )
            changes.append(change)
            self._update_by_type(by_type, resource.type, "added")

        # Find removed resources
        removed_ids = baseline_ids - current_ids
        for rid in removed_ids:
            resource = baseline_by_id[rid]
            change = ResourceChange(
                resource_id=rid,
                resource_type=resource.type,
                resource_name=resource.name,
                change_type="removed",
                before=resource.config,
                severity=self._assess_severity(resource.type, "removed", []),
            )
            changes.append(change)
            self._update_by_type(by_type, resource.type, "removed")

        # Find modified resources
        common_ids = baseline_ids & current_ids
        for rid in common_ids:
            baseline_resource = baseline_by_id[rid]
            current_resource = current_by_id[rid]

            # Quick hash comparison first
            if baseline_resource.config_hash == current_resource.config_hash:
                self._update_by_type(by_type, baseline_resource.type, "unchanged")
                continue

            # Deep diff for modified resources
            changed_attrs = self._find_changed_attributes(
                baseline_resource.config,
                current_resource.config,
            )

            if not changed_attrs:
                self._update_by_type(by_type, baseline_resource.type, "unchanged")
                continue

            change = ResourceChange(
                resource_id=rid,
                resource_type=baseline_resource.type,
                resource_name=baseline_resource.name or current_resource.name,
                change_type="modified",
                changed_attributes=changed_attrs,
                before=self._extract_changed_values(
                    baseline_resource.config, changed_attrs
                ),
                after=self._extract_changed_values(
                    current_resource.config, changed_attrs
                ),
                severity=self._assess_severity(
                    baseline_resource.type, "modified", changed_attrs
                ),
            )
            changes.append(change)
            self._update_by_type(by_type, baseline_resource.type, "modified")

        # Calculate totals
        total_added = len([c for c in changes if c.change_type == "added"])
        total_removed = len([c for c in changes if c.change_type == "removed"])
        total_modified = len([c for c in changes if c.change_type == "modified"])
        total_unchanged = len(common_ids) - total_modified

        # Identify critical changes
        critical_changes = [c for c in changes if c.severity in ("critical", "high")]

        return SnapshotDiff(
            baseline_name=baseline.name,
            baseline_date=baseline.created_at,
            current_name=current.name,
            current_date=current.created_at,
            total_added=total_added,
            total_removed=total_removed,
            total_modified=total_modified,
            total_unchanged=total_unchanged,
            changes=changes,
            by_type=by_type,
            critical_changes=critical_changes,
        )

    def _find_changed_attributes(
        self,
        before: dict[str, Any],
        after: dict[str, Any],
        prefix: str = "",
    ) -> list[str]:
        """
        Recursively find all changed attributes.

        Returns list of attribute paths that changed.
        """
        changed = []

        # Get all keys from both
        all_keys = set(before.keys()) | set(after.keys())

        for key in all_keys:
            # Skip ignored attributes
            if key in self.ignore_attributes:
                continue

            attr_path = f"{prefix}.{key}" if prefix else key
            before_val = before.get(key)
            after_val = after.get(key)

            # Both None or equal
            if before_val == after_val:
                continue

            # One is None
            if before_val is None or after_val is None:
                changed.append(attr_path)
                continue

            # Both are dicts - recurse
            if isinstance(before_val, dict) and isinstance(after_val, dict):
                nested_changes = self._find_changed_attributes(
                    before_val, after_val, attr_path
                )
                changed.extend(nested_changes)
                continue

            # Both are lists - compare
            if isinstance(before_val, list) and isinstance(after_val, list):
                if self._lists_differ(before_val, after_val):
                    changed.append(attr_path)
                continue

            # Different values
            if before_val != after_val:
                changed.append(attr_path)

        return changed

    def _lists_differ(self, list1: list, list2: list) -> bool:
        """Compare two lists for meaningful differences."""
        if len(list1) != len(list2):
            return True

        # For lists of dicts, compare sorted
        if list1 and isinstance(list1[0], dict):
            try:
                import json

                sorted1 = sorted(
                    list1, key=lambda x: json.dumps(x, sort_keys=True, default=str)
                )
                sorted2 = sorted(
                    list2, key=lambda x: json.dumps(x, sort_keys=True, default=str)
                )
                return sorted1 != sorted2
            except Exception:
                # Fall through to simple string comparison
                logger.debug("JSON sorting failed, using string comparison")

        # For simple lists
        return sorted(str(x) for x in list1) != sorted(str(x) for x in list2)

    def _extract_changed_values(
        self,
        config: dict[str, Any],
        attrs: list[str],
    ) -> dict[str, Any]:
        """Extract only the changed attribute values."""
        result = {}

        for attr in attrs:
            # Handle nested paths like "foo.bar.baz"
            parts = attr.split(".")
            value = config

            try:
                for part in parts:
                    if isinstance(value, dict):
                        value = value.get(part)
                    else:
                        value = None
                        break

                # Use the full path as key
                result[attr] = value
            except Exception:
                result[attr] = None

        return result

    def _assess_severity(
        self,
        resource_type: str,
        change_type: str,
        changed_attrs: list[str],
    ) -> str:
        """
        Assess the severity of a change.

        Returns: 'low', 'medium', 'high', or 'critical'
        """
        # Removed critical resources are always critical
        if change_type == "removed" and resource_type in CRITICAL_RESOURCE_TYPES:
            return "critical"

        # Added critical resources are high
        if change_type == "added":
            if resource_type in CRITICAL_RESOURCE_TYPES:
                return "high"
            return "medium"

        # For modifications, check if any high-severity attributes changed
        if resource_type in HIGH_SEVERITY_ATTRIBUTES:
            high_sev_attrs = HIGH_SEVERITY_ATTRIBUTES[resource_type]
            for attr in changed_attrs:
                attr_lower = attr.lower()
                for high_attr in high_sev_attrs:
                    if high_attr in attr_lower:
                        return "high"

        # Security-related attributes are always high
        security_keywords = [
            "security",
            "policy",
            "iam",
            "ingress",
            "egress",
            "public",
            "encrypted",
            "password",
            "secret",
            "kms",
        ]
        for attr in changed_attrs:
            attr_lower = attr.lower()
            if any(kw in attr_lower for kw in security_keywords):
                return "high"

        return "low"

    def _update_by_type(
        self,
        by_type: dict[str, dict[str, int]],
        resource_type: str,
        change_type: str,
    ) -> None:
        """Update the by_type counter."""
        if resource_type not in by_type:
            by_type[resource_type] = {
                "added": 0,
                "removed": 0,
                "modified": 0,
                "unchanged": 0,
            }
        by_type[resource_type][change_type] += 1
