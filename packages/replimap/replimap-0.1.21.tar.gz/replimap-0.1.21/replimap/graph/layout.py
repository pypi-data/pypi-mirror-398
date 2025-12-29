"""
Hierarchical layout engine for infrastructure graphs.

Uses nested containers instead of force-directed layout:
- Level 0: VPCs (large rectangles)
- Level 1: Subnet groups (private/public)
- Level 2: Resources (nodes within containers)

This creates a logical visual hierarchy that mirrors AWS architecture.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ContainerLevel(int, Enum):
    """Container hierarchy levels."""

    VPC = 0
    SUBNET = 1
    SERVICE = 2


@dataclass
class LayoutBox:
    """
    A rectangular container for nodes.

    Represents VPCs, subnets, or service groups as visual containers.
    """

    id: str
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0
    label: str = ""
    level: ContainerLevel = ContainerLevel.VPC
    parent_id: str | None = None
    children: list[str] = field(default_factory=list)
    style: dict[str, str] = field(default_factory=dict)
    properties: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "label": self.label,
            "level": self.level.value,
            "parent_id": self.parent_id,
            "children": self.children,
            "style": self.style,
            "properties": self.properties,
        }


@dataclass
class LayoutNode:
    """A positioned node within a container."""

    id: str
    x: float = 0.0
    y: float = 0.0
    radius: float = 24.0
    parent_box: str | None = None
    fixed: bool = True  # Fixed position in hierarchical layout

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "radius": self.radius,
            "parent_box": self.parent_box,
            "fixed": self.fixed,
        }


@dataclass
class LayoutConfig:
    """Configuration for hierarchical layout."""

    # VPC container settings
    vpc_padding: int = 40
    vpc_min_width: int = 300
    vpc_min_height: int = 200
    vpc_gap: int = 50  # Gap between VPCs
    vpc_header_height: int = 40

    # Subnet container settings
    subnet_padding: int = 20
    subnet_min_width: int = 200
    subnet_min_height: int = 150
    subnet_gap: int = 20  # Gap between subnets
    subnet_header_height: int = 30

    # Node settings
    node_spacing: int = 70  # Space between nodes
    node_radius: int = 24  # Default node radius

    # Canvas settings
    canvas_padding: int = 50  # Padding around the entire layout
    max_nodes_per_row: int = 6  # Max nodes per row in a container

    # Global resources (not in VPC)
    global_section_width: int = 400
    global_section_gap: int = 40


class HierarchicalLayoutEngine:
    """
    Creates nested container layout for AWS infrastructure.

    Strategy:
    1. Group resources by VPC
    2. Within each VPC, group by subnet type (private/public)
    3. Position containers left-to-right by VPC
    4. Position resources within containers using grid layout
    5. Global resources (S3, SQS, etc.) positioned in a separate area
    """

    def __init__(self, config: LayoutConfig | None = None) -> None:
        """Initialize the layout engine."""
        self.config = config or LayoutConfig()

    def layout(
        self,
        nodes: list[dict[str, Any]],
        links: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Create hierarchical layout from flat node/link data.

        Args:
            nodes: List of node dictionaries with id, type, properties
            links: List of link dictionaries with source, target

        Returns:
            Layout data with positioned nodes and container boxes:
            {
                'boxes': [LayoutBox.to_dict(), ...],
                'nodes': [LayoutNode.to_dict(), ...],
                'links': [...],
                'layout_type': 'hierarchical',
                'bounds': {'width': ..., 'height': ...}
            }
        """
        # Step 1: Build hierarchy
        hierarchy = self._build_hierarchy(nodes)

        # Step 2: Calculate container sizes
        self._calculate_sizes(hierarchy)

        # Step 3: Position containers
        self._position_containers(hierarchy)

        # Step 4: Position nodes within containers
        positioned_nodes = self._position_nodes(hierarchy, nodes)

        # Step 5: Flatten boxes for output
        boxes = self._flatten_boxes(hierarchy)

        # Step 6: Calculate bounds
        bounds = self._calculate_bounds(boxes, positioned_nodes)

        return {
            "boxes": [box.to_dict() for box in boxes],
            "nodes": [node.to_dict() for node in positioned_nodes],
            "links": links,
            "layout_type": "hierarchical",
            "bounds": bounds,
        }

    def _build_hierarchy(self, nodes: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Group nodes into VPC -> Subnet -> Resources hierarchy.

        Returns:
            {
                'vpcs': {
                    vpc_id: {
                        'id': vpc_id,
                        'name': str,
                        'subnets': {
                            'private': {'resources': [...]},
                            'public': {'resources': [...]},
                        },
                        'direct_resources': [...],
                        'node_data': {...}  # Original VPC node
                    }
                },
                'global': [...]  # Resources not in VPC
            }
        """
        vpcs: dict[str, dict[str, Any]] = {}
        global_resources: list[dict[str, Any]] = []

        # First pass: find VPC nodes
        for node in nodes:
            if node.get("type") == "aws_vpc":
                vpc_id = node["id"]
                vpcs[vpc_id] = {
                    "id": vpc_id,
                    "name": node.get("name", vpc_id),
                    "subnets": {},
                    "direct_resources": [],
                    "node_data": node,
                }

        # Second pass: categorize all nodes
        for node in nodes:
            if node.get("type") == "aws_vpc":
                continue  # Already processed

            vpc_id = self._get_vpc_id(node)
            subnet_id = self._get_subnet_id(node)

            if not vpc_id:
                global_resources.append(node)
                continue

            # Ensure VPC exists (might be referenced but not in nodes)
            if vpc_id not in vpcs:
                vpcs[vpc_id] = {
                    "id": vpc_id,
                    "name": vpc_id,
                    "subnets": {},
                    "direct_resources": [],
                    "node_data": None,
                }

            if subnet_id:
                subnet_type = self._get_subnet_type(node, subnet_id)
                if subnet_type not in vpcs[vpc_id]["subnets"]:
                    vpcs[vpc_id]["subnets"][subnet_type] = {
                        "type": subnet_type,
                        "resources": [],
                    }
                vpcs[vpc_id]["subnets"][subnet_type]["resources"].append(node)
            else:
                vpcs[vpc_id]["direct_resources"].append(node)

        return {
            "vpcs": vpcs,
            "global": global_resources,
        }

    def _get_vpc_id(self, node: dict[str, Any]) -> str | None:
        """Extract VPC ID from node properties or dependencies."""
        props = node.get("properties", {})

        # Direct vpc_id property
        if "vpc_id" in props:
            return props["vpc_id"]

        # Check if this IS a VPC
        if node.get("type") == "aws_vpc":
            return node["id"]

        return None

    def _get_subnet_id(self, node: dict[str, Any]) -> str | None:
        """Extract subnet ID from node properties."""
        props = node.get("properties", {})

        if "subnet_id" in props:
            return props["subnet_id"]

        subnet_ids = props.get("subnet_ids", [])
        if isinstance(subnet_ids, list) and subnet_ids:
            return subnet_ids[0]

        return None

    def _get_subnet_type(self, node: dict[str, Any], subnet_id: str) -> str:
        """Determine if subnet is public or private based on name/tags."""
        props = node.get("properties", {})

        # Check for explicit subnet name
        subnet_name = props.get("subnet_name", "")
        if not subnet_name:
            subnet_name = subnet_id

        subnet_lower = subnet_name.lower()

        if "public" in subnet_lower:
            return "public"
        if "private" in subnet_lower:
            return "private"

        # Check resource type hints
        resource_type = node.get("type", "")
        public_types = {"aws_lb", "aws_nat_gateway", "aws_internet_gateway", "aws_eip"}
        if resource_type in public_types:
            return "public"

        # Default to private for safety
        return "private"

    def _calculate_sizes(self, hierarchy: dict[str, Any]) -> None:
        """Calculate width/height for each container based on contents."""
        cfg = self.config

        for _vpc_id, vpc in hierarchy["vpcs"].items():
            # Calculate sizes for each subnet
            for _subnet_type, subnet in vpc["subnets"].items():
                resource_count = len(subnet["resources"])
                if resource_count == 0:
                    subnet["width"] = 0
                    subnet["height"] = 0
                    continue

                cols = min(
                    math.ceil(math.sqrt(resource_count)),
                    cfg.max_nodes_per_row,
                )
                rows = math.ceil(resource_count / cols) if cols > 0 else 1

                subnet["width"] = max(
                    cols * cfg.node_spacing + cfg.subnet_padding * 2,
                    cfg.subnet_min_width,
                )
                subnet["height"] = max(
                    rows * cfg.node_spacing
                    + cfg.subnet_padding * 2
                    + cfg.subnet_header_height,
                    cfg.subnet_min_height,
                )

            # Calculate sizes for direct resources (not in subnet)
            direct_count = len(vpc["direct_resources"])
            if direct_count > 0:
                direct_cols = min(
                    math.ceil(math.sqrt(direct_count)),
                    cfg.max_nodes_per_row,
                )
                direct_rows = math.ceil(direct_count / direct_cols)
                vpc["direct_width"] = direct_cols * cfg.node_spacing
                vpc["direct_height"] = direct_rows * cfg.node_spacing
            else:
                vpc["direct_width"] = 0
                vpc["direct_height"] = 0

            # Calculate VPC size based on contents
            total_subnet_width = sum(
                s.get("width", 0) + cfg.subnet_gap
                for s in vpc["subnets"].values()
                if s.get("width", 0) > 0
            )
            max_subnet_height = max(
                (s.get("height", 0) for s in vpc["subnets"].values()),
                default=0,
            )

            # Include direct resources row if any
            if vpc["direct_height"] > 0:
                max_subnet_height += vpc["direct_height"] + cfg.vpc_padding

            vpc["width"] = max(
                total_subnet_width + cfg.vpc_padding * 2,
                vpc["direct_width"] + cfg.vpc_padding * 2,
                cfg.vpc_min_width,
            )
            vpc["height"] = max(
                max_subnet_height + cfg.vpc_padding * 2 + cfg.vpc_header_height,
                cfg.vpc_min_height,
            )

    def _position_containers(self, hierarchy: dict[str, Any]) -> None:
        """Position VPCs and subnets in the canvas."""
        cfg = self.config
        x_offset = cfg.canvas_padding
        y_base = cfg.canvas_padding

        for _vpc_id, vpc in hierarchy["vpcs"].items():
            vpc["x"] = x_offset
            vpc["y"] = y_base

            # Position subnets within VPC
            subnet_x = vpc["x"] + cfg.vpc_padding
            subnet_y = vpc["y"] + cfg.vpc_padding + cfg.vpc_header_height

            # Private subnets on left, public on right
            for subnet_type in ["private", "public"]:
                if subnet_type in vpc["subnets"]:
                    subnet = vpc["subnets"][subnet_type]
                    if subnet.get("width", 0) > 0:
                        subnet["x"] = subnet_x
                        subnet["y"] = subnet_y
                        subnet_x += subnet["width"] + cfg.subnet_gap

            x_offset += vpc["width"] + cfg.vpc_gap

        # Position global resources
        if hierarchy["global"]:
            hierarchy["global_x"] = x_offset
            hierarchy["global_y"] = y_base

    def _position_nodes(
        self,
        hierarchy: dict[str, Any],
        original_nodes: list[dict[str, Any]],
    ) -> list[LayoutNode]:
        """Position individual nodes within their containers."""
        cfg = self.config
        positioned: list[LayoutNode] = []

        for vpc_id, vpc in hierarchy["vpcs"].items():
            # Position nodes in subnets
            for subnet_type, subnet in vpc["subnets"].items():
                resources = subnet.get("resources", [])
                if not resources:
                    continue

                cols = min(
                    math.ceil(math.sqrt(len(resources))),
                    cfg.max_nodes_per_row,
                )

                for i, resource in enumerate(resources):
                    row = i // cols
                    col = i % cols

                    x = (
                        subnet["x"]
                        + cfg.subnet_padding
                        + col * cfg.node_spacing
                        + cfg.node_radius
                    )
                    y = (
                        subnet["y"]
                        + cfg.subnet_header_height
                        + cfg.subnet_padding
                        + row * cfg.node_spacing
                        + cfg.node_radius
                    )

                    positioned.append(
                        LayoutNode(
                            id=resource["id"],
                            x=x,
                            y=y,
                            radius=self._get_node_radius(resource),
                            parent_box=f"{vpc_id}_{subnet_type}",
                            fixed=True,
                        )
                    )

            # Position direct VPC resources
            direct_resources = vpc.get("direct_resources", [])
            if direct_resources:
                cols = min(
                    math.ceil(math.sqrt(len(direct_resources))),
                    cfg.max_nodes_per_row,
                )

                # Position below subnets
                max_subnet_y = max(
                    (
                        s.get("y", 0) + s.get("height", 0)
                        for s in vpc["subnets"].values()
                    ),
                    default=vpc["y"] + cfg.vpc_header_height,
                )
                direct_y = max_subnet_y + cfg.vpc_padding

                for i, resource in enumerate(direct_resources):
                    row = i // cols
                    col = i % cols

                    x = (
                        vpc["x"]
                        + cfg.vpc_padding
                        + col * cfg.node_spacing
                        + cfg.node_radius
                    )
                    y = direct_y + row * cfg.node_spacing + cfg.node_radius

                    positioned.append(
                        LayoutNode(
                            id=resource["id"],
                            x=x,
                            y=y,
                            radius=self._get_node_radius(resource),
                            parent_box=vpc_id,
                            fixed=True,
                        )
                    )

        # Position global resources
        global_resources = hierarchy.get("global", [])
        if global_resources:
            global_x = hierarchy.get("global_x", cfg.canvas_padding)
            global_y = hierarchy.get("global_y", cfg.canvas_padding)

            cols = min(
                math.ceil(math.sqrt(len(global_resources))),
                cfg.max_nodes_per_row,
            )

            for i, resource in enumerate(global_resources):
                row = i // cols
                col = i % cols

                x = global_x + col * cfg.node_spacing + cfg.node_radius
                y = global_y + row * cfg.node_spacing + cfg.node_radius

                positioned.append(
                    LayoutNode(
                        id=resource["id"],
                        x=x,
                        y=y,
                        radius=self._get_node_radius(resource),
                        parent_box="global",
                        fixed=True,
                    )
                )

        return positioned

    def _get_node_radius(self, node: dict[str, Any]) -> float:
        """Calculate node radius based on importance/type."""
        importance_map = {
            "aws_vpc": 28,
            "aws_lb": 28,
            "aws_db_instance": 26,
            "aws_elasticache_cluster": 26,
            "aws_instance": 24,
            "aws_lambda_function": 24,
            "aws_nat_gateway": 24,
            "aws_subnet": 22,
            "aws_security_group": 20,
        }
        resource_type = node.get("type", "")
        return float(importance_map.get(resource_type, self.config.node_radius))

    def _flatten_boxes(self, hierarchy: dict[str, Any]) -> list[LayoutBox]:
        """Flatten hierarchy into list of LayoutBox objects."""
        cfg = self.config
        boxes: list[LayoutBox] = []

        for vpc_id, vpc in hierarchy["vpcs"].items():
            # Add VPC container
            vpc_box = LayoutBox(
                id=vpc_id,
                x=vpc["x"],
                y=vpc["y"],
                width=vpc["width"],
                height=vpc["height"],
                label=vpc["name"],
                level=ContainerLevel.VPC,
                parent_id=None,
                children=list(vpc["subnets"].keys()),
                style={
                    "fill": "rgba(30, 41, 59, 0.3)",
                    "stroke": "#334155",
                    "strokeWidth": "2",
                },
                properties={
                    "resource_count": sum(
                        len(s.get("resources", [])) for s in vpc["subnets"].values()
                    )
                    + len(vpc.get("direct_resources", [])),
                },
            )
            boxes.append(vpc_box)

            # Add subnet containers
            for subnet_type, subnet in vpc["subnets"].items():
                if subnet.get("width", 0) == 0:
                    continue

                subnet_box = LayoutBox(
                    id=f"{vpc_id}_{subnet_type}",
                    x=subnet["x"],
                    y=subnet["y"],
                    width=subnet["width"],
                    height=subnet["height"],
                    label=f"{subnet_type.title()} Subnets",
                    level=ContainerLevel.SUBNET,
                    parent_id=vpc_id,
                    children=[r["id"] for r in subnet.get("resources", [])],
                    style=self._get_subnet_style(subnet_type),
                    properties={
                        "type": subnet_type,
                        "resource_count": len(subnet.get("resources", [])),
                    },
                )
                boxes.append(subnet_box)

        # Add global resources container if any
        if hierarchy.get("global"):
            global_count = len(hierarchy["global"])
            cols = min(math.ceil(math.sqrt(global_count)), cfg.max_nodes_per_row)
            rows = math.ceil(global_count / cols) if cols > 0 else 1

            global_box = LayoutBox(
                id="global",
                x=hierarchy.get("global_x", cfg.canvas_padding),
                y=hierarchy.get("global_y", cfg.canvas_padding),
                width=cols * cfg.node_spacing + cfg.subnet_padding * 2,
                height=rows * cfg.node_spacing + cfg.subnet_padding * 2 + 30,
                label="Global Resources",
                level=ContainerLevel.VPC,
                parent_id=None,
                children=[r["id"] for r in hierarchy["global"]],
                style={
                    "fill": "rgba(99, 102, 241, 0.1)",
                    "stroke": "#6366f1",
                    "strokeWidth": "2",
                    "strokeDasharray": "5,5",
                },
                properties={
                    "resource_count": global_count,
                },
            )
            boxes.append(global_box)

        return boxes

    def _get_subnet_style(self, subnet_type: str) -> dict[str, str]:
        """Get style for subnet container based on type."""
        if subnet_type == "public":
            return {
                "fill": "rgba(16, 185, 129, 0.05)",
                "stroke": "#10b981",
                "strokeWidth": "1.5",
                "strokeDasharray": "4,4",
            }
        else:  # private
            return {
                "fill": "rgba(30, 41, 59, 0.2)",
                "stroke": "#475569",
                "strokeWidth": "1.5",
                "strokeDasharray": "4,4",
            }

    def _calculate_bounds(
        self,
        boxes: list[LayoutBox],
        nodes: list[LayoutNode],
    ) -> dict[str, float]:
        """Calculate the total bounds of the layout."""
        if not boxes and not nodes:
            return {"width": 800, "height": 600}

        max_x = 0.0
        max_y = 0.0

        for box in boxes:
            max_x = max(max_x, box.x + box.width)
            max_y = max(max_y, box.y + box.height)

        for node in nodes:
            max_x = max(max_x, node.x + node.radius)
            max_y = max(max_y, node.y + node.radius)

        return {
            "width": max_x + self.config.canvas_padding,
            "height": max_y + self.config.canvas_padding,
        }


def create_layout(
    nodes: list[dict[str, Any]],
    links: list[dict[str, Any]],
    layout_type: str = "hierarchical",
    config: LayoutConfig | None = None,
) -> dict[str, Any]:
    """
    Factory function for creating layouts.

    Args:
        nodes: List of node dictionaries
        links: List of link dictionaries
        layout_type: 'hierarchical' or 'force'
        config: Optional layout configuration

    Returns:
        Layout data with positioned nodes and container boxes
    """
    if layout_type == "hierarchical":
        engine = HierarchicalLayoutEngine(config)
        return engine.layout(nodes, links)
    elif layout_type == "force":
        # Return data in force-layout compatible format
        # D3 will handle positioning
        return {
            "nodes": nodes,
            "links": links,
            "boxes": [],
            "layout_type": "force",
            "bounds": {"width": 1200, "height": 800},
        }
    else:
        raise ValueError(f"Unknown layout type: {layout_type}")
