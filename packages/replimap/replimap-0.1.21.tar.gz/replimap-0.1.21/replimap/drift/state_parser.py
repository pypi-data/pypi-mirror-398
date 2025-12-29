"""Terraform state file parser."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class TFResource:
    """Parsed resource from Terraform state."""

    type: str  # e.g., "aws_security_group"
    name: str  # e.g., "web"
    address: str  # e.g., "aws_security_group.web"
    id: str  # AWS resource ID
    attributes: dict[str, Any]  # All resource attributes
    provider: str = "aws"
    module: str = ""  # Module path if any


@dataclass
class TFState:
    """Parsed Terraform state."""

    version: int
    terraform_version: str
    resources: list[TFResource]
    outputs: dict[str, Any]

    def get_resource_by_id(self, resource_id: str) -> TFResource | None:
        """Find resource by AWS ID."""
        for r in self.resources:
            if r.id == resource_id:
                return r
        return None

    def get_resources_by_type(self, resource_type: str) -> list[TFResource]:
        """Get all resources of a specific type."""
        return [r for r in self.resources if r.type == resource_type]


class TerraformStateParser:
    """Parse Terraform state files (v4 format)."""

    SUPPORTED_RESOURCE_TYPES = {
        # Compute
        "aws_instance",
        "aws_launch_template",
        "aws_autoscaling_group",
        "aws_lambda_function",
        # Network
        "aws_vpc",
        "aws_subnet",
        "aws_security_group",
        "aws_network_acl",
        "aws_route_table",
        "aws_internet_gateway",
        "aws_nat_gateway",
        "aws_eip",
        "aws_vpc_endpoint",
        # Load Balancing
        "aws_lb",
        "aws_lb_listener",
        "aws_lb_target_group",
        # Database
        "aws_db_instance",
        "aws_db_subnet_group",
        "aws_elasticache_cluster",
        "aws_elasticache_replication_group",
        # Storage
        "aws_s3_bucket",
        "aws_s3_bucket_policy",
        "aws_s3_bucket_public_access_block",
        "aws_ebs_volume",
        # IAM
        "aws_iam_role",
        "aws_iam_policy",
        "aws_iam_role_policy_attachment",
        # Security
        "aws_kms_key",
        # Monitoring
        "aws_cloudwatch_log_group",
        "aws_cloudwatch_metric_alarm",
    }

    def parse(self, state_path: Path) -> TFState:
        """Parse a Terraform state file.

        Args:
            state_path: Path to terraform.tfstate file

        Returns:
            Parsed TFState object

        Raises:
            ValueError: If state file is invalid or unsupported version
        """
        if not state_path.exists():
            raise FileNotFoundError(f"State file not found: {state_path}")

        with open(state_path) as f:
            raw_state = json.load(f)

        # Validate version
        version = raw_state.get("version", 0)
        if version < 4:
            raise ValueError(
                f"Unsupported state version {version}. Only v4+ supported."
            )

        # Parse resources
        resources = self._parse_resources(raw_state.get("resources", []))

        logger.info(f"Parsed {len(resources)} resources from state file")

        return TFState(
            version=version,
            terraform_version=raw_state.get("terraform_version", "unknown"),
            resources=resources,
            outputs=raw_state.get("outputs", {}),
        )

    def _parse_resources(self, raw_resources: list[dict]) -> list[TFResource]:
        """Parse resources from raw state data."""
        resources = []

        for raw in raw_resources:
            resource_type = raw.get("type", "")

            # Skip unsupported types
            if resource_type not in self.SUPPORTED_RESOURCE_TYPES:
                logger.debug(f"Skipping unsupported resource type: {resource_type}")
                continue

            # Handle module prefix
            module = raw.get("module", "")
            name = raw.get("name", "")

            if module:
                address = f"{module}.{resource_type}.{name}"
            else:
                address = f"{resource_type}.{name}"

            # Parse instances (usually one, but could be count/for_each)
            for instance in raw.get("instances", []):
                attributes = instance.get("attributes", {})
                resource_id = attributes.get("id", "")

                if not resource_id:
                    logger.warning(f"Resource {address} has no ID, skipping")
                    continue

                # Handle index key for count/for_each
                index_key = instance.get("index_key")
                if index_key is not None:
                    if isinstance(index_key, str):
                        instance_address = f'{address}["{index_key}"]'
                    else:
                        instance_address = f"{address}[{index_key}]"
                else:
                    instance_address = address

                resources.append(
                    TFResource(
                        type=resource_type,
                        name=name,
                        address=instance_address,
                        id=resource_id,
                        attributes=attributes,
                        provider=raw.get(
                            "provider",
                            'provider["registry.terraform.io/hashicorp/aws"]',
                        ),
                        module=module,
                    )
                )

        return resources

    def parse_remote_state(self, backend_config: dict[str, str]) -> TFState:
        """Parse state from remote backend (S3, etc).

        Args:
            backend_config: Backend configuration with bucket, key, region

        Returns:
            Parsed TFState
        """
        import boto3

        bucket = backend_config["bucket"]
        key = backend_config["key"]
        region = backend_config.get("region", "us-east-1")

        s3 = boto3.client("s3", region_name=region)

        response = s3.get_object(Bucket=bucket, Key=key)
        raw_state = json.loads(response["Body"].read().decode("utf-8"))

        # Reuse parsing logic
        version = raw_state.get("version", 0)
        if version < 4:
            raise ValueError(f"Unsupported state version {version}")

        resources = self._parse_resources(raw_state.get("resources", []))

        return TFState(
            version=version,
            terraform_version=raw_state.get("terraform_version", "unknown"),
            resources=resources,
            outputs=raw_state.get("outputs", {}),
        )
