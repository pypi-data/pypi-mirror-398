"""
Semantic File Router for RepliMap.

Organize resources into readable, semantic files instead of
dumping 500 resources into one main.tf.

The Seven Laws of Sovereign Code:
4. Schema is Truth - Beautiful code is true code.

Level 4 Enhancement: Instead of dumping everything into main.tf,
route resources to semantic files based on their type.

Result:
- vpc.tf: VPC, Subnet, Route Tables, IGW, NAT
- security.tf: Security Groups, NACLs, IAM
- compute.tf: EC2, ASG, Launch Templates
- database.tf: RDS, ElastiCache, DynamoDB
- storage.tf: S3, EBS, EFS
- networking.tf: ELB, ALB, CloudFront
- main.tf: Everything else
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from replimap.core.models import ResourceNode

logger = logging.getLogger(__name__)


@dataclass
class FileRoute:
    """Defines which resources go to which file."""

    filename: str
    resource_types: list[str]
    description: str = ""


# Default routing configuration
DEFAULT_ROUTES: list[FileRoute] = [
    FileRoute(
        filename="vpc.tf",
        resource_types=[
            "aws_vpc",
            "aws_subnet",
            "aws_route_table",
            "aws_route_table_association",
            "aws_route",
            "aws_internet_gateway",
            "aws_nat_gateway",
            "aws_eip",
            "aws_network_acl",
            "aws_network_acl_rule",
            "aws_vpc_endpoint",
        ],
        description="VPC and core networking resources",
    ),
    FileRoute(
        filename="security.tf",
        resource_types=[
            "aws_security_group",
            "aws_security_group_rule",
            "aws_iam_role",
            "aws_iam_policy",
            "aws_iam_role_policy",
            "aws_iam_role_policy_attachment",
            "aws_iam_instance_profile",
            "aws_iam_user",
            "aws_iam_group",
            "aws_kms_key",
            "aws_kms_alias",
        ],
        description="Security and IAM resources",
    ),
    FileRoute(
        filename="compute.tf",
        resource_types=[
            "aws_instance",
            "aws_launch_template",
            "aws_autoscaling_group",
            "aws_autoscaling_policy",
            "aws_key_pair",
            "aws_placement_group",
        ],
        description="Compute resources (EC2, ASG)",
    ),
    FileRoute(
        filename="database.tf",
        resource_types=[
            "aws_db_instance",
            "aws_db_subnet_group",
            "aws_db_parameter_group",
            "aws_db_option_group",
            "aws_rds_cluster",
            "aws_rds_cluster_instance",
            "aws_elasticache_cluster",
            "aws_elasticache_subnet_group",
            "aws_elasticache_parameter_group",
            "aws_elasticache_replication_group",
            "aws_dynamodb_table",
        ],
        description="Database resources (RDS, ElastiCache, DynamoDB)",
    ),
    FileRoute(
        filename="storage.tf",
        resource_types=[
            "aws_s3_bucket",
            "aws_s3_bucket_policy",
            "aws_s3_bucket_versioning",
            "aws_s3_bucket_lifecycle_configuration",
            "aws_s3_bucket_server_side_encryption_configuration",
            "aws_ebs_volume",
            "aws_ebs_snapshot",
            "aws_efs_file_system",
            "aws_efs_mount_target",
        ],
        description="Storage resources (S3, EBS, EFS)",
    ),
    FileRoute(
        filename="networking.tf",
        resource_types=[
            "aws_lb",
            "aws_lb_listener",
            "aws_lb_listener_rule",
            "aws_lb_target_group",
            "aws_lb_target_group_attachment",
            "aws_cloudfront_distribution",
            "aws_cloudfront_origin_access_identity",
            "aws_route53_zone",
            "aws_route53_record",
            "aws_acm_certificate",
            "aws_acm_certificate_validation",
        ],
        description="Networking resources (ALB, CloudFront, Route53)",
    ),
    FileRoute(
        filename="messaging.tf",
        resource_types=[
            "aws_sqs_queue",
            "aws_sqs_queue_policy",
            "aws_sns_topic",
            "aws_sns_topic_subscription",
            "aws_sns_topic_policy",
            "aws_kinesis_stream",
            "aws_kinesis_firehose_delivery_stream",
        ],
        description="Messaging resources (SQS, SNS, Kinesis)",
    ),
    FileRoute(
        filename="lambda.tf",
        resource_types=[
            "aws_lambda_function",
            "aws_lambda_permission",
            "aws_lambda_event_source_mapping",
            "aws_lambda_alias",
            "aws_lambda_layer_version",
        ],
        description="Lambda resources",
    ),
    FileRoute(
        filename="monitoring.tf",
        resource_types=[
            "aws_cloudwatch_log_group",
            "aws_cloudwatch_log_stream",
            "aws_cloudwatch_metric_alarm",
            "aws_cloudwatch_dashboard",
            "aws_cloudwatch_event_rule",
            "aws_cloudwatch_event_target",
        ],
        description="Monitoring resources (CloudWatch)",
    ),
]


class SemanticFileRouter:
    """
    Route resources to appropriate files based on type.

    Instead of dumping everything into main.tf, this router
    organizes resources into semantic files for better
    readability and maintainability.

    Usage:
        router = SemanticFileRouter()
        file_groups = router.route_resources(resources)

        for filename, resources in file_groups.items():
            # Write resources to filename
    """

    def __init__(self, routes: list[FileRoute] | None = None) -> None:
        """
        Initialize the file router.

        Args:
            routes: Custom routing configuration (uses defaults if None)
        """
        self.routes = routes or DEFAULT_ROUTES
        self.type_to_file: dict[str, str] = {}

        # Build reverse mapping
        for route in self.routes:
            for resource_type in route.resource_types:
                self.type_to_file[resource_type] = route.filename

    def get_file_for_resource(self, resource_type: str) -> str:
        """
        Get the appropriate filename for a resource type.

        Args:
            resource_type: Terraform resource type (e.g., "aws_instance")

        Returns:
            Filename (e.g., "compute.tf")
        """
        return self.type_to_file.get(resource_type, "main.tf")

    def route_resources(
        self,
        resources: list[ResourceNode],
    ) -> dict[str, list[ResourceNode]]:
        """
        Route resources to their appropriate files.

        Args:
            resources: List of ResourceNode objects

        Returns:
            Dictionary mapping filename to list of resources
        """
        file_groups: dict[str, list[ResourceNode]] = {}

        for resource in resources:
            resource_type = str(resource.resource_type)
            filename = self.get_file_for_resource(resource_type)

            if filename not in file_groups:
                file_groups[filename] = []
            file_groups[filename].append(resource)

        # Log summary
        logger.info(f"Routed {len(resources)} resources to {len(file_groups)} files")
        for filename, group in sorted(file_groups.items()):
            logger.debug(f"  {filename}: {len(group)} resources")

        return file_groups

    def get_file_header(self, filename: str) -> str:
        """
        Get the header comment for a file.

        Args:
            filename: The filename

        Returns:
            Header comment string
        """
        # Find matching route
        for route in self.routes:
            if route.filename == filename:
                return f"# {route.description}"

        if filename == "main.tf":
            return "# Other resources"

        return f"# {filename.replace('.tf', '').replace('_', ' ').title()}"

    def generate_file_content(
        self,
        filename: str,
        rendered_resources: list[str],
    ) -> str:
        """
        Generate file content with header and resources.

        Args:
            filename: Target filename
            rendered_resources: List of rendered resource HCL strings

        Returns:
            Complete file content
        """
        lines = [
            "# ═══════════════════════════════════════════════════════════════════════════════",
            "# Auto-generated by RepliMap",
            self.get_file_header(filename),
            "# ═══════════════════════════════════════════════════════════════════════════════",
            "",
        ]

        for rendered in rendered_resources:
            lines.append(rendered)
            lines.append("")

        return "\n".join(lines)


@dataclass
class FileStructure:
    """
    Complete file structure for a generated Terraform project.

    Tracks all files that will be generated and their contents.
    """

    files: dict[str, list[str]] = field(default_factory=dict)
    router: SemanticFileRouter = field(default_factory=SemanticFileRouter)

    def add_resource(
        self,
        resource: ResourceNode,
        rendered_hcl: str,
    ) -> None:
        """
        Add a rendered resource to the appropriate file.

        Args:
            resource: The ResourceNode
            rendered_hcl: Rendered HCL content
        """
        resource_type = str(resource.resource_type)
        filename = self.router.get_file_for_resource(resource_type)

        if filename not in self.files:
            self.files[filename] = []
        self.files[filename].append(rendered_hcl)

    def write_all(self, output_dir: Path) -> dict[str, Path]:
        """
        Write all files to the output directory.

        Args:
            output_dir: Directory to write files

        Returns:
            Dictionary mapping filename to written path
        """
        written: dict[str, Path] = {}

        for filename, resources in self.files.items():
            content = self.router.generate_file_content(filename, resources)
            file_path = output_dir / filename
            file_path.write_text(content)
            written[filename] = file_path
            logger.info(f"Wrote {filename}: {len(resources)} resources")

        return written

    def get_summary(self) -> dict[str, int]:
        """Get summary of resources per file."""
        return {filename: len(resources) for filename, resources in self.files.items()}
