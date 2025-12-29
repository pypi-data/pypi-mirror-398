"""
D3.js Interactive HTML Formatter.

Generates an interactive force-directed graph visualization using D3.js.

Enhanced with:
- Hierarchical container layout for VPCs/Subnets
- Environment detection and filtering
- Smart VPC-based aggregation
- Overview mode with progressive disclosure
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from jinja2 import Environment, PackageLoader, select_autoescape

from replimap.graph.aggregation import SmartAggregator
from replimap.graph.environment import EnvironmentDetector
from replimap.graph.layout import HierarchicalLayoutEngine
from replimap.graph.naming import ResourceNamer
from replimap.graph.views import ViewManager

if TYPE_CHECKING:
    from replimap.graph.visualizer import VisualizationGraph


class D3Formatter:
    """
    Formats a VisualizationGraph as an interactive HTML page with D3.js.

    Features:
    - Force-directed graph layout with hierarchical containers
    - Environment detection and color-coded filtering
    - Smart VPC-based aggregation
    - Overview mode with progressive disclosure
    - Drag and drop nodes
    - Zoom and pan
    - Click to highlight connections
    - Filter by resource type and environment
    - Search functionality
    - Watermark for FREE tier exports
    """

    def __init__(self, show_watermark: bool = False) -> None:
        """Initialize the formatter with Jinja2 environment and processors.

        Args:
            show_watermark: Whether to show watermark on export (FREE tier).
        """
        self._show_watermark = show_watermark
        self.env = Environment(
            loader=PackageLoader("replimap.graph", "templates"),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self._env_detector = EnvironmentDetector()
        self._namer = ResourceNamer()
        self._aggregator = SmartAggregator()
        self._layout_engine = HierarchicalLayoutEngine()

    def format(self, graph: VisualizationGraph) -> str:
        """
        Format the graph as an interactive HTML page.

        Args:
            graph: The visualization graph to format

        Returns:
            HTML content as a string
        """
        # Prepare graph data for D3.js
        graph_data = self._prepare_graph_data(graph)

        # Enrich nodes with environment and naming info
        nodes = graph_data["nodes"]
        nodes = self._env_detector.enrich_nodes(nodes)
        nodes = self._namer.enrich_nodes(nodes)

        # Apply smart aggregation
        aggregated_nodes, aggregated_links = self._aggregator.aggregate(
            nodes, graph_data["links"]
        )

        # Calculate hierarchical layout
        layout_result = self._layout_engine.layout(aggregated_nodes, aggregated_links)

        # Create view manager with the processed nodes and get overview data
        view_manager = ViewManager(aggregated_nodes, aggregated_links)
        view_data = view_manager.get_overview_data()

        # Get unique environments for filter controls
        environments = sorted(
            {node.get("environment", "unknown") for node in aggregated_nodes}
        )

        # Get unique groups for filter controls
        groups = sorted({node.get("group", "other") for node in aggregated_nodes})

        # Get unique resource types
        resource_types = sorted({node.get("type", "") for node in aggregated_nodes})

        # Prepare final graph data with enriched nodes
        final_graph_data = {
            "nodes": aggregated_nodes,
            "links": aggregated_links,
        }

        # Render template
        template = self.env.get_template("graph.html.j2")
        return template.render(
            graph_data=json.dumps(final_graph_data),
            layout_data=json.dumps(self._serialize_layout(layout_result)),
            view_data=json.dumps(view_data),
            metadata=graph.metadata,
            groups=groups,
            environments=environments,
            resource_types=resource_types,
            node_count=len(aggregated_nodes),
            edge_count=len(aggregated_links),
            show_watermark=self._show_watermark,
        )

    def _prepare_graph_data(self, graph: VisualizationGraph) -> dict[str, Any]:
        """
        Prepare graph data in D3.js-compatible format.

        D3.js force simulation expects:
        - nodes: array of {id, ...}
        - links: array of {source, target, ...}
        """
        return {
            "nodes": [
                {
                    "id": node.id,
                    "type": node.resource_type,
                    "name": node.name,
                    "icon": node.icon,
                    "color": node.color,
                    "group": node.group,
                    "properties": node.properties,
                }
                for node in graph.nodes
            ],
            "links": [
                {
                    "source": edge.source,
                    "target": edge.target,
                    "label": edge.label,
                    "type": edge.edge_type,
                }
                for edge in graph.edges
            ],
        }

    def _serialize_layout(self, layout_result: dict[str, Any]) -> dict[str, Any]:
        """Serialize layout result for JSON output.

        The layout engine returns a dictionary with:
        - boxes: List of container box dictionaries
        - nodes: List of positioned node dictionaries
        - links: Original links (unchanged)
        - width/height: Optional bounds
        """
        # Layout result is already a dictionary from HierarchicalLayoutEngine
        return {
            "containers": layout_result.get("boxes", []),
            "nodes": layout_result.get("nodes", []),
            "width": layout_result.get("width", 1200),
            "height": layout_result.get("height", 800),
        }
