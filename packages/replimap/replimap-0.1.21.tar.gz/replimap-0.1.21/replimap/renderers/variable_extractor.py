"""
Variable Extractor for RepliMap.

Extract common values as Terraform variables for DRY principle.
Don't hardcode us-east-1 fifty times.

The Seven Laws of Sovereign Code:
3. Simplicity is the Ultimate Sophistication - If you can derive it, don't store it.

Level 4 Enhancement: Detect recurring values and extract to variables.
"""

from __future__ import annotations

import logging
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from replimap.core.models import ResourceNode

logger = logging.getLogger(__name__)


@dataclass
class ExtractedVariable:
    """A variable extracted from resource attributes."""

    name: str
    value: Any
    description: str
    var_type: str = "string"
    occurrences: int = 1
    sensitive: bool = False


class VariableExtractor:
    """
    Analyze resources and extract common values as variables.

    Detects:
    - Region (appears in availability zones, ARNs)
    - Account ID (appears in ARNs, policies)
    - Environment tags (common tag patterns)
    - VPC ID (referenced by many resources)
    - Common instance types
    - Common AMI IDs

    Usage:
        extractor = VariableExtractor()
        variables = extractor.analyze(resources)

        # Generate files
        variables_tf = extractor.generate_variables_tf(variables)
        tfvars = extractor.generate_tfvars(variables)
    """

    # Minimum occurrences before extracting as variable
    MIN_OCCURRENCES = 2

    # Patterns for value detection
    REGION_PATTERN = re.compile(r"^[a-z]{2}-[a-z]+-\d+$")
    ACCOUNT_ID_PATTERN = re.compile(r"^\d{12}$")
    AZ_PATTERN = re.compile(r"^[a-z]{2}-[a-z]+-\d+[a-z]$")

    # Environment tag names to look for
    ENVIRONMENT_TAG_KEYS = {
        "Environment",
        "Env",
        "Stage",
        "environment",
        "env",
        "stage",
    }

    # Known environment values
    ENVIRONMENT_VALUES = {
        "prod",
        "production",
        "staging",
        "stage",
        "dev",
        "development",
        "test",
        "testing",
        "qa",
        "uat",
        "sandbox",
    }

    def __init__(self, min_occurrences: int = 2) -> None:
        """
        Initialize the variable extractor.

        Args:
            min_occurrences: Minimum occurrences to extract as variable
        """
        self.min_occurrences = min_occurrences

    def analyze(
        self,
        resources: list[ResourceNode],
    ) -> dict[str, ExtractedVariable]:
        """
        Analyze resources and find extractable values.

        Args:
            resources: List of ResourceNode objects

        Returns:
            Dictionary of variable name to ExtractedVariable
        """
        value_counter: Counter = Counter()
        region_counter: Counter = Counter()
        environment_counter: Counter = Counter()
        vpc_counter: Counter = Counter()
        account_id_counter: Counter = Counter()
        instance_type_counter: Counter = Counter()
        ami_counter: Counter = Counter()

        for resource in resources:
            self._scan_resource(
                resource,
                value_counter,
                region_counter,
                environment_counter,
                vpc_counter,
                account_id_counter,
                instance_type_counter,
                ami_counter,
            )

        variables: dict[str, ExtractedVariable] = {}

        # Extract region
        if region_counter:
            most_common_region = region_counter.most_common(1)[0]
            if most_common_region[1] >= self.min_occurrences:
                variables["aws_region"] = ExtractedVariable(
                    name="aws_region",
                    value=most_common_region[0],
                    description="AWS region for resources",
                    occurrences=most_common_region[1],
                )

        # Extract environment
        if environment_counter:
            most_common_env = environment_counter.most_common(1)[0]
            if most_common_env[1] >= self.min_occurrences:
                variables["environment"] = ExtractedVariable(
                    name="environment",
                    value=most_common_env[0],
                    description="Environment name (e.g., production, staging)",
                    occurrences=most_common_env[1],
                )

        # Extract VPC ID if there's a dominant one
        if vpc_counter:
            most_common_vpc = vpc_counter.most_common(1)[0]
            if most_common_vpc[1] >= self.min_occurrences:
                variables["vpc_id"] = ExtractedVariable(
                    name="vpc_id",
                    value=most_common_vpc[0],
                    description="Primary VPC ID",
                    occurrences=most_common_vpc[1],
                )

        # Extract account ID
        if account_id_counter:
            most_common_account = account_id_counter.most_common(1)[0]
            if most_common_account[1] >= self.min_occurrences:
                variables["aws_account_id"] = ExtractedVariable(
                    name="aws_account_id",
                    value=most_common_account[0],
                    description="AWS Account ID",
                    occurrences=most_common_account[1],
                )

        # Extract common instance type
        if instance_type_counter:
            most_common_type = instance_type_counter.most_common(1)[0]
            if most_common_type[1] >= self.min_occurrences:
                variables["default_instance_type"] = ExtractedVariable(
                    name="default_instance_type",
                    value=most_common_type[0],
                    description="Default EC2 instance type",
                    occurrences=most_common_type[1],
                )

        logger.info(f"Extracted {len(variables)} common variables")
        for var in variables.values():
            logger.debug(f"  {var.name} = {var.value} ({var.occurrences} occurrences)")

        return variables

    def _scan_resource(
        self,
        resource: ResourceNode,
        value_counter: Counter,
        region_counter: Counter,
        environment_counter: Counter,
        vpc_counter: Counter,
        account_id_counter: Counter,
        instance_type_counter: Counter,
        ami_counter: Counter,
    ) -> None:
        """
        Scan a single resource for extractable values.

        Args:
            resource: ResourceNode to scan
            *_counter: Counters for various value types
        """
        config = resource.config
        tags = resource.tags

        # Region from resource or config
        if resource.region:
            if self._looks_like_region(resource.region):
                region_counter[resource.region] += 1

        # Availability zone -> extract region
        az = config.get("availability_zone")
        if az and self.AZ_PATTERN.match(str(az)):
            region = az[:-1]  # Remove suffix (a, b, c, etc.)
            region_counter[region] += 1

        # Environment from tags
        for tag_key in self.ENVIRONMENT_TAG_KEYS:
            if tag_key in tags:
                env_value = tags[tag_key].lower()
                if env_value in self.ENVIRONMENT_VALUES:
                    environment_counter[env_value] += 1
                    break

        # VPC ID
        vpc_id = config.get("vpc_id")
        if vpc_id and vpc_id.startswith("vpc-"):
            vpc_counter[vpc_id] += 1

        # Instance type
        instance_type = config.get("instance_type")
        if instance_type:
            instance_type_counter[instance_type] += 1

        # AMI ID
        ami = config.get("ami") or config.get("image_id")
        if ami and ami.startswith("ami-"):
            ami_counter[ami] += 1

        # Account ID from ARN
        arn = resource.arn or config.get("arn")
        if arn:
            account_id = self._extract_account_from_arn(arn)
            if account_id:
                account_id_counter[account_id] += 1

    def _looks_like_region(self, value: str) -> bool:
        """Check if value looks like an AWS region."""
        return bool(self.REGION_PATTERN.match(str(value)))

    def _extract_account_from_arn(self, arn: str) -> str | None:
        """Extract account ID from ARN."""
        # ARN format: arn:partition:service:region:account:resource
        parts = str(arn).split(":")
        if len(parts) >= 5:
            account = parts[4]
            if self.ACCOUNT_ID_PATTERN.match(account):
                return account
        return None

    def generate_variables_tf(
        self,
        variables: dict[str, ExtractedVariable],
    ) -> str:
        """
        Generate variables.tf content.

        Args:
            variables: Dictionary of extracted variables

        Returns:
            HCL content for variables.tf
        """
        lines = [
            "# ═══════════════════════════════════════════════════════════════════════════════",
            "# Auto-generated by RepliMap",
            "# Common variables extracted from resources",
            "# ═══════════════════════════════════════════════════════════════════════════════",
            "",
        ]

        for var in sorted(variables.values(), key=lambda v: v.name):
            lines.append(f'variable "{var.name}" {{')
            lines.append(f'  description = "{var.description}"')
            lines.append(f"  type        = {var.var_type}")

            if var.sensitive:
                lines.append("  sensitive   = true")

            # Add default value
            if isinstance(var.value, bool):
                lines.append(f"  default     = {str(var.value).lower()}")
            elif isinstance(var.value, (int, float)):
                lines.append(f"  default     = {var.value}")
            elif isinstance(var.value, list):
                lines.append(f"  default     = {var.value}")
            else:
                lines.append(f'  default     = "{var.value}"')

            lines.append("}")
            lines.append("")

        return "\n".join(lines)

    def generate_tfvars(
        self,
        variables: dict[str, ExtractedVariable],
    ) -> str:
        """
        Generate terraform.tfvars content.

        Args:
            variables: Dictionary of extracted variables

        Returns:
            Content for terraform.tfvars
        """
        lines = [
            "# ═══════════════════════════════════════════════════════════════════════════════",
            "# Auto-generated by RepliMap",
            "# Override these values as needed",
            "# ═══════════════════════════════════════════════════════════════════════════════",
            "",
        ]

        for var in sorted(variables.values(), key=lambda v: v.name):
            # Add comment with occurrences
            lines.append(f"# {var.description} (found {var.occurrences} times)")

            if var.sensitive:
                lines.append(f'# {var.name} = "REDACTED"  # Sensitive value')
            elif isinstance(var.value, bool):
                lines.append(f"{var.name} = {str(var.value).lower()}")
            elif isinstance(var.value, (int, float)):
                lines.append(f"{var.name} = {var.value}")
            else:
                lines.append(f'{var.name} = "{var.value}"')

            lines.append("")

        return "\n".join(lines)

    def generate_files(
        self,
        variables: dict[str, ExtractedVariable],
        output_dir: Path,
    ) -> dict[str, Path]:
        """
        Generate variable files.

        Args:
            variables: Dictionary of extracted variables
            output_dir: Directory to write files

        Returns:
            Dictionary of generated file paths
        """
        generated: dict[str, Path] = {}

        if not variables:
            return generated

        # Generate variables.tf
        variables_path = output_dir / "variables.tf"
        variables_path.write_text(self.generate_variables_tf(variables))
        generated["variables.tf"] = variables_path
        logger.info(f"Wrote variables.tf: {len(variables)} variables")

        # Generate terraform.tfvars
        tfvars_path = output_dir / "terraform.tfvars"
        tfvars_path.write_text(self.generate_tfvars(variables))
        generated["terraform.tfvars"] = tfvars_path
        logger.info("Wrote terraform.tfvars")

        return generated
