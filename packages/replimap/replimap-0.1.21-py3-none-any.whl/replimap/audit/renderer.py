"""
Audit Terraform Renderer.

Generates raw, forensic-accurate Terraform code without any transformations.
Used for security auditing and compliance reporting.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from jinja2 import Environment, FileSystemLoader, select_autoescape

from replimap.core.models import ResourceType

if TYPE_CHECKING:
    from replimap.core import GraphEngine

logger = logging.getLogger(__name__)

# Template directory relative to this file
AUDIT_TEMPLATE_DIR = Path(__file__).parent / "templates"


class AuditRenderer:
    """
    Renders raw Terraform for audit snapshots.

    Unlike the standard TerraformRenderer, this renderer:
    - Keeps original resource values (no downsizing, no abstraction)
    - Uses original resource names (sanitized for TF)
    - Preserves hardcoded values (no variables)
    - Adds comments with AWS resource IDs for traceability
    - Marks sensitive values with placeholders

    Output is intended for security scanning, not for apply.
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

    def __init__(
        self,
        account_id: str | None = None,
        region: str | None = None,
    ) -> None:
        """
        Initialize the audit renderer.

        Args:
            account_id: AWS account ID for metadata
            region: AWS region for metadata
        """
        self.account_id = account_id or "unknown"
        self.region = region or "unknown"

        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(AUDIT_TEMPLATE_DIR),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Add custom filters
        self.env.filters["terraform_name"] = self._terraform_name_filter
        self.env.filters["quote"] = self._quote_filter
        self.env.filters["quote_key"] = self._quote_key_filter
        self.env.filters["d"] = self._default_if_none_filter

    def render(self, graph: GraphEngine, output_dir: Path) -> dict[str, Path]:
        """
        Render the graph to raw Terraform files.

        Args:
            graph: The GraphEngine containing resources
            output_dir: Directory to write .tf files

        Returns:
            Dictionary mapping filenames to their paths
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Rendering audit Terraform to {output_dir}")

        # Group resources by output file
        file_contents: dict[str, list[str]] = {}

        # Use safe dependency order to handle cycles (e.g., mutual SG references)
        for resource in graph.get_safe_dependency_order():
            output_file = self.FILE_MAPPING.get(resource.resource_type)

            if not output_file:
                logger.warning(
                    f"No file mapping for resource type: {resource.resource_type}"
                )
                continue

            # Generate raw Terraform for this resource
            rendered = self._render_resource(resource, graph)

            if output_file not in file_contents:
                file_contents[output_file] = []
            file_contents[output_file].append(rendered)

        # Write files with header
        written_files: dict[str, Path] = {}
        header = self._generate_header()

        for filename, contents in file_contents.items():
            file_path = output_dir / filename
            with open(file_path, "w") as f:
                f.write(header)
                f.write("\n\n")
                f.write("\n\n".join(contents))
            written_files[filename] = file_path
            logger.info(f"Wrote {filename} ({len(contents)} resources)")

        # Generate supporting files
        self._generate_versions(output_dir, written_files)
        self._generate_providers(output_dir, written_files)

        return written_files

    def _generate_header(self) -> str:
        """Generate audit header comment."""
        timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        return f"""# ============================================================================
# RepliMap Audit Snapshot
# Generated: {timestamp}
# Account: {self.account_id} | Region: {self.region}
#
# ⚠️  WARNING: Forensic snapshot for audit. DO NOT apply directly.
# This file contains a raw representation of infrastructure for security scanning.
# ============================================================================"""

    def _render_resource(self, resource: object, graph: GraphEngine) -> str:
        """
        Render a single resource to raw Terraform.

        This generates faithful, unmodified Terraform code.
        """
        resource_type = resource.resource_type
        terraform_type = str(resource_type)
        terraform_name = resource.terraform_name

        lines = [
            f"# Original AWS ID: {resource.id}",
            f"# Original Name: {resource.original_name or 'N/A'}",
        ]

        if resource.arn:
            lines.append(f"# ARN: {resource.arn}")

        lines.append(f'resource "{terraform_type}" "{terraform_name}" {{')

        # Generate resource-specific attributes
        config_lines = self._render_config(resource, graph)
        lines.extend(["  " + line for line in config_lines])

        # Add original tags
        if resource.tags:
            lines.append("")
            lines.append("  tags = {")
            for key, value in sorted(resource.tags.items()):
                # Filter out AWS system tags (aws:* prefix)
                if key.startswith("aws:"):
                    continue
                quoted_key = self._quote_key_filter(key)
                quoted_value = self._quote_filter(value)
                lines.append(f"    {quoted_key} = {quoted_value}")
            lines.append("  }")

        # SAFETY: Add lifecycle block to prevent accidental resource creation
        # This is a forensic snapshot for audit - it should NEVER be applied
        lines.append("")
        lines.append("  # SAFETY: Prevent accidental apply of audit snapshot")
        lines.append("  lifecycle {")
        lines.append("    prevent_destroy = true")
        lines.append("  }")

        lines.append("}")

        return "\n".join(lines)

    def _render_config(self, resource: object, graph: GraphEngine) -> list[str]:
        """
        Render resource configuration attributes.

        Different resource types need different attribute handling.
        """
        resource_type = resource.resource_type
        config = resource.config
        lines = []

        if resource_type == ResourceType.VPC:
            lines.extend(self._render_vpc(config))
        elif resource_type == ResourceType.SUBNET:
            lines.extend(self._render_subnet(config, graph))
        elif resource_type == ResourceType.SECURITY_GROUP:
            lines.extend(self._render_security_group(config, graph))
        elif resource_type == ResourceType.EC2_INSTANCE:
            lines.extend(self._render_ec2(config, graph))
        elif resource_type == ResourceType.S3_BUCKET:
            lines.extend(self._render_s3(config))
        elif resource_type == ResourceType.RDS_INSTANCE:
            lines.extend(self._render_rds(config, graph))
        elif resource_type == ResourceType.DB_SUBNET_GROUP:
            lines.extend(self._render_db_subnet_group(config))
        elif resource_type == ResourceType.EBS_VOLUME:
            lines.extend(self._render_ebs(config))
        elif resource_type == ResourceType.LB:
            lines.extend(self._render_lb(config, graph))
        elif resource_type == ResourceType.SQS_QUEUE:
            lines.extend(self._render_sqs(config))
        elif resource_type == ResourceType.SNS_TOPIC:
            lines.extend(self._render_sns(config))
        elif resource_type == ResourceType.ELASTICACHE_CLUSTER:
            lines.extend(self._render_elasticache(config, graph))
        elif resource_type == ResourceType.ROUTE_TABLE:
            lines.extend(self._render_route_table(config, graph))
        elif resource_type == ResourceType.INTERNET_GATEWAY:
            lines.extend(self._render_igw(config, graph))
        elif resource_type == ResourceType.NAT_GATEWAY:
            lines.extend(self._render_nat_gateway(config, graph))
        elif resource_type == ResourceType.VPC_ENDPOINT:
            lines.extend(self._render_vpc_endpoint(config, graph))
        elif resource_type == ResourceType.LAUNCH_TEMPLATE:
            lines.extend(self._render_launch_template(config, graph))
        elif resource_type == ResourceType.AUTOSCALING_GROUP:
            lines.extend(self._render_autoscaling_group(config, graph))
        elif resource_type == ResourceType.LB_LISTENER:
            lines.extend(self._render_lb_listener(config, graph))
        elif resource_type == ResourceType.LB_TARGET_GROUP:
            lines.extend(self._render_lb_target_group(config, graph))
        elif resource_type == ResourceType.DB_PARAMETER_GROUP:
            lines.extend(self._render_db_parameter_group(config))
        elif resource_type == ResourceType.ELASTICACHE_SUBNET_GROUP:
            lines.extend(self._render_elasticache_subnet_group(config))
        elif resource_type == ResourceType.S3_BUCKET_POLICY:
            lines.extend(self._render_s3_bucket_policy(config))
        else:
            # Generic rendering for unsupported types
            lines.extend(self._render_generic(config))

        return lines

    def _render_vpc(self, config: dict) -> list[str]:
        """Render VPC attributes."""
        lines = []
        if cidr := config.get("cidr_block"):
            lines.append(f'cidr_block = "{cidr}"')
        if config.get("enable_dns_hostnames"):
            lines.append("enable_dns_hostnames = true")
        if config.get("enable_dns_support"):
            lines.append("enable_dns_support = true")
        if instance_tenancy := config.get("instance_tenancy"):
            lines.append(f'instance_tenancy = "{instance_tenancy}"')
        return lines

    def _render_subnet(self, config: dict, graph: GraphEngine) -> list[str]:
        """Render Subnet attributes."""
        lines = []
        if vpc_id := config.get("vpc_id"):
            vpc_resource = graph.get_resource(vpc_id)
            if vpc_resource:
                lines.append(f"vpc_id = aws_vpc.{vpc_resource.terraform_name}.id")
            else:
                lines.append(f'vpc_id = "{vpc_id}"')
        if cidr := config.get("cidr_block"):
            lines.append(f'cidr_block = "{cidr}"')
        if az := config.get("availability_zone"):
            lines.append(f'availability_zone = "{az}"')
        if config.get("map_public_ip_on_launch"):
            lines.append("map_public_ip_on_launch = true")
        return lines

    def _render_security_group(self, config: dict, graph: GraphEngine) -> list[str]:
        """Render Security Group attributes."""
        lines = []
        if name := config.get("group_name"):
            lines.append(f'name = "{name}"')
        if description := config.get("description"):
            escaped = description.replace('"', '\\"')
            lines.append(f'description = "{escaped}"')
        if vpc_id := config.get("vpc_id"):
            vpc_resource = graph.get_resource(vpc_id)
            if vpc_resource:
                lines.append(f"vpc_id = aws_vpc.{vpc_resource.terraform_name}.id")
            else:
                lines.append(f'vpc_id = "{vpc_id}"')

        # Inline ingress rules (for audit, we keep them simple)
        for rule in config.get("ip_permissions", []):
            lines.append("")
            lines.append("ingress {")
            lines.extend(self._render_sg_rule(rule))
            lines.append("}")

        # Inline egress rules
        for rule in config.get("ip_permissions_egress", []):
            lines.append("")
            lines.append("egress {")
            lines.extend(self._render_sg_rule(rule))
            lines.append("}")

        return lines

    def _render_sg_rule(self, rule: dict) -> list[str]:
        """Render a single security group rule."""
        lines = []
        from_port = rule.get("from_port")
        to_port = rule.get("to_port")
        protocol = rule.get("ip_protocol", "-1")

        # Handle None ports (all traffic rules have None ports)
        if from_port is None:
            from_port = 0
        if to_port is None:
            to_port = 0

        lines.append(f"  from_port   = {from_port}")
        lines.append(f"  to_port     = {to_port}")
        lines.append(f'  protocol    = "{protocol}"')

        # CIDR blocks
        cidrs = [
            r.get("cidr_ip") for r in rule.get("ip_ranges", []) if r.get("cidr_ip")
        ]
        if cidrs:
            cidr_list = ", ".join(f'"{c}"' for c in cidrs)
            lines.append(f"  cidr_blocks = [{cidr_list}]")

        # IPv6 CIDR blocks
        ipv6_cidrs = [
            r.get("cidr_ipv6")
            for r in rule.get("ipv6_ranges", [])
            if r.get("cidr_ipv6")
        ]
        if ipv6_cidrs:
            cidr_list = ", ".join(f'"{c}"' for c in ipv6_cidrs)
            lines.append(f"  ipv6_cidr_blocks = [{cidr_list}]")

        # Security group references
        sg_refs = [
            g.get("group_id")
            for g in rule.get("user_id_group_pairs", [])
            if g.get("group_id")
        ]
        if sg_refs:
            sg_list = ", ".join(f'"{s}"' for s in sg_refs)
            lines.append(f"  security_groups = [{sg_list}]")

        return lines

    def _render_ec2(self, config: dict, graph: GraphEngine) -> list[str]:
        """Render EC2 instance attributes."""
        lines = []

        # AMI - keep original
        if ami := config.get("ami"):
            lines.append(f'ami = "{ami}"')

        # Instance type - keep original (no downsizing!)
        if instance_type := config.get("instance_type"):
            lines.append(f'instance_type = "{instance_type}"')

        # Key name
        if key_name := config.get("key_name"):
            lines.append(f'key_name = "{key_name}"')

        # Subnet
        if subnet_id := config.get("subnet_id"):
            subnet_resource = graph.get_resource(subnet_id)
            if subnet_resource:
                lines.append(
                    f"subnet_id = aws_subnet.{subnet_resource.terraform_name}.id"
                )
            else:
                lines.append(f'subnet_id = "{subnet_id}"')

        # Security groups
        if sgs := config.get("security_groups"):
            sg_list = ", ".join(f'"{sg}"' for sg in sgs)
            lines.append(f"vpc_security_group_ids = [{sg_list}]")

        # Private IP
        if private_ip := config.get("private_ip"):
            lines.append(f'private_ip = "{private_ip}"')

        # IAM instance profile
        if iam_profile := config.get("iam_instance_profile"):
            lines.append(f'iam_instance_profile = "{iam_profile}"')

        # Monitoring
        if config.get("monitoring"):
            lines.append("monitoring = true")

        # EBS optimized
        if config.get("ebs_optimized"):
            lines.append("ebs_optimized = true")

        # Metadata options (IMDSv2)
        if metadata := config.get("metadata_options"):
            lines.append("")
            lines.append("metadata_options {")
            if http_tokens := metadata.get("http_tokens"):
                lines.append(f'  http_tokens = "{http_tokens}"')
            if http_endpoint := metadata.get("http_endpoint"):
                lines.append(f'  http_endpoint = "{http_endpoint}"')
            lines.append("}")

        return lines

    def _render_s3(self, config: dict) -> list[str]:
        """Render S3 bucket attributes."""
        lines = []
        if bucket := config.get("bucket"):
            lines.append(f'bucket = "{bucket}"')
        return lines

    def _render_rds(self, config: dict, graph: GraphEngine) -> list[str]:
        """Render RDS instance attributes."""
        lines = []

        if identifier := config.get("db_instance_identifier"):
            lines.append(f'identifier = "{identifier}"')
        if engine := config.get("engine"):
            lines.append(f'engine = "{engine}"')
        if engine_version := config.get("engine_version"):
            lines.append(f'engine_version = "{engine_version}"')
        if instance_class := config.get("db_instance_class"):
            lines.append(f'instance_class = "{instance_class}"')
        if storage := config.get("allocated_storage"):
            lines.append(f"allocated_storage = {storage}")
        if storage_type := config.get("storage_type"):
            lines.append(f'storage_type = "{storage_type}"')

        # Security - this is what Checkov will scan
        if config.get("storage_encrypted"):
            lines.append("storage_encrypted = true")
        else:
            lines.append("storage_encrypted = false  # AUDIT: Not encrypted")

        if config.get("publicly_accessible"):
            lines.append("publicly_accessible = true  # AUDIT: Public access")
        else:
            lines.append("publicly_accessible = false")

        if config.get("multi_az"):
            lines.append("multi_az = true")
        else:
            lines.append("multi_az = false  # AUDIT: Single AZ")

        if config.get("deletion_protection"):
            lines.append("deletion_protection = true")
        else:
            lines.append("deletion_protection = false  # AUDIT: No deletion protection")

        # Password placeholder
        lines.append('password = "REDACTED"  # AUDIT: Sensitive value redacted')

        return lines

    def _render_db_subnet_group(self, config: dict) -> list[str]:
        """Render DB Subnet Group attributes."""
        lines = []
        if name := config.get("db_subnet_group_name"):
            lines.append(f'name = "{name}"')
        if description := config.get("db_subnet_group_description"):
            escaped = description.replace('"', '\\"')
            lines.append(f'description = "{escaped}"')
        if subnets := config.get("subnet_ids"):
            subnet_list = ", ".join(f'"{s}"' for s in subnets)
            lines.append(f"subnet_ids = [{subnet_list}]")
        return lines

    def _render_ebs(self, config: dict) -> list[str]:
        """Render EBS volume attributes."""
        lines = []
        if az := config.get("availability_zone"):
            lines.append(f'availability_zone = "{az}"')
        if size := config.get("size"):
            lines.append(f"size = {size}")
        if vtype := config.get("volume_type"):
            lines.append(f'type = "{vtype}"')
        if config.get("encrypted"):
            lines.append("encrypted = true")
        else:
            lines.append("encrypted = false  # AUDIT: Not encrypted")
        if iops := config.get("iops"):
            lines.append(f"iops = {iops}")
        return lines

    def _render_lb(self, config: dict, graph: GraphEngine) -> list[str]:
        """Render Load Balancer attributes."""
        lines = []
        if name := config.get("load_balancer_name"):
            lines.append(f'name = "{name}"')
        if config.get("internal"):
            lines.append("internal = true")
        else:
            lines.append("internal = false")
        if lb_type := config.get("type"):
            lines.append(f'load_balancer_type = "{lb_type}"')
        if subnets := config.get("subnets"):
            subnet_list = ", ".join(f'"{s}"' for s in subnets)
            lines.append(f"subnets = [{subnet_list}]")
        if sgs := config.get("security_groups"):
            sg_list = ", ".join(f'"{sg}"' for sg in sgs)
            lines.append(f"security_groups = [{sg_list}]")
        return lines

    def _render_sqs(self, config: dict) -> list[str]:
        """Render SQS queue attributes."""
        lines = []
        if name := config.get("queue_name"):
            lines.append(f'name = "{name}"')
        if delay := config.get("delay_seconds"):
            lines.append(f"delay_seconds = {delay}")
        if max_size := config.get("max_message_size"):
            lines.append(f"max_message_size = {max_size}")
        if retention := config.get("message_retention_seconds"):
            lines.append(f"message_retention_seconds = {retention}")

        # Encryption
        if kms_key := config.get("kms_master_key_id"):
            lines.append(f'kms_master_key_id = "{kms_key}"')
        elif config.get("sqs_managed_sse_enabled"):
            lines.append("sqs_managed_sse_enabled = true")
        else:
            lines.append("# AUDIT: No encryption configured")

        return lines

    def _render_sns(self, config: dict) -> list[str]:
        """Render SNS topic attributes."""
        lines = []
        if name := config.get("topic_name"):
            lines.append(f'name = "{name}"')
        if kms_key := config.get("kms_master_key_id"):
            lines.append(f'kms_master_key_id = "{kms_key}"')
        else:
            lines.append("# AUDIT: No encryption configured")
        return lines

    def _render_elasticache(self, config: dict, graph: GraphEngine) -> list[str]:
        """Render ElastiCache cluster attributes."""
        lines = []
        if cluster_id := config.get("cache_cluster_id"):
            lines.append(f'cluster_id = "{cluster_id}"')
        if engine := config.get("engine"):
            lines.append(f'engine = "{engine}"')
        if node_type := config.get("cache_node_type"):
            lines.append(f'node_type = "{node_type}"')
        if num_nodes := config.get("num_cache_nodes"):
            lines.append(f"num_cache_nodes = {num_nodes}")

        # Encryption
        if config.get("at_rest_encryption_enabled"):
            lines.append("at_rest_encryption_enabled = true")
        else:
            lines.append(
                "at_rest_encryption_enabled = false  # AUDIT: Not encrypted at rest"
            )

        if config.get("transit_encryption_enabled"):
            lines.append("transit_encryption_enabled = true")
        else:
            lines.append(
                "transit_encryption_enabled = false  # AUDIT: Not encrypted in transit"
            )

        return lines

    def _render_route_table(self, config: dict, graph: GraphEngine) -> list[str]:
        """Render Route Table attributes."""
        lines = []
        if vpc_id := config.get("vpc_id"):
            vpc_resource = graph.get_resource(vpc_id)
            if vpc_resource:
                lines.append(f"vpc_id = aws_vpc.{vpc_resource.terraform_name}.id")
            else:
                lines.append(f'vpc_id = "{vpc_id}"')
        return lines

    def _render_igw(self, config: dict, graph: GraphEngine) -> list[str]:
        """Render Internet Gateway attributes."""
        lines = []
        if vpc_id := config.get("vpc_id"):
            vpc_resource = graph.get_resource(vpc_id)
            if vpc_resource:
                lines.append(f"vpc_id = aws_vpc.{vpc_resource.terraform_name}.id")
            else:
                lines.append(f'vpc_id = "{vpc_id}"')
        return lines

    def _render_nat_gateway(self, config: dict, graph: GraphEngine) -> list[str]:
        """Render NAT Gateway attributes."""
        lines = []
        if subnet_id := config.get("subnet_id"):
            subnet_resource = graph.get_resource(subnet_id)
            if subnet_resource:
                lines.append(
                    f"subnet_id = aws_subnet.{subnet_resource.terraform_name}.id"
                )
            else:
                lines.append(f'subnet_id = "{subnet_id}"')
        if allocation_id := config.get("allocation_id"):
            lines.append(f'allocation_id = "{allocation_id}"')
        return lines

    def _render_vpc_endpoint(self, config: dict, graph: GraphEngine) -> list[str]:
        """Render VPC Endpoint attributes."""
        lines = []
        if vpc_id := config.get("vpc_id"):
            vpc_resource = graph.get_resource(vpc_id)
            if vpc_resource:
                lines.append(f"vpc_id = aws_vpc.{vpc_resource.terraform_name}.id")
            else:
                lines.append(f'vpc_id = "{vpc_id}"')
        if service_name := config.get("service_name"):
            lines.append(f'service_name = "{service_name}"')
        if vpc_endpoint_type := config.get("vpc_endpoint_type"):
            lines.append(f'vpc_endpoint_type = "{vpc_endpoint_type}"')
        if config.get("private_dns_enabled"):
            lines.append("private_dns_enabled = true")
        return lines

    def _render_launch_template(self, config: dict, graph: GraphEngine) -> list[str]:
        """Render Launch Template attributes."""
        lines = []
        if name := config.get("launch_template_name"):
            lines.append(f'name = "{name}"')
        if image_id := config.get("image_id"):
            lines.append(f'image_id = "{image_id}"')
        if instance_type := config.get("instance_type"):
            lines.append(f'instance_type = "{instance_type}"')
        if key_name := config.get("key_name"):
            lines.append(f'key_name = "{key_name}"')

        # Metadata options (IMDSv2)
        if metadata := config.get("metadata_options"):
            lines.append("")
            lines.append("metadata_options {")
            if http_tokens := metadata.get("http_tokens"):
                lines.append(f'  http_tokens = "{http_tokens}"')
            if http_endpoint := metadata.get("http_endpoint"):
                lines.append(f'  http_endpoint = "{http_endpoint}"')
            lines.append("}")

        return lines

    def _render_autoscaling_group(self, config: dict, graph: GraphEngine) -> list[str]:
        """Render Auto Scaling Group attributes."""
        lines = []
        if name := config.get("auto_scaling_group_name"):
            lines.append(f'name = "{name}"')
        if min_size := config.get("min_size"):
            lines.append(f"min_size = {min_size}")
        if max_size := config.get("max_size"):
            lines.append(f"max_size = {max_size}")
        if desired_capacity := config.get("desired_capacity"):
            lines.append(f"desired_capacity = {desired_capacity}")
        if health_check_type := config.get("health_check_type"):
            lines.append(f'health_check_type = "{health_check_type}"')
        return lines

    def _render_lb_listener(self, config: dict, graph: GraphEngine) -> list[str]:
        """Render Load Balancer Listener attributes."""
        lines = []
        if lb_arn := config.get("load_balancer_arn"):
            lines.append(f'load_balancer_arn = "{lb_arn}"')
        if port := config.get("port"):
            lines.append(f"port = {port}")
        if protocol := config.get("protocol"):
            lines.append(f'protocol = "{protocol}"')
        if ssl_policy := config.get("ssl_policy"):
            lines.append(f'ssl_policy = "{ssl_policy}"')
        if cert_arn := config.get("certificate_arn"):
            lines.append(f'certificate_arn = "{cert_arn}"')
        return lines

    def _render_lb_target_group(self, config: dict, graph: GraphEngine) -> list[str]:
        """Render Load Balancer Target Group attributes."""
        lines = []
        if name := config.get("target_group_name"):
            lines.append(f'name = "{name}"')
        if port := config.get("port"):
            lines.append(f"port = {port}")
        if protocol := config.get("protocol"):
            lines.append(f'protocol = "{protocol}"')
        if vpc_id := config.get("vpc_id"):
            vpc_resource = graph.get_resource(vpc_id)
            if vpc_resource:
                lines.append(f"vpc_id = aws_vpc.{vpc_resource.terraform_name}.id")
            else:
                lines.append(f'vpc_id = "{vpc_id}"')
        if target_type := config.get("target_type"):
            lines.append(f'target_type = "{target_type}"')
        return lines

    def _render_db_parameter_group(self, config: dict) -> list[str]:
        """Render DB Parameter Group attributes."""
        lines = []
        if name := config.get("db_parameter_group_name"):
            lines.append(f'name = "{name}"')
        if family := config.get("db_parameter_group_family"):
            lines.append(f'family = "{family}"')
        if description := config.get("description"):
            escaped = description.replace('"', '\\"').replace("\n", "\\n")
            lines.append(f'description = "{escaped}"')
        return lines

    def _render_elasticache_subnet_group(self, config: dict) -> list[str]:
        """Render ElastiCache Subnet Group attributes."""
        lines = []
        if name := config.get("cache_subnet_group_name"):
            lines.append(f'name = "{name}"')
        if description := config.get("cache_subnet_group_description"):
            escaped = description.replace('"', '\\"').replace("\n", "\\n")
            lines.append(f'description = "{escaped}"')
        if subnets := config.get("subnet_ids"):
            subnet_list = ", ".join(f'"{s}"' for s in subnets)
            lines.append(f"subnet_ids = [{subnet_list}]")
        return lines

    def _render_s3_bucket_policy(self, config: dict) -> list[str]:
        """Render S3 Bucket Policy attributes."""
        lines = []
        if bucket := config.get("bucket"):
            lines.append(f'bucket = "{bucket}"')
        # Policy is usually JSON, we'll include it as a comment
        if policy := config.get("policy"):
            lines.append("# Policy document (JSON):")
            lines.append(f'policy = "{policy[:100]}..."  # AUDIT: Policy truncated')
        return lines

    def _render_generic(self, config: dict) -> list[str]:
        """Generic config rendering for unsupported types."""
        lines = []
        for key, value in config.items():
            if key in ("tags", "Tags"):
                continue
            if isinstance(value, bool):
                lines.append(f"{key} = {str(value).lower()}")
            elif isinstance(value, (int, float)):
                lines.append(f"{key} = {value}")
            elif isinstance(value, str):
                # Escape quotes and newlines for Terraform
                escaped = (
                    value.replace("\\", "\\\\")
                    .replace('"', '\\"')
                    .replace("\n", "\\n")
                    .replace("\r", "\\r")
                )
                lines.append(f'{key} = "{escaped}"')
        return lines

    def _generate_versions(
        self,
        output_dir: Path,
        written_files: dict[str, Path],
    ) -> None:
        """Generate versions.tf with Terraform version constraints."""
        versions = """# Generated by RepliMap Audit
# Terraform and provider version constraints
# ⚠️  DO NOT APPLY - For security scanning only

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

    def _generate_providers(
        self,
        output_dir: Path,
        written_files: dict[str, Path],
    ) -> None:
        """Generate providers.tf with AWS provider configuration."""
        providers = f"""# Generated by RepliMap Audit
# AWS Provider Configuration
# ⚠️  DO NOT APPLY - For security scanning only

provider "aws" {{
  region = "{self.region}"

  # Skip credential validation for audit snapshots
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
}}
"""
        file_path = output_dir / "providers.tf"
        with open(file_path, "w") as f:
            f.write(providers)
        written_files["providers.tf"] = file_path

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
    def _quote_filter(value: str | None) -> str:
        """Quote a string for Terraform."""
        if value is None:
            return '""'
        # Escape backslashes, quotes, and newlines for Terraform
        escaped = (
            value.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\n", "\\n")
            .replace("\r", "\\r")
            .replace("\t", "\\t")
        )
        return f'"{escaped}"'

    @staticmethod
    def _quote_key_filter(key: str) -> str:
        """Quote a tag key for Terraform if necessary."""
        if not key:
            return '""'
        is_valid_identifier = (key[0].isalpha() or key[0] == "_") and all(
            c.isalnum() or c in "_-" for c in key
        )
        if is_valid_identifier:
            return key
        escaped = key.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'

    @staticmethod
    def _default_if_none_filter(value: object, default: object) -> object:
        """Return default value if value is None."""
        if value is None:
            return default
        return value
