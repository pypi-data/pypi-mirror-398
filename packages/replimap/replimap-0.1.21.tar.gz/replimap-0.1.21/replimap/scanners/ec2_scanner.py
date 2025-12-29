"""
EC2 Scanner for RepliMap.

Scans EC2 instances, capturing their configuration for replication
in a staging environment.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar

from botocore.exceptions import ClientError

from replimap.core.models import DependencyType, ResourceNode, ResourceType

from .base import BaseScanner, ScannerRegistry

if TYPE_CHECKING:
    from replimap.core import GraphEngine


logger = logging.getLogger(__name__)


@ScannerRegistry.register
class EC2Scanner(BaseScanner):
    """
    Scans EC2 instances.

    Captures instance configuration including:
    - Instance type (will be downsized by transformer)
    - AMI ID
    - Network configuration (subnet, security groups)
    - Storage configuration (EBS volumes)
    - IAM instance profile
    - User data (will be sanitized)
    """

    resource_types: ClassVar[list[str]] = ["aws_instance"]

    # EC2 instances reference subnets and security groups for dependency edges
    depends_on_types: ClassVar[list[str]] = [
        "aws_subnet",
        "aws_security_group",
    ]

    def scan(self, graph: GraphEngine) -> None:
        """Scan all EC2 instances and add to graph."""
        logger.info(f"Scanning EC2 instances in {self.region}...")

        try:
            ec2 = self.get_client("ec2")
            self._scan_instances(ec2, graph)

        except ClientError as e:
            self._handle_aws_error(e, "EC2 scanning")

    def _scan_instances(self, ec2: Any, graph: GraphEngine) -> None:
        """Scan all EC2 instances in the region."""
        logger.debug("Scanning EC2 instances...")

        paginator = ec2.get_paginator("describe_instances")
        for page in paginator.paginate():
            for reservation in page.get("Reservations", []):
                for instance in reservation.get("Instances", []):
                    self._process_instance(instance, graph)

    def _process_instance(self, instance: dict[str, Any], graph: GraphEngine) -> None:
        """
        Process a single EC2 instance.

        Args:
            instance: AWS instance data
            graph: Graph to add the resource to
        """
        instance_id = instance["InstanceId"]
        state = instance.get("State", {}).get("Name", "unknown")

        # Only include running instances - skip stopped, terminated, etc.
        if state != "running":
            logger.debug(f"Skipping {state} instance: {instance_id}")
            return

        tags = self._extract_tags(instance.get("Tags"))
        subnet_id = instance.get("SubnetId")
        vpc_id = instance.get("VpcId")

        # Extract security group IDs
        security_groups = [sg["GroupId"] for sg in instance.get("SecurityGroups", [])]

        # Extract block device mappings (EBS volumes)
        block_devices = []
        for mapping in instance.get("BlockDeviceMappings", []):
            ebs = mapping.get("Ebs", {})
            block_devices.append(
                {
                    "device_name": mapping["DeviceName"],
                    "volume_id": ebs.get("VolumeId"),
                    "delete_on_termination": ebs.get("DeleteOnTermination", True),
                }
            )

        # Extract network interfaces
        network_interfaces = []
        for eni in instance.get("NetworkInterfaces", []):
            network_interfaces.append(
                {
                    "network_interface_id": eni["NetworkInterfaceId"],
                    "device_index": eni["Attachment"]["DeviceIndex"],
                    "subnet_id": eni.get("SubnetId"),
                    "private_ip_address": eni.get("PrivateIpAddress"),
                    "security_groups": [sg["GroupId"] for sg in eni.get("Groups", [])],
                }
            )

        # Build config dictionary
        config = {
            "ami": instance["ImageId"],
            "instance_type": instance["InstanceType"],
            "key_name": instance.get("KeyName"),
            "subnet_id": subnet_id,
            "vpc_id": vpc_id,
            "security_group_ids": security_groups,
            "private_ip_address": instance.get("PrivateIpAddress"),
            "public_ip_address": instance.get("PublicIpAddress"),
            "availability_zone": instance.get("Placement", {}).get("AvailabilityZone"),
            "tenancy": instance.get("Placement", {}).get("Tenancy", "default"),
            "ebs_optimized": instance.get("EbsOptimized", False),
            "monitoring": instance.get("Monitoring", {}).get("State") == "enabled",
            "iam_instance_profile": self._extract_iam_profile(
                instance.get("IamInstanceProfile")
            ),
            "block_device_mappings": block_devices,
            "network_interfaces": network_interfaces,
            "metadata_options": self._extract_metadata_options(
                instance.get("MetadataOptions", {})
            ),
            "state": state,
        }

        # Get root volume info
        root_volume = self._get_root_volume_config(instance, block_devices)
        if root_volume:
            config["root_block_device"] = root_volume

        node = ResourceNode(
            id=instance_id,
            resource_type=ResourceType.EC2_INSTANCE,
            region=self.region,
            config=config,
            arn=f"arn:aws:ec2:{self.region}:{instance.get('OwnerId', '')}:instance/{instance_id}",
            tags=tags,
        )

        graph.add_resource(node)

        # Establish dependencies
        self._add_dependencies(node, graph)

        logger.debug(
            f"Added EC2 instance: {instance_id} ({tags.get('Name', 'unnamed')}) "
            f"- {instance['InstanceType']}"
        )

    def _add_dependencies(self, node: ResourceNode, graph: GraphEngine) -> None:
        """
        Add dependency edges for an EC2 instance.

        Dependencies:
        - EC2 -> Subnet (belongs_to)
        - EC2 -> Security Groups (uses)
        """
        instance_id = node.id
        config = node.config

        # Subnet dependency
        subnet_id = config.get("subnet_id")
        if subnet_id and graph.get_resource(subnet_id):
            graph.add_dependency(instance_id, subnet_id, DependencyType.BELONGS_TO)

        # Security group dependencies
        for sg_id in config.get("security_group_ids", []):
            if graph.get_resource(sg_id):
                graph.add_dependency(instance_id, sg_id, DependencyType.USES)

    def _extract_iam_profile(
        self, profile: dict[str, Any] | None
    ) -> dict[str, str] | None:
        """Extract IAM instance profile information."""
        if not profile:
            return None
        return {
            "arn": profile.get("Arn", ""),
            "name": profile.get("Arn", "").split("/")[-1] if profile.get("Arn") else "",
        }

    def _extract_metadata_options(self, options: dict[str, Any]) -> dict[str, Any]:
        """Extract instance metadata options."""
        return {
            "http_endpoint": options.get("HttpEndpoint", "enabled"),
            "http_tokens": options.get("HttpTokens", "optional"),
            "http_put_response_hop_limit": options.get("HttpPutResponseHopLimit", 1),
            "instance_metadata_tags": options.get("InstanceMetadataTags", "disabled"),
        }

    def _get_root_volume_config(
        self,
        instance: dict[str, Any],
        block_devices: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        """
        Get root volume configuration.

        This requires an additional API call to describe the volume.
        """
        root_device_name = instance.get("RootDeviceName")
        if not root_device_name:
            return None

        for bd in block_devices:
            if bd["device_name"] == root_device_name:
                # We have the basic info, could enhance with describe_volumes
                return {
                    "device_name": bd["device_name"],
                    "delete_on_termination": bd.get("delete_on_termination", True),
                    # Volume size/type would need describe_volumes call
                }

        return None
