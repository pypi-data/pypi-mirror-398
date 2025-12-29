"""
Local Module Extractor for RepliMap.

Detect patterns of related resources and suggest local module extraction.
This is NOT about mapping to community modules - it's about organizing
generated code into sensible local modules.

The Seven Laws of Sovereign Code:
6. Mimic the Environment - Respect existing versions, backends, structure.

Level 5 Enhancement: Flat resources → Local Module Extraction

Key Insight from Gemini:
"Don't map to community modules. Extract LOCAL modules from related resources."

Example Pattern Detection:
- VPC + Subnets + Route Tables + IGW + NAT = vpc_module
- ALB + Listeners + Target Groups = alb_module
- ASG + Launch Template + Security Group = compute_module

The extractor:
1. Detects resource clusters (related by references)
2. Suggests module boundaries
3. Generates module structure
4. Generates moved blocks for migration
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from replimap.core.config import RepliMapConfig
    from replimap.core.models import ResourceNode

logger = logging.getLogger(__name__)


# Module patterns - what resources typically belong together
MODULE_PATTERNS: dict[str, dict[str, Any]] = {
    "vpc": {
        "description": "VPC networking infrastructure",
        "anchor_types": ["aws_vpc"],
        "related_types": [
            "aws_subnet",
            "aws_internet_gateway",
            "aws_nat_gateway",
            "aws_route_table",
            "aws_route_table_association",
            "aws_eip",  # For NAT Gateway
            "aws_vpc_endpoint",
            "aws_network_acl",
            "aws_network_acl_rule",
            "aws_default_route_table",
            "aws_default_network_acl",
        ],
        "min_resources": 3,
        "suggested_name": "vpc_{vpc_name}",
    },
    "security": {
        "description": "Security groups and rules",
        "anchor_types": ["aws_security_group"],
        "related_types": [
            "aws_security_group_rule",
        ],
        "min_resources": 2,
        "suggested_name": "security_{sg_name}",
    },
    "alb": {
        "description": "Application Load Balancer infrastructure",
        "anchor_types": ["aws_lb"],
        "related_types": [
            "aws_lb_listener",
            "aws_lb_listener_rule",
            "aws_lb_target_group",
            "aws_lb_target_group_attachment",
        ],
        "min_resources": 2,
        "suggested_name": "alb_{lb_name}",
    },
    "compute": {
        "description": "Compute infrastructure (ASG/EC2)",
        "anchor_types": ["aws_autoscaling_group", "aws_instance"],
        "related_types": [
            "aws_launch_template",
            "aws_launch_configuration",
            "aws_autoscaling_policy",
            "aws_autoscaling_schedule",
        ],
        "min_resources": 2,
        "suggested_name": "compute_{asg_name}",
    },
    "rds": {
        "description": "RDS database infrastructure",
        "anchor_types": ["aws_db_instance"],
        "related_types": [
            "aws_db_subnet_group",
            "aws_db_parameter_group",
            "aws_db_option_group",
        ],
        "min_resources": 2,
        "suggested_name": "rds_{db_name}",
    },
    "elasticache": {
        "description": "ElastiCache infrastructure",
        "anchor_types": [
            "aws_elasticache_cluster",
            "aws_elasticache_replication_group",
        ],
        "related_types": [
            "aws_elasticache_subnet_group",
            "aws_elasticache_parameter_group",
        ],
        "min_resources": 2,
        "suggested_name": "cache_{cluster_name}",
    },
    "lambda": {
        "description": "Lambda function infrastructure",
        "anchor_types": ["aws_lambda_function"],
        "related_types": [
            "aws_lambda_permission",
            "aws_lambda_event_source_mapping",
            "aws_lambda_layer_version",
            "aws_cloudwatch_log_group",
        ],
        "min_resources": 2,
        "suggested_name": "lambda_{function_name}",
    },
    "iam": {
        "description": "IAM role and policies",
        "anchor_types": ["aws_iam_role"],
        "related_types": [
            "aws_iam_role_policy",
            "aws_iam_role_policy_attachment",
            "aws_iam_instance_profile",
            "aws_iam_policy",
        ],
        "min_resources": 2,
        "suggested_name": "iam_{role_name}",
    },
    "s3": {
        "description": "S3 bucket infrastructure",
        "anchor_types": ["aws_s3_bucket"],
        "related_types": [
            "aws_s3_bucket_policy",
            "aws_s3_bucket_versioning",
            "aws_s3_bucket_lifecycle_configuration",
            "aws_s3_bucket_server_side_encryption_configuration",
            "aws_s3_bucket_public_access_block",
            "aws_s3_bucket_notification",
        ],
        "min_resources": 2,
        "suggested_name": "s3_{bucket_name}",
    },
}


@dataclass
class ModuleSuggestion:
    """A suggested module extraction."""

    module_type: str  # e.g., "vpc", "alb", "compute"
    module_name: str  # e.g., "vpc_production"
    description: str
    anchor_resource: str  # The primary resource ID
    member_resources: list[str] = field(default_factory=list)
    resource_addresses: dict[str, str] = field(
        default_factory=dict
    )  # aws_id -> address

    @property
    def resource_count(self) -> int:
        """Total resources including anchor."""
        return len(self.member_resources) + 1

    def __str__(self) -> str:
        return f"module.{self.module_name} ({self.resource_count} resources)"


@dataclass
class ExtractionPlan:
    """Plan for extracting resources into modules."""

    suggestions: list[ModuleSuggestion] = field(default_factory=list)
    unassigned_resources: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)

    @property
    def total_modules(self) -> int:
        """Number of suggested modules."""
        return len(self.suggestions)

    @property
    def total_extracted_resources(self) -> int:
        """Total resources that would be extracted."""
        return sum(s.resource_count for s in self.suggestions)

    def summary(self) -> str:
        """Generate a human-readable summary."""
        lines = [
            "Module Extraction Analysis:",
            f"  - {self.total_modules} modules suggested",
            f"  - {self.total_extracted_resources} resources to extract",
            f"  - {len(self.unassigned_resources)} resources unassigned",
        ]

        if self.suggestions:
            lines.append("\nSuggested Modules:")
            for suggestion in self.suggestions:
                lines.append(f"  - {suggestion}")

        if self.conflicts:
            lines.append(f"\n⚠️ {len(self.conflicts)} conflicts detected")

        return "\n".join(lines)


class LocalModuleExtractor:
    """
    Detect and suggest local module extraction.

    This is a SUGGESTION engine - it identifies patterns and proposes
    module boundaries. The actual extraction is a separate step.

    Key Principle: Extract LOCAL modules, don't map to community modules.
    Community modules have their own opinions. We generate flat, sovereign code.

    Usage:
        extractor = LocalModuleExtractor(config)
        plan = extractor.analyze(resources)

        if plan.suggestions:
            for suggestion in plan.suggestions:
                print(f"Suggested: {suggestion}")
    """

    def __init__(self, config: RepliMapConfig | None = None) -> None:
        """
        Initialize the module extractor.

        Args:
            config: User configuration for extraction settings
        """
        self.config = config
        self.patterns = MODULE_PATTERNS.copy()

        # Get config options
        if config:
            self.enabled = config.get("modules.suggest_extraction", True)
            self.min_resources = config.get("modules.min_resources_for_module", 3)
        else:
            self.enabled = True
            self.min_resources = 3

    def analyze(self, resources: list[ResourceNode]) -> ExtractionPlan:
        """
        Analyze resources and suggest module extractions.

        Args:
            resources: List of ResourceNode objects

        Returns:
            ExtractionPlan with suggestions
        """
        if not self.enabled:
            return ExtractionPlan()

        plan = ExtractionPlan()

        # Build lookup maps
        by_type: dict[str, list[ResourceNode]] = defaultdict(list)
        by_id: dict[str, ResourceNode] = {}

        for resource in resources:
            resource_type = str(resource.resource_type)
            by_type[resource_type].append(resource)
            by_id[resource.id] = resource

        # Track which resources are already assigned
        assigned: set[str] = set()

        # Find module patterns
        for pattern_name, pattern in self.patterns.items():
            suggestions = self._find_pattern(
                pattern_name,
                pattern,
                by_type,
                by_id,
                assigned,
            )

            for suggestion in suggestions:
                if suggestion.resource_count >= self.min_resources:
                    plan.suggestions.append(suggestion)
                    assigned.add(suggestion.anchor_resource)
                    assigned.update(suggestion.member_resources)

        # Track unassigned resources
        for resource in resources:
            if resource.id not in assigned:
                plan.unassigned_resources.append(resource.id)

        logger.info(plan.summary())
        return plan

    def _find_pattern(
        self,
        pattern_name: str,
        pattern: dict[str, Any],
        by_type: dict[str, list[ResourceNode]],
        by_id: dict[str, ResourceNode],
        assigned: set[str],
    ) -> list[ModuleSuggestion]:
        """
        Find instances of a module pattern.

        Args:
            pattern_name: Name of the pattern (e.g., "vpc")
            pattern: Pattern definition
            by_type: Resources indexed by type
            by_id: Resources indexed by ID
            assigned: Already-assigned resource IDs

        Returns:
            List of ModuleSuggestion objects
        """
        suggestions: list[ModuleSuggestion] = []
        anchor_types = pattern["anchor_types"]
        related_types = pattern["related_types"]

        # Find anchor resources
        for anchor_type in anchor_types:
            for anchor in by_type.get(anchor_type, []):
                if anchor.id in assigned:
                    continue

                # Find related resources
                members = self._find_related_resources(
                    anchor,
                    related_types,
                    by_type,
                    by_id,
                    assigned,
                )

                if members:
                    # Generate module name
                    module_name = self._generate_module_name(
                        pattern_name,
                        pattern.get("suggested_name", pattern_name),
                        anchor,
                    )

                    suggestion = ModuleSuggestion(
                        module_type=pattern_name,
                        module_name=module_name,
                        description=pattern["description"],
                        anchor_resource=anchor.id,
                        member_resources=list(members.keys()),
                        resource_addresses={
                            anchor.id: f"{anchor.resource_type}.{anchor.terraform_name}",
                            **{
                                rid: f"{r.resource_type}.{r.terraform_name}"
                                for rid, r in members.items()
                            },
                        },
                    )

                    suggestions.append(suggestion)

        return suggestions

    def _find_related_resources(
        self,
        anchor: ResourceNode,
        related_types: list[str],
        by_type: dict[str, list[ResourceNode]],
        by_id: dict[str, ResourceNode],
        assigned: set[str],
    ) -> dict[str, ResourceNode]:
        """
        Find resources related to an anchor resource.

        Relationship detection:
        1. Direct reference (e.g., subnet.vpc_id == vpc.id)
        2. Tag-based (e.g., same Name tag prefix)
        3. Config-based (e.g., subnet_ids contains subnet.id)

        Args:
            anchor: The anchor resource
            related_types: Types of resources to look for
            by_type: Resources indexed by type
            by_id: Resources indexed by ID
            assigned: Already-assigned resource IDs

        Returns:
            Dict of resource_id -> ResourceNode for related resources
        """
        related: dict[str, ResourceNode] = {}

        for resource_type in related_types:
            for resource in by_type.get(resource_type, []):
                if resource.id in assigned or resource.id == anchor.id:
                    continue

                if self._is_related(anchor, resource):
                    related[resource.id] = resource

        return related

    def _is_related(
        self,
        anchor: ResourceNode,
        candidate: ResourceNode,
    ) -> bool:
        """
        Check if a candidate resource is related to an anchor.

        Args:
            anchor: The anchor resource
            candidate: The candidate resource

        Returns:
            True if resources are related
        """
        anchor_type = str(anchor.resource_type)
        candidate_type = str(candidate.resource_type)

        # VPC-based relationships
        if anchor_type == "aws_vpc":
            # Check if candidate references this VPC
            vpc_id = candidate.config.get("vpc_id")
            if vpc_id == anchor.id:
                return True

            # Check for gateway attachment
            if candidate_type == "aws_internet_gateway":
                attached_vpc = candidate.config.get("vpc_id")
                if attached_vpc == anchor.id:
                    return True

            # Check for NAT gateway (via subnet relationship)
            if candidate_type == "aws_nat_gateway":
                # NAT gateways are related if in a subnet of this VPC
                # (Would need to trace through subnets - simplified here)
                return vpc_id == anchor.id if vpc_id else False

        # Security group relationships
        if anchor_type == "aws_security_group":
            # Security group rules reference their parent
            if candidate_type == "aws_security_group_rule":
                sg_id = candidate.config.get("security_group_id")
                if sg_id == anchor.id:
                    return True

        # ALB relationships
        if anchor_type == "aws_lb":
            arn = anchor.config.get("arn", anchor.id)
            # Listeners reference their LB
            if candidate_type == "aws_lb_listener":
                lb_arn = candidate.config.get("load_balancer_arn")
                if lb_arn == arn:
                    return True

            # Target groups associated via tags or naming
            if candidate_type == "aws_lb_target_group":
                # Check if name suggests relationship
                anchor_name = anchor.config.get("name", "")
                candidate_name = candidate.config.get("name", "")
                if anchor_name and candidate_name.startswith(anchor_name.split("-")[0]):
                    return True

        # ASG relationships
        if anchor_type == "aws_autoscaling_group":
            # Launch template reference
            if candidate_type == "aws_launch_template":
                lt_config = anchor.config.get("launch_template", {})
                if isinstance(lt_config, dict):
                    lt_id = lt_config.get("id")
                    if lt_id == candidate.id:
                        return True

        # RDS relationships
        if anchor_type == "aws_db_instance":
            # Subnet group reference
            if candidate_type == "aws_db_subnet_group":
                subnet_group = anchor.config.get("db_subnet_group_name")
                candidate_name = candidate.config.get("name")
                if subnet_group == candidate_name:
                    return True

            # Parameter group reference
            if candidate_type == "aws_db_parameter_group":
                param_group = anchor.config.get("parameter_group_name")
                candidate_name = candidate.config.get("name")
                if param_group == candidate_name:
                    return True

        # S3 bucket relationships (same bucket name)
        if anchor_type == "aws_s3_bucket":
            bucket_name = anchor.config.get("bucket", anchor.id)
            if candidate_type.startswith("aws_s3_bucket_"):
                candidate_bucket = candidate.config.get("bucket")
                if candidate_bucket == bucket_name:
                    return True

        # IAM role relationships
        if anchor_type == "aws_iam_role":
            role_name = anchor.config.get("name", "")
            # Role policies reference their role
            if candidate_type in [
                "aws_iam_role_policy",
                "aws_iam_role_policy_attachment",
            ]:
                policy_role = candidate.config.get("role")
                if policy_role == role_name:
                    return True

            # Instance profiles reference their role
            if candidate_type == "aws_iam_instance_profile":
                profile_role = candidate.config.get("role")
                if profile_role == role_name:
                    return True

        # Lambda function relationships
        if anchor_type == "aws_lambda_function":
            function_name = anchor.config.get("function_name", "")
            # Lambda permissions reference their function
            if candidate_type == "aws_lambda_permission":
                perm_function = candidate.config.get("function_name")
                if perm_function == function_name:
                    return True

            # Event source mappings reference their function
            if candidate_type == "aws_lambda_event_source_mapping":
                esm_function = candidate.config.get("function_name")
                if esm_function == function_name:
                    return True

        return False

    def _generate_module_name(
        self,
        pattern_name: str,
        template: str,
        anchor: ResourceNode,
    ) -> str:
        """
        Generate a module name from the pattern and anchor.

        Args:
            pattern_name: Pattern name (e.g., "vpc")
            template: Name template (e.g., "vpc_{vpc_name}")
            anchor: The anchor resource

        Returns:
            Generated module name
        """
        # Extract name from anchor
        anchor_name = (
            anchor.config.get("name")
            or anchor.config.get("bucket")
            or anchor.config.get("function_name")
            or anchor.config.get("db_instance_identifier")
            or anchor.terraform_name
        )

        # Clean name for Terraform
        clean_name = self._sanitize_name(anchor_name)

        # Try to apply template
        try:
            # Simple template substitution
            name = template.replace("{vpc_name}", clean_name)
            name = name.replace("{sg_name}", clean_name)
            name = name.replace("{lb_name}", clean_name)
            name = name.replace("{asg_name}", clean_name)
            name = name.replace("{db_name}", clean_name)
            name = name.replace("{cluster_name}", clean_name)
            name = name.replace("{function_name}", clean_name)
            name = name.replace("{role_name}", clean_name)
            name = name.replace("{bucket_name}", clean_name)
            return name
        except Exception:
            return f"{pattern_name}_{clean_name}"

    def _sanitize_name(self, name: str) -> str:
        """
        Sanitize a name for use in Terraform module names.

        Args:
            name: Original name

        Returns:
            Sanitized name
        """
        import re

        # Remove non-alphanumeric characters except underscore
        sanitized = re.sub(r"[^a-zA-Z0-9_]", "_", name)

        # Remove consecutive underscores
        sanitized = re.sub(r"_+", "_", sanitized)

        # Remove leading/trailing underscores
        sanitized = sanitized.strip("_")

        # Ensure starts with letter
        if sanitized and not sanitized[0].isalpha():
            sanitized = f"m_{sanitized}"

        return sanitized.lower() or "module"


class ModuleGenerator:
    """
    Generate local module structure from extraction plan.

    Creates:
    - modules/<module_name>/main.tf
    - modules/<module_name>/variables.tf
    - modules/<module_name>/outputs.tf
    - Module call in root
    - Moved blocks for migration
    """

    def __init__(self, config: RepliMapConfig | None = None) -> None:
        """
        Initialize the module generator.

        Args:
            config: User configuration
        """
        self.config = config

    def generate_module_structure(
        self,
        suggestion: ModuleSuggestion,
        resources: dict[str, ResourceNode],
        output_dir: Path,
    ) -> dict[str, Path]:
        """
        Generate module files for a suggestion.

        Args:
            suggestion: The module suggestion
            resources: Dict of resource_id -> ResourceNode
            output_dir: Base output directory

        Returns:
            Dict of file type -> path for generated files
        """
        module_dir = output_dir / "modules" / suggestion.module_name
        module_dir.mkdir(parents=True, exist_ok=True)

        generated: dict[str, Path] = {}

        # Generate main.tf with resource blocks
        main_path = module_dir / "main.tf"
        main_content = self._generate_main_tf(suggestion, resources)
        main_path.write_text(main_content)
        generated["main.tf"] = main_path

        # Generate variables.tf
        variables_path = module_dir / "variables.tf"
        variables_content = self._generate_variables_tf(suggestion, resources)
        variables_path.write_text(variables_content)
        generated["variables.tf"] = variables_path

        # Generate outputs.tf
        outputs_path = module_dir / "outputs.tf"
        outputs_content = self._generate_outputs_tf(suggestion, resources)
        outputs_path.write_text(outputs_content)
        generated["outputs.tf"] = outputs_path

        logger.info(f"Generated module: {suggestion.module_name}")
        return generated

    def _generate_main_tf(
        self,
        suggestion: ModuleSuggestion,
        resources: dict[str, ResourceNode],
    ) -> str:
        """Generate main.tf content for module."""
        lines = [
            "# ═══════════════════════════════════════════════════════════════════════════════",
            f"# Module: {suggestion.module_name}",
            f"# Description: {suggestion.description}",
            "# ═══════════════════════════════════════════════════════════════════════════════",
            "#",
            "# Auto-generated by RepliMap",
            "# This module extracts related resources for better organization",
            "#",
            "# ═══════════════════════════════════════════════════════════════════════════════",
            "",
        ]

        # Add resource blocks (simplified - actual implementation would render full HCL)
        all_ids = [suggestion.anchor_resource] + suggestion.member_resources

        for resource_id in all_ids:
            if resource_id in resources:
                resource = resources[resource_id]
                lines.extend(
                    [
                        f"# Resource: {resource_id}",
                        f'resource "{resource.resource_type}" "{resource.terraform_name}" {{',
                        "  # Configuration extracted from AWS",
                        "  # See full resource definition in terraform plan",
                        "}",
                        "",
                    ]
                )

        return "\n".join(lines)

    def _generate_variables_tf(
        self,
        suggestion: ModuleSuggestion,
        resources: dict[str, ResourceNode],
    ) -> str:
        """Generate variables.tf content for module."""
        lines = [
            "# ═══════════════════════════════════════════════════════════════════════════════",
            f"# Variables for module: {suggestion.module_name}",
            "# ═══════════════════════════════════════════════════════════════════════════════",
            "",
        ]

        # Common variables based on module type
        if suggestion.module_type == "vpc":
            lines.extend(
                [
                    'variable "vpc_cidr" {',
                    '  description = "CIDR block for the VPC"',
                    "  type        = string",
                    "}",
                    "",
                    'variable "environment" {',
                    '  description = "Environment name"',
                    "  type        = string",
                    '  default     = "production"',
                    "}",
                    "",
                ]
            )
        elif suggestion.module_type == "security":
            lines.extend(
                [
                    'variable "vpc_id" {',
                    '  description = "VPC ID for security groups"',
                    "  type        = string",
                    "}",
                    "",
                ]
            )

        return "\n".join(lines)

    def _generate_outputs_tf(
        self,
        suggestion: ModuleSuggestion,
        resources: dict[str, ResourceNode],
    ) -> str:
        """Generate outputs.tf content for module."""
        lines = [
            "# ═══════════════════════════════════════════════════════════════════════════════",
            f"# Outputs for module: {suggestion.module_name}",
            "# ═══════════════════════════════════════════════════════════════════════════════",
            "",
        ]

        # Add outputs based on module type
        if suggestion.module_type == "vpc":
            lines.extend(
                [
                    'output "vpc_id" {',
                    '  description = "The VPC ID"',
                    "  value       = aws_vpc.this.id",
                    "}",
                    "",
                    'output "subnet_ids" {',
                    '  description = "List of subnet IDs"',
                    "  value       = aws_subnet.this[*].id",
                    "}",
                    "",
                ]
            )
        elif suggestion.module_type == "alb":
            lines.extend(
                [
                    'output "lb_arn" {',
                    '  description = "The ALB ARN"',
                    "  value       = aws_lb.this.arn",
                    "}",
                    "",
                    'output "lb_dns_name" {',
                    '  description = "The ALB DNS name"',
                    "  value       = aws_lb.this.dns_name",
                    "}",
                    "",
                ]
            )

        return "\n".join(lines)

    def generate_module_call(
        self,
        suggestion: ModuleSuggestion,
    ) -> str:
        """
        Generate the module call block for root configuration.

        Args:
            suggestion: The module suggestion

        Returns:
            HCL module call block
        """
        lines = [
            f'module "{suggestion.module_name}" {{',
            f'  source = "./modules/{suggestion.module_name}"',
            "",
            "  # Pass required variables",
        ]

        # Add variable assignments based on module type
        if suggestion.module_type == "vpc":
            lines.extend(
                [
                    '  vpc_cidr    = "10.0.0.0/16"  # TODO: Replace with actual CIDR',
                    '  environment = "production"',
                ]
            )
        elif suggestion.module_type == "security":
            lines.append("  vpc_id = module.vpc.vpc_id  # TODO: Adjust reference")

        lines.append("}")

        return "\n".join(lines)

    def generate_moved_blocks(
        self,
        suggestion: ModuleSuggestion,
    ) -> list[str]:
        """
        Generate moved blocks for migrating resources into module.

        Args:
            suggestion: The module suggestion

        Returns:
            List of HCL moved block strings
        """
        blocks: list[str] = []

        for _aws_id, address in suggestion.resource_addresses.items():
            # Parse resource type and name from address
            parts = address.split(".")
            if len(parts) >= 2:
                resource_type = parts[0]
                old_name = parts[1]

                # Determine new name in module (simplified)
                new_name = (
                    "this" if old_name == suggestion.anchor_resource else old_name
                )

                block = f"""moved {{
  from = {address}
  to   = module.{suggestion.module_name}.{resource_type}.{new_name}
}}"""
                blocks.append(block)

        return blocks

    def generate_moved_file(
        self,
        suggestions: list[ModuleSuggestion],
        output_path: Path,
    ) -> None:
        """
        Generate module-moves.tf file for all suggestions.

        Args:
            suggestions: List of module suggestions
            output_path: Path to write the file
        """
        if not suggestions:
            return

        lines = [
            "# ═══════════════════════════════════════════════════════════════════════════════",
            "# Auto-generated by RepliMap",
            "# These blocks move resources INTO local modules",
            "# ═══════════════════════════════════════════════════════════════════════════════",
            "#",
            "# Requires Terraform 1.1+",
            "#",
            "# After applying, resources will be organized into local modules",
            "# while maintaining their AWS state.",
            "#",
            "# ═══════════════════════════════════════════════════════════════════════════════",
            "",
        ]

        for suggestion in suggestions:
            lines.append(f"# Module: {suggestion.module_name}")
            lines.append(f"# {suggestion.description}")
            lines.append("")

            moved_blocks = self.generate_moved_blocks(suggestion)
            for block in moved_blocks:
                lines.append(block)
                lines.append("")

        output_path.write_text("\n".join(lines))
        logger.info(f"Wrote module-moves.tf: {len(suggestions)} modules")
