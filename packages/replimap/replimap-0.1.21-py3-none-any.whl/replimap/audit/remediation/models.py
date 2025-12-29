"""
Remediation data models.

Core data structures for representing Terraform remediation code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class RemediationType(Enum):
    """Type of remediation resource."""

    S3_ENCRYPTION = "s3_encryption"
    S3_VERSIONING = "s3_versioning"
    S3_LOGGING = "s3_logging"
    S3_PUBLIC_ACCESS = "s3_public_access"
    S3_SSL_POLICY = "s3_ssl_policy"
    EC2_IMDSV2 = "ec2_imdsv2"
    EC2_EBS_ENCRYPTION = "ec2_ebs_encryption"
    EC2_MONITORING = "ec2_monitoring"
    SECURITY_GROUP = "security_group"
    RDS_ENCRYPTION = "rds_encryption"
    RDS_MULTI_AZ = "rds_multi_az"
    RDS_DELETION_PROTECTION = "rds_deletion_protection"
    RDS_MONITORING = "rds_monitoring"
    RDS_IAM_AUTH = "rds_iam_auth"
    KMS_ROTATION = "kms_rotation"
    KMS_POLICY = "kms_policy"
    ALB_HTTPS = "alb_https"
    ALB_TLS_POLICY = "alb_tls_policy"
    ALB_LOGGING = "alb_logging"
    VPC_FLOW_LOGS = "vpc_flow_logs"
    CLOUDTRAIL = "cloudtrail"
    SQS_ENCRYPTION = "sqs_encryption"
    SNS_ENCRYPTION = "sns_encryption"
    ELASTICACHE_ENCRYPTION = "elasticache_encryption"
    LAMBDA_VPC = "lambda_vpc"
    LAMBDA_DLQ = "lambda_dlq"
    LAMBDA_TRACING = "lambda_tracing"
    GUARDDUTY = "guardduty"
    CONFIG = "config"
    OTHER = "other"


class RemediationSeverity(Enum):
    """Severity of the issue being remediated."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class RemediationFile:
    """
    Represents a generated Terraform remediation file.

    Attributes:
        path: Relative path where the file should be written
        content: Terraform HCL content
        description: Human-readable description of the remediation
        check_ids: List of Checkov check IDs this remediates
        remediation_type: Type of remediation (for categorization)
        severity: Severity of the issue being remediated
        resource_ids: AWS resource IDs being remediated
        requires_import: Whether this requires terraform import
        import_commands: Import commands if requires_import is True
    """

    path: Path
    content: str
    description: str
    check_ids: list[str] = field(default_factory=list)
    remediation_type: RemediationType = RemediationType.OTHER
    severity: RemediationSeverity = RemediationSeverity.MEDIUM
    resource_ids: list[str] = field(default_factory=list)
    requires_import: bool = False
    import_commands: list[str] = field(default_factory=list)

    def write(self, base_dir: Path) -> Path:
        """
        Write the remediation file to disk.

        Args:
            base_dir: Base directory to write files to

        Returns:
            Full path to the written file
        """
        full_path = base_dir / self.path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(self.content)
        return full_path


@dataclass
class RemediationPlan:
    """
    Complete remediation plan containing all generated files.

    Attributes:
        files: List of remediation files to generate
        total_findings: Total number of findings analyzed
        remediable_findings: Number of findings with available remediation
        skipped_findings: Number of findings without remediation templates
        warnings: Any warnings about the remediation plan
        import_script: Shell script content for terraform imports
        readme_content: README content explaining the remediation
    """

    files: list[RemediationFile] = field(default_factory=list)
    total_findings: int = 0
    remediable_findings: int = 0
    skipped_findings: int = 0
    warnings: list[str] = field(default_factory=list)
    import_script: str = ""
    readme_content: str = ""

    @property
    def coverage_percent(self) -> float:
        """Percentage of findings with available remediation."""
        if self.total_findings == 0:
            return 100.0
        return round((self.remediable_findings / self.total_findings) * 100, 1)

    @property
    def has_critical(self) -> bool:
        """Check if any remediation is for critical severity."""
        return any(f.severity == RemediationSeverity.CRITICAL for f in self.files)

    @property
    def has_imports(self) -> bool:
        """Check if any remediation requires terraform import."""
        return any(f.requires_import for f in self.files)

    def files_by_type(self) -> dict[RemediationType, list[RemediationFile]]:
        """Group files by remediation type."""
        result: dict[RemediationType, list[RemediationFile]] = {}
        for file in self.files:
            if file.remediation_type not in result:
                result[file.remediation_type] = []
            result[file.remediation_type].append(file)
        return result

    def files_by_severity(self) -> dict[RemediationSeverity, list[RemediationFile]]:
        """Group files by severity."""
        result: dict[RemediationSeverity, list[RemediationFile]] = {
            RemediationSeverity.CRITICAL: [],
            RemediationSeverity.HIGH: [],
            RemediationSeverity.MEDIUM: [],
            RemediationSeverity.LOW: [],
        }
        for file in self.files:
            result[file.severity].append(file)
        return result

    def write_all(self, base_dir: Path) -> list[Path]:
        """
        Write all remediation files to disk.

        Args:
            base_dir: Base directory to write files to

        Returns:
            List of paths to written files
        """
        base_dir.mkdir(parents=True, exist_ok=True)
        paths = []

        # Write remediation files
        for file in self.files:
            paths.append(file.write(base_dir))

        # Write README
        if self.readme_content:
            readme_path = base_dir / "README.md"
            readme_path.write_text(self.readme_content)
            paths.append(readme_path)

        # Write import script if needed
        if self.import_script:
            import_path = base_dir / "import.sh"
            import_path.write_text(self.import_script)
            import_path.chmod(0o755)
            paths.append(import_path)

        return paths

    def summary(self) -> str:
        """Generate a summary of the remediation plan."""
        lines = [
            "Remediation Plan Summary",
            "========================",
            "",
            f"Total findings analyzed: {self.total_findings}",
            f"Remediable findings: {self.remediable_findings} ({self.coverage_percent}%)",
            f"Skipped findings: {self.skipped_findings}",
            "",
            f"Files to generate: {len(self.files)}",
        ]

        by_severity = self.files_by_severity()
        for severity in [
            RemediationSeverity.CRITICAL,
            RemediationSeverity.HIGH,
            RemediationSeverity.MEDIUM,
            RemediationSeverity.LOW,
        ]:
            count = len(by_severity[severity])
            if count > 0:
                lines.append(f"  - {severity.value.upper()}: {count} fixes")

        if self.has_imports:
            lines.append("")
            lines.append("⚠️  Some fixes require terraform import (see import.sh)")

        if self.warnings:
            lines.append("")
            lines.append("Warnings:")
            for warning in self.warnings:
                lines.append(f"  - {warning}")

        return "\n".join(lines)
