"""
Pulumi Renderer for RepliMap.

Converts the resource graph to Pulumi Python code.
This renderer requires Pro plan or higher.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from replimap.core.models import ResourceType
from replimap.licensing import Feature
from replimap.licensing.gates import feature_gate
from replimap.renderers.base import BaseRenderer

if TYPE_CHECKING:
    from replimap.core import GraphEngine, ResourceNode

logger = logging.getLogger(__name__)


class PulumiRenderer(BaseRenderer):
    """
    Renders the resource graph to Pulumi Python code.

    Output structure:
    - __main__.py: Main Pulumi program
    - network.py: VPCs, Subnets, Security Groups
    - compute.py: EC2 Instances
    - database.py: RDS Instances
    - storage.py: S3 Buckets
    - Pulumi.yaml: Project configuration
    - requirements.txt: Python dependencies

    Requires: Pro plan or higher
    """

    # Mapping of resource types to output files
    FILE_MAPPING = {
        # Phase 1 (MVP)
        ResourceType.VPC: "network.py",
        ResourceType.SUBNET: "network.py",
        ResourceType.SECURITY_GROUP: "network.py",
        ResourceType.EC2_INSTANCE: "compute.py",
        ResourceType.S3_BUCKET: "storage.py",
        ResourceType.RDS_INSTANCE: "database.py",
        ResourceType.DB_SUBNET_GROUP: "database.py",
        # Phase 2 - Networking
        ResourceType.ROUTE_TABLE: "network.py",
        ResourceType.INTERNET_GATEWAY: "network.py",
        ResourceType.NAT_GATEWAY: "network.py",
        ResourceType.VPC_ENDPOINT: "network.py",
        # Phase 2 - Compute
        ResourceType.LAUNCH_TEMPLATE: "compute.py",
        ResourceType.AUTOSCALING_GROUP: "compute.py",
        ResourceType.LB: "loadbalancing.py",
        ResourceType.LB_LISTENER: "loadbalancing.py",
        ResourceType.LB_TARGET_GROUP: "loadbalancing.py",
        # Phase 2 - Database
        ResourceType.DB_PARAMETER_GROUP: "database.py",
        ResourceType.ELASTICACHE_CLUSTER: "cache.py",
        ResourceType.ELASTICACHE_SUBNET_GROUP: "cache.py",
        # Phase 2 - Storage/Messaging
        ResourceType.EBS_VOLUME: "storage.py",
        ResourceType.S3_BUCKET_POLICY: "storage.py",
        ResourceType.SQS_QUEUE: "messaging.py",
        ResourceType.SNS_TOPIC: "messaging.py",
    }

    @property
    def name(self) -> str:
        return "Pulumi"

    @property
    def format_name(self) -> str:
        return "pulumi"

    @feature_gate(Feature.PULUMI_OUTPUT)
    def render(self, graph: GraphEngine, output_dir: Path) -> dict[str, Path]:
        """
        Render the graph to Pulumi Python files.

        Args:
            graph: The GraphEngine containing resources
            output_dir: Directory to write Python files

        Returns:
            Dictionary mapping filenames to their paths
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Rendering Pulumi to {output_dir}")

        # Group resources by output file
        file_resources: dict[str, list[ResourceNode]] = {}

        # Use safe dependency order to handle cycles (e.g., mutual SG references)
        for resource in graph.get_safe_dependency_order():
            output_file = self.FILE_MAPPING.get(resource.resource_type)
            if output_file:
                if output_file not in file_resources:
                    file_resources[output_file] = []
                file_resources[output_file].append(resource)

        # Generate module files
        written_files: dict[str, Path] = {}
        module_imports = []

        for filename, resources in file_resources.items():
            code = self._generate_module(filename, resources, graph)
            file_path = output_dir / filename

            with open(file_path, "w") as f:
                f.write(code)

            written_files[filename] = file_path
            module_imports.append(filename.replace(".py", ""))
            logger.info(f"Wrote {filename} ({len(resources)} resources)")

        # Generate main entry point
        self._generate_main(output_dir, module_imports, written_files)

        # Generate project configuration
        self._generate_pulumi_yaml(output_dir, written_files)

        # Generate requirements.txt
        self._generate_requirements(output_dir, written_files)

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

    def _generate_module(
        self, filename: str, resources: list[ResourceNode], graph: GraphEngine
    ) -> str:
        """Generate a Pulumi Python module for a set of resources."""
        lines = [
            '"""',
            f"Generated by RepliMap - {filename}",
            '"""',
            "",
            "import pulumi",
            "import pulumi_aws as aws",
            "",
            "",
        ]

        # Generate resource definitions
        for resource in resources:
            resource_code = self._convert_resource(resource, graph)
            if resource_code:
                lines.append(resource_code)
                lines.append("")

        # Generate exports
        lines.append("# Exports")
        for resource in resources:
            var_name = self._to_variable_name(resource.terraform_name or resource.id)
            if resource.resource_type == ResourceType.VPC:
                lines.append(f"pulumi.export('{var_name}_id', {var_name}.id)")
            elif resource.resource_type == ResourceType.SUBNET:
                lines.append(f"pulumi.export('{var_name}_id', {var_name}.id)")

        return "\n".join(lines)

    def _convert_resource(
        self, resource: ResourceNode, graph: GraphEngine
    ) -> str | None:
        """Convert a ResourceNode to Pulumi Python code."""
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

    def _convert_vpc(self, resource: ResourceNode, graph: GraphEngine) -> str:
        """Convert VPC to Pulumi."""
        config = resource.config
        var_name = self._to_variable_name(resource.terraform_name or resource.id)

        return f'''{var_name} = aws.ec2.Vpc(
    "{resource.terraform_name}",
    cidr_block="{config.get("cidr_block", "10.0.0.0/16")}",
    enable_dns_hostnames={config.get("enable_dns_hostnames", True)},
    enable_dns_support={config.get("enable_dns_support", True)},
    tags={{
        "Name": "{resource.original_name}",
        "ManagedBy": "RepliMap",
    }},
)'''

    def _convert_subnet(self, resource: ResourceNode, graph: GraphEngine) -> str:
        """Convert Subnet to Pulumi."""
        config = resource.config
        var_name = self._to_variable_name(resource.terraform_name or resource.id)

        # Find VPC reference
        vpc_ref = "vpc.id"  # Default
        for dep_id in resource.dependencies:
            dep_resource = graph.get_resource(dep_id)
            if dep_resource and dep_resource.resource_type == ResourceType.VPC:
                vpc_var = self._to_variable_name(
                    dep_resource.terraform_name or dep_resource.id
                )
                vpc_ref = f"{vpc_var}.id"
                break

        az = config.get("availability_zone", "us-east-1a")
        cidr = config.get("cidr_block", "10.0.1.0/24")
        map_public = config.get("map_public_ip_on_launch", False)

        return f'''{var_name} = aws.ec2.Subnet(
    "{resource.terraform_name}",
    vpc_id={vpc_ref},
    cidr_block="{cidr}",
    availability_zone="{az}",
    map_public_ip_on_launch={map_public},
    tags={{
        "Name": "{resource.original_name}",
        "ManagedBy": "RepliMap",
    }},
)'''

    def _convert_security_group(
        self, resource: ResourceNode, graph: GraphEngine
    ) -> str:
        """Convert Security Group to Pulumi."""
        config = resource.config
        var_name = self._to_variable_name(resource.terraform_name or resource.id)

        # Find VPC reference
        vpc_ref = "vpc.id"
        for dep_id in resource.dependencies:
            dep_resource = graph.get_resource(dep_id)
            if dep_resource and dep_resource.resource_type == ResourceType.VPC:
                vpc_var = self._to_variable_name(
                    dep_resource.terraform_name or dep_resource.id
                )
                vpc_ref = f"{vpc_var}.id"
                break

        # Convert ingress rules
        ingress_rules = []
        for rule in config.get("ingress", []):
            rule_dict = {
                "protocol": rule.get("protocol", "-1"),
                "from_port": rule.get("from_port", 0),
                "to_port": rule.get("to_port", 0),
                "cidr_blocks": rule.get("cidr_blocks", ["0.0.0.0/0"]),
            }
            ingress_rules.append(rule_dict)

        ingress_str = self._format_ingress_rules(ingress_rules)
        description = config.get(
            "description", f"Security group {resource.original_name}"
        )

        return f'''{var_name} = aws.ec2.SecurityGroup(
    "{resource.terraform_name}",
    vpc_id={vpc_ref},
    description="{description}",
    ingress=[{ingress_str}],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"],
        ),
    ],
    tags={{
        "Name": "{resource.original_name}",
        "ManagedBy": "RepliMap",
    }},
)'''

    def _convert_ec2(self, resource: ResourceNode, graph: GraphEngine) -> str:
        """Convert EC2 Instance to Pulumi."""
        config = resource.config
        var_name = self._to_variable_name(resource.terraform_name or resource.id)

        # Find subnet and security group references
        subnet_ref = "subnet.id"
        sg_refs = []
        for dep_id in resource.dependencies:
            dep_resource = graph.get_resource(dep_id)
            if dep_resource:
                dep_var = self._to_variable_name(
                    dep_resource.terraform_name or dep_resource.id
                )
                if dep_resource.resource_type == ResourceType.SUBNET:
                    subnet_ref = f"{dep_var}.id"
                elif dep_resource.resource_type == ResourceType.SECURITY_GROUP:
                    sg_refs.append(f"{dep_var}.id")

        sg_list = ", ".join(sg_refs) if sg_refs else "[]"
        instance_type = config.get("instance_type", "t3.micro")
        ami = config.get("ami", "ami-0123456789abcdef0")

        return f'''{var_name} = aws.ec2.Instance(
    "{resource.terraform_name}",
    instance_type="{instance_type}",
    ami="{ami}",
    subnet_id={subnet_ref},
    vpc_security_group_ids=[{sg_list}],
    tags={{
        "Name": "{resource.original_name}",
        "ManagedBy": "RepliMap",
    }},
)'''

    def _convert_s3(self, resource: ResourceNode, graph: GraphEngine) -> str:
        """Convert S3 Bucket to Pulumi."""
        config = resource.config
        var_name = self._to_variable_name(resource.terraform_name or resource.id)

        bucket_name = config.get("bucket_name", resource.terraform_name)

        return f'''{var_name} = aws.s3.Bucket(
    "{resource.terraform_name}",
    bucket="{bucket_name}",
    versioning=aws.s3.BucketVersioningArgs(
        enabled={config.get("versioning", False)},
    ),
    tags={{
        "Name": "{resource.original_name}",
        "ManagedBy": "RepliMap",
    }},
)'''

    def _convert_rds(self, resource: ResourceNode, graph: GraphEngine) -> str:
        """Convert RDS Instance to Pulumi."""
        config = resource.config
        var_name = self._to_variable_name(resource.terraform_name or resource.id)

        # Find security group references
        sg_refs = []
        for dep_id in resource.dependencies:
            dep_resource = graph.get_resource(dep_id)
            if (
                dep_resource
                and dep_resource.resource_type == ResourceType.SECURITY_GROUP
            ):
                dep_var = self._to_variable_name(
                    dep_resource.terraform_name or dep_resource.id
                )
                sg_refs.append(f"{dep_var}.id")

        sg_list = ", ".join(sg_refs) if sg_refs else "[]"
        identifier = config.get("identifier", resource.terraform_name)
        instance_class = config.get("instance_class", "db.t3.micro")
        engine = config.get("engine", "mysql")
        allocated_storage = config.get("allocated_storage", 20)

        return f'''{var_name} = aws.rds.Instance(
    "{resource.terraform_name}",
    identifier="{identifier}",
    instance_class="{instance_class}",
    engine="{engine}",
    allocated_storage={allocated_storage},
    username="admin",
    password="CHANGE_ME",  # Use pulumi.Config or secrets manager
    vpc_security_group_ids=[{sg_list}],
    skip_final_snapshot=True,
    tags={{
        "Name": "{resource.original_name}",
        "ManagedBy": "RepliMap",
    }},
)'''

    # Phase 2 Converters

    def _convert_igw(self, resource: ResourceNode, graph: GraphEngine) -> str:
        """Convert Internet Gateway to Pulumi."""
        var_name = self._to_variable_name(resource.terraform_name or resource.id)

        # Find VPC reference
        vpc_ref = "vpc.id"
        for dep_id in resource.dependencies:
            dep_resource = graph.get_resource(dep_id)
            if dep_resource and dep_resource.resource_type == ResourceType.VPC:
                vpc_var = self._to_variable_name(
                    dep_resource.terraform_name or dep_resource.id
                )
                vpc_ref = f"{vpc_var}.id"
                break

        return f'''{var_name} = aws.ec2.InternetGateway(
    "{resource.terraform_name}",
    vpc_id={vpc_ref},
    tags={{
        "Name": "{resource.original_name}",
        "ManagedBy": "RepliMap",
    }},
)'''

    def _convert_nat(self, resource: ResourceNode, graph: GraphEngine) -> str:
        """Convert NAT Gateway to Pulumi."""
        config = resource.config
        var_name = self._to_variable_name(resource.terraform_name or resource.id)

        # Find subnet reference
        subnet_ref = "subnet.id"
        for dep_id in resource.dependencies:
            dep_resource = graph.get_resource(dep_id)
            if dep_resource and dep_resource.resource_type == ResourceType.SUBNET:
                subnet_var = self._to_variable_name(
                    dep_resource.terraform_name or dep_resource.id
                )
                subnet_ref = f"{subnet_var}.id"
                break

        connectivity = config.get("connectivity_type", "public")
        allocation_id = config.get("allocation_id", "")

        lines = [
            f'''{var_name} = aws.ec2.NatGateway(
    "{resource.terraform_name}",
    subnet_id={subnet_ref},
    connectivity_type="{connectivity}",'''
        ]

        if allocation_id and connectivity == "public":
            lines.append(f'    allocation_id="{allocation_id}",')

        lines.append(
            '''    tags={
        "Name": "'''
            + (resource.original_name or resource.terraform_name or "unnamed")
            + """",
        "ManagedBy": "RepliMap",
    },
)"""
        )

        return "\n".join(lines)

    def _convert_route_table(self, resource: ResourceNode, graph: GraphEngine) -> str:
        """Convert Route Table to Pulumi."""
        config = resource.config
        var_name = self._to_variable_name(resource.terraform_name or resource.id)

        # Find VPC reference
        vpc_ref = "vpc.id"
        for dep_id in resource.dependencies:
            dep_resource = graph.get_resource(dep_id)
            if dep_resource and dep_resource.resource_type == ResourceType.VPC:
                vpc_var = self._to_variable_name(
                    dep_resource.terraform_name or dep_resource.id
                )
                vpc_ref = f"{vpc_var}.id"
                break

        # Build routes
        routes = config.get("routes", [])
        route_args = []
        for route in routes:
            dest = route.get("destination_cidr_block", "0.0.0.0/0")
            route_args.append(f'''        aws.ec2.RouteTableRouteArgs(
            cidr_block="{dest}",
        )''')

        routes_str = ",\n".join(route_args) if route_args else ""

        return f'''{var_name} = aws.ec2.RouteTable(
    "{resource.terraform_name}",
    vpc_id={vpc_ref},
    routes=[
{routes_str}
    ],
    tags={{
        "Name": "{resource.original_name}",
        "ManagedBy": "RepliMap",
    }},
)'''

    def _convert_lb(self, resource: ResourceNode, graph: GraphEngine) -> str:
        """Convert Load Balancer to Pulumi."""
        config = resource.config
        var_name = self._to_variable_name(resource.terraform_name or resource.id)

        lb_type = config.get("load_balancer_type", "application")
        internal = config.get("internal", False)

        # Find subnet and security group references
        subnet_refs = []
        sg_refs = []
        for dep_id in resource.dependencies:
            dep_resource = graph.get_resource(dep_id)
            if dep_resource:
                dep_var = self._to_variable_name(
                    dep_resource.terraform_name or dep_resource.id
                )
                if dep_resource.resource_type == ResourceType.SUBNET:
                    subnet_refs.append(f"{dep_var}.id")
                elif dep_resource.resource_type == ResourceType.SECURITY_GROUP:
                    sg_refs.append(f"{dep_var}.id")

        subnets_str = ", ".join(subnet_refs) if subnet_refs else ""
        sg_str = ", ".join(sg_refs) if sg_refs else ""

        return f'''{var_name} = aws.lb.LoadBalancer(
    "{resource.terraform_name}",
    load_balancer_type="{lb_type}",
    internal={internal},
    subnets=[{subnets_str}],
    security_groups=[{sg_str}],
    tags={{
        "Name": "{resource.original_name}",
        "ManagedBy": "RepliMap",
    }},
)'''

    def _convert_target_group(self, resource: ResourceNode, graph: GraphEngine) -> str:
        """Convert Target Group to Pulumi."""
        config = resource.config
        var_name = self._to_variable_name(resource.terraform_name or resource.id)

        # Find VPC reference
        vpc_ref = "vpc.id"
        for dep_id in resource.dependencies:
            dep_resource = graph.get_resource(dep_id)
            if dep_resource and dep_resource.resource_type == ResourceType.VPC:
                vpc_var = self._to_variable_name(
                    dep_resource.terraform_name or dep_resource.id
                )
                vpc_ref = f"{vpc_var}.id"
                break

        port = config.get("port", 80)
        protocol = config.get("protocol", "HTTP")
        target_type = config.get("target_type", "instance")

        return f'''{var_name} = aws.lb.TargetGroup(
    "{resource.terraform_name}",
    port={port},
    protocol="{protocol}",
    target_type="{target_type}",
    vpc_id={vpc_ref},
    health_check=aws.lb.TargetGroupHealthCheckArgs(
        enabled=True,
        path="/",
        protocol="{protocol}",
    ),
    tags={{
        "Name": "{resource.original_name}",
        "ManagedBy": "RepliMap",
    }},
)'''

    def _convert_elasticache(self, resource: ResourceNode, graph: GraphEngine) -> str:
        """Convert ElastiCache Cluster to Pulumi."""
        config = resource.config
        var_name = self._to_variable_name(resource.terraform_name or resource.id)

        cluster_id = config.get("cluster_id", resource.terraform_name or resource.id)
        engine = config.get("engine", "redis")
        node_type = config.get("node_type", "cache.t3.micro")
        num_nodes = config.get("num_cache_nodes", 1)

        # Find security group references
        sg_refs = []
        for dep_id in resource.dependencies:
            dep_resource = graph.get_resource(dep_id)
            if (
                dep_resource
                and dep_resource.resource_type == ResourceType.SECURITY_GROUP
            ):
                dep_var = self._to_variable_name(
                    dep_resource.terraform_name or dep_resource.id
                )
                sg_refs.append(f"{dep_var}.id")

        sg_str = ", ".join(sg_refs) if sg_refs else ""

        return f'''{var_name} = aws.elasticache.Cluster(
    "{resource.terraform_name}",
    cluster_id="{cluster_id}",
    engine="{engine}",
    node_type="{node_type}",
    num_cache_nodes={num_nodes},
    security_group_ids=[{sg_str}],
    tags={{
        "Name": "{resource.original_name}",
        "ManagedBy": "RepliMap",
    }},
)'''

    def _convert_sqs(self, resource: ResourceNode, graph: GraphEngine) -> str:
        """Convert SQS Queue to Pulumi."""
        config = resource.config
        var_name = self._to_variable_name(resource.terraform_name or resource.id)

        name = config.get("name", resource.terraform_name)
        visibility_timeout = config.get("visibility_timeout_seconds", 30)
        message_retention = config.get("message_retention_seconds", 345600)

        fifo_str = ""
        if config.get("fifo_queue"):
            fifo_str = """
    fifo_queue=True,
    content_based_deduplication=True,"""

        return f'''{var_name} = aws.sqs.Queue(
    "{resource.terraform_name}",
    name="{name}",
    visibility_timeout_seconds={visibility_timeout},
    message_retention_seconds={message_retention},{fifo_str}
    tags={{
        "Name": "{resource.original_name}",
        "ManagedBy": "RepliMap",
    }},
)'''

    def _convert_sns(self, resource: ResourceNode, graph: GraphEngine) -> str:
        """Convert SNS Topic to Pulumi."""
        config = resource.config
        var_name = self._to_variable_name(resource.terraform_name or resource.id)

        name = config.get("name", resource.terraform_name)

        fifo_str = ""
        if config.get("fifo_topic"):
            fifo_str = """
    fifo_topic=True,
    content_based_deduplication=True,"""

        return f'''{var_name} = aws.sns.Topic(
    "{resource.terraform_name}",
    name="{name}",{fifo_str}
    tags={{
        "Name": "{resource.original_name}",
        "ManagedBy": "RepliMap",
    }},
)'''

    def _format_ingress_rules(self, rules: list[dict]) -> str:
        """Format ingress rules as Pulumi args."""
        if not rules:
            return ""

        rule_strs = []
        for rule in rules:
            cidr_blocks = rule.get("cidr_blocks", ["0.0.0.0/0"])
            cidr_str = ", ".join(f'"{c}"' for c in cidr_blocks)
            rule_strs.append(f'''
        aws.ec2.SecurityGroupIngressArgs(
            protocol="{rule.get("protocol", "-1")}",
            from_port={rule.get("from_port", 0)},
            to_port={rule.get("to_port", 0)},
            cidr_blocks=[{cidr_str}],
        )''')

        return ",".join(rule_strs)

    def _generate_main(
        self, output_dir: Path, modules: list[str], written_files: dict[str, Path]
    ) -> None:
        """Generate the main Pulumi entry point."""
        imports = "\n".join(f"from . import {m}" for m in modules)

        main_code = f'''"""
RepliMap - Pulumi Infrastructure
Generated staging environment from AWS production scan.
"""

import pulumi

# Import infrastructure modules
{imports}

# Stack configuration
config = pulumi.Config()
environment = config.get("environment") or "staging"

pulumi.export("environment", environment)
'''

        main_path = output_dir / "__main__.py"
        with open(main_path, "w") as f:
            f.write(main_code)
        written_files["__main__.py"] = main_path
        logger.info("Wrote __main__.py")

    def _generate_pulumi_yaml(
        self, output_dir: Path, written_files: dict[str, Path]
    ) -> None:
        """Generate Pulumi.yaml project configuration."""
        config = """name: replimap-staging
runtime:
  name: python
  options:
    virtualenv: venv
description: Staging environment generated by RepliMap
"""

        config_path = output_dir / "Pulumi.yaml"
        with open(config_path, "w") as f:
            f.write(config)
        written_files["Pulumi.yaml"] = config_path
        logger.info("Wrote Pulumi.yaml")

    def _generate_requirements(
        self, output_dir: Path, written_files: dict[str, Path]
    ) -> None:
        """Generate requirements.txt for Pulumi dependencies."""
        requirements = """pulumi>=3.0.0
pulumi-aws>=6.0.0
"""

        req_path = output_dir / "requirements.txt"
        with open(req_path, "w") as f:
            f.write(requirements)
        written_files["requirements.txt"] = req_path
        logger.info("Wrote requirements.txt")

    @staticmethod
    def _to_variable_name(name: str) -> str:
        """Convert a name to a valid Python variable name."""
        result = ""
        for char in name:
            if char.isalnum() or char == "_":
                result += char
            else:
                result += "_"

        # Ensure it starts with a letter or underscore
        if result and result[0].isdigit():
            result = f"r_{result}"

        return result.lower() or "resource"
