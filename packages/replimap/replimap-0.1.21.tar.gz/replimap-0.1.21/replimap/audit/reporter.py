"""
HTML Report Generator for Audit Findings.

Generates professional security reports with findings, code snippets, and fix suggestions.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

from replimap.audit.checkov_runner import CheckovFinding, CheckovResults
from replimap.audit.fix_suggestions import get_fix_suggestion
from replimap.audit.soc2_mapping import get_soc2_mapping, get_soc2_summary

logger = logging.getLogger(__name__)


@dataclass
class EnrichedFinding:
    """A finding enriched with code snippets and fix suggestions."""

    finding: CheckovFinding
    code_snippet: str | None
    fix_suggestion: str | None
    soc2_control: str | None
    soc2_category: str | None
    soc2_description: str | None


@dataclass
class ReportMetadata:
    """Metadata for the audit report."""

    account_id: str
    region: str
    profile: str | None = None
    vpc_id: str | None = None
    generated_at: str | None = None

    def __post_init__(self) -> None:
        if not self.generated_at:
            self.generated_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


class AuditReporter:
    """
    Generates HTML security reports from Checkov results.

    The report includes:
    - Executive summary with score and grade
    - High severity findings highlighted
    - SOC2 control mapping
    - Code snippets with line numbers
    - Fix suggestions for each finding
    """

    def __init__(self) -> None:
        """Initialize the reporter with Jinja2 environment."""
        self.env = Environment(
            loader=PackageLoader("replimap.audit", "templates"),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Add custom filters
        self.env.filters["severity_color"] = self._severity_color_filter
        self.env.filters["severity_badge"] = self._severity_badge_filter

    def generate(
        self,
        results: CheckovResults,
        hcl_dir: Path,
        output: Path,
        metadata: ReportMetadata,
    ) -> Path:
        """
        Generate HTML report.

        Args:
            results: Checkov scan results
            hcl_dir: Directory containing Terraform files
            output: Path for output HTML file
            metadata: Report metadata

        Returns:
            Path to generated report
        """
        logger.info(f"Generating audit report: {output}")

        # Enrich findings with code snippets and fixes
        enriched_findings = self._enrich_findings(results.findings, hcl_dir)

        # Generate SOC2 summary
        failed_check_ids = [f.check_id for f in results.findings]
        soc2_summary = get_soc2_summary(failed_check_ids)

        # Render template
        template = self.env.get_template("audit_report.html.j2")
        html = template.render(
            # Metadata
            generated_at=metadata.generated_at,
            account_id=metadata.account_id,
            region=metadata.region,
            profile=metadata.profile,
            vpc_id=metadata.vpc_id,
            # Results summary
            score=results.score,
            grade=results.grade,
            passed=results.passed,
            failed=results.failed,
            skipped=results.skipped,
            total=results.total,
            # Findings
            high_severity=results.high_severity,
            critical_count=len(results.findings_by_severity["CRITICAL"]),
            high_count=len(results.findings_by_severity["HIGH"]),
            medium_count=len(results.findings_by_severity["MEDIUM"]),
            low_count=len(results.findings_by_severity["LOW"]),
            all_findings=enriched_findings,
            findings_by_severity=results.findings_by_severity,
            # SOC2
            soc2_summary=soc2_summary,
        )

        # Write output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(html)

        logger.info(f"Report generated: {output}")
        return output

    def _enrich_findings(
        self,
        findings: list[CheckovFinding],
        hcl_dir: Path,
    ) -> list[EnrichedFinding]:
        """
        Enrich findings with code snippets and fix suggestions.

        Args:
            findings: List of Checkov findings
            hcl_dir: Directory containing Terraform files

        Returns:
            List of enriched findings
        """
        enriched = []

        for finding in findings:
            # Get code snippet
            code_snippet = self._extract_code_snippet(finding, hcl_dir)

            # Get fix suggestion
            fix_suggestion = get_fix_suggestion(finding.check_id)

            # Get SOC2 mapping
            soc2 = get_soc2_mapping(finding.check_id)
            soc2_control = soc2.control if soc2 else None
            soc2_category = soc2.category if soc2 else None
            soc2_description = soc2.description if soc2 else None

            enriched.append(
                EnrichedFinding(
                    finding=finding,
                    code_snippet=code_snippet,
                    fix_suggestion=fix_suggestion,
                    soc2_control=soc2_control,
                    soc2_category=soc2_category,
                    soc2_description=soc2_description,
                )
            )

        return enriched

    def _extract_code_snippet(
        self,
        finding: CheckovFinding,
        hcl_dir: Path,
    ) -> str | None:
        """
        Extract code snippet from the affected file.

        Args:
            finding: The Checkov finding
            hcl_dir: Base directory for Terraform files

        Returns:
            Code snippet with line numbers, or None if not found
        """
        try:
            # Get file path
            file_path = finding.file_path
            if not file_path:
                return None

            # Handle relative paths
            if not Path(file_path).is_absolute():
                file_path = str(hcl_dir / file_path)

            full_path = Path(file_path)
            if not full_path.exists():
                # Try with hcl_dir as base
                full_path = hcl_dir / Path(finding.file_path).name
                if not full_path.exists():
                    return None

            # Read file
            content = full_path.read_text()
            lines = content.splitlines()

            # Get line range
            start_line, end_line = finding.file_line_range
            if start_line <= 0:
                return None

            # Add context (2 lines before and after)
            context_start = max(0, start_line - 3)
            context_end = min(len(lines), end_line + 2)

            # Extract lines with line numbers
            snippet_lines = []
            for i in range(context_start, context_end):
                line_num = i + 1
                line_content = lines[i] if i < len(lines) else ""

                # Mark affected lines
                if start_line <= line_num <= end_line:
                    prefix = ">"
                else:
                    prefix = " "

                snippet_lines.append(f"{prefix} {line_num:4d} | {line_content}")

            return "\n".join(snippet_lines)

        except Exception as e:
            logger.debug(f"Failed to extract code snippet: {e}")
            return None

    @staticmethod
    def _severity_color_filter(severity: str) -> str:
        """Return Tailwind CSS color class for severity."""
        colors = {
            "CRITICAL": "purple",
            "HIGH": "red",
            "MEDIUM": "yellow",
            "LOW": "blue",
            "UNKNOWN": "gray",
        }
        return colors.get(severity, "gray")

    @staticmethod
    def _severity_badge_filter(severity: str) -> str:
        """Return Tailwind CSS classes for severity badge."""
        badges = {
            "CRITICAL": "bg-purple-100 text-purple-800 border-purple-200",
            "HIGH": "bg-red-100 text-red-800 border-red-200",
            "MEDIUM": "bg-yellow-100 text-yellow-800 border-yellow-200",
            "LOW": "bg-blue-100 text-blue-800 border-blue-200",
            "UNKNOWN": "bg-gray-100 text-gray-800 border-gray-200",
        }
        return badges.get(severity, "bg-gray-100 text-gray-800 border-gray-200")
