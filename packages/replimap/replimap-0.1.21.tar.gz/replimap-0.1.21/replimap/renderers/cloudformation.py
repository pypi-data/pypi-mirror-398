"""
CloudFormation Renderer for RepliMap.

Converts the resource graph to AWS CloudFormation YAML templates.
This renderer requires Solo plan or higher.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from replimap.core.models import ResourceType
from replimap.licensing import Feature
from replimap.licensing.gates import feature_gate
from replimap.renderers.base import BaseRenderer

if TYPE_CHECKING:
    from replimap.core import GraphEngine, ResourceNode

logger = logging.getLogger(__name__)


class CloudFormationRenderer(BaseRenderer):
    """
    Renders the resource graph to AWS CloudFormation YAML templates.

    Output structure:
    - network.yaml: VPCs, Subnets, Security Groups
    - compute.yaml: EC2 Instances
    - database.yaml: RDS Instances
    - storage.yaml: S3 Buckets

    Requires: Solo plan or higher
    """

    # Mapping of resource types to output files
    FILE_MAPPING = {
        # Phase 1 (MVP)
        ResourceType.VPC: "network.yaml",
        ResourceType.SUBNET: "network.yaml",
        ResourceType.SECURITY_GROUP: "network.yaml",
        ResourceType.EC2_INSTANCE: "compute.yaml",
        ResourceType.S3_BUCKET: "storage.yaml",
        ResourceType.RDS_INSTANCE: "database.yaml",
        ResourceType.DB_SUBNET_GROUP: "database.yaml",
        # Phase 2 - Networking
        ResourceType.ROUTE_TABLE: "network.yaml",
        ResourceType.INTERNET_GATEWAY: "network.yaml",
        ResourceType.NAT_GATEWAY: "network.yaml",
        ResourceType.VPC_ENDPOINT: "network.yaml",
        # Phase 2 - Compute
        ResourceType.LAUNCH_TEMPLATE: "compute.yaml",
        ResourceType.AUTOSCALING_GROUP: "compute.yaml",
        ResourceType.LB: "loadbalancing.yaml",
        ResourceType.LB_LISTENER: "loadbalancing.yaml",
        ResourceType.LB_TARGET_GROUP: "loadbalancing.yaml",
        # Phase 2 - Database
        ResourceType.DB_PARAMETER_GROUP: "database.yaml",
        ResourceType.ELASTICACHE_CLUSTER: "cache.yaml",
        ResourceType.ELASTICACHE_SUBNET_GROUP: "cache.yaml",
        # Phase 2 - Storage/Messaging
        ResourceType.EBS_VOLUME: "storage.yaml",
        ResourceType.S3_BUCKET_POLICY: "storage.yaml",
        ResourceType.SQS_QUEUE: "messaging.yaml",
        ResourceType.SNS_TOPIC: "messaging.yaml",
    }

    @property
    def name(self) -> str:
        return "CloudFormation"

    @property
    def format_name(self) -> str:
        return "cloudformation"

    @feature_gate(Feature.PULUMI_OUTPUT)  # Using PULUMI_OUTPUT as proxy for CFN (Solo+)
    def render(self, graph: GraphEngine, output_dir: Path) -> dict[str, Path]:
        """
        Render the graph to CloudFormation YAML files.

        Args:
            graph: The GraphEngine containing resources
            output_dir: Directory to write .yaml files

        Returns:
            Dictionary mapping filenames to their paths
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Rendering CloudFormation to {output_dir}")

        # Group resources by output file
        file_resources: dict[str, list[ResourceNode]] = {}

        # Use safe dependency order to handle cycles (e.g., mutual SG references)
        for resource in graph.get_safe_dependency_order():
            output_file = self.FILE_MAPPING.get(resource.resource_type)
            if output_file:
                if output_file not in file_resources:
                    file_resources[output_file] = []
                file_resources[output_file].append(resource)

        # Generate CloudFormation templates
        written_files: dict[str, Path] = {}
        for filename, resources in file_resources.items():
            template = self._generate_template(resources, graph)
            file_path = output_dir / filename

            with open(file_path, "w") as f:
                yaml.dump(template, f, default_flow_style=False, sort_keys=False)

            written_files[filename] = file_path
            logger.info(f"Wrote {filename} ({len(resources)} resources)")

        # Generate main template with nested stacks
        self._generate_main_template(output_dir, written_files)

        return written_files

    def preview(self, graph: GraphEngine) -> dict[str, list[str]]:
        """Preview what would be generated without writing files."""
        preview: dict[str, list[str]] = {}

        for resource in graph.iter_resources():
            output_file = self.FILE_MAPPING.get(resource.resource_type)
            if output_file:
                if output_file not in preview:
                    preview[output_file] = []
                preview[output_file].append(resource.id)

        return preview

    def _generate_template(
        self, resources: list[ResourceNode], graph: GraphEngine
    ) -> dict[str, Any]:
        """Generate a CloudFormation template for a set of resources."""
        template: dict[str, Any] = {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Description": "Generated by RepliMap - AWS Infrastructure Staging Cloner",
            "Parameters": {
                "Environment": {
                    "Type": "String",
                    "Default": "staging",
                    "Description": "Environment name",
                },
            },
            "Resources": {},
            "Outputs": {},
        }

        for resource in resources:
            cfn_resource = self._convert_resource(resource, graph)
            if cfn_resource:
                logical_id = self._to_logical_id(resource.terraform_name)
                template["Resources"][logical_id] = cfn_resource

                # Add output for key resources
                if resource.resource_type in (ResourceType.VPC, ResourceType.SUBNET):
                    template["Outputs"][f"{logical_id}Id"] = {
                        "Description": f"ID of {resource.original_name}",
                        "Value": {"Ref": logical_id},
                        "Export": {"Name": f"!Sub '${{AWS::StackName}}-{logical_id}'"},
                    }

        return template

    def _convert_resource(
        self, resource: ResourceNode, graph: GraphEngine
    ) -> dict[str, Any] | None:
        """Convert a ResourceNode to CloudFormation resource definition."""
        converters = {
            # Phase 1
            ResourceType.VPC: self._convert_vpc,
            ResourceType.SUBNET: self._convert_subnet,
            ResourceType.SECURITY_GROUP: self._convert_security_group,
            ResourceType.EC2_INSTANCE: self._convert_ec2,
            ResourceType.S3_BUCKET: self._convert_s3,
            ResourceType.RDS_INSTANCE: self._convert_rds,
            # Phase 2 - Networking
            ResourceType.INTERNET_GATEWAY: self._convert_igw,
            ResourceType.NAT_GATEWAY: self._convert_nat,
            ResourceType.ROUTE_TABLE: self._convert_route_table,
            # Phase 2 - Compute
            ResourceType.LAUNCH_TEMPLATE: self._convert_launch_template,
            ResourceType.LB: self._convert_lb,
            ResourceType.LB_TARGET_GROUP: self._convert_target_group,
            # Phase 2 - Database
            ResourceType.ELASTICACHE_CLUSTER: self._convert_elasticache,
            # Phase 2 - Messaging
            ResourceType.SQS_QUEUE: self._convert_sqs,
            ResourceType.SNS_TOPIC: self._convert_sns,
        }

        converter = converters.get(resource.resource_type)
        if converter:
            return converter(resource, graph)
        return None

    def _convert_vpc(
        self, resource: ResourceNode, graph: GraphEngine
    ) -> dict[str, Any]:
        """Convert VPC to CloudFormation."""
        config = resource.config
        return {
            "Type": "AWS::EC2::VPC",
            "Properties": {
                "CidrBlock": config.get("cidr_block", "10.0.0.0/16"),
                "EnableDnsHostnames": config.get("enable_dns_hostnames", True),
                "EnableDnsSupport": config.get("enable_dns_support", True),
                "Tags": self._convert_tags(resource.tags, resource.original_name),
            },
        }

    def _convert_subnet(
        self, resource: ResourceNode, graph: GraphEngine
    ) -> dict[str, Any]:
        """Convert Subnet to CloudFormation."""
        config = resource.config

        # Find VPC reference
        vpc_ref = {"Ref": "VPC"}  # Default
        for dep_id in resource.dependencies:
            dep_resource = graph.get_resource(dep_id)
            if dep_resource and dep_resource.resource_type == ResourceType.VPC:
                vpc_ref = {"Ref": self._to_logical_id(dep_resource.terraform_name)}
                break

        return {
            "Type": "AWS::EC2::Subnet",
            "Properties": {
                "VpcId": vpc_ref,
                "CidrBlock": config.get("cidr_block", "10.0.1.0/24"),
                "AvailabilityZone": config.get("availability_zone"),
                "MapPublicIpOnLaunch": config.get("map_public_ip_on_launch", False),
                "Tags": self._convert_tags(resource.tags, resource.original_name),
            },
        }

    def _convert_security_group(
        self, resource: ResourceNode, graph: GraphEngine
    ) -> dict[str, Any]:
        """Convert Security Group to CloudFormation."""
        config = resource.config

        # Find VPC reference
        vpc_ref = {"Ref": "VPC"}
        for dep_id in resource.dependencies:
            dep_resource = graph.get_resource(dep_id)
            if dep_resource and dep_resource.resource_type == ResourceType.VPC:
                vpc_ref = {"Ref": self._to_logical_id(dep_resource.terraform_name)}
                break

        # Convert ingress rules
        ingress_rules = []
        for rule in config.get("ingress", []):
            cfn_rule: dict[str, Any] = {
                "IpProtocol": rule.get("protocol", "-1"),
            }
            if rule.get("from_port"):
                cfn_rule["FromPort"] = rule["from_port"]
            if rule.get("to_port"):
                cfn_rule["ToPort"] = rule["to_port"]
            if rule.get("cidr_blocks"):
                cfn_rule["CidrIp"] = rule["cidr_blocks"][0]
            ingress_rules.append(cfn_rule)

        return {
            "Type": "AWS::EC2::SecurityGroup",
            "Properties": {
                "GroupDescription": config.get(
                    "description", f"Security group {resource.original_name}"
                ),
                "VpcId": vpc_ref,
                "SecurityGroupIngress": ingress_rules if ingress_rules else None,
                "Tags": self._convert_tags(resource.tags, resource.original_name),
            },
        }

    def _convert_ec2(
        self, resource: ResourceNode, graph: GraphEngine
    ) -> dict[str, Any]:
        """Convert EC2 Instance to CloudFormation."""
        config = resource.config

        # Find subnet and security group references
        subnet_ref = None
        sg_refs = []
        for dep_id in resource.dependencies:
            dep_resource = graph.get_resource(dep_id)
            if dep_resource:
                if dep_resource.resource_type == ResourceType.SUBNET:
                    subnet_ref = {
                        "Ref": self._to_logical_id(dep_resource.terraform_name)
                    }
                elif dep_resource.resource_type == ResourceType.SECURITY_GROUP:
                    sg_refs.append(
                        {"Ref": self._to_logical_id(dep_resource.terraform_name)}
                    )

        properties: dict[str, Any] = {
            "InstanceType": config.get("instance_type", "t3.micro"),
            "ImageId": config.get("ami", "ami-0123456789abcdef0"),
            "Tags": self._convert_tags(resource.tags, resource.original_name),
        }

        if subnet_ref:
            properties["SubnetId"] = subnet_ref
        if sg_refs:
            properties["SecurityGroupIds"] = sg_refs

        return {
            "Type": "AWS::EC2::Instance",
            "Properties": properties,
        }

    def _convert_s3(self, resource: ResourceNode, graph: GraphEngine) -> dict[str, Any]:
        """Convert S3 Bucket to CloudFormation."""
        config = resource.config
        return {
            "Type": "AWS::S3::Bucket",
            "Properties": {
                "BucketName": config.get("bucket_name"),
                "VersioningConfiguration": {
                    "Status": "Enabled" if config.get("versioning") else "Suspended"
                },
                "Tags": self._convert_tags(resource.tags, resource.original_name),
            },
        }

    def _convert_rds(
        self, resource: ResourceNode, graph: GraphEngine
    ) -> dict[str, Any]:
        """Convert RDS Instance to CloudFormation."""
        config = resource.config

        # Find security group references
        sg_refs = []
        for dep_id in resource.dependencies:
            dep_resource = graph.get_resource(dep_id)
            if (
                dep_resource
                and dep_resource.resource_type == ResourceType.SECURITY_GROUP
            ):
                sg_refs.append(
                    {"Ref": self._to_logical_id(dep_resource.terraform_name)}
                )

        return {
            "Type": "AWS::RDS::DBInstance",
            "Properties": {
                "DBInstanceIdentifier": config.get("identifier"),
                "DBInstanceClass": config.get("instance_class", "db.t3.micro"),
                "Engine": config.get("engine", "mysql"),
                "EngineVersion": config.get("engine_version"),
                "AllocatedStorage": config.get("allocated_storage", 20),
                "MasterUsername": "admin",
                "MasterUserPassword": "{{resolve:secretsmanager:rds-password}}",
                "VPCSecurityGroups": sg_refs if sg_refs else None,
                "Tags": self._convert_tags(resource.tags, resource.original_name),
            },
        }

    def _convert_tags(
        self, tags: dict[str, str], name: str | None
    ) -> list[dict[str, str]]:
        """Convert tags dict to CloudFormation tag list."""
        cfn_tags = [{"Key": "Name", "Value": name or "unnamed"}]
        for key, value in tags.items():
            if key != "Name":
                cfn_tags.append({"Key": key, "Value": value})
        cfn_tags.append({"Key": "ManagedBy", "Value": "RepliMap"})
        return cfn_tags

    # Phase 2 Converters

    def _convert_igw(
        self, resource: ResourceNode, graph: GraphEngine
    ) -> dict[str, Any]:
        """Convert Internet Gateway to CloudFormation."""
        return {
            "Type": "AWS::EC2::InternetGateway",
            "Properties": {
                "Tags": self._convert_tags(resource.tags, resource.original_name),
            },
        }

    def _convert_nat(
        self, resource: ResourceNode, graph: GraphEngine
    ) -> dict[str, Any]:
        """Convert NAT Gateway to CloudFormation."""
        subnet_ref = {"Ref": "Subnet"}

        for dep_id in resource.dependencies:
            dep_resource = graph.get_resource(dep_id)
            if dep_resource and dep_resource.resource_type == ResourceType.SUBNET:
                subnet_ref = {"Ref": self._to_logical_id(dep_resource.terraform_name)}
                break

        return {
            "Type": "AWS::EC2::NatGateway",
            "Properties": {
                "AllocationId": {
                    "Fn::GetAtt": [
                        f"{self._to_logical_id(resource.terraform_name)}EIP",
                        "AllocationId",
                    ]
                },
                "SubnetId": subnet_ref,
                "Tags": self._convert_tags(resource.tags, resource.original_name),
            },
        }

    def _convert_route_table(
        self, resource: ResourceNode, graph: GraphEngine
    ) -> dict[str, Any]:
        """Convert Route Table to CloudFormation."""
        vpc_ref = {"Ref": "VPC"}

        for dep_id in resource.dependencies:
            dep_resource = graph.get_resource(dep_id)
            if dep_resource and dep_resource.resource_type == ResourceType.VPC:
                vpc_ref = {"Ref": self._to_logical_id(dep_resource.terraform_name)}
                break

        return {
            "Type": "AWS::EC2::RouteTable",
            "Properties": {
                "VpcId": vpc_ref,
                "Tags": self._convert_tags(resource.tags, resource.original_name),
            },
        }

    def _convert_launch_template(
        self, resource: ResourceNode, graph: GraphEngine
    ) -> dict[str, Any]:
        """Convert Launch Template to CloudFormation."""
        config = resource.config
        lt_data: dict[str, Any] = {}

        if config.get("instance_type"):
            lt_data["InstanceType"] = config["instance_type"]
        if config.get("image_id"):
            lt_data["ImageId"] = config["image_id"]
        if config.get("key_name"):
            lt_data["KeyName"] = config["key_name"]

        return {
            "Type": "AWS::EC2::LaunchTemplate",
            "Properties": {
                "LaunchTemplateName": config.get("name"),
                "LaunchTemplateData": lt_data,
            },
        }

    def _convert_lb(self, resource: ResourceNode, graph: GraphEngine) -> dict[str, Any]:
        """Convert Load Balancer to CloudFormation."""
        config = resource.config
        subnet_refs = []
        sg_refs = []

        for dep_id in resource.dependencies:
            dep_resource = graph.get_resource(dep_id)
            if dep_resource:
                if dep_resource.resource_type == ResourceType.SUBNET:
                    subnet_refs.append(
                        {"Ref": self._to_logical_id(dep_resource.terraform_name)}
                    )
                elif dep_resource.resource_type == ResourceType.SECURITY_GROUP:
                    sg_refs.append(
                        {"Ref": self._to_logical_id(dep_resource.terraform_name)}
                    )

        properties: dict[str, Any] = {
            "Name": config.get("name"),
            "Type": config.get("type", "application").lower(),
            "Scheme": config.get("scheme", "internet-facing"),
            "Subnets": subnet_refs if subnet_refs else None,
            "Tags": self._convert_tags(resource.tags, resource.original_name),
        }

        if config.get("type", "").lower() == "application" and sg_refs:
            properties["SecurityGroups"] = sg_refs

        return {
            "Type": "AWS::ElasticLoadBalancingV2::LoadBalancer",
            "Properties": properties,
        }

    def _convert_target_group(
        self, resource: ResourceNode, graph: GraphEngine
    ) -> dict[str, Any]:
        """Convert Target Group to CloudFormation."""
        config = resource.config
        vpc_ref = {"Ref": "VPC"}

        for dep_id in resource.dependencies:
            dep_resource = graph.get_resource(dep_id)
            if dep_resource and dep_resource.resource_type == ResourceType.VPC:
                vpc_ref = {"Ref": self._to_logical_id(dep_resource.terraform_name)}
                break

        health_check = config.get("health_check", {})

        return {
            "Type": "AWS::ElasticLoadBalancingV2::TargetGroup",
            "Properties": {
                "Name": config.get("name"),
                "Port": config.get("port"),
                "Protocol": config.get("protocol"),
                "VpcId": vpc_ref,
                "TargetType": config.get("target_type", "instance"),
                "HealthCheckEnabled": health_check.get("enabled", True),
                "HealthCheckPath": health_check.get("path", "/"),
                "HealthCheckProtocol": health_check.get("protocol", "HTTP"),
                "Tags": self._convert_tags(resource.tags, resource.original_name),
            },
        }

    def _convert_elasticache(
        self, resource: ResourceNode, graph: GraphEngine
    ) -> dict[str, Any]:
        """Convert ElastiCache Cluster to CloudFormation."""
        config = resource.config
        sg_refs = []

        for dep_id in resource.dependencies:
            dep_resource = graph.get_resource(dep_id)
            if (
                dep_resource
                and dep_resource.resource_type == ResourceType.SECURITY_GROUP
            ):
                sg_refs.append(
                    {"Ref": self._to_logical_id(dep_resource.terraform_name)}
                )

        return {
            "Type": "AWS::ElastiCache::CacheCluster",
            "Properties": {
                "ClusterName": config.get("cluster_id"),
                "Engine": config.get("engine"),
                "EngineVersion": config.get("engine_version"),
                "CacheNodeType": config.get("node_type"),
                "NumCacheNodes": config.get("num_cache_nodes", 1),
                "VpcSecurityGroupIds": sg_refs if sg_refs else None,
                "Tags": self._convert_tags(resource.tags, resource.original_name),
            },
        }

    def _convert_sqs(
        self, resource: ResourceNode, graph: GraphEngine
    ) -> dict[str, Any]:
        """Convert SQS Queue to CloudFormation."""
        config = resource.config

        properties: dict[str, Any] = {
            "QueueName": config.get("name"),
            "VisibilityTimeout": config.get("visibility_timeout_seconds", 30),
            "MessageRetentionPeriod": config.get("message_retention_seconds", 345600),
            "DelaySeconds": config.get("delay_seconds", 0),
            "MaximumMessageSize": config.get("max_message_size", 262144),
            "ReceiveMessageWaitTimeSeconds": config.get("receive_wait_time_seconds", 0),
            "Tags": self._convert_tags(resource.tags, resource.original_name),
        }

        if config.get("fifo_queue"):
            properties["FifoQueue"] = True
            properties["ContentBasedDeduplication"] = config.get(
                "content_based_deduplication", False
            )

        return {
            "Type": "AWS::SQS::Queue",
            "Properties": properties,
        }

    def _convert_sns(
        self, resource: ResourceNode, graph: GraphEngine
    ) -> dict[str, Any]:
        """Convert SNS Topic to CloudFormation."""
        config = resource.config

        properties: dict[str, Any] = {
            "TopicName": config.get("name"),
            "Tags": self._convert_tags(resource.tags, resource.original_name),
        }

        if config.get("display_name"):
            properties["DisplayName"] = config["display_name"]

        if config.get("fifo_topic"):
            properties["FifoTopic"] = True
            properties["ContentBasedDeduplication"] = config.get(
                "content_based_deduplication", False
            )

        return {
            "Type": "AWS::SNS::Topic",
            "Properties": properties,
        }

    def _generate_main_template(
        self, output_dir: Path, written_files: dict[str, Path]
    ) -> None:
        """Generate a main template that references nested stacks."""
        main_template: dict[str, Any] = {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Description": "RepliMap - Main Stack",
            "Parameters": {
                "Environment": {
                    "Type": "String",
                    "Default": "staging",
                    "Description": "Environment name",
                },
                "S3BucketName": {
                    "Type": "String",
                    "Description": "S3 bucket containing nested templates",
                },
            },
            "Resources": {},
        }

        # Add nested stack references
        for filename in written_files:
            stack_name = filename.replace(".yaml", "").title() + "Stack"
            main_template["Resources"][stack_name] = {
                "Type": "AWS::CloudFormation::Stack",
                "Properties": {
                    "TemplateURL": {
                        "Fn::Sub": f"https://${{S3BucketName}}.s3.amazonaws.com/{filename}"
                    },
                    "Parameters": {"Environment": {"Ref": "Environment"}},
                },
            }

        main_path = output_dir / "main.yaml"
        with open(main_path, "w") as f:
            yaml.dump(main_template, f, default_flow_style=False, sort_keys=False)
        written_files["main.yaml"] = main_path
        logger.info("Wrote main.yaml")

    @staticmethod
    def _to_logical_id(name: str | None) -> str:
        """Convert a name to a CloudFormation logical ID."""
        if not name:
            return "Resource"
        # CloudFormation logical IDs must be alphanumeric
        result = ""
        capitalize_next = True
        for char in name:
            if char.isalnum():
                result += char.upper() if capitalize_next else char
                capitalize_next = False
            else:
                capitalize_next = True

        # Ensure it starts with a letter
        if result and not result[0].isalpha():
            result = "R" + result

        return result or "Resource"
