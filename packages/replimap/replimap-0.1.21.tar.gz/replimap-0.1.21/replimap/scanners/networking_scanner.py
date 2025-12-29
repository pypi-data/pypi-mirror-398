"""
Networking Scanner for RepliMap Phase 2.

Scans Route Tables, Internet Gateways, NAT Gateways, and VPC Endpoints.
These resources complete the VPC networking topology.
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
class NetworkingScanner(BaseScanner):
    """
    Scans additional networking resources.

    Dependency chain:
        VPC <- Route Table <- Route
        VPC <- Internet Gateway
        Subnet <- NAT Gateway -> Internet Gateway
        VPC <- VPC Endpoint
    """

    resource_types: ClassVar[list[str]] = [
        "aws_route_table",
        "aws_route",
        "aws_internet_gateway",
        "aws_nat_gateway",
        "aws_vpc_endpoint",
        "aws_network_acl",
    ]

    # These resources reference VPCs and subnets for dependency edges
    depends_on_types: ClassVar[list[str]] = [
        "aws_vpc",
        "aws_subnet",
        "aws_security_group",
    ]

    def scan(self, graph: GraphEngine) -> None:
        """Scan all networking resources and add to graph.

        Each resource type is scanned independently with its own error handling.
        This ensures partial success - if one resource type fails (e.g., due to
        IAM permissions), others will still be scanned.
        """
        logger.info(f"Scanning networking resources in {self.region}...")

        ec2 = self.get_client("ec2")

        # Define scan steps - each wrapped independently for resilience
        scan_steps = [
            (self._scan_internet_gateways, "Internet Gateways"),
            (self._scan_nat_gateways, "NAT Gateways"),
            (self._scan_route_tables, "Route Tables"),
            (self._scan_vpc_endpoints, "VPC Endpoints"),
            (self._scan_network_acls, "Network ACLs"),
        ]

        for scan_func, resource_name in scan_steps:
            try:
                scan_func(ec2, graph)
            except ClientError as e:
                # Log error but continue to next resource type
                self._handle_aws_error(e, resource_name)
                logger.warning(f"Continuing scan despite {resource_name} failure")

    def _scan_internet_gateways(self, ec2: Any, graph: GraphEngine) -> None:
        """Scan all Internet Gateways in the region."""
        logger.debug("Scanning Internet Gateways...")

        paginator = ec2.get_paginator("describe_internet_gateways")
        for page in paginator.paginate():
            for igw in page.get("InternetGateways", []):
                igw_id = igw["InternetGatewayId"]
                tags = self._extract_tags(igw.get("Tags"))

                # Get attached VPC
                attachments = igw.get("Attachments", [])
                vpc_id = attachments[0]["VpcId"] if attachments else None

                node = ResourceNode(
                    id=igw_id,
                    resource_type=ResourceType.INTERNET_GATEWAY,
                    region=self.region,
                    config={
                        "vpc_id": vpc_id,
                        "attachments": [
                            {"vpc_id": att["VpcId"], "state": att.get("State")}
                            for att in attachments
                        ],
                    },
                    arn=f"arn:aws:ec2:{self.region}:{igw.get('OwnerId', '')}:internet-gateway/{igw_id}",
                    tags=tags,
                )

                graph.add_resource(node)

                # Establish dependency: IGW -> VPC
                if vpc_id and graph.get_resource(vpc_id):
                    graph.add_dependency(igw_id, vpc_id, DependencyType.BELONGS_TO)

                logger.debug(f"Added Internet Gateway: {igw_id}")

    def _scan_nat_gateways(self, ec2: Any, graph: GraphEngine) -> None:
        """Scan all NAT Gateways in the region."""
        logger.debug("Scanning NAT Gateways...")

        paginator = ec2.get_paginator("describe_nat_gateways")
        for page in paginator.paginate():
            for nat in page.get("NatGateways", []):
                # Skip deleted NAT gateways
                if nat.get("State") == "deleted":
                    continue

                nat_id = nat["NatGatewayId"]
                vpc_id = nat.get("VpcId")
                subnet_id = nat.get("SubnetId")
                tags = self._extract_tags(nat.get("Tags"))

                # Get EIP allocation
                addresses = nat.get("NatGatewayAddresses", [])
                allocation_id = addresses[0].get("AllocationId") if addresses else None
                public_ip = addresses[0].get("PublicIp") if addresses else None

                node = ResourceNode(
                    id=nat_id,
                    resource_type=ResourceType.NAT_GATEWAY,
                    region=self.region,
                    config={
                        "vpc_id": vpc_id,
                        "subnet_id": subnet_id,
                        "allocation_id": allocation_id,
                        "public_ip": public_ip,
                        "connectivity_type": nat.get("ConnectivityType", "public"),
                        "state": nat.get("State"),
                    },
                    arn=f"arn:aws:ec2:{self.region}::natgateway/{nat_id}",
                    tags=tags,
                )

                graph.add_resource(node)

                # Establish dependencies
                if subnet_id and graph.get_resource(subnet_id):
                    graph.add_dependency(nat_id, subnet_id, DependencyType.BELONGS_TO)

                logger.debug(f"Added NAT Gateway: {nat_id}")

    def _scan_route_tables(self, ec2: Any, graph: GraphEngine) -> None:
        """Scan all Route Tables in the region."""
        logger.debug("Scanning Route Tables...")

        paginator = ec2.get_paginator("describe_route_tables")
        for page in paginator.paginate():
            for rt in page.get("RouteTables", []):
                rt_id = rt["RouteTableId"]
                vpc_id = rt.get("VpcId")
                tags = self._extract_tags(rt.get("Tags"))

                # Process routes
                routes = []
                for route in rt.get("Routes", []):
                    route_config = {
                        "destination_cidr_block": route.get("DestinationCidrBlock"),
                        "destination_ipv6_cidr_block": route.get(
                            "DestinationIpv6CidrBlock"
                        ),
                        "gateway_id": route.get("GatewayId"),
                        "nat_gateway_id": route.get("NatGatewayId"),
                        "instance_id": route.get("InstanceId"),
                        "vpc_endpoint_id": route.get("VpcEndpointId"),
                        "vpc_peering_connection_id": route.get(
                            "VpcPeeringConnectionId"
                        ),
                        "transit_gateway_id": route.get("TransitGatewayId"),
                        "state": route.get("State"),
                    }
                    # Remove None values
                    routes.append({k: v for k, v in route_config.items() if v})

                # Detect if this is the VPC's main route table
                is_main_route_table = any(
                    assoc.get("Main", False) for assoc in rt.get("Associations", [])
                )

                # Process associations
                associations = []
                for assoc in rt.get("Associations", []):
                    associations.append(
                        {
                            "association_id": assoc.get("RouteTableAssociationId"),
                            "subnet_id": assoc.get("SubnetId"),
                            "gateway_id": assoc.get("GatewayId"),
                            "main": assoc.get("Main", False),
                        }
                    )

                node = ResourceNode(
                    id=rt_id,
                    resource_type=ResourceType.ROUTE_TABLE,
                    region=self.region,
                    config={
                        "vpc_id": vpc_id,
                        "routes": routes,
                        "associations": associations,
                        "is_main": is_main_route_table,
                        "propagating_vgws": [
                            vgw["GatewayId"] for vgw in rt.get("PropagatingVgws", [])
                        ],
                    },
                    arn=f"arn:aws:ec2:{self.region}:{rt.get('OwnerId', '')}:route-table/{rt_id}",
                    tags=tags,
                )

                graph.add_resource(node)

                # Establish dependency: Route Table -> VPC
                if vpc_id and graph.get_resource(vpc_id):
                    graph.add_dependency(rt_id, vpc_id, DependencyType.BELONGS_TO)

                # Add dependencies for route targets
                for route in routes:
                    if route.get("gateway_id") and route["gateway_id"].startswith(
                        "igw-"
                    ):
                        if graph.get_resource(route["gateway_id"]):
                            graph.add_dependency(
                                rt_id, route["gateway_id"], DependencyType.REFERENCES
                            )
                    if route.get("nat_gateway_id"):
                        if graph.get_resource(route["nat_gateway_id"]):
                            graph.add_dependency(
                                rt_id,
                                route["nat_gateway_id"],
                                DependencyType.REFERENCES,
                            )

                logger.debug(f"Added Route Table: {rt_id}")

    def _scan_vpc_endpoints(self, ec2: Any, graph: GraphEngine) -> None:
        """Scan all VPC Endpoints in the region."""
        logger.debug("Scanning VPC Endpoints...")

        paginator = ec2.get_paginator("describe_vpc_endpoints")
        for page in paginator.paginate():
            for endpoint in page.get("VpcEndpoints", []):
                endpoint_id = endpoint["VpcEndpointId"]
                vpc_id = endpoint.get("VpcId")
                tags = self._extract_tags(endpoint.get("Tags"))

                node = ResourceNode(
                    id=endpoint_id,
                    resource_type=ResourceType.VPC_ENDPOINT,
                    region=self.region,
                    config={
                        "vpc_id": vpc_id,
                        "service_name": endpoint.get("ServiceName"),
                        "vpc_endpoint_type": endpoint.get("VpcEndpointType"),
                        "state": endpoint.get("State"),
                        "policy_document": endpoint.get("PolicyDocument"),
                        "route_table_ids": endpoint.get("RouteTableIds", []),
                        "subnet_ids": endpoint.get("SubnetIds", []),
                        "security_group_ids": [
                            sg["GroupId"] for sg in endpoint.get("Groups", [])
                        ],
                        "private_dns_enabled": endpoint.get("PrivateDnsEnabled"),
                    },
                    arn=f"arn:aws:ec2:{self.region}::vpc-endpoint/{endpoint_id}",
                    tags=tags,
                )

                graph.add_resource(node)

                # Establish dependency: VPC Endpoint -> VPC
                if vpc_id and graph.get_resource(vpc_id):
                    graph.add_dependency(endpoint_id, vpc_id, DependencyType.BELONGS_TO)

                # Add dependencies on security groups
                for sg_id in node.config.get("security_group_ids", []):
                    if graph.get_resource(sg_id):
                        graph.add_dependency(endpoint_id, sg_id, DependencyType.USES)

                logger.debug(f"Added VPC Endpoint: {endpoint_id}")

    def _scan_network_acls(self, ec2: Any, graph: GraphEngine) -> None:
        """Scan all Network ACLs in the region."""
        logger.debug("Scanning Network ACLs...")

        paginator = ec2.get_paginator("describe_network_acls")
        for page in paginator.paginate():
            for nacl in page.get("NetworkAcls", []):
                nacl_id = nacl["NetworkAclId"]
                vpc_id = nacl.get("VpcId")
                tags = self._extract_tags(nacl.get("Tags"))
                is_default = nacl.get("IsDefault", False)

                # Process ingress rules (Egress=False)
                ingress_rules = []
                egress_rules = []
                for entry in nacl.get("Entries", []):
                    rule = {
                        "rule_number": entry.get("RuleNumber"),
                        "protocol": entry.get("Protocol"),
                        "rule_action": entry.get("RuleAction"),
                        "cidr_block": entry.get("CidrBlock"),
                        "ipv6_cidr_block": entry.get("Ipv6CidrBlock"),
                        "from_port": entry.get("PortRange", {}).get("From"),
                        "to_port": entry.get("PortRange", {}).get("To"),
                        "icmp_type": entry.get("IcmpTypeCode", {}).get("Type"),
                        "icmp_code": entry.get("IcmpTypeCode", {}).get("Code"),
                    }
                    # Remove None values
                    rule = {k: v for k, v in rule.items() if v is not None}

                    if entry.get("Egress"):
                        egress_rules.append(rule)
                    else:
                        ingress_rules.append(rule)

                # Get subnet associations
                subnet_ids = [
                    assoc["SubnetId"]
                    for assoc in nacl.get("Associations", [])
                    if assoc.get("SubnetId")
                ]

                node = ResourceNode(
                    id=nacl_id,
                    resource_type=ResourceType.NETWORK_ACL,
                    region=self.region,
                    config={
                        "vpc_id": vpc_id,
                        "is_default": is_default,
                        "ingress": ingress_rules,
                        "egress": egress_rules,
                        "subnet_ids": subnet_ids,
                    },
                    arn=f"arn:aws:ec2:{self.region}:{nacl.get('OwnerId', '')}:network-acl/{nacl_id}",
                    tags=tags,
                )

                graph.add_resource(node)

                # Establish dependency: NACL -> VPC
                if vpc_id and graph.get_resource(vpc_id):
                    graph.add_dependency(nacl_id, vpc_id, DependencyType.BELONGS_TO)

                # Add dependencies on subnets
                for subnet_id in subnet_ids:
                    if graph.get_resource(subnet_id):
                        graph.add_dependency(
                            nacl_id, subnet_id, DependencyType.REFERENCES
                        )

                logger.debug(
                    f"Added Network ACL: {nacl_id} "
                    f"({'default' if is_default else 'custom'})"
                )
