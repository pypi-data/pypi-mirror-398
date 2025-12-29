"""
JSON Formatter for Graph Visualization.

Exports the graph data as a structured JSON document.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from replimap.graph.visualizer import VisualizationGraph


class JSONFormatter:
    """
    Formats a VisualizationGraph as JSON.

    The output includes nodes, edges, and metadata in a structured format
    suitable for further processing or integration with other tools.
    """

    def format(self, graph: VisualizationGraph, indent: int = 2) -> str:
        """
        Format the graph as JSON.

        Args:
            graph: The visualization graph to format
            indent: JSON indentation level (default: 2)

        Returns:
            JSON string representation of the graph
        """
        output = self._build_output(graph)
        return json.dumps(output, indent=indent, default=str)

    def _build_output(self, graph: VisualizationGraph) -> dict[str, Any]:
        """Build the output dictionary structure."""
        # Calculate statistics
        nodes_by_group = self._group_nodes_by_category(graph)
        nodes_by_type = self._group_nodes_by_type(graph)

        return {
            "version": "1.0",
            "generated_at": datetime.now(UTC).isoformat(),
            "metadata": {
                **graph.metadata,
            },
            "statistics": {
                "total_nodes": len(graph.nodes),
                "total_edges": len(graph.edges),
                "nodes_by_group": {
                    group: len(nodes) for group, nodes in nodes_by_group.items()
                },
                "nodes_by_type": {
                    rtype: len(nodes) for rtype, nodes in nodes_by_type.items()
                },
            },
            "nodes": [
                {
                    "id": node.id,
                    "type": node.resource_type,
                    "name": node.name,
                    "group": node.group,
                    "properties": node.properties,
                    "visual": {
                        "icon": node.icon,
                        "color": node.color,
                    },
                }
                for node in graph.nodes
            ],
            "edges": [
                {
                    "source": edge.source,
                    "target": edge.target,
                    "label": edge.label,
                    "type": edge.edge_type,
                }
                for edge in graph.edges
            ],
        }

    def _group_nodes_by_category(
        self, graph: VisualizationGraph
    ) -> dict[str, list[str]]:
        """Group node IDs by their category."""
        groups: dict[str, list[str]] = {}
        for node in graph.nodes:
            if node.group not in groups:
                groups[node.group] = []
            groups[node.group].append(node.id)
        return groups

    def _group_nodes_by_type(self, graph: VisualizationGraph) -> dict[str, list[str]]:
        """Group node IDs by their resource type."""
        types: dict[str, list[str]] = {}
        for node in graph.nodes:
            if node.resource_type not in types:
                types[node.resource_type] = []
            types[node.resource_type].append(node.id)
        return types
