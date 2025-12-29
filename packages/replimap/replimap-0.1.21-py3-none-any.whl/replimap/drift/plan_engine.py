"""
Plan-based Drift Engine for RepliMap.

Uses terraform plan to detect drift instead of hardcoded COMPARABLE_ATTRIBUTES.
This is the CORRECT approach - Terraform knows ALL attributes and their semantics.

The Seven Laws of Sovereign Code:
4. Schema is Truth - Beautiful code is true code.

Key Insight from Gemini:
"DELETE COMPARABLE_ATTRIBUTES. Use terraform plan to detect actual drift."

Why terraform plan is better:
1. COMPLETE - Knows every attribute, not just hardcoded ones
2. SEMANTIC - Understands computed vs user-specified attributes
3. ACCURATE - Uses same logic as apply, so no false positives
4. MAINTAINED - Hashicorp maintains it, not us

The old approach (COMPARABLE_ATTRIBUTES):
- Hardcoded dict of ~15 resource types
- Manually specified which attributes to compare
- WILL BE INCOMPLETE for new resources
- Severity assignment was arbitrary

The new approach (terraform plan):
- Run terraform plan -json
- Parse the changes array
- Extract before/after values
- Assign severity based on change type
"""

from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from replimap.drift.models import (
    AttributeDiff,
    DriftReport,
    DriftSeverity,
    DriftType,
    ResourceDrift,
)

if TYPE_CHECKING:
    from replimap.core.config import RepliMapConfig

logger = logging.getLogger(__name__)


# Severity classification based on action types
# terraform plan actions: "create", "read", "update", "delete", "no-op"
# Also: "replace" = delete + create (destroy and recreate)
ACTION_SEVERITIES: dict[str, DriftSeverity] = {
    "delete": DriftSeverity.CRITICAL,  # Resource will be destroyed
    "replace": DriftSeverity.CRITICAL,  # Resource will be destroyed and recreated
    "create": DriftSeverity.HIGH,  # New resource will be created
    "update": DriftSeverity.MEDIUM,  # Resource will be modified
    "read": DriftSeverity.INFO,  # Data source refresh
    "no-op": DriftSeverity.INFO,  # No changes
}

# Specific attributes that bump severity
CRITICAL_ATTRIBUTES: set[str] = {
    # Security-related
    "ingress",
    "egress",
    "security_groups",
    "vpc_security_group_ids",
    "assume_role_policy",
    "policy",
    "policy_document",
    "publicly_accessible",
    "acl",
    # Data loss risk
    "storage_encrypted",
    "deletion_protection",
    "skip_final_snapshot",
    "prevent_destroy",
}

HIGH_ATTRIBUTES: set[str] = {
    # Infrastructure changes
    "instance_type",
    "ami",
    "engine_version",
    "instance_class",
    "multi_az",
    "availability_zone",
    "subnet_id",
    "vpc_id",
    "cidr_block",
}


@dataclass
class PlanChange:
    """A single change from terraform plan."""

    resource_address: str  # e.g., "aws_instance.web"
    resource_type: str  # e.g., "aws_instance"
    resource_name: str  # e.g., "web"
    actions: list[str]  # e.g., ["update"] or ["delete", "create"]
    before: dict[str, Any]  # State before change
    after: dict[str, Any]  # State after change
    after_unknown: dict[str, Any] = field(default_factory=dict)  # Computed values

    @property
    def primary_action(self) -> str:
        """Get the primary action for severity calculation."""
        if "delete" in self.actions and "create" in self.actions:
            return "replace"
        if "delete" in self.actions:
            return "delete"
        if "create" in self.actions:
            return "create"
        if "update" in self.actions:
            return "update"
        return "no-op"

    @property
    def is_destructive(self) -> bool:
        """Check if this change is destructive."""
        return "delete" in self.actions


@dataclass
class PlanResult:
    """Result of parsing terraform plan."""

    changes: list[PlanChange] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    plan_output: str = ""
    format_version: str = ""

    @property
    def has_changes(self) -> bool:
        """Check if plan has any changes."""
        return bool(self.changes)

    @property
    def destructive_changes(self) -> list[PlanChange]:
        """Get all destructive changes."""
        return [c for c in self.changes if c.is_destructive]


class PlanParser:
    """
    Parse terraform plan -json output.

    Extracts resource changes and their before/after values.
    """

    def parse(self, plan_json: str) -> PlanResult:
        """
        Parse terraform plan JSON output.

        Args:
            plan_json: JSON string from terraform plan -json

        Returns:
            PlanResult with parsed changes
        """
        result = PlanResult(plan_output=plan_json)

        try:
            data = json.loads(plan_json)
        except json.JSONDecodeError as e:
            result.errors.append(f"Invalid JSON: {e}")
            return result

        result.format_version = data.get("format_version", "")

        # Parse resource changes
        resource_changes = data.get("resource_changes", [])

        for change_data in resource_changes:
            try:
                change = self._parse_change(change_data)
                if change:
                    result.changes.append(change)
            except Exception as e:
                logger.warning(f"Failed to parse change: {e}")
                result.errors.append(str(e))

        return result

    def _parse_change(self, data: dict[str, Any]) -> PlanChange | None:
        """
        Parse a single resource change.

        Args:
            data: Resource change data from plan

        Returns:
            PlanChange or None if no change
        """
        change = data.get("change", {})
        actions = change.get("actions", [])

        # Skip no-op changes
        if actions == ["no-op"]:
            return None

        address = data.get("address", "")
        resource_type = data.get("type", "")
        name = data.get("name", "")

        before = change.get("before") or {}
        after = change.get("after") or {}
        after_unknown = change.get("after_unknown") or {}

        return PlanChange(
            resource_address=address,
            resource_type=resource_type,
            resource_name=name,
            actions=actions,
            before=before,
            after=after,
            after_unknown=after_unknown,
        )


class PlanBasedDriftEngine:
    """
    Drift detection using terraform plan.

    This is the CORRECT approach - let Terraform do the comparison.
    We just parse the results and format them for reporting.

    Benefits:
    1. No hardcoded attribute lists (COMPARABLE_ATTRIBUTES = DELETED)
    2. Accurate - uses same logic as terraform apply
    3. Complete - knows all attributes and computed values
    4. Maintained - Hashicorp keeps it up to date

    Usage:
        engine = PlanBasedDriftEngine(working_dir="./terraform")
        report = engine.detect_drift()

        if report.has_drift:
            for drift in report.critical_drifts:
                print(f"CRITICAL: {drift.resource_id}")
    """

    def __init__(
        self,
        working_dir: str | Path = ".",
        config: RepliMapConfig | None = None,
    ) -> None:
        """
        Initialize the drift engine.

        Args:
            working_dir: Directory containing Terraform configuration
            config: User configuration
        """
        self.working_dir = Path(working_dir)
        self.config = config
        self.parser = PlanParser()

        # Get config options
        if config:
            self.ignore_attributes = set(config.get("drift.ignore_attributes", []))
            self.ignore_resources = set(config.get("drift.ignore_resources", []))
        else:
            self.ignore_attributes = set()
            self.ignore_resources = set()

    def detect_drift(
        self,
        target: str | None = None,
        refresh: bool = True,
    ) -> DriftReport:
        """
        Detect drift using terraform plan.

        Args:
            target: Optional target resource to check
            refresh: Whether to refresh state (default True)

        Returns:
            DriftReport with all detected drift
        """
        start_time = datetime.now(UTC)

        # Run terraform plan
        plan_result = self._run_plan(target=target, refresh=refresh)

        if plan_result.errors:
            logger.error(f"Plan errors: {plan_result.errors}")

        # Convert plan changes to drift report
        report = self._convert_to_report(plan_result)

        # Add metadata
        report.scanned_at = start_time
        report.scan_duration_seconds = (datetime.now(UTC) - start_time).total_seconds()

        return report

    def _run_plan(
        self,
        target: str | None = None,
        refresh: bool = True,
    ) -> PlanResult:
        """
        Run terraform plan and parse output.

        Args:
            target: Optional target resource
            refresh: Whether to refresh state

        Returns:
            PlanResult with parsed changes
        """
        cmd = ["terraform", "plan", "-json", "-detailed-exitcode"]

        if not refresh:
            cmd.append("-refresh=false")

        if target:
            cmd.extend(["-target", target])

        logger.info(f"Running: {' '.join(cmd)}")

        try:
            result = subprocess.run(  # noqa: S603 - terraform called with controlled args
                cmd,
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            # Exit codes:
            # 0 = No changes
            # 1 = Error
            # 2 = Changes pending (this is what we want for drift)

            if result.returncode == 1 and result.stderr:
                # Actual error
                return PlanResult(errors=[result.stderr])

            # Parse the JSON lines output
            # terraform plan -json outputs one JSON object per line
            plan_json = self._extract_plan_json(result.stdout)

            if plan_json:
                return self.parser.parse(plan_json)
            else:
                return PlanResult(errors=["No plan output found"])

        except subprocess.TimeoutExpired:
            return PlanResult(errors=["terraform plan timed out"])
        except FileNotFoundError:
            return PlanResult(errors=["terraform not found in PATH"])
        except Exception as e:
            return PlanResult(errors=[str(e)])

    def _extract_plan_json(self, output: str) -> str | None:
        """
        Extract the plan JSON from terraform output.

        terraform plan -json outputs multiple JSON objects, one per line.
        We need the one with "resource_changes".

        Args:
            output: Raw terraform output

        Returns:
            Plan JSON string or None
        """
        for line in output.strip().split("\n"):
            try:
                data = json.loads(line)
                if "resource_changes" in data:
                    return line
            except json.JSONDecodeError:
                continue

        return None

    def _convert_to_report(self, plan_result: PlanResult) -> DriftReport:
        """
        Convert plan result to drift report.

        Args:
            plan_result: Parsed plan result

        Returns:
            DriftReport
        """
        report = DriftReport()
        report.total_resources = len(plan_result.changes)

        for change in plan_result.changes:
            # Skip ignored resources
            if change.resource_address in self.ignore_resources:
                continue

            drift = self._change_to_drift(change)

            if drift.is_drifted:
                report.drifts.append(drift)

                if drift.drift_type == DriftType.ADDED:
                    report.added_resources += 1
                elif drift.drift_type == DriftType.REMOVED:
                    report.removed_resources += 1
                elif drift.drift_type == DriftType.MODIFIED:
                    report.modified_resources += 1

        report.drifted_resources = (
            report.added_resources
            + report.removed_resources
            + report.modified_resources
        )

        return report

    def _change_to_drift(self, change: PlanChange) -> ResourceDrift:
        """
        Convert a plan change to a drift record.

        Args:
            change: Plan change

        Returns:
            ResourceDrift
        """
        # Determine drift type from actions
        if change.actions == ["create"]:
            drift_type = DriftType.ADDED
        elif change.actions == ["delete"]:
            drift_type = DriftType.REMOVED
        elif "update" in change.actions:
            drift_type = DriftType.MODIFIED
        elif "delete" in change.actions and "create" in change.actions:
            drift_type = DriftType.MODIFIED  # Replace is a modification
        else:
            drift_type = DriftType.UNCHANGED

        # Calculate attribute diffs
        diffs = self._calculate_diffs(change)

        # Determine severity
        severity = self._calculate_severity(change, diffs)

        # Extract resource ID
        resource_id = change.before.get("id") or change.after.get("id") or ""

        return ResourceDrift(
            resource_type=change.resource_type,
            resource_id=resource_id,
            resource_name=change.resource_name,
            tf_address=change.resource_address,
            drift_type=drift_type,
            diffs=diffs,
            severity=severity,
        )

    def _calculate_diffs(self, change: PlanChange) -> list[AttributeDiff]:
        """
        Calculate attribute diffs from before/after.

        Args:
            change: Plan change

        Returns:
            List of AttributeDiff
        """
        diffs: list[AttributeDiff] = []
        all_keys = set(change.before.keys()) | set(change.after.keys())

        for key in all_keys:
            # Skip ignored attributes
            if key in self.ignore_attributes:
                continue

            # Skip common computed attributes
            if key in {"id", "arn", "owner_id", "unique_id"}:
                continue

            before_val = change.before.get(key)
            after_val = change.after.get(key)

            # Skip if values are equal
            if before_val == after_val:
                continue

            # Skip if both are empty-ish
            if before_val in (None, "", [], {}) and after_val in (None, "", [], {}):
                continue

            # Determine attribute severity
            if key in CRITICAL_ATTRIBUTES:
                severity = DriftSeverity.CRITICAL
            elif key in HIGH_ATTRIBUTES:
                severity = DriftSeverity.HIGH
            elif key == "tags":
                severity = DriftSeverity.LOW
            else:
                severity = DriftSeverity.MEDIUM

            diffs.append(
                AttributeDiff(
                    attribute=key,
                    expected=after_val,  # After is what TF wants
                    actual=before_val,  # Before is current state
                    severity=severity,
                )
            )

        return diffs

    def _calculate_severity(
        self,
        change: PlanChange,
        diffs: list[AttributeDiff],
    ) -> DriftSeverity:
        """
        Calculate overall severity for a change.

        Args:
            change: Plan change
            diffs: Attribute diffs

        Returns:
            DriftSeverity
        """
        # Start with action-based severity
        action_severity = ACTION_SEVERITIES.get(
            change.primary_action,
            DriftSeverity.MEDIUM,
        )

        # Check for critical attributes in diffs
        max_diff_severity = DriftSeverity.INFO
        for diff in diffs:
            if self._severity_rank(diff.severity) > self._severity_rank(
                max_diff_severity
            ):
                max_diff_severity = diff.severity

        # Return the higher severity
        if self._severity_rank(max_diff_severity) > self._severity_rank(
            action_severity
        ):
            return max_diff_severity

        return action_severity

    def _severity_rank(self, severity: DriftSeverity) -> int:
        """Get numeric rank for severity comparison."""
        ranks = {
            DriftSeverity.INFO: 0,
            DriftSeverity.LOW: 1,
            DriftSeverity.MEDIUM: 2,
            DriftSeverity.HIGH: 3,
            DriftSeverity.CRITICAL: 4,
        }
        return ranks.get(severity, 0)


class PlanDriftReporter:
    """
    Format drift reports for various outputs (plan-based engine).

    Generates human-readable reports, JSON, and CI-friendly output.
    Different from DriftReporter in reporter.py which uses to_console/to_json/to_html.
    """

    def __init__(self, config: RepliMapConfig | None = None) -> None:
        """Initialize the reporter."""
        self.config = config

    def format_summary(self, report: DriftReport) -> str:
        """
        Generate a summary of the drift report.

        Args:
            report: Drift report

        Returns:
            Human-readable summary
        """
        lines = [
            "═" * 79,
            "DRIFT DETECTION REPORT",
            "═" * 79,
            "",
            f"Total Resources Analyzed: {report.total_resources}",
            f"Drifted Resources: {report.drifted_resources}",
            "",
        ]

        if report.has_drift:
            lines.extend(
                [
                    "BREAKDOWN:",
                    f"  - Added (in AWS, not in TF): {report.added_resources}",
                    f"  - Removed (in TF, not in AWS): {report.removed_resources}",
                    f"  - Modified (different attributes): {report.modified_resources}",
                    "",
                ]
            )

            # Show critical/high drifts
            critical = report.critical_drifts
            high = report.high_drifts

            if critical:
                lines.extend(
                    [
                        "🔴 CRITICAL DRIFT:",
                    ]
                )
                for drift in critical:
                    lines.append(f"  - {drift.tf_address or drift.resource_id}")
                lines.append("")

            if high:
                lines.extend(
                    [
                        "🟠 HIGH SEVERITY DRIFT:",
                    ]
                )
                for drift in high:
                    lines.append(f"  - {drift.tf_address or drift.resource_id}")
                lines.append("")

        else:
            lines.append("✅ No drift detected!")

        lines.extend(
            [
                "",
                f"Scan Duration: {report.scan_duration_seconds:.2f}s",
                f"Scanned At: {report.scanned_at.isoformat()}",
                "═" * 79,
            ]
        )

        return "\n".join(lines)

    def format_details(self, report: DriftReport) -> str:
        """
        Generate detailed drift information.

        Args:
            report: Drift report

        Returns:
            Detailed drift report
        """
        if not report.has_drift:
            return "No drift detected."

        lines = []

        for drift in report.drifts:
            if not drift.is_drifted:
                continue

            lines.extend(
                [
                    "",
                    f"{'─' * 79}",
                    f"Resource: {drift.tf_address or drift.resource_type}",
                    f"Type: {drift.drift_type.value.upper()}",
                    f"Severity: {drift.severity.value.upper()}",
                    f"ID: {drift.resource_id}",
                ]
            )

            if drift.diffs:
                lines.append("")
                lines.append("Attribute Changes:")
                for diff in drift.diffs:
                    lines.append(f"  - {diff.attribute}:")
                    lines.append(f"      Before: {diff.actual!r}")
                    lines.append(f"      After:  {diff.expected!r}")

        return "\n".join(lines)

    def format_json(self, report: DriftReport) -> str:
        """
        Generate JSON output.

        Args:
            report: Drift report

        Returns:
            JSON string
        """
        return json.dumps(report.to_dict(), indent=2, default=str)

    def format_ci(self, report: DriftReport) -> str:
        """
        Generate CI-friendly output (GitHub Actions, etc.).

        Args:
            report: Drift report

        Returns:
            CI annotation format
        """
        lines = []

        if report.critical_drifts:
            for drift in report.critical_drifts:
                lines.append(
                    f"::error title=Critical Drift::{drift.tf_address}: "
                    f"{drift.drift_type.value}"
                )

        if report.high_drifts:
            for drift in report.high_drifts:
                lines.append(
                    f"::warning title=High Severity Drift::{drift.tf_address}: "
                    f"{drift.drift_type.value}"
                )

        # Summary
        if report.has_drift:
            lines.append(
                f"::notice title=Drift Summary::{report.drifted_resources} resources "
                f"drifted ({report.added_resources} added, {report.removed_resources} "
                f"removed, {report.modified_resources} modified)"
            )
        else:
            lines.append("::notice title=No Drift::All resources are in sync")

        return "\n".join(lines)
