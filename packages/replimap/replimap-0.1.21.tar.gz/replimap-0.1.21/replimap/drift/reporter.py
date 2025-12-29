"""Drift report generation."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from jinja2 import Environment, PackageLoader, select_autoescape

from replimap.drift.models import DriftReport, DriftSeverity, DriftType, ResourceDrift

if TYPE_CHECKING:
    pass


class DriftReporter:
    """Generate drift reports in various formats."""

    def __init__(self) -> None:
        """Initialize the reporter with Jinja2 environment."""
        self.env = Environment(
            loader=PackageLoader("replimap.drift", "templates"),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def to_console(self, report: DriftReport) -> str:
        """Generate console-friendly output."""
        lines = []

        # Header
        lines.append("")
        if report.has_drift:
            lines.append("DRIFT DETECTED")
        else:
            lines.append("NO DRIFT")
        lines.append("=" * 50)

        # Summary
        lines.append(f"Total resources: {report.total_resources}")
        lines.append(f"Drifted: {report.drifted_resources}")
        if report.added_resources:
            lines.append(f"  - Added (not in TF): {report.added_resources}")
        if report.removed_resources:
            lines.append(f"  - Removed (deleted from AWS): {report.removed_resources}")
        if report.modified_resources:
            lines.append(f"  - Modified: {report.modified_resources}")
        lines.append("")

        # Critical/High drifts first
        critical_high = report.critical_drifts + report.high_drifts
        if critical_high:
            lines.append("HIGH PRIORITY DRIFTS:")
            lines.append("-" * 50)
            for drift in critical_high[:10]:  # Limit to 10
                lines.append(self._format_drift(drift))
            if len(critical_high) > 10:
                lines.append(f"  ... and {len(critical_high) - 10} more")
            lines.append("")

        # Other drifts
        other = [
            d
            for d in report.drifts
            if d.severity not in (DriftSeverity.CRITICAL, DriftSeverity.HIGH)
        ]
        if other:
            lines.append("OTHER DRIFTS:")
            lines.append("-" * 50)
            for drift in other[:10]:
                lines.append(self._format_drift(drift))
            if len(other) > 10:
                lines.append(f"  ... and {len(other) - 10} more")

        lines.append("")
        lines.append(f"Scan completed in {report.scan_duration_seconds}s")

        return "\n".join(lines)

    def _format_drift(self, drift: ResourceDrift) -> str:
        """Format a single drift for console output."""
        icon = {
            DriftType.ADDED: "[+]",
            DriftType.REMOVED: "[-]",
            DriftType.MODIFIED: "[~]",
        }.get(drift.drift_type, "[?]")

        severity_label = {
            DriftSeverity.CRITICAL: "[CRITICAL]",
            DriftSeverity.HIGH: "[HIGH]",
            DriftSeverity.MEDIUM: "[MEDIUM]",
            DriftSeverity.LOW: "[LOW]",
        }.get(drift.severity, "[INFO]")

        line = f"{severity_label} {icon} {drift.resource_type}: {drift.resource_id}"

        if drift.tf_address:
            line += f" ({drift.tf_address})"

        # Show diffs for modified resources
        if drift.drift_type == DriftType.MODIFIED and drift.diffs:
            for diff in drift.diffs[:3]:  # Limit to 3
                line += (
                    f"\n      {diff.attribute}: {diff.expected!r} -> {diff.actual!r}"
                )
            if len(drift.diffs) > 3:
                line += f"\n      ... and {len(drift.diffs) - 3} more changes"

        return line

    def to_json(self, report: DriftReport, output_path: Path) -> Path:
        """Export report as JSON."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report.to_dict(), indent=2, default=str))
        return output_path

    def to_html(self, report: DriftReport, output_path: Path) -> Path:
        """Generate HTML report."""
        template = self.env.get_template("drift_report.html.j2")

        html = template.render(
            report=report,
            generated_at=datetime.now(UTC).isoformat(),
            DriftType=DriftType,
            DriftSeverity=DriftSeverity,
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html)
        return output_path
