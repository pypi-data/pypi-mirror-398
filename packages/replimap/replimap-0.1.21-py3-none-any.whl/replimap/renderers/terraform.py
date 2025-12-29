"""
Terraform Renderer for RepliMap.

Converts the resource graph to Terraform HCL files using Jinja2 templates.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from jinja2 import Environment, FileSystemLoader, select_autoescape

from replimap.core.models import ResourceType
from replimap.core.naming import get_variable_name_for_resource, sanitize_name

if TYPE_CHECKING:
    from replimap.core import GraphEngine


logger = logging.getLogger(__name__)

# Template directory relative to this file (inside package)
TEMPLATE_DIR = Path(__file__).parent.parent / "templates"


class TerraformRenderer:
    """
    Renders the resource graph to Terraform HCL files.

    Output structure:
    - vpc.tf: VPCs and Subnets
    - security_groups.tf: Security Groups
    - ec2.tf: EC2 Instances
    - rds.tf: RDS Instances and DB Subnet Groups
    - s3.tf: S3 Buckets
    - variables.tf: Extracted variables
    - outputs.tf: Useful outputs
    """

    # Mapping of resource types to output files
    FILE_MAPPING = {
        # Phase 1 (MVP)
        ResourceType.VPC: "vpc.tf",
        ResourceType.SUBNET: "vpc.tf",
        ResourceType.SECURITY_GROUP: "security_groups.tf",
        ResourceType.EC2_INSTANCE: "ec2.tf",
        ResourceType.S3_BUCKET: "s3.tf",
        ResourceType.RDS_INSTANCE: "rds.tf",
        ResourceType.DB_SUBNET_GROUP: "rds.tf",
        # Phase 2 - Networking
        ResourceType.ROUTE_TABLE: "networking.tf",
        ResourceType.INTERNET_GATEWAY: "networking.tf",
        ResourceType.NAT_GATEWAY: "networking.tf",
        ResourceType.VPC_ENDPOINT: "networking.tf",
        # Phase 2 - Compute
        ResourceType.LAUNCH_TEMPLATE: "compute.tf",
        ResourceType.AUTOSCALING_GROUP: "compute.tf",
        ResourceType.LB: "alb.tf",
        ResourceType.LB_LISTENER: "alb.tf",
        ResourceType.LB_TARGET_GROUP: "alb.tf",
        # Phase 2 - Database
        ResourceType.DB_PARAMETER_GROUP: "rds.tf",
        ResourceType.ELASTICACHE_CLUSTER: "elasticache.tf",
        ResourceType.ELASTICACHE_SUBNET_GROUP: "elasticache.tf",
        # Phase 2 - Storage/Messaging
        ResourceType.EBS_VOLUME: "storage.tf",
        ResourceType.S3_BUCKET_POLICY: "s3.tf",
        ResourceType.SQS_QUEUE: "messaging.tf",
        ResourceType.SNS_TOPIC: "messaging.tf",
    }

    # Mapping of resource types to template files
    TEMPLATE_MAPPING = {
        # Phase 1 (MVP)
        ResourceType.VPC: "vpc.tf.j2",
        ResourceType.SUBNET: "subnet.tf.j2",
        ResourceType.SECURITY_GROUP: "security_group.tf.j2",
        ResourceType.EC2_INSTANCE: "ec2_instance.tf.j2",
        ResourceType.S3_BUCKET: "s3_bucket.tf.j2",
        ResourceType.RDS_INSTANCE: "rds_instance.tf.j2",
        ResourceType.DB_SUBNET_GROUP: "db_subnet_group.tf.j2",
        # Phase 2 - Networking
        ResourceType.ROUTE_TABLE: "route_table.tf.j2",
        ResourceType.INTERNET_GATEWAY: "internet_gateway.tf.j2",
        ResourceType.NAT_GATEWAY: "nat_gateway.tf.j2",
        ResourceType.VPC_ENDPOINT: "vpc_endpoint.tf.j2",
        # Phase 2 - Compute
        ResourceType.LAUNCH_TEMPLATE: "launch_template.tf.j2",
        ResourceType.AUTOSCALING_GROUP: "autoscaling_group.tf.j2",
        ResourceType.LB: "lb.tf.j2",
        ResourceType.LB_LISTENER: "lb_listener.tf.j2",
        ResourceType.LB_TARGET_GROUP: "lb_target_group.tf.j2",
        # Phase 2 - Database
        ResourceType.DB_PARAMETER_GROUP: "db_parameter_group.tf.j2",
        ResourceType.ELASTICACHE_CLUSTER: "elasticache_cluster.tf.j2",
        ResourceType.ELASTICACHE_SUBNET_GROUP: "elasticache_subnet_group.tf.j2",
        # Phase 2 - Storage/Messaging
        ResourceType.EBS_VOLUME: "ebs_volume.tf.j2",
        ResourceType.S3_BUCKET_POLICY: "s3_bucket_policy.tf.j2",
        ResourceType.SQS_QUEUE: "sqs_queue.tf.j2",
        ResourceType.SNS_TOPIC: "sns_topic.tf.j2",
    }

    def __init__(self, template_dir: Path | None = None) -> None:
        """
        Initialize the renderer.

        Args:
            template_dir: Path to Jinja2 templates (defaults to built-in)
        """
        self.template_dir = template_dir or TEMPLATE_DIR

        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Add custom filters
        self.env.filters["terraform_name"] = self._terraform_name_filter
        self.env.filters["quote"] = self._quote_filter
        self.env.filters["quote_key"] = self._quote_key_filter
        self.env.filters["tf_ref"] = self._tf_ref_filter
        self.env.filters["d"] = self._default_if_none_filter  # Short alias
        self.env.filters["sanitize"] = sanitize_name  # For variable name sanitization

        # Add custom tests
        self.env.tests["tf_ref"] = self._is_tf_ref_test

        # Track used terraform names for uniqueness
        self._used_names: dict[str, set[str]] = {}

    def render(self, graph: GraphEngine, output_dir: Path) -> dict[str, Path]:
        """
        Render the graph to Terraform files.

        Args:
            graph: The GraphEngine containing resources
            output_dir: Directory to write .tf files

        Returns:
            Dictionary mapping filenames to their paths
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Rendering Terraform to {output_dir}")

        # Ensure unique terraform names before rendering
        self._ensure_unique_names(graph)

        # Group resources by output file
        file_contents: dict[str, list[str]] = {}

        # Use safe dependency order to handle cycles (e.g., mutual SG references)
        for resource in graph.get_safe_dependency_order():
            template_name = self.TEMPLATE_MAPPING.get(resource.resource_type)
            output_file = self.FILE_MAPPING.get(resource.resource_type)

            if not template_name or not output_file:
                logger.warning(
                    f"No template for resource type: {resource.resource_type}"
                )
                continue

            try:
                template = self.env.get_template(template_name)

                # Pre-calculate variable names for Right-Sizer compatibility
                # This ensures templates use sanitized names (underscores) matching variables.tf
                resource_type_str = (
                    resource.resource_type.value
                    if hasattr(resource.resource_type, "value")
                    else str(resource.resource_type)
                )
                variable_names = get_variable_name_for_resource(
                    resource_type_str, resource.terraform_name
                )

                rendered = template.render(
                    resource=resource,
                    graph=graph,
                    variable_names=variable_names,
                )

                if output_file not in file_contents:
                    file_contents[output_file] = []
                file_contents[output_file].append(rendered)

            except Exception as e:
                logger.error(f"Error rendering {resource.id}: {e}")

        # Write files
        written_files: dict[str, Path] = {}
        for filename, contents in file_contents.items():
            file_path = output_dir / filename
            with open(file_path, "w") as f:
                f.write("\n\n".join(contents))
            written_files[filename] = file_path
            logger.info(f"Wrote {filename} ({len(contents)} resources)")

        # Generate supporting Terraform files
        self._generate_versions(output_dir, written_files)
        self._generate_providers(output_dir, written_files)
        self._generate_data_sources(output_dir, written_files)
        self._generate_variables(graph, output_dir, written_files)
        self._generate_outputs(graph, output_dir, written_files)

        # Run terraform fmt to ensure consistent formatting
        self._run_terraform_fmt(output_dir)

        return written_files

    def _ensure_unique_names(self, graph: GraphEngine) -> None:
        """
        Ensure all resources have unique terraform names within their type.

        If multiple resources of the same type have the same terraform_name,
        append a numeric suffix to make them unique.
        """
        # Group resources by type and terraform_name
        type_names: dict[str, dict[str, list[object]]] = {}

        for resource in graph.iter_resources():
            resource_type = str(resource.resource_type)
            if resource_type not in type_names:
                type_names[resource_type] = {}

            name = resource.terraform_name or "unnamed"
            if name not in type_names[resource_type]:
                type_names[resource_type][name] = []
            type_names[resource_type][name].append(resource)

        # Resolve duplicates using numeric suffixes
        for resource_type, names in type_names.items():
            for name, resources in names.items():
                if len(resources) > 1:
                    logger.warning(
                        f"Found {len(resources)} {resource_type} resources "
                        f"with terraform_name '{name}', making unique"
                    )
                    # Track all names used to ensure uniqueness
                    used_names: set[str] = {name}
                    for i, resource in enumerate(resources):
                        if i > 0:
                            # Use numeric suffix to guarantee uniqueness
                            suffix_num = i
                            new_name = f"{name}_{suffix_num}"
                            # Ensure the new name isn't already used
                            while new_name in used_names:
                                suffix_num += 1
                                new_name = f"{name}_{suffix_num}"
                            used_names.add(new_name)
                            resource.terraform_name = new_name
                            logger.info(
                                f"Renamed {resource.id} from '{name}' to '{new_name}'"
                            )

    def preview(self, graph: GraphEngine) -> dict[str, list[str]]:
        """
        Preview what would be generated without writing files.

        Args:
            graph: The GraphEngine containing resources

        Returns:
            Dictionary mapping filenames to lists of resource IDs
        """
        preview: dict[str, list[str]] = {}

        for resource in graph.iter_resources():
            output_file = self.FILE_MAPPING.get(resource.resource_type)
            if output_file:
                if output_file not in preview:
                    preview[output_file] = []
                preview[output_file].append(resource.id)

        return preview

    def _generate_versions(
        self,
        output_dir: Path,
        written_files: dict[str, Path],
    ) -> None:
        """Generate versions.tf with Terraform and provider version constraints."""
        versions = """# Generated by RepliMap
# Terraform and provider version constraints

terraform {
  required_version = ">= 1.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 4.0.0"
    }
  }
}
"""
        file_path = output_dir / "versions.tf"
        with open(file_path, "w") as f:
            f.write(versions)
        written_files["versions.tf"] = file_path
        logger.info("Wrote versions.tf")

    def _generate_providers(
        self,
        output_dir: Path,
        written_files: dict[str, Path],
    ) -> None:
        """Generate providers.tf with AWS provider configuration."""
        providers = """# Generated by RepliMap
# AWS Provider Configuration

provider "aws" {
  region = var.aws_region

  # Assume role for cross-account access (optional)
  # assume_role {
  #   role_arn = "arn:aws:iam::${var.aws_account_id}:role/RepliMapDeployRole"
  # }

  default_tags {
    tags = merge(var.common_tags, {
      ManagedBy   = "replimap"
      Environment = var.environment
    })
  }
}
"""
        file_path = output_dir / "providers.tf"
        with open(file_path, "w") as f:
            f.write(providers)
        written_files["providers.tf"] = file_path
        logger.info("Wrote providers.tf")

    def _generate_data_sources(
        self,
        output_dir: Path,
        written_files: dict[str, Path],
    ) -> None:
        """Generate data.tf with useful data sources for dynamic values."""
        data_sources = """# Generated by RepliMap
# Data sources for dynamic values (account ID, region, availability zones, etc.)

# Get current AWS account ID
data "aws_caller_identity" "current" {}

# Get current AWS region
data "aws_region" "current" {}

# Get available availability zones in the target region
data "aws_availability_zones" "available" {
  state = "available"
}

# Locals for commonly used values
locals {
  account_id = data.aws_caller_identity.current.account_id
  region     = data.aws_region.current.id

  # Availability zones - use these for cross-region cloning
  # Maps index to AZ: local.azs[0] = first AZ (e.g., us-east-1a -> ap-southeast-2a)
  azs = data.aws_availability_zones.available.names

  # Helper to map AZ suffix (a, b, c) to target region AZ
  # Usage: local.az_map["a"] returns first AZ in target region
  az_map = {
    "a" = local.azs[0]
    "b" = length(local.azs) > 1 ? local.azs[1] : local.azs[0]
    "c" = length(local.azs) > 2 ? local.azs[2] : local.azs[0]
    "d" = length(local.azs) > 3 ? local.azs[3] : local.azs[0]
    "e" = length(local.azs) > 4 ? local.azs[4] : local.azs[0]
    "f" = length(local.azs) > 5 ? local.azs[5] : local.azs[0]
  }
}

# Example usage in policies:
# "Resource": "arn:aws:sqs:${local.region}:${local.account_id}:queue-name"
#
# For availability zones, use local.az_map with the original AZ suffix:
# Original: us-east-1a -> Use: local.az_map["a"]
"""
        file_path = output_dir / "data.tf"
        with open(file_path, "w") as f:
            f.write(data_sources)
        written_files["data.tf"] = file_path
        logger.info("Wrote data.tf")

    def _generate_variables(
        self,
        graph: GraphEngine,
        output_dir: Path,
        written_files: dict[str, Path],
    ) -> None:
        """Generate variables.tf with common and resource-specific variables."""
        lines = [
            "# Generated by RepliMap",
            "# Common variables for the replicated environment",
            "",
            'variable "environment" {',
            '  description = "Environment name (e.g., staging, dev)"',
            "  type        = string",
            '  default     = "staging"',
            "}",
            "",
            'variable "aws_account_id" {',
            '  description = "Target AWS account ID"',
            "  type        = string",
            "}",
            "",
            'variable "aws_region" {',
            '  description = "AWS region for deployment"',
            "  type        = string",
            "}",
            "",
            'variable "common_tags" {',
            '  description = "Common tags to apply to all resources"',
            "  type        = map(string)",
            "  default     = {}",
            "}",
        ]

        # Add AMI variable for EC2 instances
        ec2_instances = graph.get_resources_by_type(ResourceType.EC2_INSTANCE)
        if ec2_instances:
            lines.extend(
                [
                    "",
                    "# EC2 AMI Variable",
                    "# NOTE: AMI IDs are region-specific. Update for your target region.",
                ]
            )
            # Get original AMIs for reference
            original_amis = [ec2.config.get("ami", "unknown") for ec2 in ec2_instances]
            lines.extend(
                [
                    "",
                    'variable "ami_id" {',
                    '  description = "AMI ID for EC2 instances"',
                    "  type        = string",
                    f"  # Original AMIs: {', '.join(set(original_amis))}",
                    "}",
                ]
            )

            # Add per-instance instance_type variables for Right-Sizer compatibility
            lines.extend(
                [
                    "",
                    "# ─────────────────────────────────────────────────────────────────────────────",
                    "# EC2 Instance Type Variables (for Right-Sizer compatibility)",
                    "# Override these in terraform.tfvars or right-sizer.auto.tfvars",
                    "# ─────────────────────────────────────────────────────────────────────────────",
                ]
            )
            for ec2 in ec2_instances:
                tf_name = sanitize_name(ec2.terraform_name)
                var_name = f"aws_instance_{tf_name}_instance_type"
                original_type = ec2.config.get("instance_type", "t3.micro")
                ec2_name = ec2.original_name or ec2.terraform_name
                lines.extend(
                    [
                        "",
                        f'variable "{var_name}" {{',
                        f'  description = "Instance type for EC2 {ec2_name}"',
                        "  type        = string",
                        f'  default     = "{original_type}"',
                        "}",
                    ]
                )

        # Add AMI variables for Launch Templates
        launch_templates = graph.get_resources_by_type(ResourceType.LAUNCH_TEMPLATE)
        if launch_templates:
            lines.extend(
                [
                    "",
                    "# Launch Template AMI Variables",
                    "# NOTE: AMI IDs are region-specific. Update for your target region.",
                ]
            )
            for lt in launch_templates:
                tf_name = sanitize_name(lt.terraform_name)
                var_name = f"ami_id_{tf_name}"
                original_ami = lt.config.get("image_id", "unknown")
                lines.extend(
                    [
                        "",
                        f'variable "{var_name}" {{',
                        f'  description = "AMI ID for Launch Template {lt.original_name}"',
                        "  type        = string",
                        f"  # Original AMI: {original_ami}",
                        "}",
                    ]
                )

            # Add per-template instance_type variables for Right-Sizer compatibility
            lines.extend(
                [
                    "",
                    "# ─────────────────────────────────────────────────────────────────────────────",
                    "# Launch Template Instance Type Variables (for Right-Sizer compatibility)",
                    "# Override these in terraform.tfvars or right-sizer.auto.tfvars",
                    "# ─────────────────────────────────────────────────────────────────────────────",
                ]
            )
            for lt in launch_templates:
                if lt.config.get("instance_type"):
                    tf_name = sanitize_name(lt.terraform_name)
                    var_name = f"aws_launch_template_{tf_name}_instance_type"
                    original_type = lt.config.get("instance_type", "t3.micro")
                    lt_name = lt.original_name or lt.terraform_name
                    lines.extend(
                        [
                            "",
                            f'variable "{var_name}" {{',
                            f'  description = "Instance type for Launch Template {lt_name}"',
                            "  type        = string",
                            f'  default     = "{original_type}"',
                            "}",
                        ]
                    )

        # Add key_name variable if any EC2/Launch Templates use keys
        has_key_name = any(ec2.config.get("key_name") for ec2 in ec2_instances) or any(
            lt.config.get("key_name") for lt in launch_templates
        )
        if has_key_name:
            lines.extend(
                [
                    "",
                    "# SSH Key Pair Variable",
                    'variable "key_name" {',
                    '  description = "Name of the SSH key pair for EC2 instances"',
                    "  type        = string",
                    '  default     = ""',
                    "}",
                ]
            )

        # Add ACM certificate variable if any listeners use certificates
        lb_listeners = graph.get_resources_by_type(ResourceType.LB_LISTENER)
        has_certificate = any(
            listener.config.get("certificate_arn") for listener in lb_listeners
        )
        if has_certificate:
            original_certs = [
                listener.config.get("certificate_arn")
                for listener in lb_listeners
                if listener.config.get("certificate_arn")
            ]
            lines.extend(
                [
                    "",
                    "# ACM Certificate Variable",
                    "# NOTE: Certificate must match your staging domain",
                    'variable "acm_certificate_arn" {',
                    '  description = "ARN of ACM certificate for HTTPS listeners"',
                    "  type        = string",
                    f"  # Original certificate(s): {', '.join(set(original_certs))}",
                    "}",
                ]
            )

        # Add RDS password variables
        rds_instances = graph.get_resources_by_type(ResourceType.RDS_INSTANCE)
        if rds_instances:
            lines.extend(
                [
                    "",
                    "# RDS Database Password Variables",
                    "# IMPORTANT: Change the default before applying!",
                ]
            )
            for rds in rds_instances:
                tf_name = sanitize_name(rds.terraform_name)
                var_name = f"db_password_{tf_name}"
                lines.extend(
                    [
                        "",
                        f'variable "{var_name}" {{',
                        f'  description = "Password for RDS instance {rds.id}"',
                        "  type        = string",
                        "  sensitive   = true",
                        '  default     = "CHANGE-ME-BEFORE-APPLY"  # Placeholder for plan',
                        "}",
                    ]
                )

            # Add per-RDS instance configuration variables for Right-Sizer compatibility
            lines.extend(
                [
                    "",
                    "# ─────────────────────────────────────────────────────────────────────────────",
                    "# RDS Instance Configuration Variables (for Right-Sizer compatibility)",
                    "# Override these in terraform.tfvars or right-sizer.auto.tfvars",
                    "# ─────────────────────────────────────────────────────────────────────────────",
                ]
            )
            for rds in rds_instances:
                tf_name = sanitize_name(rds.terraform_name)
                rds_name = rds.original_name or rds.terraform_name

                # instance_class variable
                var_name = f"aws_db_instance_{tf_name}_instance_class"
                original_class = rds.config.get("instance_class", "db.t3.micro")
                lines.extend(
                    [
                        "",
                        f'variable "{var_name}" {{',
                        f'  description = "Instance class for RDS {rds_name}"',
                        "  type        = string",
                        f'  default     = "{original_class}"',
                        "}",
                    ]
                )

                # storage_type variable
                var_name = f"aws_db_instance_{tf_name}_storage_type"
                original_storage = rds.config.get("storage_type", "gp2")
                lines.extend(
                    [
                        "",
                        f'variable "{var_name}" {{',
                        f'  description = "Storage type for RDS {rds_name}"',
                        "  type        = string",
                        f'  default     = "{original_storage}"',
                        "}",
                    ]
                )

                # allocated_storage variable
                var_name = f"aws_db_instance_{tf_name}_allocated_storage"
                original_size = rds.config.get("allocated_storage", 20)
                lines.extend(
                    [
                        "",
                        f'variable "{var_name}" {{',
                        f'  description = "Allocated storage (GB) for RDS {rds_name}"',
                        "  type        = number",
                        f"  default     = {original_size}",
                        "}",
                    ]
                )

                # multi_az variable
                var_name = f"aws_db_instance_{tf_name}_multi_az"
                original_multi_az = rds.config.get("multi_az", False)
                lines.extend(
                    [
                        "",
                        f'variable "{var_name}" {{',
                        f'  description = "Enable Multi-AZ for RDS {rds_name}"',
                        "  type        = bool",
                        f"  default     = {str(original_multi_az).lower()}",
                        "}",
                    ]
                )

        # Add RDS snapshot variables for instances that have snapshots
        rds_with_snapshots = [
            rds for rds in rds_instances if rds.config.get("snapshot_identifier")
        ]
        if rds_with_snapshots:
            lines.extend(
                [
                    "",
                    "# RDS Snapshot Variables (optional - leave empty to create fresh DB)",
                ]
            )
            for rds in rds_with_snapshots:
                tf_name = sanitize_name(rds.terraform_name)
                var_name = f"db_snapshot_{tf_name}"
                original_snapshot = rds.config.get("snapshot_identifier", "")
                lines.extend(
                    [
                        "",
                        f'variable "{var_name}" {{',
                        f'  description = "Snapshot ID to restore RDS instance {rds.id} from (leave empty for fresh DB)"',
                        "  type        = string",
                        '  default     = ""',
                        f"  # Original snapshot: {original_snapshot}",
                        "}",
                    ]
                )

        # Add ElastiCache variables for Right-Sizer compatibility
        elasticache_clusters = graph.get_resources_by_type(
            ResourceType.ELASTICACHE_CLUSTER
        )
        if elasticache_clusters:
            lines.extend(
                [
                    "",
                    "# ─────────────────────────────────────────────────────────────────────────────",
                    "# ElastiCache Configuration Variables (for Right-Sizer compatibility)",
                    "# Override these in terraform.tfvars or right-sizer.auto.tfvars",
                    "# ─────────────────────────────────────────────────────────────────────────────",
                ]
            )
            for cache in elasticache_clusters:
                tf_name = sanitize_name(cache.terraform_name)
                cache_name = cache.original_name or cache.terraform_name

                # node_type variable
                var_name = f"aws_elasticache_cluster_{tf_name}_node_type"
                original_type = cache.config.get("node_type", "cache.t3.micro")
                lines.extend(
                    [
                        "",
                        f'variable "{var_name}" {{',
                        f'  description = "Node type for ElastiCache {cache_name}"',
                        "  type        = string",
                        f'  default     = "{original_type}"',
                        "}",
                    ]
                )

                # num_cache_nodes variable
                var_name = f"aws_elasticache_cluster_{tf_name}_num_cache_nodes"
                original_nodes = cache.config.get("num_cache_nodes", 1)
                lines.extend(
                    [
                        "",
                        f'variable "{var_name}" {{',
                        f'  description = "Number of cache nodes for ElastiCache {cache_name}"',
                        "  type        = number",
                        f"  default     = {original_nodes}",
                        "}",
                    ]
                )

        lines.append("")  # Trailing newline
        file_path = output_dir / "variables.tf"
        with open(file_path, "w") as f:
            f.write("\n".join(lines))
        written_files["variables.tf"] = file_path
        logger.info("Wrote variables.tf")

    def _generate_outputs(
        self,
        graph: GraphEngine,
        output_dir: Path,
        written_files: dict[str, Path],
    ) -> None:
        """Generate outputs.tf with useful outputs."""
        outputs_lines = [
            "# Generated by RepliMap",
            "# Useful outputs for reference",
            "",
        ]

        # Add VPC outputs
        vpcs = graph.get_resources_by_type(ResourceType.VPC)
        for vpc in vpcs:
            outputs_lines.append(f'''output "{vpc.terraform_name}_id" {{
  description = "ID of VPC {vpc.original_name}"
  value       = aws_vpc.{vpc.terraform_name}.id
}}
''')

        # Add RDS endpoint outputs
        rds_instances = graph.get_resources_by_type(ResourceType.RDS_INSTANCE)
        for rds in rds_instances:
            outputs_lines.append(f'''output "{rds.terraform_name}_endpoint" {{
  description = "Endpoint for RDS instance {rds.original_name}"
  value       = aws_db_instance.{rds.terraform_name}.endpoint
}}
''')

        # Add Load Balancer DNS outputs
        lbs = graph.get_resources_by_type(ResourceType.LB)
        for lb in lbs:
            outputs_lines.append(f'''output "{lb.terraform_name}_dns_name" {{
  description = "DNS name for Load Balancer {lb.original_name}"
  value       = aws_lb.{lb.terraform_name}.dns_name
}}
''')

        file_path = output_dir / "outputs.tf"
        with open(file_path, "w") as f:
            f.write("\n".join(outputs_lines))
        written_files["outputs.tf"] = file_path
        logger.info("Wrote outputs.tf")

        # Generate terraform.tfvars.example
        self._generate_tfvars_example(graph, output_dir, written_files)

    def _generate_tfvars_example(
        self,
        graph: GraphEngine,
        output_dir: Path,
        written_files: dict[str, Path],
    ) -> None:
        """Generate terraform.tfvars.example with sample variable values."""
        lines = [
            "# =============================================================================",
            "# Generated by RepliMap - Terraform Variables",
            "# =============================================================================",
            "#",
            "# Copy this file to terraform.tfvars and update the values for your environment.",
            "#",
            "# Usage:",
            "#   cp terraform.tfvars.example terraform.tfvars",
            "#   terraform init",
            "#   terraform plan -var-file=terraform.tfvars",
            "#",
            "# =============================================================================",
            "",
            "# -----------------------------------------------------------------------------",
            "# ENVIRONMENT & ACCOUNT CONFIGURATION",
            "# -----------------------------------------------------------------------------",
            "",
            "# Environment name - used in resource naming and tags",
            'environment = "staging"',
            "",
            "# Target AWS account ID",
            '# Run: aws sts get-caller-identity --query "Account" --output text',
            'aws_account_id = "123456789012"',
            "",
            "# Target AWS region",
            "# Run: aws configure get region",
            'aws_region = "ap-southeast-2"',
            "",
            "# Common tags applied to all resources",
            "common_tags = {",
            '  Project   = "replimap-staging"',
            '  Team      = "platform"',
            '  ManagedBy = "terraform"',
            "}",
        ]

        # Gather all EC2 instances
        ec2_instances = graph.get_resources_by_type(ResourceType.EC2_INSTANCE)
        if ec2_instances:
            # Get original AMIs for reference
            original_amis = list(
                {ec2.config.get("ami", "unknown") for ec2 in ec2_instances}
            )
            lines.extend(
                [
                    "",
                    "# -----------------------------------------------------------------------------",
                    "# COMPUTE - EC2 INSTANCES",
                    "# -----------------------------------------------------------------------------",
                    "#",
                    "# IMPORTANT: AMI IDs are region-specific! Find one for your target region.",
                    "#",
                    "# Amazon Linux 2 (most common):",
                    "#   aws ec2 describe-images --owners amazon \\",
                    '#     --filters "Name=name,Values=amzn2-ami-hvm-*-x86_64-gp2" \\',
                    "#     --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' --output text",
                    "#",
                    "# Ubuntu 22.04 LTS:",
                    "#   aws ec2 describe-images --owners 099720109477 \\",
                    '#     --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" \\',
                    "#     --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' --output text",
                    "#",
                    f"# Original AMI(s) in source environment: {', '.join(original_amis)}",
                    "",
                    'ami_id = "ami-0123456789abcdef0"  # CHANGE: Use AMI for your region',
                ]
            )

        # Gather all Launch Templates
        launch_templates = graph.get_resources_by_type(ResourceType.LAUNCH_TEMPLATE)
        if launch_templates:
            lines.extend(
                [
                    "",
                    "# -----------------------------------------------------------------------------",
                    "# COMPUTE - LAUNCH TEMPLATES",
                    "# -----------------------------------------------------------------------------",
                    "#",
                    "# Each Launch Template may need its own AMI ID.",
                    "# Use the same AWS CLI commands above to find appropriate AMIs.",
                    "",
                ]
            )
            for lt in launch_templates:
                tf_name = sanitize_name(lt.terraform_name)
                var_name = f"ami_id_{tf_name}"
                original_ami = lt.config.get("image_id", "unknown")
                lt_name = lt.original_name or lt.terraform_name
                lines.append(
                    f"# Launch Template: {lt_name} (original AMI: {original_ami})"
                )
                lines.append(f'{var_name} = "ami-0123456789abcdef0"')
                lines.append("")

        # Check for SSH key requirement
        has_key_name = any(ec2.config.get("key_name") for ec2 in ec2_instances) or any(
            lt.config.get("key_name") for lt in launch_templates
        )
        if has_key_name:
            lines.extend(
                [
                    "# -----------------------------------------------------------------------------",
                    "# SSH KEY PAIR",
                    "# -----------------------------------------------------------------------------",
                    "#",
                    '# List existing keys: aws ec2 describe-key-pairs --query "KeyPairs[*].KeyName"',
                    "# Create new key: aws ec2 create-key-pair --key-name staging-key \\",
                    "#   --query 'KeyMaterial' --output text > staging-key.pem",
                    "#",
                    "# Leave empty if not using SSH keys (e.g., SSM Session Manager only)",
                    "",
                    'key_name = ""',
                    "",
                ]
            )

        # Check for ACM certificate requirement
        lb_listeners = graph.get_resources_by_type(ResourceType.LB_LISTENER)
        has_certificate = any(
            listener.config.get("certificate_arn") for listener in lb_listeners
        )
        if has_certificate:
            original_certs = list(
                {
                    listener.config.get("certificate_arn")
                    for listener in lb_listeners
                    if listener.config.get("certificate_arn")
                }
            )
            lines.extend(
                [
                    "# -----------------------------------------------------------------------------",
                    "# TLS/SSL - ACM CERTIFICATE",
                    "# -----------------------------------------------------------------------------",
                    "#",
                    '# List certificates: aws acm list-certificates --query "CertificateSummaryList[*].[DomainName,CertificateArn]" --output table',
                    "#",
                    "# Request new certificate:",
                    "#   aws acm request-certificate --domain-name staging.example.com \\",
                    "#     --validation-method DNS --region <your-region>",
                    "#",
                    f"# Original certificate(s): {', '.join(original_certs)}",
                    "#",
                    "# NOTE: Leave empty for HTTP-only testing (HTTPS listeners will fail validation)",
                    "",
                    'acm_certificate_arn = ""',
                    "",
                ]
            )

        # Add RDS password variables
        rds_instances = graph.get_resources_by_type(ResourceType.RDS_INSTANCE)
        if rds_instances:
            lines.extend(
                [
                    "# -----------------------------------------------------------------------------",
                    "# DATABASE - RDS CREDENTIALS",
                    "# -----------------------------------------------------------------------------",
                    "#",
                    "# SECURITY WARNING: Do not commit actual passwords to version control!",
                    "#",
                    "# Alternative methods:",
                    "#   1. Environment variable: export TF_VAR_db_password_<name>=YourPassword",
                    "#   2. Command line: terraform plan -var='db_password_<name>=YourPassword'",
                    "#   3. AWS Secrets Manager (recommended for production)",
                    "#",
                    "# Password requirements:",
                    "#   - At least 8 characters",
                    '#   - Printable ASCII except /, @, ", and space',
                    "",
                ]
            )
            for rds in rds_instances:
                tf_name = sanitize_name(rds.terraform_name)
                var_name = f"db_password_{tf_name}"
                rds_name = rds.original_name or rds.terraform_name
                engine = rds.config.get("engine", "unknown")
                lines.append(f"# RDS: {rds_name} ({engine})")
                lines.append(
                    f'{var_name} = "ChangeMe123!"  # CHANGE: Use a strong password'
                )
                lines.append("")

        # Add RDS snapshot variables if any
        rds_with_snapshots = [
            rds for rds in rds_instances if rds.config.get("snapshot_identifier")
        ]
        if rds_with_snapshots:
            lines.extend(
                [
                    "# -----------------------------------------------------------------------------",
                    "# DATABASE - RDS SNAPSHOTS (Optional)",
                    "# -----------------------------------------------------------------------------",
                    "#",
                    "# Leave empty to create a fresh database, or provide a snapshot identifier",
                    "# to restore from an existing snapshot.",
                    "#",
                    '# List snapshots: aws rds describe-db-snapshots --query "DBSnapshots[*].[DBSnapshotIdentifier,SnapshotCreateTime]" --output table',
                    "",
                ]
            )
            for rds in rds_with_snapshots:
                tf_name = sanitize_name(rds.terraform_name)
                var_name = f"db_snapshot_{tf_name}"
                original_snapshot = rds.config.get("snapshot_identifier", "")
                lines.append(f"# Original snapshot: {original_snapshot}")
                lines.append(f'{var_name} = ""')
                lines.append("")

        # Add footer with testing instructions
        lines.extend(
            [
                "# -----------------------------------------------------------------------------",
                "# TESTING YOUR CONFIGURATION",
                "# -----------------------------------------------------------------------------",
                "#",
                "# 1. Validate syntax:",
                "#    terraform init && terraform validate",
                "#",
                "# 2. Check formatting:",
                "#    terraform fmt -check -recursive",
                "#",
                "# 3. Plan (dry-run):",
                "#    terraform plan -var-file=terraform.tfvars -out=tfplan",
                "#",
                "# 4. Review plan, then apply:",
                "#    terraform apply tfplan",
                "#",
                "# 5. Clean up when done:",
                "#    terraform destroy -var-file=terraform.tfvars",
                "#",
                "# =============================================================================",
                "",
            ]
        )

        file_path = output_dir / "terraform.tfvars.example"
        with open(file_path, "w") as f:
            f.write("\n".join(lines))
        written_files["terraform.tfvars.example"] = file_path
        logger.info("Wrote terraform.tfvars.example")

        # Generate test script
        self._generate_test_script(output_dir, written_files)

    def _generate_test_script(
        self,
        output_dir: Path,
        written_files: dict[str, Path],
    ) -> None:
        """Generate test-terraform.sh script for validating generated Terraform."""
        script = r"""#!/usr/bin/env bash
# =============================================================================
# RepliMap Terraform Test Script
# =============================================================================
#
# Validates generated Terraform configuration through multiple phases:
#   1. terraform fmt -check (formatting)
#   2. terraform init (initialization)
#   3. terraform validate (syntax/semantics)
#   4. terraform plan (optional, requires AWS credentials)
#
# Usage:
#   ./test-terraform.sh                    # Basic validation (no AWS)
#   ./test-terraform.sh --plan             # Full validation including plan
#   ./test-terraform.sh --plan --profile myprofile  # With AWS profile
#
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
RUN_PLAN=false
AWS_PROFILE=""
TFVARS_FILE="terraform.tfvars"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --plan|-p)
            RUN_PLAN=true
            shift
            ;;
        --profile)
            AWS_PROFILE="$2"
            shift 2
            ;;
        --tfvars)
            TFVARS_FILE="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --plan, -p        Run terraform plan (requires AWS credentials)"
            echo "  --profile NAME    AWS profile to use"
            echo "  --tfvars FILE     Terraform variables file (default: terraform.tfvars)"
            echo "  --help, -h        Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Set AWS profile if provided
if [[ -n "$AWS_PROFILE" ]]; then
    export AWS_PROFILE="$AWS_PROFILE"
    echo -e "${BLUE}Using AWS profile: $AWS_PROFILE${NC}"
fi

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}RepliMap Terraform Validation${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# Check terraform is installed
if ! command -v terraform &> /dev/null; then
    echo -e "${RED}ERROR: terraform not found in PATH${NC}"
    echo "Install terraform: https://www.terraform.io/downloads"
    exit 1
fi

# Extract version - handle both compact and pretty-printed JSON
TERRAFORM_VERSION=$(terraform version -json 2>/dev/null | tr -d '[:space:]' | sed 's/.*"terraform_version":"\([^"]*\)".*/\1/')
if [[ -z "$TERRAFORM_VERSION" ]]; then
    TERRAFORM_VERSION=$(terraform version | head -1 | sed 's/Terraform v//')
fi
echo -e "${GREEN}✓${NC} Terraform version: $TERRAFORM_VERSION"
echo ""

# Phase 1: Format Check
echo -e "${BLUE}[1/4] Checking formatting...${NC}"
if terraform fmt -check -recursive > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} All files properly formatted"
else
    echo -e "${YELLOW}!${NC} Some files need formatting. Run: terraform fmt -recursive"
    # Not a fatal error, continue
fi
echo ""

# Phase 2: Initialize
echo -e "${BLUE}[2/4] Initializing Terraform...${NC}"
if terraform init -backend=false > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Terraform initialized successfully"
else
    echo -e "${RED}✗${NC} Terraform init failed"
    terraform init -backend=false
    exit 1
fi
echo ""

# Phase 3: Validate
echo -e "${BLUE}[3/4] Validating configuration...${NC}"
VALIDATE_OUTPUT=$(terraform validate -json 2>&1)

# Check if valid is true using bash pattern matching (more reliable than grep)
if [[ "$VALIDATE_OUTPUT" == *'"valid": true'* ]] || [[ "$VALIDATE_OUTPUT" == *'"valid":true'* ]]; then
    echo -e "${GREEN}✓${NC} Configuration is valid"
else
    echo -e "${RED}✗${NC} Validation failed"
    echo "$VALIDATE_OUTPUT" | python3 -m json.tool 2>/dev/null || echo "$VALIDATE_OUTPUT"
    exit 1
fi
echo ""

# Phase 4: Plan (optional)
if [[ "$RUN_PLAN" == "true" ]]; then
    echo -e "${BLUE}[4/4] Running terraform plan...${NC}"

    # Check if tfvars file exists
    if [[ ! -f "$TFVARS_FILE" ]]; then
        if [[ -f "terraform.tfvars.example" ]]; then
            echo -e "${YELLOW}!${NC} $TFVARS_FILE not found. Creating from example..."
            cp terraform.tfvars.example "$TFVARS_FILE"
            echo -e "${YELLOW}!${NC} Please edit $TFVARS_FILE with real values before running plan"
            exit 1
        else
            echo -e "${RED}✗${NC} No tfvars file found"
            exit 1
        fi
    fi

    # Run plan
    if terraform plan -var-file="$TFVARS_FILE" -out=tfplan -input=false; then
        # Generate human-readable plan output
        terraform show -no-color tfplan > tfplan.txt
        echo ""
        echo -e "${GREEN}✓${NC} Plan completed successfully"
        echo ""
        echo "Plan saved to: tfplan (binary), tfplan.txt (readable)"
        echo "To apply: terraform apply tfplan"
    else
        echo ""
        echo -e "${RED}✗${NC} Plan failed"
        exit 1
    fi
else
    echo -e "${BLUE}[4/4] Skipping terraform plan (use --plan to enable)${NC}"
fi

echo ""
echo -e "${BLUE}=========================================${NC}"
echo -e "${GREEN}All validation checks passed!${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""
echo "Next steps:"
echo "  1. Copy terraform.tfvars.example to terraform.tfvars"
echo "  2. Edit terraform.tfvars with your values"
echo "  3. Run: ./test-terraform.sh --plan"
echo "  4. Review the plan and apply: terraform apply tfplan"
"""
        file_path = output_dir / "test-terraform.sh"
        with open(file_path, "w") as f:
            f.write(script)
        # Make executable
        file_path.chmod(0o755)
        written_files["test-terraform.sh"] = file_path
        logger.info("Wrote test-terraform.sh")

        # Generate Makefile for easier TF management
        self._generate_makefile(output_dir, written_files)

    def _generate_makefile(
        self,
        output_dir: Path,
        written_files: dict[str, Path],
    ) -> None:
        """Generate Makefile for easier Terraform workflow management."""
        makefile = r"""# =============================================================================
# RepliMap Terraform Makefile
# =============================================================================
#
# This Makefile provides convenient targets for common Terraform operations.
#
# Usage:
#   make help          # Show all available targets
#   make init          # Initialize Terraform
#   make plan          # Run terraform plan
#   make apply         # Apply changes
#   make destroy       # Destroy all resources
#
# =============================================================================

# Configuration
SHELL := /bin/bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := help
.DELETE_ON_ERROR:
.NOTPARALLEL:

# Variables
TF := terraform
TFVARS := terraform.tfvars
TFPLAN := tfplan
AWS_PROFILE ?=
PARALLELISM ?= 10

# Export AWS profile if provided
ifdef AWS_PROFILE
  export AWS_PROFILE
endif

# Terraform flags
TF_FLAGS := -var-file=$(TFVARS)

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m

# =============================================================================
# HELP
# =============================================================================

.PHONY: help
help: ## Show this help message
	@echo -e "$(BLUE)RepliMap Terraform Makefile$(NC)"
	@echo ""
	@echo "Usage: make [target] [VAR=value]"
	@echo ""
	@echo "Variables:"
	@echo "  AWS_PROFILE    AWS profile to use (optional)"
	@echo "  PARALLELISM    Terraform parallelism (default: 10)"
	@echo "  INCLUDE        Resource pattern for plan-include"
	@echo "  EXCLUDE        Resource pattern for plan-exclude"
	@echo "  TARGET         Resource address for plan-target"
	@echo ""
	@echo "Targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# =============================================================================
# SETUP & INITIALIZATION
# =============================================================================

.PHONY: init
init: ## Initialize Terraform (download providers)
	@echo -e "$(BLUE)Initializing Terraform...$(NC)"
	$(TF) init

.PHONY: init-upgrade
init-upgrade: ## Initialize and upgrade providers
	@echo -e "$(BLUE)Initializing Terraform with provider upgrade...$(NC)"
	$(TF) init -upgrade

.PHONY: setup
setup: check-tfvars init ## Setup: check tfvars and initialize

.PHONY: check-tfvars
check-tfvars: ## Check if terraform.tfvars exists
	@if [ ! -f "$(TFVARS)" ]; then \
		echo -e "$(YELLOW)WARNING: $(TFVARS) not found$(NC)"; \
		if [ -f "terraform.tfvars.example" ]; then \
			echo -e "$(BLUE)Creating from example...$(NC)"; \
			cp terraform.tfvars.example $(TFVARS); \
			echo -e "$(YELLOW)Please edit $(TFVARS) with your values$(NC)"; \
			exit 1; \
		fi; \
	fi
	@echo -e "$(GREEN)✓$(NC) $(TFVARS) exists"

# =============================================================================
# VALIDATION & FORMATTING
# =============================================================================

.PHONY: validate
validate: ## Validate Terraform configuration
	@echo -e "$(BLUE)Validating configuration...$(NC)"
	$(TF) validate

.PHONY: fmt
fmt: ## Format Terraform files
	@echo -e "$(BLUE)Formatting Terraform files...$(NC)"
	$(TF) fmt -recursive

.PHONY: fmt-check
fmt-check: ## Check Terraform formatting
	@echo -e "$(BLUE)Checking Terraform formatting...$(NC)"
	$(TF) fmt -check -recursive

.PHONY: lint
lint: fmt-check validate ## Run all linting checks

.PHONY: quick-validate
quick-validate: ## Quick validation (no tfvars needed, init + validate only)
	@echo -e "$(BLUE)Quick validation (no tfvars required)...$(NC)"
	@$(TF) init -backend=false > /dev/null 2>&1 || $(TF) init -backend=false
	@$(TF) validate
	@echo -e "$(GREEN)✓$(NC) Configuration is valid"

.PHONY: test
test: ## Run test-terraform.sh validation script
	@echo -e "$(BLUE)Running validation script...$(NC)"
	./test-terraform.sh

# =============================================================================
# PLANNING
# =============================================================================

.PHONY: plan
plan: check-tfvars ## Plan infrastructure changes
	@echo -e "$(BLUE)Running terraform plan...$(NC)"
	$(TF) plan $(TF_FLAGS) -out=$(TFPLAN) -parallelism=$(PARALLELISM)
	@$(TF) show -no-color $(TFPLAN) > tfplan.txt
	@echo "Plan saved to: $(TFPLAN) (binary), tfplan.txt (readable)"

.PHONY: plan-destroy
plan-destroy: check-tfvars ## Plan destruction of all resources
	@echo -e "$(RED)Planning DESTRUCTION of all resources...$(NC)"
	$(TF) plan $(TF_FLAGS) -destroy -out=$(TFPLAN) -parallelism=$(PARALLELISM)
	@$(TF) show -no-color $(TFPLAN) > tfplan.txt

.PHONY: plan-target
plan-target: check-tfvars ## Plan specific resource (TARGET=aws_instance.example)
ifndef TARGET
	$(error TARGET is required. Usage: make plan-target TARGET=aws_instance.example)
endif
	@echo -e "$(BLUE)Planning target: $(TARGET)$(NC)"
	$(TF) plan $(TF_FLAGS) -target=$(TARGET) -out=$(TFPLAN) -parallelism=$(PARALLELISM)
	@$(TF) show -no-color $(TFPLAN) > tfplan.txt

.PHONY: plan-json
plan-json: check-tfvars ## Plan with JSON output (for automation/parsing)
	@echo -e "$(BLUE)Running terraform plan (JSON output)...$(NC)"
	$(TF) plan $(TF_FLAGS) -out=$(TFPLAN) -parallelism=$(PARALLELISM)
	@$(TF) show -json $(TFPLAN) > tfplan.json
	@$(TF) show -no-color $(TFPLAN) > tfplan.txt
	@echo "Plan saved to: $(TFPLAN), tfplan.txt (readable), tfplan.json (parseable)"

.PHONY: plan-include
plan-include: check-tfvars ## Plan resources matching pattern (INCLUDE=aws_instance)
ifndef INCLUDE
	$(error INCLUDE is required. Usage: make plan-include INCLUDE=aws_instance)
endif
	@echo -e "$(BLUE)Planning resources matching: $(INCLUDE)$(NC)"
	@echo -e "$(YELLOW)Note: Requires existing state. Run 'make apply' first.$(NC)"
	@TARGETS=$$($(TF) state list 2>/dev/null | grep "$(INCLUDE)" || true); \
	if [ -z "$$TARGETS" ]; then \
		echo -e "$(YELLOW)No resources match pattern: $(INCLUDE)$(NC)"; \
		exit 1; \
	fi; \
	TARGET_FLAGS=$$(echo "$$TARGETS" | xargs -I {} echo "-target={}"); \
	$(TF) plan $(TF_FLAGS) $$TARGET_FLAGS -out=$(TFPLAN) -parallelism=$(PARALLELISM); \
	$(TF) show -no-color $(TFPLAN) > tfplan.txt

.PHONY: plan-exclude
plan-exclude: check-tfvars ## Plan all except pattern (EXCLUDE=aws_db_instance)
ifndef EXCLUDE
	$(error EXCLUDE is required. Usage: make plan-exclude EXCLUDE=aws_db_instance)
endif
	@echo -e "$(BLUE)Planning all except: $(EXCLUDE)$(NC)"
	@echo -e "$(YELLOW)Note: Requires existing state. Run 'make apply' first.$(NC)"
	@TARGETS=$$($(TF) state list 2>/dev/null | grep -v "$(EXCLUDE)" || true); \
	if [ -z "$$TARGETS" ]; then \
		echo -e "$(YELLOW)No resources after excluding: $(EXCLUDE)$(NC)"; \
		exit 1; \
	fi; \
	TARGET_FLAGS=$$(echo "$$TARGETS" | xargs -I {} echo "-target={}"); \
	$(TF) plan $(TF_FLAGS) $$TARGET_FLAGS -out=$(TFPLAN) -parallelism=$(PARALLELISM); \
	$(TF) show -no-color $(TFPLAN) > tfplan.txt

.PHONY: plan-refresh-only
plan-refresh-only: check-tfvars ## Refresh state only (no changes)
	@echo -e "$(BLUE)Refreshing state only...$(NC)"
	$(TF) plan $(TF_FLAGS) -refresh-only -out=$(TFPLAN)
	@$(TF) show -no-color $(TFPLAN) > tfplan.txt

# =============================================================================
# APPLY & DESTROY
# =============================================================================

.PHONY: apply
apply: ## Apply the planned changes
	@if [ ! -f "$(TFPLAN)" ]; then \
		echo -e "$(RED)No plan file found. Run 'make plan' first.$(NC)"; \
		exit 1; \
	fi
	@echo -e "$(BLUE)Applying terraform plan...$(NC)"
	$(TF) apply -parallelism=$(PARALLELISM) $(TFPLAN)
	@rm -f $(TFPLAN)

.PHONY: apply-auto
apply-auto: check-tfvars ## Apply with auto-approve (DANGEROUS)
	@echo -e "$(RED)WARNING: Auto-approving changes!$(NC)"
	@read -p "Are you sure? (yes/no): " confirm && [ "$$confirm" = "yes" ] || exit 1
	$(TF) apply $(TF_FLAGS) -auto-approve -parallelism=$(PARALLELISM)

.PHONY: apply-target
apply-target: check-tfvars ## Apply specific resource (TARGET=aws_instance.example)
ifndef TARGET
	$(error TARGET is required. Usage: make apply-target TARGET=aws_instance.example)
endif
	@echo -e "$(YELLOW)Applying target: $(TARGET)$(NC)"
	$(TF) apply $(TF_FLAGS) -target=$(TARGET) -parallelism=$(PARALLELISM)

.PHONY: destroy
destroy: check-tfvars ## Destroy all resources (DANGEROUS)
	@echo -e "$(RED)╔═══════════════════════════════════════════════════════════════╗$(NC)"
	@echo -e "$(RED)║  WARNING: This will DESTROY ALL resources managed by Terraform ║$(NC)"
	@echo -e "$(RED)╚═══════════════════════════════════════════════════════════════╝$(NC)"
	@read -p "Type 'destroy' to confirm: " confirm && [ "$$confirm" = "destroy" ] || exit 1
	$(TF) destroy $(TF_FLAGS) -parallelism=$(PARALLELISM)

.PHONY: destroy-target
destroy-target: check-tfvars ## Destroy specific resource (TARGET=aws_instance.example)
ifndef TARGET
	$(error TARGET is required. Usage: make destroy-target TARGET=aws_instance.example)
endif
	@echo -e "$(RED)Destroying target: $(TARGET)$(NC)"
	$(TF) destroy $(TF_FLAGS) -target=$(TARGET)

# =============================================================================
# STATE MANAGEMENT
# =============================================================================

.PHONY: state-list
state-list: ## List all resources in state
	@echo -e "$(BLUE)Resources in state:$(NC)"
	$(TF) state list

.PHONY: state-show
state-show: ## Show resource details (TARGET=aws_instance.example)
ifndef TARGET
	$(error TARGET is required. Usage: make state-show TARGET=aws_instance.example)
endif
	$(TF) state show $(TARGET)

.PHONY: state-pull
state-pull: ## Pull and display current state
	$(TF) state pull

.PHONY: state-mv
state-mv: ## Move resource in state (SRC=old.name DST=new.name)
ifndef SRC
	$(error SRC is required. Usage: make state-mv SRC=old.name DST=new.name)
endif
ifndef DST
	$(error DST is required. Usage: make state-mv SRC=old.name DST=new.name)
endif
	@echo -e "$(YELLOW)Moving $(SRC) to $(DST)$(NC)"
	$(TF) state mv $(SRC) $(DST)

.PHONY: state-rm
state-rm: ## Remove resource from state (TARGET=aws_instance.example)
ifndef TARGET
	$(error TARGET is required. Usage: make state-rm TARGET=aws_instance.example)
endif
	@echo -e "$(RED)Removing $(TARGET) from state (resource will NOT be destroyed)$(NC)"
	@read -p "Are you sure? (yes/no): " confirm && [ "$$confirm" = "yes" ] || exit 1
	$(TF) state rm $(TARGET)

.PHONY: refresh
refresh: check-tfvars ## Refresh state from real infrastructure
	@echo -e "$(BLUE)Refreshing state...$(NC)"
	$(TF) refresh $(TF_FLAGS)

# =============================================================================
# OUTPUT & INFORMATION
# =============================================================================

.PHONY: output
output: ## Show all outputs
	$(TF) output

.PHONY: output-json
output-json: ## Show outputs in JSON format
	$(TF) output -json

.PHONY: show
show: ## Show current state
	$(TF) show

.PHONY: providers
providers: ## List required providers
	$(TF) providers

.PHONY: graph
graph: ## Generate dependency graph (DOT format)
	@echo -e "$(BLUE)Generating graph...$(NC)"
	$(TF) graph > graph.dot
	@echo "Graph saved to graph.dot"
	@echo "To visualize: dot -Tpng graph.dot -o graph.png"

# =============================================================================
# IMPORT & TAINT
# =============================================================================

.PHONY: import
import: ## Import existing resource (TARGET=aws_instance.example ID=i-12345)
ifndef TARGET
	$(error TARGET is required. Usage: make import TARGET=aws_instance.example ID=i-12345)
endif
ifndef ID
	$(error ID is required. Usage: make import TARGET=aws_instance.example ID=i-12345)
endif
	@echo -e "$(BLUE)Importing $(ID) as $(TARGET)$(NC)"
	$(TF) import $(TF_FLAGS) $(TARGET) $(ID)

.PHONY: taint
taint: ## Mark resource for recreation (TARGET=aws_instance.example)
ifndef TARGET
	$(error TARGET is required. Usage: make taint TARGET=aws_instance.example)
endif
	@echo -e "$(YELLOW)Tainting $(TARGET) for recreation$(NC)"
	$(TF) taint $(TARGET)

.PHONY: untaint
untaint: ## Remove taint from resource (TARGET=aws_instance.example)
ifndef TARGET
	$(error TARGET is required. Usage: make untaint TARGET=aws_instance.example)
endif
	@echo -e "$(BLUE)Untainting $(TARGET)$(NC)"
	$(TF) untaint $(TARGET)

# =============================================================================
# CLEANUP
# =============================================================================

.PHONY: clean
clean: ## Remove generated files (plan, graph, etc.)
	@echo -e "$(BLUE)Cleaning up...$(NC)"
	rm -f $(TFPLAN) tfplan.txt tfplan.json graph.dot graph.png
	rm -rf .terraform.lock.hcl
	@echo -e "$(GREEN)✓$(NC) Cleaned"

.PHONY: clean-all
clean-all: clean ## Remove all generated and cached files
	@echo -e "$(RED)Removing .terraform directory...$(NC)"
	rm -rf .terraform
	@echo -e "$(GREEN)✓$(NC) All cleaned"

# =============================================================================
# CONSOLE & DEBUG
# =============================================================================

.PHONY: console
console: ## Open Terraform console
	$(TF) console $(TF_FLAGS)

.PHONY: version
version: ## Show Terraform version
	$(TF) version

.PHONY: debug
debug: ## Show debug information
	@echo -e "$(BLUE)Debug Information$(NC)"
	@echo "Terraform version:"
	@$(TF) version
	@echo ""
	@echo "AWS identity:"
	@aws sts get-caller-identity 2>/dev/null || echo "AWS CLI not configured"
	@echo ""
	@echo "Files:"
	@ls -la *.tf 2>/dev/null || echo "No .tf files found"
"""
        file_path = output_dir / "Makefile"
        with open(file_path, "w") as f:
            f.write(makefile)
        written_files["Makefile"] = file_path
        logger.info("Wrote Makefile")

    @staticmethod
    def _terraform_name_filter(value: str) -> str:
        """Convert a string to a valid Terraform name."""
        result = ""
        for char in value:
            if char.isalnum() or char in "_-":
                result += char
            else:
                result += "_"
        if result and not (result[0].isalpha() or result[0] == "_"):
            result = f"r_{result}"
        return result or "unnamed"

    @staticmethod
    def _quote_filter(value: str) -> str:
        """Quote a string for Terraform."""
        if value is None:
            return '""'
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'

    @staticmethod
    def _quote_key_filter(key: str) -> str:
        """
        Quote a tag key for Terraform if necessary.

        Terraform keys must be valid identifiers or quoted strings.
        Keys with spaces, special characters, or starting with digits need quotes.
        """
        if not key:
            return '""'
        # Check if key is a valid Terraform identifier
        # Must start with letter or underscore, contain only alphanumeric, underscore, hyphen
        is_valid_identifier = (key[0].isalpha() or key[0] == "_") and all(
            c.isalnum() or c in "_-" for c in key
        )
        if is_valid_identifier:
            return key
        # Quote the key
        escaped = key.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'

    @staticmethod
    def _tf_ref_filter(resource_node: object, resource_type: str) -> str:
        """
        Generate a Terraform resource reference.

        Returns the reference (e.g., 'aws_vpc.my_vpc.id') or an empty string
        if the resource is not valid.
        """
        if resource_node is None:
            return ""
        terraform_name = getattr(resource_node, "terraform_name", None)
        if not terraform_name:
            return ""
        return f"{resource_type}.{terraform_name}.id"

    @staticmethod
    def _is_tf_ref_test(value: str) -> bool:
        """
        Test if a value is already a Terraform resource reference.

        Terraform references look like: aws_vpc.name.id, aws_subnet.name.id, etc.
        This is used to detect when NetworkRemapTransformer has already converted
        an ID to a Terraform reference, so templates should output it without quotes.

        Args:
            value: The string to test

        Returns:
            True if the value looks like a Terraform reference
        """
        if not isinstance(value, str):
            return False

        # Terraform references pattern: aws_<type>.<name>.<attribute>
        # Common patterns: aws_vpc.name.id, aws_subnet.name.id, aws_security_group.name.id
        tf_ref_prefixes = (
            "aws_vpc.",
            "aws_subnet.",
            "aws_security_group.",
            "aws_instance.",
            "aws_db_instance.",
            "aws_db_subnet_group.",
            "aws_lb.",
            "aws_lb_target_group.",
            "aws_s3_bucket.",
            "aws_elasticache_cluster.",
            "aws_internet_gateway.",
            "aws_nat_gateway.",
            "aws_route_table.",
            "aws_ebs_volume.",
            "aws_sqs_queue.",
            "aws_sns_topic.",
            "aws_launch_template.",
            "aws_autoscaling_group.",
        )

        return any(value.startswith(prefix) for prefix in tf_ref_prefixes)

    @staticmethod
    def _default_if_none_filter(value: object, default: object) -> object:
        """
        Return default value if value is None or undefined.

        Unlike Jinja2's built-in default filter which only handles undefined,
        this filter also handles Python None values which commonly come from
        AWS API responses.

        Args:
            value: The value to check
            default: The default value to return if value is None

        Returns:
            value if not None, otherwise default
        """
        if value is None:
            return default
        return value

    def _run_terraform_fmt(self, output_dir: Path) -> bool:
        """
        Run terraform fmt on the generated files to ensure consistent formatting.

        Args:
            output_dir: Directory containing the generated .tf files

        Returns:
            True if formatting succeeded or terraform is not installed,
            False if terraform fmt failed
        """
        # Check if terraform is available
        terraform_path = shutil.which("terraform")
        if not terraform_path:
            logger.warning(
                "terraform not found in PATH - skipping format step. "
                "Install terraform to enable automatic formatting."
            )
            return True  # Not an error, just skip

        try:
            # Run terraform fmt on the output directory
            result = subprocess.run(
                ["terraform", "fmt", "-recursive"],
                cwd=output_dir,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                # Log which files were formatted (terraform fmt outputs modified files)
                if result.stdout.strip():
                    formatted_files = result.stdout.strip().split("\n")
                    logger.info(
                        f"terraform fmt: formatted {len(formatted_files)} file(s)"
                    )
                else:
                    logger.info("terraform fmt: all files already formatted")
                return True
            else:
                logger.warning(
                    f"terraform fmt failed (exit code {result.returncode}): "
                    f"{result.stderr.strip()}"
                )
                return False

        except subprocess.TimeoutExpired:
            logger.warning("terraform fmt timed out after 30 seconds")
            return False
        except Exception as e:
            logger.warning(f"terraform fmt error: {e}")
            return False
