"""
Build dependency graph from scanned resources.

Analyzes resource configurations to find dependencies:
- Security Group -> EC2 Instance
- Subnet -> VPC
- RDS -> Subnet Group -> Subnets
- etc.
"""

from __future__ import annotations

import logging
from typing import Any

import networkx as nx

from replimap.blast.models import BlastNode, DependencyEdge, DependencyType
from replimap.core import GraphEngine

logger = logging.getLogger(__name__)


# Dependency patterns: (source_type, target_type, attribute_path)
DEPENDENCY_PATTERNS: list[tuple[str, str, str]] = [
    # EC2 dependencies
    ("aws_instance", "aws_security_group", "vpc_security_group_ids"),
    ("aws_instance", "aws_security_group", "security_groups"),
    ("aws_instance", "aws_subnet", "subnet_id"),
    ("aws_instance", "aws_iam_instance_profile", "iam_instance_profile"),
    ("aws_instance", "aws_key_pair", "key_name"),
    # Security Group dependencies
    ("aws_security_group", "aws_vpc", "vpc_id"),
    ("aws_security_group_rule", "aws_security_group", "security_group_id"),
    ("aws_security_group_rule", "aws_security_group", "source_security_group_id"),
    # Network dependencies
    ("aws_subnet", "aws_vpc", "vpc_id"),
    ("aws_internet_gateway", "aws_vpc", "vpc_id"),
    ("aws_nat_gateway", "aws_subnet", "subnet_id"),
    ("aws_nat_gateway", "aws_eip", "allocation_id"),
    ("aws_route_table", "aws_vpc", "vpc_id"),
    ("aws_route_table_association", "aws_subnet", "subnet_id"),
    ("aws_route_table_association", "aws_route_table", "route_table_id"),
    ("aws_route", "aws_route_table", "route_table_id"),
    ("aws_route", "aws_nat_gateway", "nat_gateway_id"),
    ("aws_route", "aws_internet_gateway", "gateway_id"),
    # RDS dependencies
    ("aws_db_instance", "aws_db_subnet_group", "db_subnet_group_name"),
    ("aws_db_instance", "aws_security_group", "vpc_security_group_ids"),
    ("aws_db_instance", "aws_kms_key", "kms_key_id"),
    ("aws_db_subnet_group", "aws_subnet", "subnet_ids"),
    # Load Balancer dependencies
    ("aws_lb", "aws_subnet", "subnets"),
    ("aws_lb", "aws_security_group", "security_groups"),
    ("aws_lb_target_group", "aws_vpc", "vpc_id"),
    ("aws_lb_listener", "aws_lb", "load_balancer_arn"),
    ("aws_lb_target_group_attachment", "aws_lb_target_group", "target_group_arn"),
    ("aws_lb_target_group_attachment", "aws_instance", "target_id"),
    # S3 dependencies
    ("aws_s3_bucket_policy", "aws_s3_bucket", "bucket"),
    ("aws_s3_bucket_versioning", "aws_s3_bucket", "bucket"),
    ("aws_s3_bucket_encryption", "aws_s3_bucket", "bucket"),
    # IAM dependencies
    ("aws_iam_role_policy_attachment", "aws_iam_role", "role"),
    ("aws_iam_role_policy_attachment", "aws_iam_policy", "policy_arn"),
    ("aws_iam_instance_profile", "aws_iam_role", "role"),
    # Lambda dependencies
    ("aws_lambda_function", "aws_iam_role", "role"),
    ("aws_lambda_function", "aws_security_group", "vpc_config.security_group_ids"),
    ("aws_lambda_function", "aws_subnet", "vpc_config.subnet_ids"),
    # CloudWatch dependencies
    ("aws_cloudwatch_metric_alarm", "aws_sns_topic", "alarm_actions"),
    (
        "aws_cloudwatch_log_subscription_filter",
        "aws_cloudwatch_log_group",
        "log_group_name",
    ),
    # Auto Scaling dependencies
    ("aws_autoscaling_group", "aws_launch_template", "launch_template.id"),
    ("aws_autoscaling_group", "aws_subnet", "vpc_zone_identifier"),
    ("aws_autoscaling_group", "aws_lb_target_group", "target_group_arns"),
    # ElastiCache dependencies
    ("aws_elasticache_cluster", "aws_elasticache_subnet_group", "subnet_group_name"),
    ("aws_elasticache_cluster", "aws_security_group", "security_group_ids"),
    ("aws_elasticache_subnet_group", "aws_subnet", "subnet_ids"),
    # EBS dependencies
    ("aws_volume_attachment", "aws_ebs_volume", "volume_id"),
    ("aws_volume_attachment", "aws_instance", "instance_id"),
    # SQS/SNS dependencies
    ("aws_sqs_queue_policy", "aws_sqs_queue", "queue_url"),
    ("aws_sns_topic_subscription", "aws_sns_topic", "topic_arn"),
]


class DependencyGraphBuilder:
    """
    Builds a dependency graph from RepliMap's GraphEngine.

    Uses the existing dependency information from GraphEngine and
    enhances it with blast-specific analysis.
    """

    def __init__(self) -> None:
        self.graph: nx.DiGraph = nx.DiGraph()
        self.nodes: dict[str, BlastNode] = {}
        self.edges: list[DependencyEdge] = []

    def build_from_graph_engine(
        self, graph_engine: GraphEngine, region: str = ""
    ) -> nx.DiGraph:
        """
        Build dependency graph from RepliMap's GraphEngine.

        Args:
            graph_engine: Existing graph engine with scanned resources
            region: AWS region for metadata

        Returns:
            NetworkX directed graph
        """
        # Step 1: Create nodes from GraphEngine resources
        for resource in graph_engine.get_all_resources():
            node = BlastNode(
                id=resource.id,
                type=str(resource.resource_type),
                name=resource.original_name or resource.id,
                arn=resource.arn,
                region=region or resource.region,
            )
            self.nodes[node.id] = node
            self.graph.add_node(node.id, **node.to_dict())

        # Step 2: Build edges from existing dependencies
        for resource in graph_engine.get_all_resources():
            for dep_id in resource.dependencies:
                if dep_id in self.nodes:
                    edge = DependencyEdge(
                        source_id=resource.id,
                        target_id=dep_id,
                        dependency_type=DependencyType.HARD,
                        description=f"{resource.resource_type} depends on {dep_id}",
                    )
                    self.edges.append(edge)
                    self.graph.add_edge(resource.id, dep_id)

        # Step 3: Find additional dependencies from config patterns
        for resource in graph_engine.get_all_resources():
            self._find_config_dependencies(resource)

        # Step 4: Calculate reverse dependencies
        self._calculate_reverse_dependencies()

        return self.graph

    def build_from_resources(self, resources: list[dict[str, Any]]) -> nx.DiGraph:
        """
        Build dependency graph from resource dictionaries.

        Args:
            resources: List of resource dicts from scanner

        Returns:
            NetworkX directed graph
        """
        # Step 1: Create nodes
        for resource in resources:
            node = BlastNode(
                id=resource["id"],
                type=resource["type"],
                name=resource.get("name", resource["id"]),
                arn=resource.get("arn"),
                region=resource.get("region", ""),
            )
            self.nodes[node.id] = node
            self.graph.add_node(node.id, **node.to_dict())

        # Step 2: Find and create edges
        for resource in resources:
            self._find_dependencies(resource)

        # Step 3: Calculate reverse dependencies
        self._calculate_reverse_dependencies()

        return self.graph

    def _find_config_dependencies(self, resource: Any) -> None:
        """Find dependencies from resource config for GraphEngine resources."""
        resource_type = str(resource.resource_type)
        resource_id = resource.id
        config = resource.config or {}

        for pattern in DEPENDENCY_PATTERNS:
            source_type, target_type, attr_path = pattern

            if resource_type != source_type:
                continue

            # Get the attribute value
            target_ids = self._get_attribute(config, attr_path)

            if not target_ids:
                continue

            # Normalize to list
            if isinstance(target_ids, str):
                target_ids = [target_ids]

            # Create edges
            for target_ref in target_ids:
                # Find the actual resource (might be ID, ARN, or name)
                actual_target = self._resolve_target(target_ref, target_type)

                if actual_target and actual_target in self.nodes:
                    # Check if edge already exists
                    if not self.graph.has_edge(resource_id, actual_target):
                        edge = DependencyEdge(
                            source_id=resource_id,
                            target_id=actual_target,
                            dependency_type=DependencyType.HARD,
                            attribute=attr_path,
                            description=f"{resource_type} -> {target_type} via {attr_path}",
                        )
                        self.edges.append(edge)
                        self.graph.add_edge(resource_id, actual_target)

    def _find_dependencies(self, resource: dict[str, Any]) -> None:
        """Find dependencies for a resource dictionary."""
        resource_type = resource["type"]
        resource_id = resource["id"]
        config = resource.get("config", {})

        for pattern in DEPENDENCY_PATTERNS:
            source_type, target_type, attr_path = pattern

            if resource_type != source_type:
                continue

            # Get the attribute value
            target_ids = self._get_attribute(config, attr_path)

            if not target_ids:
                continue

            # Normalize to list
            if isinstance(target_ids, str):
                target_ids = [target_ids]

            # Create edges
            for target_ref in target_ids:
                # Find the actual resource (might be ID, ARN, or name)
                actual_target = self._resolve_target(target_ref, target_type)

                if actual_target and actual_target in self.nodes:
                    edge = DependencyEdge(
                        source_id=resource_id,
                        target_id=actual_target,
                        dependency_type=DependencyType.HARD,
                        attribute=attr_path,
                        description=f"{resource_type} -> {target_type} via {attr_path}",
                    )
                    self.edges.append(edge)
                    self.graph.add_edge(resource_id, actual_target)

    def _get_attribute(self, config: dict[str, Any], path: str) -> Any | None:
        """Get nested attribute from config."""
        parts = path.split(".")
        value: Any = config

        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            elif isinstance(value, list) and part.isdigit():
                idx = int(part)
                value = value[idx] if idx < len(value) else None
            else:
                return None

            if value is None:
                return None

        return value

    def _resolve_target(self, target_ref: str, target_type: str) -> str | None:
        """
        Resolve a target reference to an actual resource ID.

        The reference might be:
        - Direct ID: "sg-12345"
        - ARN: "arn:aws:ec2:..."
        - Name: "my-security-group"
        """
        # Direct match
        if target_ref in self.nodes:
            return target_ref

        # Try to find by matching patterns
        for node_id, node in self.nodes.items():
            if node.type != target_type:
                continue

            # Match by ARN
            if node.arn and target_ref in node.arn:
                return node_id

            # Match by ID suffix
            if node_id.endswith(target_ref) or target_ref.endswith(node_id):
                return node_id

            # Match by name
            if node.name == target_ref:
                return node_id

        return None

    def _calculate_reverse_dependencies(self) -> None:
        """Calculate which resources depend on each resource."""
        for edge in self.edges:
            source = self.nodes.get(edge.source_id)
            target = self.nodes.get(edge.target_id)

            if source and target:
                if edge.target_id not in source.depends_on:
                    source.depends_on.append(edge.target_id)
                if edge.source_id not in target.depended_by:
                    target.depended_by.append(edge.source_id)

    def get_nodes(self) -> dict[str, BlastNode]:
        """Get all nodes."""
        return self.nodes

    def get_edges(self) -> list[DependencyEdge]:
        """Get all edges."""
        return self.edges
