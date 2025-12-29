"""
Intelligent resource naming for better readability.

Extracts meaningful names from:
- ARNs (e.g., arn:aws:elasticloadbalancing:.../app/alb-name/xxx)
- Resource tags (Name tag)
- Naming patterns

Provides consistent, human-readable display names across all resource types.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class DisplayName:
    """Processed display name for a resource."""

    short_name: str  # For node labels (e.g., "elementtime")
    full_name: str  # For tooltips/details (e.g., "alb-elementtime-prod")
    service_name: str | None  # Extracted service name (e.g., "elementtime")


class ResourceNamer:
    """
    Extract human-readable names from AWS resources.

    Handles ARN parsing, tag extraction, and cleanup of
    common AWS naming patterns like hash suffixes.
    """

    # ARN patterns for extracting meaningful names
    # Format: (service_in_arn, regex_pattern, group_to_extract)
    ARN_PATTERNS: dict[str, str] = {
        "elasticloadbalancing": r"/app/([^/]+)/",  # ALB: .../app/NAME/hash
        "rds": r":db:([^:]+)$",  # RDS: ...db:NAME
        "sqs": r":([^:]+)$",  # SQS: ...QUEUE_NAME
        "sns": r":([^:]+)$",  # SNS: ...TOPIC_NAME
        "s3": r":::([^:/]+)",  # S3: :::BUCKET_NAME
        "lambda": r":function:([^:]+)",  # Lambda: ...function:NAME
        "elasticache": r":cluster:([^:]+)",  # ElastiCache: ...cluster:NAME
        "ec2": r":instance/([^:]+)",  # EC2: ...instance/ID
    }

    # Patterns to remove from IDs for cleaner display
    CLEANUP_PATTERNS: list[tuple[str, str]] = [
        (r"^arn:aws:[^:]+:[^:]*:[^:]*:", ""),  # Remove ARN prefix
        (r"[a-f0-9]{32}$", ""),  # Remove 32-char hash suffix
        (r"[a-f0-9]{12,}$", ""),  # Remove 12+ char hash suffix
        (r"-[a-z0-9]{12,}$", ""),  # Remove -hash suffix
        (r"_[a-z0-9]{12,}$", ""),  # Remove _hash suffix
    ]

    # Service name extraction patterns for ALBs
    ALB_SERVICE_PATTERNS: list[str] = [
        r"^alb-([a-z][a-z0-9]*)-",  # alb-{service}-{env}
        r"^([a-z][a-z0-9]*)-alb",  # {service}-alb
        r"^([a-z][a-z0-9]*)ALB",  # {service}ALB
        r"^([a-z][a-z0-9]*)-lb",  # {service}-lb
    ]

    # Maximum display name length
    MAX_SHORT_NAME = 20
    MAX_FULL_NAME = 40

    def get_display_name(self, resource: dict[str, Any]) -> DisplayName:
        """
        Get the best human-readable name for a resource.

        Priority:
        1. Name tag
        2. Extracted from ARN (for supported types)
        3. Cleaned up ID

        Args:
            resource: Resource dictionary with id, name, properties

        Returns:
            DisplayName with short, full, and service names
        """
        # Try Name tag first (most reliable)
        tags = resource.get("properties", {}).get("tags", {})
        if isinstance(tags, dict) and "Name" in tags:
            name = str(tags["Name"])
            return DisplayName(
                short_name=self._truncate(name, self.MAX_SHORT_NAME),
                full_name=self._truncate(name, self.MAX_FULL_NAME),
                service_name=self._extract_service_name(name),
            )

        # Try extracting from ARN
        resource_id = resource.get("id", "")
        if resource_id.startswith("arn:"):
            extracted = self._extract_from_arn(resource_id)
            if extracted:
                return DisplayName(
                    short_name=self._truncate(extracted, self.MAX_SHORT_NAME),
                    full_name=self._truncate(extracted, self.MAX_FULL_NAME),
                    service_name=self._extract_service_name(extracted),
                )

        # Use existing name if different from ID
        existing_name = resource.get("name", "")
        if existing_name and existing_name != resource_id:
            return DisplayName(
                short_name=self._truncate(existing_name, self.MAX_SHORT_NAME),
                full_name=self._truncate(existing_name, self.MAX_FULL_NAME),
                service_name=self._extract_service_name(existing_name),
            )

        # Clean up and use ID
        cleaned = self._cleanup_id(resource_id)
        return DisplayName(
            short_name=self._truncate(cleaned, self.MAX_SHORT_NAME),
            full_name=self._truncate(cleaned, self.MAX_FULL_NAME),
            service_name=self._extract_service_name(cleaned),
        )

    def _extract_from_arn(self, arn: str) -> str | None:
        """Extract meaningful name from ARN."""
        for service, pattern in self.ARN_PATTERNS.items():
            if service in arn:
                match = re.search(pattern, arn)
                if match:
                    return match.group(1)

        # Generic fallback: try to get last meaningful segment
        parts = arn.split("/")
        if len(parts) > 1:
            # For paths like .../app/NAME/hash, return NAME
            for i, part in enumerate(parts):
                if part == "app" and i + 1 < len(parts) - 1:
                    return parts[i + 1]

        # Try colon-separated
        parts = arn.split(":")
        if len(parts) > 5:
            return parts[-1] if parts[-1] else parts[-2]

        return None

    def _cleanup_id(self, id_str: str) -> str:
        """Clean up resource ID for display."""
        result = id_str

        for pattern, replacement in self.CLEANUP_PATTERNS:
            result = re.sub(pattern, replacement, result)

        # Remove trailing/leading separators
        result = result.strip("-_/:")

        return result or id_str  # Return original if cleanup removed everything

    def _truncate(self, name: str, max_len: int) -> str:
        """Truncate long names with ellipsis."""
        if not name:
            return ""
        if len(name) <= max_len:
            return name
        return name[: max_len - 1] + "\u2026"  # Unicode ellipsis

    def _extract_service_name(self, name: str) -> str | None:
        """
        Extract service/application name from resource name.

        Handles patterns like:
        - alb-elementtime-prod -> elementtime
        - elementtime-alb -> elementtime
        - rds-prod-elementcentre -> elementcentre
        """
        if not name:
            return None

        # Try ALB-specific patterns first
        for pattern in self.ALB_SERVICE_PATTERNS:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                return match.group(1).lower()

        # Generic pattern: extract word between common prefixes/suffixes
        # Patterns like: {prefix}-{service}-{env}
        generic_patterns = [
            r"^(?:alb|elb|rds|ec2|cache|redis|sqs|sns)-([a-z][a-z0-9]*)-",
            r"^([a-z][a-z0-9]*)-(?:prod|stage|test|dev|staging)$",
            r"-([a-z][a-z0-9]*)-(?:prod|stage|test|dev|staging)$",
        ]

        for pattern in generic_patterns:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                return match.group(1).lower()

        return None

    def enrich_nodes(self, nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Add display name metadata to all nodes.

        Modifies nodes in place and returns them.

        Args:
            nodes: List of node dictionaries

        Returns:
            Same list with display_name, full_name, service_name added
        """
        for node in nodes:
            display = self.get_display_name(node)
            node["display_name"] = display.short_name
            node["full_name"] = display.full_name
            if display.service_name:
                node["service_name"] = display.service_name

            # Update the main name field for compatibility
            if display.short_name:
                node["name"] = display.short_name

        return nodes

    def group_by_service(
        self,
        resources: list[dict[str, Any]],
        resource_type: str | None = None,
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Group resources by their extracted service name.

        Useful for grouping ALBs or other resources by application.

        Args:
            resources: List of resource dictionaries
            resource_type: Optional filter by resource type

        Returns:
            Dict of service_name -> list of resources
        """
        groups: dict[str, list[dict[str, Any]]] = {}

        for resource in resources:
            if resource_type and resource.get("type") != resource_type:
                continue

            display = self.get_display_name(resource)
            service = display.service_name or "other"

            if service not in groups:
                groups[service] = []
            groups[service].append(resource)

        return groups


def get_type_display_name(resource_type: str) -> str:
    """
    Get human-readable display name for a resource type.

    Args:
        resource_type: AWS resource type (e.g., 'aws_lb')

    Returns:
        Human-readable name (e.g., 'Application Load Balancer')
    """
    type_names: dict[str, str] = {
        "aws_vpc": "VPC",
        "aws_subnet": "Subnet",
        "aws_security_group": "Security Group",
        "aws_instance": "EC2 Instance",
        "aws_db_instance": "RDS Database",
        "aws_s3_bucket": "S3 Bucket",
        "aws_lb": "Load Balancer",
        "aws_lb_listener": "LB Listener",
        "aws_lb_target_group": "Target Group",
        "aws_lambda_function": "Lambda Function",
        "aws_iam_role": "IAM Role",
        "aws_kms_key": "KMS Key",
        "aws_elasticache_cluster": "ElastiCache",
        "aws_nat_gateway": "NAT Gateway",
        "aws_eip": "Elastic IP",
        "aws_route_table": "Route Table",
        "aws_internet_gateway": "Internet Gateway",
        "aws_db_subnet_group": "DB Subnet Group",
        "aws_elasticache_subnet_group": "ElastiCache Subnet Group",
        "aws_sqs_queue": "SQS Queue",
        "aws_sns_topic": "SNS Topic",
        "aws_ebs_volume": "EBS Volume",
        "aws_s3_bucket_policy": "S3 Bucket Policy",
        "aws_vpc_endpoint": "VPC Endpoint",
        "aws_launch_template": "Launch Template",
        "aws_autoscaling_group": "Auto Scaling Group",
        "aws_db_parameter_group": "DB Parameter Group",
        "aws_route": "Route",
    }

    if resource_type in type_names:
        return type_names[resource_type]

    # Generic conversion: aws_foo_bar -> Foo Bar
    name = resource_type.replace("aws_", "").replace("_", " ")
    return name.title()


def get_type_plural_name(resource_type: str, count: int = 2) -> str:
    """
    Get plural form of resource type name.

    Args:
        resource_type: AWS resource type
        count: Number of resources (for singular vs plural)

    Returns:
        Plural form (e.g., 'EC2 Instances')
    """
    if count == 1:
        return get_type_display_name(resource_type)

    plural_forms: dict[str, str] = {
        "aws_vpc": "VPCs",
        "aws_subnet": "Subnets",
        "aws_security_group": "Security Groups",
        "aws_instance": "EC2 Instances",
        "aws_db_instance": "RDS Databases",
        "aws_s3_bucket": "S3 Buckets",
        "aws_lb": "Load Balancers",
        "aws_lb_listener": "LB Listeners",
        "aws_lb_target_group": "Target Groups",
        "aws_lambda_function": "Lambda Functions",
        "aws_iam_role": "IAM Roles",
        "aws_kms_key": "KMS Keys",
        "aws_elasticache_cluster": "ElastiCache Clusters",
        "aws_nat_gateway": "NAT Gateways",
        "aws_eip": "Elastic IPs",
        "aws_route_table": "Route Tables",
        "aws_internet_gateway": "Internet Gateways",
        "aws_db_subnet_group": "DB Subnet Groups",
        "aws_elasticache_subnet_group": "ElastiCache Subnet Groups",
        "aws_sqs_queue": "SQS Queues",
        "aws_sns_topic": "SNS Topics",
        "aws_ebs_volume": "EBS Volumes",
        "aws_s3_bucket_policy": "S3 Bucket Policies",
        "aws_vpc_endpoint": "VPC Endpoints",
        "aws_launch_template": "Launch Templates",
        "aws_autoscaling_group": "Auto Scaling Groups",
        "aws_db_parameter_group": "DB Parameter Groups",
        "aws_route": "Routes",
    }

    if resource_type in plural_forms:
        return plural_forms[resource_type]

    # Generic: just add 's'
    singular = get_type_display_name(resource_type)
    return singular + "s"
