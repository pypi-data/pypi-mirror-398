"""
Network Remapping Transformer for RepliMap.

Updates network references when cloning to a new VPC:
- Remaps subnet IDs
- Remaps security group IDs
- Maintains old->new ID mapping for consistent references
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from replimap.core.models import ResourceType

from .base import BaseTransformer

if TYPE_CHECKING:
    from replimap.core import GraphEngine


logger = logging.getLogger(__name__)


class NetworkRemapTransformer(BaseTransformer):
    """
    Updates network references for new VPC deployment.

    When cloning resources to a new VPC, all references to the
    original VPC, subnets, and security groups need to be updated.

    This transformer:
    1. Builds a mapping of old IDs to new Terraform references
    2. Updates all config fields that reference network resources
    3. Maintains consistency across all resources

    The output uses Terraform resource references (aws_vpc.name.id)
    instead of hardcoded IDs, enabling proper resource ordering.
    """

    name = "NetworkRemapTransformer"

    def __init__(
        self,
        target_vpc_id: str | None = None,
        use_terraform_refs: bool = True,
    ) -> None:
        """
        Initialize the network remapper.

        Args:
            target_vpc_id: If specified, remap to an existing VPC ID
            use_terraform_refs: Use Terraform references vs hardcoded IDs
        """
        self.target_vpc_id = target_vpc_id
        self.use_terraform_refs = use_terraform_refs
        self._id_map: dict[str, str] = {}

    def transform(self, graph: GraphEngine) -> GraphEngine:
        """
        Remap network references in all resources.

        Args:
            graph: The GraphEngine to transform

        Returns:
            The same GraphEngine with remapped references
        """
        # Build ID mapping from graph
        self._build_id_map(graph)

        # Remap all resources
        for resource in graph.iter_resources():
            resource.config = self._remap_config(resource.config)

        logger.info(f"Remapped {len(self._id_map)} network resource references")

        return graph

    def _build_id_map(self, graph: GraphEngine) -> None:
        """
        Build mapping of old IDs to new Terraform references.

        Args:
            graph: The GraphEngine containing resources
        """
        self._id_map = {}

        for resource in graph.iter_resources():
            if self.use_terraform_refs:
                # Map to Terraform references
                if resource.resource_type == ResourceType.VPC:
                    if self.target_vpc_id:
                        self._id_map[resource.id] = self.target_vpc_id
                    else:
                        self._id_map[resource.id] = (
                            f"aws_vpc.{resource.terraform_name}.id"
                        )
                elif resource.resource_type == ResourceType.SUBNET:
                    self._id_map[resource.id] = (
                        f"aws_subnet.{resource.terraform_name}.id"
                    )
                elif resource.resource_type == ResourceType.SECURITY_GROUP:
                    self._id_map[resource.id] = (
                        f"aws_security_group.{resource.terraform_name}.id"
                    )
                elif resource.resource_type == ResourceType.DB_SUBNET_GROUP:
                    self._id_map[resource.id] = (
                        f"aws_db_subnet_group.{resource.terraform_name}.name"
                    )
                elif resource.resource_type == ResourceType.EC2_INSTANCE:
                    self._id_map[resource.id] = (
                        f"aws_instance.{resource.terraform_name}.id"
                    )
                elif resource.resource_type == ResourceType.ROUTE_TABLE:
                    self._id_map[resource.id] = (
                        f"aws_route_table.{resource.terraform_name}.id"
                    )
                elif resource.resource_type == ResourceType.INTERNET_GATEWAY:
                    self._id_map[resource.id] = (
                        f"aws_internet_gateway.{resource.terraform_name}.id"
                    )
                elif resource.resource_type == ResourceType.NAT_GATEWAY:
                    self._id_map[resource.id] = (
                        f"aws_nat_gateway.{resource.terraform_name}.id"
                    )
                elif resource.resource_type == ResourceType.LAUNCH_TEMPLATE:
                    self._id_map[resource.id] = (
                        f"aws_launch_template.{resource.terraform_name}.id"
                    )
                elif resource.resource_type == ResourceType.LB_TARGET_GROUP:
                    # For target groups, also map the ARN pattern
                    self._id_map[resource.id] = (
                        f"aws_lb_target_group.{resource.terraform_name}.arn"
                    )

    def _remap_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """
        Recursively remap IDs in configuration.

        Args:
            config: Configuration dictionary

        Returns:
            Configuration with remapped IDs
        """
        result: dict[str, Any] = {}

        # Fields that contain network/compute resource IDs
        id_fields = {
            "vpc_id",
            "subnet_id",
            "security_group_id",
            "db_subnet_group_name",
            "instance_id",
            "route_table_id",
            "gateway_id",
            "nat_gateway_id",
            "network_interface_id",
            "launch_template_id",
            "target_group_arn",
        }
        list_id_fields = {
            "subnet_ids",
            "security_group_ids",
            "vpc_security_group_ids",
            "route_table_ids",
            "target_group_arns",
        }

        for key, value in config.items():
            if isinstance(value, str):
                if key in id_fields and value in self._id_map:
                    result[key] = self._id_map[value]
                    logger.debug(f"Remapped {key}: {value} -> {self._id_map[value]}")
                elif value in self._id_map:
                    # Check if it's a network ID even if field name is different
                    if self._looks_like_network_id(value):
                        result[key] = self._id_map[value]
                    else:
                        result[key] = value
                else:
                    result[key] = value

            elif isinstance(value, list):
                if key in list_id_fields:
                    result[key] = [
                        self._id_map.get(v, v) if isinstance(v, str) else v
                        for v in value
                    ]
                else:
                    result[key] = self._remap_list(value)

            elif isinstance(value, dict):
                result[key] = self._remap_config(value)

            else:
                result[key] = value

        return result

    def _remap_list(self, data: list[Any]) -> list[Any]:
        """
        Recursively remap IDs in a list.

        Args:
            data: List to process

        Returns:
            List with remapped IDs
        """
        result: list[Any] = []
        for item in data:
            if isinstance(item, dict):
                result.append(self._remap_config(item))
            elif isinstance(item, list):
                result.append(self._remap_list(item))
            elif isinstance(item, str) and item in self._id_map:
                result.append(self._id_map[item])
            else:
                result.append(item)
        return result

    def _looks_like_network_id(self, value: str) -> bool:
        """
        Check if a string looks like a network or compute resource ID.

        Args:
            value: String to check

        Returns:
            True if it looks like a known AWS resource ID pattern
        """
        prefixes = (
            "vpc-",  # VPC
            "subnet-",  # Subnet
            "sg-",  # Security Group
            "i-",  # EC2 Instance
            "rtb-",  # Route Table
            "igw-",  # Internet Gateway
            "nat-",  # NAT Gateway
            "eni-",  # Network Interface
            "lt-",  # Launch Template
        )
        return any(value.startswith(prefix) for prefix in prefixes)
