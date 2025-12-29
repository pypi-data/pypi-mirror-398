"""
Mermaid Diagram Formatter.

Generates Mermaid flowchart syntax from visualization graphs.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from replimap.graph.visualizer import GraphEdge, GraphNode, VisualizationGraph


class MermaidFormatter:
    """
    Formats a VisualizationGraph as a Mermaid flowchart diagram.

    Groups nodes by resource category (network, compute, database, etc.)
    and creates styled subgraphs.
    """

    # Resource group display names
    GROUP_NAMES: dict[str, str] = {
        "network": "Network Resources",
        "compute": "Compute Resources",
        "database": "Database Resources",
        "storage": "Storage Resources",
        "security": "Security Resources",
        "messaging": "Messaging Resources",
        "other": "Other Resources",
    }

    def format(self, graph: VisualizationGraph) -> str:
        """
        Format the graph as a Mermaid diagram.

        Args:
            graph: The visualization graph to format

        Returns:
            Mermaid diagram syntax as a string
        """
        lines = [
            "# AWS Infrastructure Dependency Graph",
            "",
            "```mermaid",
            "flowchart TB",
            "",
        ]

        # Group nodes by category
        grouped = self._group_nodes(graph.nodes)

        # Generate subgraphs for each group
        for group, nodes in grouped.items():
            if not nodes:
                continue

            group_name = self.GROUP_NAMES.get(group, group.title())
            lines.append(f"    subgraph {self._sanitize_id(group)}[{group_name}]")

            for node in nodes:
                lines.append(f"        {self._format_node(node)}")

            lines.append("    end")
            lines.append("")

        # Generate edges
        lines.append("    %% Dependencies")
        for edge in graph.edges:
            lines.append(f"    {self._format_edge(edge)}")

        # Add styles
        lines.append("")
        lines.extend(self._generate_styles(graph.nodes))

        lines.append("```")
        lines.append("")

        # Add legend
        lines.append("## Legend")
        lines.append("")
        lines.append("| Icon | Resource Type |")
        lines.append("|------|---------------|")
        lines.append("| VPC | Virtual Private Cloud |")
        lines.append("| SUB | Subnet |")
        lines.append("| SG | Security Group |")
        lines.append("| EC2 | EC2 Instance |")
        lines.append("| RDS | RDS Database |")
        lines.append("| S3 | S3 Bucket |")
        lines.append("| ALB | Application Load Balancer |")
        lines.append("| LAM | Lambda Function |")
        lines.append("| IAM | IAM Role |")
        lines.append("| NAT | NAT Gateway |")
        lines.append("")

        # Add metadata
        if graph.metadata:
            lines.append("## Metadata")
            lines.append("")
            lines.append(f"- **Region:** {graph.metadata.get('region', 'N/A')}")
            lines.append(f"- **Profile:** {graph.metadata.get('profile', 'N/A')}")
            lines.append(f"- **Resources:** {graph.metadata.get('resource_count', 0)}")
            lines.append(f"- **Dependencies:** {graph.metadata.get('edge_count', 0)}")
            lines.append("")

        return "\n".join(lines)

    def _group_nodes(self, nodes: list[GraphNode]) -> dict[str, list[GraphNode]]:
        """Group nodes by their resource category."""
        groups: dict[str, list[GraphNode]] = {
            "network": [],
            "compute": [],
            "database": [],
            "storage": [],
            "security": [],
            "messaging": [],
            "other": [],
        }

        for node in nodes:
            group = node.group if node.group in groups else "other"
            groups[group].append(node)

        return groups

    def _format_node(self, node: GraphNode) -> str:
        """
        Format a single node as Mermaid syntax.

        Uses different shapes based on resource type.
        """
        node_id = self._sanitize_id(node.id)
        label = f"{node.icon}: {node.name}"

        # Escape special characters in label
        label = label.replace('"', "'")

        # Use different shapes for different resource types
        if node.group == "network":
            return f'{node_id}["{label}"]'  # Rectangle
        elif node.group == "compute":
            return f'{node_id}("{label}")'  # Rounded rectangle
        elif node.group == "database":
            return f'{node_id}[("{label}")]'  # Cylinder (database)
        elif node.group == "security":
            return f"{node_id}{{{'{label}'}}}"  # Hexagon
        elif node.group == "storage":
            return f'{node_id}[["{label}"]]'  # Subroutine
        else:
            return f'{node_id}["{label}"]'  # Default rectangle

    def _format_edge(self, edge: GraphEdge) -> str:
        """Format an edge as Mermaid syntax."""
        source = self._sanitize_id(edge.source)
        target = self._sanitize_id(edge.target)

        if edge.label:
            return f"{source} -->|{edge.label}| {target}"
        else:
            return f"{source} --> {target}"

    def _generate_styles(self, nodes: list[GraphNode]) -> list[str]:
        """Generate Mermaid style definitions."""
        styles = ["    %% Styles"]

        # Collect unique colors by node
        for node in nodes:
            node_id = self._sanitize_id(node.id)
            color = node.color
            # Convert hex to Mermaid style
            styles.append(
                f"    style {node_id} fill:{color},stroke:#333,stroke-width:2px"
            )

        return styles

    @staticmethod
    def _sanitize_id(node_id: str) -> str:
        """
        Sanitize a node ID for use in Mermaid.

        Mermaid has restrictions on node IDs:
        - No special characters except underscore
        - No starting with numbers in some cases
        """
        # Replace hyphens with underscores
        sanitized = node_id.replace("-", "_")
        # Remove other special characters
        sanitized = re.sub(r"[^a-zA-Z0-9_]", "", sanitized)
        # Ensure it starts with a letter
        if sanitized and sanitized[0].isdigit():
            sanitized = "n" + sanitized
        return sanitized
