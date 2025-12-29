"""
Import Block Generator for RepliMap.

Generates Terraform import blocks to bridge AWS resources to generated code.
This is THE MISSING LINK that makes RepliMap actually useful.

Without import blocks, generated Terraform code cannot manage existing resources.
With import blocks, terraform plan shows "0 to add" - perfect state sync.

The Seven Laws of Sovereign Code:
5. Refactor, Don't Recreate - Use moved blocks, never destroy to rename.

Requires: Terraform 1.5+ for import blocks
         Terraform 1.1+ for moved blocks (handled by RefactoringEngine)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from replimap.core.config import RepliMapConfig

logger = logging.getLogger(__name__)


# Some resources need special import ID formats
# LEVEL 2 INSIGHT: This list WILL be incomplete!
# Complex resources have unpredictable formats.
# Solution: Allow user overrides via .replimap.yaml
IMPORT_ID_FORMATS: dict[str, str] = {
    # Simple resources - just use ID
    "aws_vpc": "{id}",
    "aws_subnet": "{id}",
    "aws_security_group": "{id}",
    "aws_instance": "{id}",
    "aws_internet_gateway": "{id}",
    "aws_nat_gateway": "{id}",
    "aws_route_table": "{id}",
    "aws_ebs_volume": "{id}",
    "aws_elasticache_cluster": "{id}",
    "aws_elasticache_subnet_group": "{name}",
    "aws_vpc_endpoint": "{id}",
    "aws_eip": "{allocation_id}",
    "aws_launch_template": "{id}",
    "aws_autoscaling_group": "{name}",
    "aws_lb": "{arn}",
    "aws_lb_listener": "{arn}",
    "aws_lb_target_group": "{arn}",
    # Resources that use ARN or name
    "aws_iam_role": "{name}",
    "aws_iam_policy": "{arn}",
    "aws_iam_instance_profile": "{name}",
    "aws_lambda_function": "{name}",
    "aws_s3_bucket": "{bucket}",
    "aws_s3_bucket_policy": "{bucket}",
    "aws_db_instance": "{identifier}",
    "aws_db_subnet_group": "{name}",
    "aws_db_parameter_group": "{name}",
    "aws_sqs_queue": "{url}",
    "aws_sns_topic": "{arn}",
    # Complex resources - marked for user attention
    # These often fail and need manual intervention
    "aws_route_table_association": "COMPLEX_SEE_DOCS",
    "aws_security_group_rule": "COMPLEX_SEE_DOCS",
    "aws_route": "COMPLEX_SEE_DOCS",
}


@dataclass
class ImportMapping:
    """Maps a Terraform resource address to an AWS resource ID."""

    terraform_address: str  # e.g., "aws_instance.web_server_a1B2c3D4"
    aws_id: str  # e.g., "i-0abc123def456"
    resource_type: str  # e.g., "aws_instance"
    # Additional attributes for complex import formats
    attributes: dict | None = None


class ImportBlockGenerator:
    """
    Generate Terraform 1.5+ import blocks.

    These blocks tell Terraform: "The resource at this address
    corresponds to this existing AWS resource. Don't create it,
    just start managing it."

    Usage:
        generator = ImportBlockGenerator()
        mappings = [
            ImportMapping(
                terraform_address="aws_instance.web_a1b2",
                aws_id="i-0abc123",
                resource_type="aws_instance",
            ),
        ]
        generator.generate_import_file(mappings, Path("./terraform/imports.tf"))
    """

    def __init__(self, config: RepliMapConfig | None = None) -> None:
        """
        Initialize the import block generator.

        Args:
            config: User configuration for format overrides
        """
        self.import_formats = IMPORT_ID_FORMATS.copy()

        # Load user overrides from config
        if config:
            user_formats = config.get_import_formats()
            if user_formats:
                self.import_formats.update(user_formats)
                logger.info(f"Applied user import formats: {list(user_formats.keys())}")

    def format_import_id(self, mapping: ImportMapping) -> str:
        """
        Format the import ID based on resource type.

        Different AWS resources have different import ID formats.
        Most use the resource ID, but some need ARN, name, or composite keys.

        Args:
            mapping: Import mapping with resource details

        Returns:
            Formatted import ID string
        """
        format_template = self.import_formats.get(mapping.resource_type, "{id}")

        if format_template == "COMPLEX_SEE_DOCS":
            logger.warning(
                f"Resource {mapping.resource_type} has complex import format. "
                f"You may need to add override in .replimap.yaml. "
                f"See: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/{mapping.resource_type.replace('aws_', '')}"
            )
            # Return the ID as-is with a TODO marker
            return f"TODO_COMPLEX_FORMAT:{mapping.aws_id}"

        # For simple templates, just return the ID
        if format_template == "{id}":
            return mapping.aws_id

        # For named resources, try to extract the name
        if format_template == "{name}":
            if mapping.attributes and "name" in mapping.attributes:
                return mapping.attributes["name"]
            # Fall back to extracting from ID or ARN
            return self._extract_name_from_id(mapping.aws_id)

        # For ARN format
        if format_template == "{arn}":
            if mapping.aws_id.startswith("arn:"):
                return mapping.aws_id
            if mapping.attributes and "arn" in mapping.attributes:
                return mapping.attributes["arn"]
            return mapping.aws_id

        # For bucket format
        if format_template == "{bucket}":
            if mapping.attributes and "bucket" in mapping.attributes:
                return mapping.attributes["bucket"]
            return mapping.aws_id

        # For identifier format (RDS)
        if format_template == "{identifier}":
            if mapping.attributes and "identifier" in mapping.attributes:
                return mapping.attributes["identifier"]
            if mapping.attributes and "db_instance_identifier" in mapping.attributes:
                return mapping.attributes["db_instance_identifier"]
            return mapping.aws_id

        # For URL format (SQS)
        if format_template == "{url}":
            if mapping.attributes and "url" in mapping.attributes:
                return mapping.attributes["url"]
            return mapping.aws_id

        # For allocation_id format (EIP)
        if format_template == "{allocation_id}":
            if mapping.aws_id.startswith("eipalloc-"):
                return mapping.aws_id
            if mapping.attributes and "allocation_id" in mapping.attributes:
                return mapping.attributes["allocation_id"]
            return mapping.aws_id

        # Default: return the ID
        return mapping.aws_id

    def _extract_name_from_id(self, resource_id: str) -> str:
        """
        Extract a name from an AWS ID or ARN.

        Args:
            resource_id: AWS resource ID or ARN

        Returns:
            Extracted name or original ID
        """
        if resource_id.startswith("arn:"):
            # ARN format: arn:partition:service:region:account:resource-type/resource-id
            parts = resource_id.split(":")
            if len(parts) >= 6:
                resource_part = parts[5]
                if "/" in resource_part:
                    return resource_part.split("/")[-1]
                return resource_part
        return resource_id

    def generate_import_file(
        self,
        mappings: list[ImportMapping],
        output_path: Path,
    ) -> None:
        """
        Generate imports.tf file with all import blocks.

        Example output:
        ```hcl
        # Auto-generated by RepliMap
        # These import blocks map existing AWS resources to Terraform addresses

        import {
          to = aws_instance.web_server_a1B2c3D4
          id = "i-0abc123def456"
        }
        ```

        Args:
            mappings: List of import mappings
            output_path: Path to write the imports.tf file
        """
        if not mappings:
            logger.info("No import mappings to generate")
            return

        lines = [
            "# ═══════════════════════════════════════════════════════════════════════════════",
            "# Auto-generated by RepliMap",
            "# These import blocks map existing AWS resources to Terraform addresses",
            "# ═══════════════════════════════════════════════════════════════════════════════",
            "#",
            "# Run 'terraform plan' to verify, then 'terraform apply' to sync state",
            "#",
            "# Terraform 1.5+ required for import blocks",
            "# See: https://developer.hashicorp.com/terraform/language/import",
            "#",
            "# ═══════════════════════════════════════════════════════════════════════════════",
            "",
        ]

        # Track complex imports that need manual attention
        complex_imports: list[ImportMapping] = []

        for mapping in mappings:
            import_id = self.format_import_id(mapping)

            if import_id.startswith("TODO_COMPLEX_FORMAT:"):
                complex_imports.append(mapping)
                # Still generate the block but commented out
                lines.extend(
                    [
                        f"# WARNING: Complex import format for {mapping.resource_type}",
                        "# You may need to manually determine the correct import ID",
                        "# See Terraform docs for this resource type",
                        "# import {",
                        f"#   to = {mapping.terraform_address}",
                        f'#   id = "TODO: Determine correct import ID for {mapping.aws_id}"',
                        "# }",
                        "",
                    ]
                )
            else:
                lines.extend(
                    [
                        "import {",
                        f"  to = {mapping.terraform_address}",
                        f'  id = "{import_id}"',
                        "}",
                        "",
                    ]
                )

        # Add summary of complex imports
        if complex_imports:
            lines.extend(
                [
                    "# ═══════════════════════════════════════════════════════════════════════════════",
                    "# ATTENTION: The following resources need manual import configuration",
                    "# ═══════════════════════════════════════════════════════════════════════════════",
                    "#",
                ]
            )
            for mapping in complex_imports:
                lines.append(f"# - {mapping.terraform_address} ({mapping.aws_id})")
            lines.extend(
                [
                    "#",
                    "# Consult the Terraform AWS provider documentation for correct import IDs:",
                    "# https://registry.terraform.io/providers/hashicorp/aws/latest/docs",
                    "",
                ]
            )

        output_path.write_text("\n".join(lines))
        logger.info(
            f"Wrote imports.tf: {len(mappings)} imports "
            f"({len(complex_imports)} need manual attention)"
        )

    def generate_import_commands(
        self,
        mappings: list[ImportMapping],
    ) -> list[str]:
        """
        Generate legacy import commands for Terraform < 1.5.

        For users on older Terraform versions, generate shell commands:
        terraform import aws_instance.web_server_a1B2c3D4 i-0abc123def456

        Args:
            mappings: List of import mappings

        Returns:
            List of shell commands
        """
        commands = [
            "#!/bin/bash",
            "# ═══════════════════════════════════════════════════════════════════════════════",
            "# RepliMap Import Script",
            "# ═══════════════════════════════════════════════════════════════════════════════",
            "#",
            "# Run this to import existing resources into Terraform state.",
            "# Requires: Terraform initialized (terraform init)",
            "#",
            "# For Terraform 1.5+, use imports.tf instead (recommended).",
            "#",
            "# ═══════════════════════════════════════════════════════════════════════════════",
            "",
            "set -e  # Exit on error",
            "",
            "echo 'Starting resource imports...'",
            "",
        ]

        for i, mapping in enumerate(mappings):
            import_id = self.format_import_id(mapping)

            if import_id.startswith("TODO_COMPLEX_FORMAT:"):
                commands.extend(
                    [
                        f"# WARNING: Complex import for {mapping.resource_type}",
                        f"# terraform import {mapping.terraform_address} 'TODO: Determine ID'",
                        "",
                    ]
                )
            else:
                # Escape special characters in import ID
                escaped_id = import_id.replace("'", "'\\''")
                commands.extend(
                    [
                        f"echo '[{i + 1}/{len(mappings)}] Importing {mapping.terraform_address}'",
                        f"terraform import {mapping.terraform_address} '{escaped_id}'",
                        "",
                    ]
                )

        commands.extend(
            [
                "echo ''",
                "echo 'All imports completed successfully!'",
                "echo 'Run terraform plan to verify state.'",
            ]
        )

        return commands

    def generate_import_script(
        self,
        mappings: list[ImportMapping],
        output_path: Path,
    ) -> None:
        """
        Generate import.sh script file.

        Args:
            mappings: List of import mappings
            output_path: Path to write the import.sh file
        """
        if not mappings:
            logger.info("No import mappings for script")
            return

        commands = self.generate_import_commands(mappings)
        output_path.write_text("\n".join(commands))
        output_path.chmod(0o755)  # Make executable
        logger.info(f"Wrote import.sh: {len(mappings)} imports")
