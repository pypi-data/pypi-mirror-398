"""
VPC Scanner for RepliMap.

Scans VPCs, Subnets, and Security Groups - the foundational networking
resources that most other resources depend on.
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
class VPCScanner(BaseScanner):
    """
    Scans VPC, Subnet, and Security Group resources.

    These are foundational resources that form the network topology.
    The dependency chain is:
        VPC <- Subnet <- EC2/RDS
        VPC <- SecurityGroup <- EC2/RDS
    """

    resource_types: ClassVar[list[str]] = [
        "aws_vpc",
        "aws_subnet",
        "aws_security_group",
    ]

    def scan(self, graph: GraphEngine) -> None:
        """
        Scan all VPC-related resources and add to graph.

        Order matters: VPCs first, then Subnets and Security Groups.
        """
        logger.info(f"Scanning VPC resources in {self.region}...")

        try:
            ec2 = self.get_client("ec2")

            # Scan in dependency order
            self._scan_vpcs(ec2, graph)
            self._scan_subnets(ec2, graph)
            self._scan_security_groups(ec2, graph)

        except ClientError as e:
            self._handle_aws_error(e, "VPC scanning")

    def _scan_vpcs(self, ec2: Any, graph: GraphEngine) -> None:
        """Scan all VPCs in the region."""
        logger.debug("Scanning VPCs...")

        paginator = ec2.get_paginator("describe_vpcs")
        for page in paginator.paginate():
            for vpc in page.get("Vpcs", []):
                vpc_id = vpc["VpcId"]
                tags = self._extract_tags(vpc.get("Tags"))

                node = ResourceNode(
                    id=vpc_id,
                    resource_type=ResourceType.VPC,
                    region=self.region,
                    config={
                        "cidr_block": vpc["CidrBlock"],
                        "instance_tenancy": vpc.get("InstanceTenancy", "default"),
                        "enable_dns_support": True,  # Default, could query
                        "enable_dns_hostnames": vpc.get("EnableDnsHostnames", False),
                        "cidr_block_association_set": [
                            {
                                "cidr_block": assoc["CidrBlock"],
                                "state": assoc["CidrBlockState"]["State"],
                            }
                            for assoc in vpc.get("CidrBlockAssociationSet", [])
                        ],
                    },
                    arn=f"arn:aws:ec2:{self.region}:{self._get_account_id(vpc)}:vpc/{vpc_id}",
                    tags=tags,
                )

                graph.add_resource(node)
                logger.debug(f"Added VPC: {vpc_id} ({tags.get('Name', 'unnamed')})")

    def _scan_subnets(self, ec2: Any, graph: GraphEngine) -> None:
        """Scan all Subnets in the region."""
        logger.debug("Scanning Subnets...")

        paginator = ec2.get_paginator("describe_subnets")
        for page in paginator.paginate():
            for subnet in page.get("Subnets", []):
                subnet_id = subnet["SubnetId"]
                vpc_id = subnet["VpcId"]
                tags = self._extract_tags(subnet.get("Tags"))

                node = ResourceNode(
                    id=subnet_id,
                    resource_type=ResourceType.SUBNET,
                    region=self.region,
                    config={
                        "vpc_id": vpc_id,
                        "cidr_block": subnet["CidrBlock"],
                        "availability_zone": subnet["AvailabilityZone"],
                        "map_public_ip_on_launch": subnet.get(
                            "MapPublicIpOnLaunch", False
                        ),
                        "available_ip_address_count": subnet.get(
                            "AvailableIpAddressCount"
                        ),
                    },
                    arn=subnet.get("SubnetArn"),
                    tags=tags,
                )

                graph.add_resource(node)

                # Establish dependency: Subnet -> VPC
                if graph.get_resource(vpc_id):
                    graph.add_dependency(subnet_id, vpc_id, DependencyType.BELONGS_TO)

                logger.debug(
                    f"Added Subnet: {subnet_id} in {subnet['AvailabilityZone']}"
                )

    def _scan_security_groups(self, ec2: Any, graph: GraphEngine) -> None:
        """Scan all Security Groups in the region."""
        logger.debug("Scanning Security Groups...")

        paginator = ec2.get_paginator("describe_security_groups")
        for page in paginator.paginate():
            for sg in page.get("SecurityGroups", []):
                sg_id = sg["GroupId"]
                vpc_id = sg.get("VpcId")
                tags = self._extract_tags(sg.get("Tags"))

                # Process ingress rules
                ingress_rules = []
                for rule in sg.get("IpPermissions", []):
                    ingress_rules.append(self._process_rule(rule))

                # Process egress rules
                egress_rules = []
                for rule in sg.get("IpPermissionsEgress", []):
                    egress_rules.append(self._process_rule(rule))

                node = ResourceNode(
                    id=sg_id,
                    resource_type=ResourceType.SECURITY_GROUP,
                    region=self.region,
                    config={
                        "vpc_id": vpc_id,
                        "name": sg["GroupName"],
                        "description": sg.get("Description", ""),
                        "ingress": ingress_rules,
                        "egress": egress_rules,
                    },
                    arn=f"arn:aws:ec2:{self.region}:{sg.get('OwnerId', '')}:security-group/{sg_id}",
                    tags=tags,
                )

                graph.add_resource(node)

                # Establish dependency: SecurityGroup -> VPC
                if vpc_id and graph.get_resource(vpc_id):
                    graph.add_dependency(sg_id, vpc_id, DependencyType.BELONGS_TO)

                logger.debug(f"Added Security Group: {sg_id} ({sg['GroupName']})")

    def _process_rule(self, rule: dict[str, Any]) -> dict[str, Any]:
        """
        Process a security group rule into a cleaner format.

        Args:
            rule: AWS security group rule

        Returns:
            Cleaned rule dictionary
        """
        processed = {
            "protocol": rule.get("IpProtocol", "-1"),
            "from_port": rule.get("FromPort", 0),
            "to_port": rule.get("ToPort", 0),
        }

        # Handle CIDR blocks
        cidr_blocks = [ip["CidrIp"] for ip in rule.get("IpRanges", [])]
        if cidr_blocks:
            processed["cidr_blocks"] = cidr_blocks

        # Handle IPv6 CIDR blocks
        ipv6_blocks = [ip["CidrIpv6"] for ip in rule.get("Ipv6Ranges", [])]
        if ipv6_blocks:
            processed["ipv6_cidr_blocks"] = ipv6_blocks

        # Handle security group references
        sg_refs = [
            {
                "security_group_id": pair.get("GroupId"),
                "user_id": pair.get("UserId"),
            }
            for pair in rule.get("UserIdGroupPairs", [])
        ]
        if sg_refs:
            processed["security_groups"] = sg_refs

        # Handle prefix lists
        prefix_lists = [pl["PrefixListId"] for pl in rule.get("PrefixListIds", [])]
        if prefix_lists:
            processed["prefix_list_ids"] = prefix_lists

        return processed

    def _get_account_id(self, vpc: dict[str, Any]) -> str:
        """Extract account ID from VPC data."""
        return vpc.get("OwnerId", "")
