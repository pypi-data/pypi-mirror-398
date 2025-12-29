"""
Summary link calculation for cross-container connections.

When showing VPCs as summary nodes, we need to:
1. Detect if any resource in VPC A connects to any resource in VPC B
2. Create a single "VPC A -> VPC B" summary link
3. Store metadata about the actual connections for tooltip
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SummaryLink:
    """A summary link between containers."""

    id: str
    source: str
    target: str
    link_type: str = "vpc_connection"
    is_summary: bool = True
    count: int = 0
    bidirectional: bool = False
    connection_types: list[str] = field(default_factory=list)
    sample_connections: list[dict[str, Any]] = field(default_factory=list)
    label: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "type": self.link_type,
            "is_summary": self.is_summary,
            "count": self.count,
            "bidirectional": self.bidirectional,
            "connection_types": self.connection_types,
            "sample_connections": self.sample_connections,
            "label": self.label,
        }


class SummaryLinkCalculator:
    """
    Calculates summary links between containers (VPCs, Subnets).

    When drilling down from Overview -> VPC Detail, links should:
    - Overview: VPC-to-VPC summary links (thick, labeled with count)
    - Detail: Individual resource links within the focused VPC
    """

    def __init__(
        self,
        nodes: list[dict[str, Any]],
        links: list[dict[str, Any]],
        vpc_map: dict[str, str] | None = None,
    ) -> None:
        """
        Initialize the calculator.

        Args:
            nodes: All resource nodes
            links: All resource links
            vpc_map: Mapping of resource_id -> vpc_id
        """
        self.nodes = nodes
        self.links = links
        self.vpc_map = vpc_map or {}
        self.node_map = {n["id"]: n for n in nodes}

        # Build VPC map from node properties if not provided
        if not self.vpc_map:
            self._build_vpc_map()

    def _build_vpc_map(self) -> None:
        """Build VPC map from node properties."""
        for node in self.nodes:
            node_id = node["id"]
            vpc_id = node.get("properties", {}).get("vpc_id")
            if vpc_id:
                self.vpc_map[node_id] = vpc_id
            elif node.get("type") == "aws_vpc":
                self.vpc_map[node_id] = node_id

    def calculate_vpc_summary_links(self) -> list[dict[str, Any]]:
        """
        Calculate VPC-to-VPC summary links.

        Returns:
            List of summary link dicts with:
            - source: vpc_id
            - target: vpc_id
            - count: number of actual connections
            - connection_types: set of connection types
            - sample_connections: first 5 actual connections for tooltip
        """
        # Group connections by VPC pair
        vpc_connections: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)

        for link in self.links:
            source_id = (
                link["source"]
                if isinstance(link["source"], str)
                else link["source"].get("id", link["source"])
            )
            target_id = (
                link["target"]
                if isinstance(link["target"], str)
                else link["target"].get("id", link["target"])
            )

            source_vpc = self.vpc_map.get(source_id)
            target_vpc = self.vpc_map.get(target_id)

            # Skip if same VPC or no VPC (global resources)
            if not source_vpc or not target_vpc:
                continue
            if source_vpc == target_vpc:
                continue

            # Normalize direction (alphabetically smaller first)
            vpc_pair = tuple(sorted([source_vpc, target_vpc]))
            vpc_connections[vpc_pair].append(
                {
                    "source": source_id,
                    "target": target_id,
                    "source_type": self.node_map.get(source_id, {}).get("type"),
                    "target_type": self.node_map.get(target_id, {}).get("type"),
                }
            )

        # Create summary links
        summary_links = []
        for (vpc_a, vpc_b), connections in vpc_connections.items():
            # Determine primary direction (which VPC has more outgoing)
            outgoing_from_a = sum(
                1 for c in connections if self.vpc_map.get(c["source"]) == vpc_a
            )

            summary_link = SummaryLink(
                id=f"summary_link_{vpc_a}_{vpc_b}",
                source=f"summary_{vpc_a}",
                target=f"summary_{vpc_b}",
                link_type="vpc_connection",
                is_summary=True,
                count=len(connections),
                bidirectional=0 < outgoing_from_a < len(connections),
                connection_types=list(
                    {f"{c['source_type']}->{c['target_type']}" for c in connections}
                ),
                sample_connections=connections[:5],
                label=f"{len(connections)} connections",
            )
            summary_links.append(summary_link.to_dict())

        return summary_links

    def calculate_global_service_links(
        self, global_category_nodes: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Calculate links between VPCs and global services (S3, SQS, etc).

        Returns summary links from VPC summary nodes to global category nodes.
        """
        summary_links = []

        for category_node in global_category_nodes:
            # Find all VPCs that connect to resources in this category
            member_ids = set(category_node.get("member_ids", []))
            connected_vpcs: set[str] = set()

            for link in self.links:
                source_id = (
                    link["source"]
                    if isinstance(link["source"], str)
                    else link["source"].get("id", link["source"])
                )
                target_id = (
                    link["target"]
                    if isinstance(link["target"], str)
                    else link["target"].get("id", link["target"])
                )

                if source_id in member_ids:
                    vpc = self.vpc_map.get(target_id)
                    if vpc:
                        connected_vpcs.add(vpc)
                if target_id in member_ids:
                    vpc = self.vpc_map.get(source_id)
                    if vpc:
                        connected_vpcs.add(vpc)

            # Create summary links
            for vpc_id in connected_vpcs:
                summary_links.append(
                    {
                        "id": f"summary_link_{vpc_id}_{category_node['id']}",
                        "source": f"summary_{vpc_id}",
                        "target": category_node["id"],
                        "type": "global_service_connection",
                        "is_summary": True,
                    }
                )

        return summary_links

    def get_cross_vpc_links(self) -> list[dict[str, Any]]:
        """Get all links that cross VPC boundaries."""
        cross_vpc = []

        for link in self.links:
            source_id = (
                link["source"]
                if isinstance(link["source"], str)
                else link["source"].get("id", link["source"])
            )
            target_id = (
                link["target"]
                if isinstance(link["target"], str)
                else link["target"].get("id", link["target"])
            )

            source_vpc = self.vpc_map.get(source_id)
            target_vpc = self.vpc_map.get(target_id)

            if source_vpc and target_vpc and source_vpc != target_vpc:
                cross_vpc.append(
                    {
                        **link,
                        "is_cross_vpc": True,
                        "source_vpc": source_vpc,
                        "target_vpc": target_vpc,
                    }
                )

        return cross_vpc


def calculate_summary_links(
    nodes: list[dict[str, Any]],
    links: list[dict[str, Any]],
    vpc_map: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """
    Convenience function to calculate VPC summary links.

    Args:
        nodes: All resource nodes
        links: All resource links
        vpc_map: Optional mapping of resource_id -> vpc_id

    Returns:
        List of summary link dictionaries
    """
    calculator = SummaryLinkCalculator(nodes, links, vpc_map)
    return calculator.calculate_vpc_summary_links()
