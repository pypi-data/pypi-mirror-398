"""
Remediation Generator - Core logic for generating Terraform fix code.

Transforms Checkov findings into actionable Terraform remediation code.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from replimap.audit.remediation.models import (
    RemediationFile,
    RemediationPlan,
    RemediationSeverity,
    RemediationType,
)
from replimap.audit.remediation.templates import (
    generate_ebs_encryption,
    generate_ec2_detailed_monitoring,
    generate_ec2_imdsv2,
    generate_kms_policy,
    generate_kms_rotation,
    generate_rds_deletion_protection,
    generate_rds_encryption,
    generate_rds_iam_auth,
    generate_rds_monitoring,
    generate_rds_multi_az,
    generate_s3_encryption,
    generate_s3_logging,
    generate_s3_public_access_block,
    generate_s3_ssl_policy,
    generate_s3_versioning,
    generate_security_group_restrict,
)

if TYPE_CHECKING:
    from replimap.audit.checkov_runner import CheckovFinding

logger = logging.getLogger(__name__)


# Mapping of check IDs to severity levels
SEVERITY_MAP: dict[str, RemediationSeverity] = {
    # Critical
    "CKV_AWS_20": RemediationSeverity.CRITICAL,  # S3 public access
    "CKV_AWS_24": RemediationSeverity.CRITICAL,  # SSH open to internet
    "CKV_AWS_25": RemediationSeverity.CRITICAL,  # RDP open to internet
    "CKV_AWS_53": RemediationSeverity.CRITICAL,  # S3 public ACL
    "CKV_AWS_54": RemediationSeverity.CRITICAL,  # S3 public
    "CKV_AWS_55": RemediationSeverity.CRITICAL,  # S3 public policy
    "CKV_AWS_56": RemediationSeverity.CRITICAL,  # S3 public bucket
    "CKV_AWS_57": RemediationSeverity.CRITICAL,  # S3 public
    # High
    "CKV_AWS_19": RemediationSeverity.HIGH,  # S3 encryption
    "CKV_AWS_3": RemediationSeverity.HIGH,  # EBS encryption
    "CKV_AWS_16": RemediationSeverity.HIGH,  # RDS encryption
    "CKV_AWS_17": RemediationSeverity.HIGH,  # RDS snapshot encryption
    "CKV_AWS_23": RemediationSeverity.HIGH,  # SG unrestricted
    "CKV_AWS_7": RemediationSeverity.HIGH,  # KMS rotation
    "CKV_AWS_33": RemediationSeverity.HIGH,  # KMS policy
    "CKV_AWS_79": RemediationSeverity.HIGH,  # IMDSv2
    # Medium
    "CKV_AWS_18": RemediationSeverity.MEDIUM,  # S3 versioning
    "CKV_AWS_21": RemediationSeverity.MEDIUM,  # S3 logging
    "CKV_AWS_91": RemediationSeverity.MEDIUM,  # RDS monitoring
    "CKV_AWS_118": RemediationSeverity.MEDIUM,  # RDS IAM auth
    "CKV_AWS_126": RemediationSeverity.MEDIUM,  # EC2 monitoring
    "CKV_AWS_128": RemediationSeverity.MEDIUM,  # RDS deletion protection
    "CKV_AWS_157": RemediationSeverity.MEDIUM,  # RDS multi-AZ
    "CKV_AWS_15": RemediationSeverity.MEDIUM,  # RDS multi-AZ
    # Low
    "CKV_AWS_4": RemediationSeverity.LOW,  # EBS snapshot encryption
}


def _get_severity(check_id: str) -> RemediationSeverity:
    """Get severity for a check ID."""
    return SEVERITY_MAP.get(check_id, RemediationSeverity.MEDIUM)


def _extract_bucket_name(resource: str, file_path: str) -> str:
    """Extract bucket name from resource or file path."""
    # Try to extract from resource like "aws_s3_bucket.my_bucket"
    if "." in resource:
        return resource.split(".")[-1]
    # Try to extract from file path
    path = Path(file_path)
    if path.stem.startswith("s3_"):
        return path.stem[3:]
    return resource


def _extract_instance_id(resource: str) -> str:
    """Extract instance ID from resource string."""
    if "." in resource:
        return resource.split(".")[-1]
    return resource


def _extract_db_identifier(resource: str) -> str:
    """Extract RDS identifier from resource string."""
    if "." in resource:
        return resource.split(".")[-1]
    return resource


def _extract_key_id(resource: str) -> str:
    """Extract KMS key ID from resource string."""
    if "." in resource:
        return resource.split(".")[-1]
    return resource


def _extract_security_group_id(resource: str) -> str:
    """Extract security group ID from resource string."""
    if "." in resource:
        return resource.split(".")[-1]
    return resource


class RemediationGenerator:
    """
    Generates Terraform remediation code from Checkov findings.

    Usage:
        from replimap.audit.remediation import RemediationGenerator

        generator = RemediationGenerator(findings)
        plan = generator.generate()

        # Write remediation files
        plan.write_all(Path("./remediation"))
    """

    # Mapping of check IDs to template functions
    TEMPLATE_MAP: dict[str, tuple[Callable, RemediationType]] = {
        # S3
        "CKV_AWS_19": (
            lambda f: generate_s3_encryption(
                _extract_bucket_name(f.resource, f.file_path),
                f.resource,
            ),
            RemediationType.S3_ENCRYPTION,
        ),
        "CKV_AWS_145": (
            lambda f: generate_s3_encryption(
                _extract_bucket_name(f.resource, f.file_path),
                f.resource,
                use_kms=True,
            ),
            RemediationType.S3_ENCRYPTION,
        ),
        "CKV_AWS_18": (
            lambda f: generate_s3_versioning(
                _extract_bucket_name(f.resource, f.file_path),
                f.resource,
            ),
            RemediationType.S3_VERSIONING,
        ),
        "CKV_AWS_21": (
            lambda f: generate_s3_logging(
                _extract_bucket_name(f.resource, f.file_path),
                f.resource,
            ),
            RemediationType.S3_LOGGING,
        ),
        "CKV_AWS_53": (
            lambda f: generate_s3_public_access_block(
                _extract_bucket_name(f.resource, f.file_path),
                f.resource,
            ),
            RemediationType.S3_PUBLIC_ACCESS,
        ),
        "CKV_AWS_54": (
            lambda f: generate_s3_public_access_block(
                _extract_bucket_name(f.resource, f.file_path),
                f.resource,
            ),
            RemediationType.S3_PUBLIC_ACCESS,
        ),
        "CKV_AWS_55": (
            lambda f: generate_s3_public_access_block(
                _extract_bucket_name(f.resource, f.file_path),
                f.resource,
            ),
            RemediationType.S3_PUBLIC_ACCESS,
        ),
        "CKV_AWS_56": (
            lambda f: generate_s3_public_access_block(
                _extract_bucket_name(f.resource, f.file_path),
                f.resource,
            ),
            RemediationType.S3_PUBLIC_ACCESS,
        ),
        "CKV_AWS_57": (
            lambda f: generate_s3_public_access_block(
                _extract_bucket_name(f.resource, f.file_path),
                f.resource,
            ),
            RemediationType.S3_PUBLIC_ACCESS,
        ),
        "CKV_AWS_20": (
            lambda f: generate_s3_ssl_policy(
                _extract_bucket_name(f.resource, f.file_path),
                f.resource,
            ),
            RemediationType.S3_SSL_POLICY,
        ),
        # EC2
        "CKV_AWS_79": (
            lambda f: generate_ec2_imdsv2(
                _extract_instance_id(f.resource),
                f.resource,
            ),
            RemediationType.EC2_IMDSV2,
        ),
        "CKV_AWS_3": (
            lambda f: generate_ebs_encryption(
                _extract_instance_id(f.resource),
                f.resource,
            ),
            RemediationType.EC2_EBS_ENCRYPTION,
        ),
        "CKV_AWS_4": (
            lambda f: generate_ebs_encryption(
                _extract_instance_id(f.resource),
                f.resource,
            ),
            RemediationType.EC2_EBS_ENCRYPTION,
        ),
        "CKV_AWS_126": (
            lambda f: generate_ec2_detailed_monitoring(
                _extract_instance_id(f.resource),
                f.resource,
            ),
            RemediationType.EC2_MONITORING,
        ),
        # Security Groups
        "CKV_AWS_23": (
            lambda f: generate_security_group_restrict(
                _extract_security_group_id(f.resource),
                f.resource,
            ),
            RemediationType.SECURITY_GROUP,
        ),
        "CKV_AWS_24": (
            lambda f: generate_security_group_restrict(
                _extract_security_group_id(f.resource),
                f.resource,
                port=22,
            ),
            RemediationType.SECURITY_GROUP,
        ),
        "CKV_AWS_25": (
            lambda f: generate_security_group_restrict(
                _extract_security_group_id(f.resource),
                f.resource,
                port=3389,
            ),
            RemediationType.SECURITY_GROUP,
        ),
        # RDS
        "CKV_AWS_16": (
            lambda f: generate_rds_encryption(
                _extract_db_identifier(f.resource),
                f.resource,
            ),
            RemediationType.RDS_ENCRYPTION,
        ),
        "CKV_AWS_17": (
            lambda f: generate_rds_encryption(
                _extract_db_identifier(f.resource),
                f.resource,
            ),
            RemediationType.RDS_ENCRYPTION,
        ),
        "CKV_AWS_157": (
            lambda f: generate_rds_multi_az(
                _extract_db_identifier(f.resource),
                f.resource,
            ),
            RemediationType.RDS_MULTI_AZ,
        ),
        "CKV_AWS_15": (
            lambda f: generate_rds_multi_az(
                _extract_db_identifier(f.resource),
                f.resource,
            ),
            RemediationType.RDS_MULTI_AZ,
        ),
        "CKV_AWS_128": (
            lambda f: generate_rds_deletion_protection(
                _extract_db_identifier(f.resource),
                f.resource,
            ),
            RemediationType.RDS_DELETION_PROTECTION,
        ),
        "CKV_AWS_91": (
            lambda f: generate_rds_monitoring(
                _extract_db_identifier(f.resource),
                f.resource,
            ),
            RemediationType.RDS_MONITORING,
        ),
        "CKV_AWS_118": (
            lambda f: generate_rds_iam_auth(
                _extract_db_identifier(f.resource),
                f.resource,
            ),
            RemediationType.RDS_IAM_AUTH,
        ),
        # KMS
        "CKV_AWS_7": (
            lambda f: generate_kms_rotation(
                _extract_key_id(f.resource),
                f.resource,
            ),
            RemediationType.KMS_ROTATION,
        ),
        "CKV_AWS_33": (
            lambda f: generate_kms_policy(
                _extract_key_id(f.resource),
                f.resource,
            ),
            RemediationType.KMS_POLICY,
        ),
    }

    def __init__(
        self,
        findings: list[CheckovFinding],
        output_dir: Path | None = None,
    ) -> None:
        """
        Initialize the remediation generator.

        Args:
            findings: List of Checkov findings to remediate
            output_dir: Optional output directory for generated files
        """
        self.findings = findings
        self.output_dir = output_dir or Path("./remediation")

    def generate(self) -> RemediationPlan:
        """
        Generate remediation plan from findings.

        Returns:
            RemediationPlan with all generated files
        """
        plan = RemediationPlan(total_findings=len(self.findings))

        # Track generated files to avoid duplicates
        generated_resources: set[str] = set()

        for finding in self.findings:
            if finding.check_id not in self.TEMPLATE_MAP:
                plan.skipped_findings += 1
                continue

            # Create unique key for this resource + check combination
            resource_key = f"{finding.resource}:{finding.check_id}"
            if resource_key in generated_resources:
                continue
            generated_resources.add(resource_key)

            try:
                template_func, remediation_type = self.TEMPLATE_MAP[finding.check_id]
                content = template_func(finding)

                # Generate file path based on remediation type
                file_path = self._get_file_path(finding, remediation_type)

                # Extract import commands from content
                import_commands = self._extract_import_commands(content)

                file = RemediationFile(
                    path=file_path,
                    content=content,
                    description=finding.check_name,
                    check_ids=[finding.check_id],
                    remediation_type=remediation_type,
                    severity=_get_severity(finding.check_id),
                    resource_ids=[finding.resource],
                    requires_import=bool(import_commands),
                    import_commands=import_commands,
                )

                plan.files.append(file)
                plan.remediable_findings += 1

            except Exception as e:
                logger.warning(
                    f"Failed to generate remediation for {finding.check_id}: {e}"
                )
                plan.skipped_findings += 1
                plan.warnings.append(
                    f"Failed to generate fix for {finding.check_id} on {finding.resource}"
                )

        # Generate Terraform 1.5+ import blocks (modern, preferred)
        import_blocks = self._generate_import_blocks(plan)
        if import_blocks:
            plan.files.append(
                RemediationFile(
                    path=Path("imports.tf"),
                    content=import_blocks,
                    description="Terraform 1.5+ Import Blocks",
                    remediation_type=RemediationType.OTHER,
                )
            )

        # Generate legacy import script (deprecated, for backward compatibility)
        plan.import_script = self._generate_import_script(plan)

        # Generate README
        plan.readme_content = self._generate_readme(plan)

        return plan

    def _get_file_path(
        self, finding: CheckovFinding, remediation_type: RemediationType
    ) -> Path:
        """Generate file path for remediation file."""
        # Extract resource name for file naming
        resource_name = (
            finding.resource.split(".")[-1]
            if "." in finding.resource
            else finding.resource
        )
        safe_name = "".join(c if c.isalnum() else "_" for c in resource_name).strip("_")

        # Group by remediation type
        type_prefix = remediation_type.value.split("_")[
            0
        ]  # e.g., "s3" from "s3_encryption"

        return Path(f"{type_prefix}/{safe_name}_{remediation_type.value}.tf")

    def _extract_import_commands(self, content: str) -> list[str]:
        """Extract terraform import commands from content."""
        commands = []
        for line in content.split("\n"):
            if line.strip().startswith("# terraform import"):
                cmd = line.strip()[2:].strip()  # Remove "# " prefix
                commands.append(cmd)
        return commands

    def _generate_import_blocks(self, plan: RemediationPlan) -> str:
        """
        Generate Terraform 1.5+ import blocks.

        This is the modern, preferred approach that:
        - Works on all platforms (no bash required)
        - Integrates with `terraform plan` workflow
        - Provides better error messages
        """
        lines = [
            "# ============================================================================",
            "# RepliMap Remediation Import Blocks",
            f"# Generated: {datetime.now(UTC).isoformat()}",
            "#",
            "# These Terraform 1.5+ import blocks automatically import existing resources.",
            "# Run `terraform plan` to preview the imports before applying.",
            "#",
            "# WARNING: Review each import and replace placeholder values (REPLACE_WITH_*)",
            "# ============================================================================",
            "",
        ]

        has_imports = False
        for file in plan.files:
            if file.import_commands:
                has_imports = True
                lines.append(f"# Imports for: {file.description}")
                for cmd in file.import_commands:
                    # Parse: "terraform import aws_type.name id"
                    parts = cmd.split(" ", 3)  # Split into max 4 parts
                    if len(parts) >= 4:
                        resource_addr = parts[2]
                        resource_id = parts[3]
                        lines.append("import {")
                        lines.append(f"  to = {resource_addr}")
                        lines.append(f'  id = "{resource_id}"')
                        lines.append("}")
                        lines.append("")

        if not has_imports:
            return ""

        return "\n".join(lines)

    def _generate_import_script(self, plan: RemediationPlan) -> str:
        """Generate shell script for terraform imports."""
        lines = [
            "#!/bin/bash",
            "# RepliMap Remediation Import Script",
            f"# Generated: {datetime.now(UTC).isoformat()}",
            "#",
            "# This script imports existing AWS resources into Terraform state.",
            "# Run this BEFORE applying the remediation Terraform.",
            "#",
            "# WARNING: Review each import command before running.",
            "#          Replace placeholder values (REPLACE_WITH_*) with actual values.",
            "",
            "set -e",
            "",
            "# Check that we're in the right directory",
            'if [ ! -f "main.tf" ] && [ ! -f "terraform.tf" ]; then',
            '    echo "Error: No Terraform files found. Run from your Terraform directory."',
            "    exit 1",
            "fi",
            "",
            "echo 'Starting Terraform imports...'",
            "",
        ]

        for file in plan.files:
            if file.import_commands:
                lines.append(f"# {file.description}")
                for cmd in file.import_commands:
                    lines.append(f"echo 'Importing: {cmd}'")
                    lines.append(cmd)
                lines.append("")

        lines.extend(
            [
                "echo 'All imports complete!'",
                "echo 'Run terraform plan to verify the import was successful.'",
            ]
        )

        return "\n".join(lines)

    def _generate_readme(self, plan: RemediationPlan) -> str:
        """Generate README for remediation files."""
        timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

        by_severity = plan.files_by_severity()

        readme = f"""# RepliMap Security Remediation

Generated: {timestamp}

## Summary

| Metric | Value |
|--------|-------|
| Total findings | {plan.total_findings} |
| Remediable | {plan.remediable_findings} ({plan.coverage_percent}%) |
| Skipped | {plan.skipped_findings} |
| Files generated | {len(plan.files)} |

## Findings by Severity

| Severity | Count |
|----------|-------|
| Critical | {len(by_severity[RemediationSeverity.CRITICAL])} |
| High | {len(by_severity[RemediationSeverity.HIGH])} |
| Medium | {len(by_severity[RemediationSeverity.MEDIUM])} |
| Low | {len(by_severity[RemediationSeverity.LOW])} |

## How to Apply

### 1. Review the Generated Code

Each `.tf` file contains:
- Comments explaining what the fix does
- The Terraform resource definition
- Import commands for existing resources

**WARNING**: Review ALL generated code before applying. Some fixes may:
- Require additional configuration
- Have placeholders that need replacement (REPLACE_WITH_*)
- Conflict with existing resources
- Have cost implications (e.g., Multi-AZ)

### 2. Import Existing Resources (if needed)

If you're managing existing AWS resources with Terraform:

**Modern Approach (Terraform 1.5+, Recommended):**

The generated `imports.tf` file contains `import` blocks that work with `terraform plan`:

```bash
terraform plan   # Preview imports and changes
terraform apply  # Apply imports and remediation
```

**Legacy Approach (Deprecated):**

For older Terraform versions, use the import script:

```bash
chmod +x import.sh
./import.sh
```

### 3. Apply the Remediation

```bash
terraform init
terraform plan
terraform apply
```

## Generated Files

"""

        # List files by type
        by_type = plan.files_by_type()
        for remediation_type, files in sorted(
            by_type.items(), key=lambda x: x[0].value
        ):
            readme += f"\n### {remediation_type.value.replace('_', ' ').title()}\n\n"
            for file in files:
                severity_emoji = {
                    RemediationSeverity.CRITICAL: "🔴",
                    RemediationSeverity.HIGH: "🟠",
                    RemediationSeverity.MEDIUM: "🟡",
                    RemediationSeverity.LOW: "🟢",
                }[file.severity]
                readme += f"- {severity_emoji} `{file.path}` - {file.description}\n"

        if plan.warnings:
            readme += "\n## Warnings\n\n"
            for warning in plan.warnings:
                readme += f"- ⚠️ {warning}\n"

        readme += """
## Disclaimer

This remediation code is generated based on Checkov security findings.
It provides a starting point for addressing security issues but:

- May require customization for your environment
- Should be reviewed by your security team
- Does not guarantee complete security coverage
- May have unintended side effects

Always test in a non-production environment first.

---
Generated by [RepliMap](https://replimap.com)
"""

        return readme
