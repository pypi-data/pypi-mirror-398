"""
Graph Visualization Engine.

Generates visual representations of AWS infrastructure dependency graphs
in multiple formats: Mermaid, HTML (D3.js), and JSON.

Supports graph simplification through:
- Filtering: Hide noisy resources (SG rules, routes) by default
- Grouping: Collapse large collections into single nodes
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import boto3

    from replimap.core import GraphEngine
    from replimap.core.models import ResourceNode
    from replimap.graph.filters import GraphFilter
    from replimap.graph.grouper import GroupingConfig

logger = logging.getLogger(__name__)


class OutputFormat(str, Enum):
    """Output format for graph visualization."""

    MERMAID = "mermaid"
    HTML = "html"
    JSON = "json"

    def __str__(self) -> str:
        return self.value


@dataclass
class GraphNode:
    """A node in the visualization graph."""

    id: str  # e.g., "vpc-abc123"
    resource_type: str  # e.g., "aws_vpc"
    name: str  # e.g., "production-vpc"
    properties: dict[str, Any] = field(default_factory=dict)  # Key attributes

    # Visual properties
    icon: str = ""
    color: str = "#6366f1"
    group: str = "other"


@dataclass
class GraphEdge:
    """An edge (dependency) in the graph."""

    source: str  # Source node ID
    target: str  # Target node ID
    label: str = ""  # e.g., "subnet_id", "vpc_id"
    edge_type: str = "dependency"  # dependency, reference, contains


@dataclass
class VisualizationGraph:
    """Complete graph for visualization."""

    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "nodes": [
                {
                    "id": n.id,
                    "type": n.resource_type,
                    "name": n.name,
                    "properties": n.properties,
                    "icon": n.icon,
                    "color": n.color,
                    "group": n.group,
                }
                for n in self.nodes
            ],
            "edges": [
                {
                    "source": e.source,
                    "target": e.target,
                    "label": e.label,
                    "type": e.edge_type,
                }
                for e in self.edges
            ],
            "metadata": self.metadata,
        }


# Resource type to visual properties mapping
RESOURCE_VISUALS: dict[str, dict[str, str]] = {
    "aws_vpc": {"icon": "VPC", "color": "#10b981", "group": "network"},
    "aws_subnet": {"icon": "SUB", "color": "#34d399", "group": "network"},
    "aws_security_group": {"icon": "SG", "color": "#f59e0b", "group": "security"},
    "aws_instance": {"icon": "EC2", "color": "#6366f1", "group": "compute"},
    "aws_db_instance": {"icon": "RDS", "color": "#8b5cf6", "group": "database"},
    "aws_s3_bucket": {"icon": "S3", "color": "#ec4899", "group": "storage"},
    "aws_lb": {"icon": "ALB", "color": "#14b8a6", "group": "network"},
    "aws_lb_listener": {"icon": "LSN", "color": "#0d9488", "group": "network"},
    "aws_lb_target_group": {"icon": "TG", "color": "#0f766e", "group": "network"},
    "aws_lambda_function": {"icon": "LAM", "color": "#f97316", "group": "compute"},
    "aws_iam_role": {"icon": "IAM", "color": "#eab308", "group": "security"},
    "aws_kms_key": {"icon": "KMS", "color": "#a855f7", "group": "security"},
    "aws_elasticache_cluster": {"icon": "EC", "color": "#ef4444", "group": "database"},
    "aws_nat_gateway": {"icon": "NAT", "color": "#22c55e", "group": "network"},
    "aws_eip": {"icon": "EIP", "color": "#84cc16", "group": "network"},
    "aws_route_table": {"icon": "RT", "color": "#06b6d4", "group": "network"},
    "aws_internet_gateway": {"icon": "IGW", "color": "#0ea5e9", "group": "network"},
    "aws_db_subnet_group": {"icon": "DSG", "color": "#7c3aed", "group": "database"},
    "aws_elasticache_subnet_group": {
        "icon": "ESG",
        "color": "#dc2626",
        "group": "database",
    },
    "aws_sqs_queue": {"icon": "SQS", "color": "#f472b6", "group": "messaging"},
    "aws_sns_topic": {"icon": "SNS", "color": "#fb7185", "group": "messaging"},
    "aws_ebs_volume": {"icon": "EBS", "color": "#a78bfa", "group": "storage"},
    "aws_s3_bucket_policy": {"icon": "S3P", "color": "#f9a8d4", "group": "storage"},
    "aws_vpc_endpoint": {"icon": "VPE", "color": "#2dd4bf", "group": "network"},
    "aws_launch_template": {"icon": "LT", "color": "#818cf8", "group": "compute"},
    "aws_autoscaling_group": {"icon": "ASG", "color": "#4f46e5", "group": "compute"},
    "aws_db_parameter_group": {"icon": "PG", "color": "#c084fc", "group": "database"},
    "aws_route": {"icon": "RTE", "color": "#38bdf8", "group": "network"},
}


class GraphVisualizer:
    """
    Main visualization engine.

    Scans AWS resources using existing scanners, builds the dependency graph,
    and generates visualizations in multiple formats.
    """

    def __init__(
        self,
        session: boto3.Session,
        region: str,
        profile: str | None = None,
    ) -> None:
        """
        Initialize the visualizer.

        Args:
            session: Boto3 session for AWS access
            region: AWS region to scan
            profile: AWS profile name (for display)
        """
        self.session = session
        self.region = region
        self.profile = profile

    def generate(
        self,
        vpc_id: str | None = None,
        output_format: OutputFormat = OutputFormat.HTML,
        output_path: Path | None = None,
        *,
        filter_config: GraphFilter | None = None,
        grouping_config: GroupingConfig | None = None,
        show_all: bool = False,
        show_sg_rules: bool = False,
        show_routes: bool = False,
        no_collapse: bool = False,
    ) -> str | Path:
        """
        Generate visualization in specified format.

        Args:
            vpc_id: Optional VPC to scope the scan
            output_format: mermaid, html, or json
            output_path: Where to save (None for stdout)
            filter_config: Custom filter configuration
            grouping_config: Custom grouping configuration
            show_all: Show all resources (overrides filter)
            show_sg_rules: Show security group rules
            show_routes: Show routes and route tables
            no_collapse: Disable resource grouping

        Returns:
            Generated content (str) or path to file
        """
        from replimap.core import GraphEngine
        from replimap.graph.builder import BuilderConfig, GraphBuilder
        from replimap.graph.filters import GraphFilter as GF
        from replimap.graph.grouper import GroupingConfig as GC
        from replimap.scanners import run_all_scanners

        # 1. Build dependency graph using existing scanners
        graph = GraphEngine()
        logger.info(f"Scanning AWS resources in {self.region}...")
        run_all_scanners(self.session, self.region, graph)

        # 2. Configure filter
        if filter_config is not None:
            graph_filter = filter_config
        elif show_all:
            graph_filter = GF.show_everything()
        else:
            graph_filter = GF(
                show_all=False,
                show_sg_rules=show_sg_rules,
                show_routes=show_routes,
            )

        # 3. Configure grouping
        if grouping_config is not None:
            grouping = grouping_config
        elif no_collapse:
            grouping = GC.disabled()
        else:
            grouping = GC()

        # 4. Build visualization graph with filtering and grouping
        builder_config = BuilderConfig(
            filter=graph_filter,
            grouping=grouping,
        )
        builder = GraphBuilder(builder_config)
        viz_graph = builder.build(graph, vpc_id=vpc_id)

        # Add region/profile to metadata
        viz_graph.metadata.update(
            {
                "region": self.region,
                "profile": self.profile,
            }
        )

        # 5. Format output
        if output_format == OutputFormat.MERMAID:
            content = self._to_mermaid(viz_graph)
            suffix = ".md"
        elif output_format == OutputFormat.JSON:
            content = self._to_json(viz_graph)
            suffix = ".json"
        else:  # HTML
            content = self._to_html(viz_graph)
            suffix = ".html"

        # 6. Save or return
        if output_path:
            # Ensure correct suffix
            if output_path.suffix != suffix:
                output_path = output_path.with_suffix(suffix)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content)
            return output_path
        return content

    def generate_simplified(
        self,
        vpc_id: str | None = None,
        output_format: OutputFormat = OutputFormat.HTML,
        output_path: Path | None = None,
    ) -> str | Path:
        """
        Generate simplified visualization (default behavior).

        Hides noisy resources and collapses large groups.
        Equivalent to generate() with default options.

        Args:
            vpc_id: Optional VPC to scope the scan
            output_format: mermaid, html, or json
            output_path: Where to save (None for stdout)

        Returns:
            Generated content (str) or path to file
        """
        return self.generate(
            vpc_id=vpc_id,
            output_format=output_format,
            output_path=output_path,
        )

    def generate_full(
        self,
        vpc_id: str | None = None,
        output_format: OutputFormat = OutputFormat.HTML,
        output_path: Path | None = None,
    ) -> str | Path:
        """
        Generate full visualization showing all resources.

        Shows all resources without filtering or grouping.

        Args:
            vpc_id: Optional VPC to scope the scan
            output_format: mermaid, html, or json
            output_path: Where to save (None for stdout)

        Returns:
            Generated content (str) or path to file
        """
        return self.generate(
            vpc_id=vpc_id,
            output_format=output_format,
            output_path=output_path,
            show_all=True,
            no_collapse=True,
        )

    def _filter_by_vpc(self, graph: GraphEngine, vpc_id: str) -> GraphEngine:
        """Filter graph to only include resources in a specific VPC."""
        from replimap.core.models import ResourceType

        # Get resources that belong to the VPC
        vpc_resource_ids: set[str] = {vpc_id}

        # Find all resources that depend on or are connected to this VPC
        for resource in graph.get_all_resources():
            # Check if resource is directly in the VPC
            config = resource.config
            if config.get("vpc_id") == vpc_id:
                vpc_resource_ids.add(resource.id)
            # Check for subnet association with VPC
            if resource.resource_type == ResourceType.SUBNET:
                if config.get("vpc_id") == vpc_id:
                    vpc_resource_ids.add(resource.id)
            # Check security groups
            if resource.resource_type == ResourceType.SECURITY_GROUP:
                if config.get("vpc_id") == vpc_id:
                    vpc_resource_ids.add(resource.id)

        # Add resources that depend on VPC resources
        for resource in graph.get_all_resources():
            for dep_id in resource.dependencies:
                if dep_id in vpc_resource_ids:
                    vpc_resource_ids.add(resource.id)

        return graph.get_subgraph(list(vpc_resource_ids))

    def _to_visualization_graph(self, graph: GraphEngine) -> VisualizationGraph:
        """Convert GraphEngine to visualization graph."""
        nodes: list[GraphNode] = []
        edges: list[GraphEdge] = []
        node_ids: set[str] = set()

        for resource in graph.get_all_resources():
            # Get visual properties
            resource_type_str = str(resource.resource_type)
            visuals = RESOURCE_VISUALS.get(
                resource_type_str,
                {"icon": "RES", "color": "#6b7280", "group": "other"},
            )

            # Extract key properties for display
            properties = self._extract_key_properties(resource)

            node = GraphNode(
                id=resource.id,
                resource_type=resource_type_str,
                name=resource.original_name or resource.terraform_name or resource.id,
                properties=properties,
                icon=visuals["icon"],
                color=visuals["color"],
                group=visuals["group"],
            )
            nodes.append(node)
            node_ids.add(resource.id)

        # Extract edges from dependencies
        for resource in graph.get_all_resources():
            for dep_id in resource.dependencies:
                if dep_id in node_ids:
                    edge = GraphEdge(
                        source=resource.id,
                        target=dep_id,
                        label="",
                        edge_type="dependency",
                    )
                    edges.append(edge)

        return VisualizationGraph(
            nodes=nodes,
            edges=edges,
            metadata={
                "region": self.region,
                "profile": self.profile,
                "resource_count": len(nodes),
                "edge_count": len(edges),
            },
        )

    def _extract_key_properties(self, resource: ResourceNode) -> dict[str, Any]:
        """Extract key properties for display."""
        props: dict[str, Any] = {}
        config = resource.config

        # Common properties to extract
        key_attrs = [
            "cidr_block",
            "instance_type",
            "engine",
            "engine_version",
            "availability_zone",
            "public",
            "encrypted",
            "multi_az",
            "port",
            "protocol",
            "node_type",
            "num_cache_nodes",
        ]

        for attr in key_attrs:
            if attr in config and config[attr] is not None:
                props[attr] = config[attr]

        return props

    def _to_mermaid(self, graph: VisualizationGraph) -> str:
        """Convert to Mermaid diagram syntax."""
        from replimap.graph.formatters.mermaid import MermaidFormatter

        return MermaidFormatter().format(graph)

    def _to_json(self, graph: VisualizationGraph) -> str:
        """Convert to JSON."""
        from replimap.graph.formatters.json_format import JSONFormatter

        return JSONFormatter().format(graph)

    def _to_html(self, graph: VisualizationGraph) -> str:
        """Convert to interactive HTML with D3.js."""
        from replimap.graph.formatters.d3 import D3Formatter
        from replimap.licensing import check_graph_export_watermark

        # Check if watermark should be shown (FREE tier only)
        show_watermark = check_graph_export_watermark()

        return D3Formatter(show_watermark=show_watermark).format(graph)
