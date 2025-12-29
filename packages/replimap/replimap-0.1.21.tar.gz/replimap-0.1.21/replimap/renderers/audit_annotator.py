"""
Audit Annotator for RepliMap.

Inject security findings directly into generated Terraform code as comments.
Code should explain WHY it's dangerous.

The Seven Laws of Sovereign Code:
4. Schema is Truth - Beautiful code is true code.

Level 5 Enhancement: Smart audit annotation with noise control.

NOISE CONTROL:
- CRITICAL/HIGH: Inline annotation above resource
- MEDIUM/LOW: Aggregated in file header or separate report
- If resource has >3 findings: Summarize, don't list all
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from replimap.core.config import RepliMapConfig

logger = logging.getLogger(__name__)


@dataclass
class AuditFinding:
    """A security finding for a resource."""

    resource_id: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    rule_id: str  # e.g., "SG-001"
    title: str  # e.g., "SSH Open to World"
    description: str
    remediation: str  # Suggested fix
    resource_type: str = ""


class AuditAnnotator:
    """
    Annotate generated Terraform code with audit findings.

    NOISE CONTROL STRATEGY:
    1. Only CRITICAL and HIGH get inline annotations
    2. MEDIUM/LOW are aggregated at file header
    3. Resources with >3 findings get a summary
    4. Optional: Write full report to separate file

    Usage:
        annotator = AuditAnnotator(findings)

        # Get annotations for a specific resource
        annotation = annotator.get_inline_annotations(resource_id)

        # Get file header summary
        header = annotator.get_file_header_summary()
    """

    SEVERITY_ICONS: dict[str, str] = {
        "CRITICAL": "🔴",
        "HIGH": "🟠",
        "MEDIUM": "🟡",
        "LOW": "🔵",
        "INFO": "ℹ️",
    }

    SEVERITY_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]

    def __init__(
        self,
        findings: list[AuditFinding],
        config: RepliMapConfig | None = None,
    ) -> None:
        """
        Initialize the audit annotator.

        Args:
            findings: List of audit findings
            config: User configuration for noise control
        """
        self.findings_by_resource: dict[str, list[AuditFinding]] = defaultdict(list)
        self.findings_by_severity: dict[str, list[AuditFinding]] = defaultdict(list)

        for finding in findings:
            self.findings_by_resource[finding.resource_id].append(finding)
            self.findings_by_severity[finding.severity].append(finding)

        # Get configuration
        if config:
            self.inline_severities = set(config.get_inline_severities())
            self.max_inline_findings = config.get_max_inline_findings()
        else:
            self.inline_severities = {"CRITICAL", "HIGH"}
            self.max_inline_findings = 3

    def get_inline_annotations(self, resource_id: str) -> str | None:
        """
        Get INLINE annotations for a resource (CRITICAL/HIGH only).

        Returns HCL comment block for inline placement, or None.

        Args:
            resource_id: AWS resource ID

        Returns:
            HCL comment block or None
        """
        findings = self.findings_by_resource.get(resource_id, [])

        # Filter to only inline severities
        inline_findings = [f for f in findings if f.severity in self.inline_severities]

        if not inline_findings:
            return None

        # Sort by severity
        inline_findings = sorted(
            inline_findings,
            key=lambda f: self.SEVERITY_ORDER.index(f.severity)
            if f.severity in self.SEVERITY_ORDER
            else 999,
        )

        lines: list[str] = []

        # If too many findings, summarize
        if len(inline_findings) > self.max_inline_findings:
            severity_counts: dict[str, int] = defaultdict(int)
            for f in inline_findings:
                severity_counts[f.severity] += 1

            lines.extend(
                [
                    "# ⚠️ SECURITY REVIEW REQUIRED",
                    f"# This resource has {len(inline_findings)} high-priority findings:",
                ]
            )

            for severity in self.SEVERITY_ORDER:
                if severity in severity_counts:
                    icon = self.SEVERITY_ICONS.get(severity, "")
                    lines.append(f"#   - {severity_counts[severity]} {icon} {severity}")

            lines.append("# Run 'replimap audit' for full details")
            lines.append("#")

            # Show only the most critical one
            most_critical = inline_findings[0]
            icon = self.SEVERITY_ICONS.get(most_critical.severity, "⚪")
            lines.extend(
                [
                    f"# {icon} Top Issue: {most_critical.title} [{most_critical.rule_id}]",
                    f"# 💡 {most_critical.remediation}",
                ]
            )
        else:
            # Show all findings
            for finding in inline_findings:
                icon = self.SEVERITY_ICONS.get(finding.severity, "⚪")
                lines.extend(
                    [
                        f"# {icon} {finding.severity}: {finding.title} [{finding.rule_id}]",
                        f"# {finding.description}",
                        f"# 💡 Remediation: {finding.remediation}",
                        "#",
                    ]
                )

        return "\n".join(filter(None, lines))

    def get_file_header_summary(self) -> str | None:
        """
        Get aggregated summary for file header.

        Includes MEDIUM/LOW findings and overall stats.

        Returns:
            HCL comment block for file header
        """
        total = sum(len(f) for f in self.findings_by_resource.values())

        if total == 0:
            return None

        lines = [
            "# ═══════════════════════════════════════════════════════════════════════════════",
            "# SECURITY AUDIT SUMMARY",
            "# ═══════════════════════════════════════════════════════════════════════════════",
            "#",
            f"# Total Findings: {total}",
        ]

        for severity in self.SEVERITY_ORDER:
            count = len(self.findings_by_severity.get(severity, []))
            if count > 0:
                icon = self.SEVERITY_ICONS.get(severity, "")
                lines.append(f"#   {icon} {severity}: {count}")

        lines.extend(
            [
                "#",
                "# CRITICAL/HIGH issues are annotated inline above each resource.",
                "# Run 'replimap audit --full' for complete report.",
                "#",
                "# ═══════════════════════════════════════════════════════════════════════════════",
                "",
            ]
        )

        return "\n".join(lines)

    def generate_full_report(self) -> str:
        """
        Generate a full audit report file.

        This goes to audit-report.md, not inline in TF files.

        Returns:
            Markdown report content
        """
        lines = [
            "# RepliMap Security Audit Report",
            "",
            f"Generated: {datetime.now().isoformat()}",
            "",
            "## Summary",
            "",
            "| Severity | Count |",
            "|----------|-------|",
        ]

        for severity in self.SEVERITY_ORDER:
            count = len(self.findings_by_severity.get(severity, []))
            if count > 0:
                icon = self.SEVERITY_ICONS.get(severity, "")
                lines.append(f"| {icon} {severity} | {count} |")

        lines.extend(
            [
                "",
                "## Findings by Resource",
                "",
            ]
        )

        for resource_id, findings in sorted(self.findings_by_resource.items()):
            lines.append(f"### {resource_id}")
            lines.append("")

            sorted_findings = sorted(
                findings,
                key=lambda f: self.SEVERITY_ORDER.index(f.severity)
                if f.severity in self.SEVERITY_ORDER
                else 999,
            )

            for finding in sorted_findings:
                icon = self.SEVERITY_ICONS.get(finding.severity, "")
                lines.extend(
                    [
                        f"- **{icon} {finding.severity}**: {finding.title} (`{finding.rule_id}`)",
                        f"  - {finding.description}",
                        f"  - 💡 *Remediation*: {finding.remediation}",
                        "",
                    ]
                )

        return "\n".join(lines)

    def generate_report_file(self, output_path: Path) -> None:
        """
        Write the full audit report to file.

        Args:
            output_path: Path to write the report
        """
        content = self.generate_full_report()
        output_path.write_text(content)
        logger.info(f"Wrote audit report: {output_path}")

    def has_findings_for_resource(self, resource_id: str) -> bool:
        """Check if a resource has any findings."""
        return resource_id in self.findings_by_resource

    def get_finding_count(self, resource_id: str) -> int:
        """Get the number of findings for a resource."""
        return len(self.findings_by_resource.get(resource_id, []))

    @property
    def total_findings(self) -> int:
        """Total number of findings."""
        return sum(len(f) for f in self.findings_by_resource.values())

    @property
    def critical_count(self) -> int:
        """Number of critical findings."""
        return len(self.findings_by_severity.get("CRITICAL", []))

    @property
    def high_count(self) -> int:
        """Number of high findings."""
        return len(self.findings_by_severity.get("HIGH", []))


class SecurityCheckRunner:
    """
    Run basic security checks on resources.

    This provides built-in security checks that don't require
    external tools like Checkov.
    """

    def __init__(self) -> None:
        """Initialize the security check runner."""
        self.checks: list[tuple[str, callable]] = [
            ("SG-001", self._check_sg_open_to_world),
            ("SG-002", self._check_sg_unrestricted_egress),
            ("RDS-001", self._check_rds_public),
            ("RDS-002", self._check_rds_unencrypted),
            ("S3-001", self._check_s3_public),
            ("EC2-001", self._check_ec2_public_ip),
        ]

    def run_checks(
        self,
        resources: list[Any],
    ) -> list[AuditFinding]:
        """
        Run all security checks on resources.

        Args:
            resources: List of ResourceNode objects

        Returns:
            List of AuditFinding objects
        """
        findings: list[AuditFinding] = []

        for resource in resources:
            for rule_id, check_fn in self.checks:
                finding = check_fn(resource)
                if finding:
                    finding.rule_id = rule_id
                    findings.append(finding)

        logger.info(f"Security checks found {len(findings)} issues")
        return findings

    def _check_sg_open_to_world(self, resource: Any) -> AuditFinding | None:
        """Check for security groups open to 0.0.0.0/0."""
        if str(resource.resource_type) != "aws_security_group":
            return None

        ingress_rules = resource.config.get("ingress", [])

        for rule in ingress_rules:
            cidr_blocks = rule.get("cidr_blocks", [])
            ipv6_cidr_blocks = rule.get("ipv6_cidr_blocks", [])
            from_port = rule.get("from_port", 0)

            if "0.0.0.0/0" in cidr_blocks or "::/0" in ipv6_cidr_blocks:
                # Critical for SSH/RDP
                if from_port in [22, 3389]:
                    port_name = "SSH" if from_port == 22 else "RDP"
                    return AuditFinding(
                        resource_id=resource.id,
                        severity="CRITICAL",
                        rule_id="",
                        title=f"{port_name} Open to World",
                        description=f"Port {from_port} is accessible from 0.0.0.0/0",
                        remediation=f"Restrict {port_name} access to specific IP ranges or VPN",
                        resource_type=str(resource.resource_type),
                    )
                else:
                    return AuditFinding(
                        resource_id=resource.id,
                        severity="HIGH",
                        rule_id="",
                        title="Security Group Open to World",
                        description=f"Port {from_port} is accessible from 0.0.0.0/0",
                        remediation="Restrict ingress to specific IP ranges",
                        resource_type=str(resource.resource_type),
                    )

        return None

    def _check_sg_unrestricted_egress(self, resource: Any) -> AuditFinding | None:
        """Check for unrestricted egress rules."""
        if str(resource.resource_type) != "aws_security_group":
            return None

        egress_rules = resource.config.get("egress", [])

        for rule in egress_rules:
            cidr_blocks = rule.get("cidr_blocks", [])
            from_port = rule.get("from_port", 0)
            to_port = rule.get("to_port", 0)

            # All ports open to world
            if "0.0.0.0/0" in cidr_blocks and from_port == 0 and to_port == 0:
                return AuditFinding(
                    resource_id=resource.id,
                    severity="MEDIUM",
                    rule_id="",
                    title="Unrestricted Egress",
                    description="Security Group allows all outbound traffic to 0.0.0.0/0",
                    remediation="Limit egress to required destinations and ports only",
                    resource_type=str(resource.resource_type),
                )

        return None

    def _check_rds_public(self, resource: Any) -> AuditFinding | None:
        """Check for publicly accessible RDS instances."""
        if str(resource.resource_type) != "aws_db_instance":
            return None

        if resource.config.get("publicly_accessible") is True:
            return AuditFinding(
                resource_id=resource.id,
                severity="CRITICAL",
                rule_id="",
                title="RDS Publicly Accessible",
                description="Database instance is publicly accessible",
                remediation="Set publicly_accessible = false",
                resource_type=str(resource.resource_type),
            )

        return None

    def _check_rds_unencrypted(self, resource: Any) -> AuditFinding | None:
        """Check for unencrypted RDS instances."""
        if str(resource.resource_type) != "aws_db_instance":
            return None

        if resource.config.get("storage_encrypted") is False:
            return AuditFinding(
                resource_id=resource.id,
                severity="HIGH",
                rule_id="",
                title="RDS Storage Not Encrypted",
                description="Database storage is not encrypted",
                remediation="Enable storage_encrypted = true",
                resource_type=str(resource.resource_type),
            )

        return None

    def _check_s3_public(self, resource: Any) -> AuditFinding | None:
        """Check for public S3 buckets."""
        if str(resource.resource_type) != "aws_s3_bucket":
            return None

        acl = resource.config.get("acl")
        if acl in ["public-read", "public-read-write"]:
            return AuditFinding(
                resource_id=resource.id,
                severity="CRITICAL" if acl == "public-read-write" else "HIGH",
                rule_id="",
                title="S3 Bucket Publicly Accessible",
                description=f"Bucket has public ACL: {acl}",
                remediation="Set acl = private and use bucket policies for access control",
                resource_type=str(resource.resource_type),
            )

        return None

    def _check_ec2_public_ip(self, resource: Any) -> AuditFinding | None:
        """Check for EC2 instances with public IPs."""
        if str(resource.resource_type) != "aws_instance":
            return None

        if resource.config.get("associate_public_ip_address") is True:
            return AuditFinding(
                resource_id=resource.id,
                severity="MEDIUM",
                rule_id="",
                title="EC2 Has Public IP",
                description="Instance has a public IP address",
                remediation="Use NAT Gateway for outbound access if public IP not required",
                resource_type=str(resource.resource_type),
            )

        return None
