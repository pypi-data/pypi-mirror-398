"""
Graph Builder for creating filtered and grouped visualization graphs.

Combines filtering and grouping to produce simplified graph visualizations.
Works with the GraphVisualizer to create readable infrastructure graphs.

Enhanced with:
- Environment detection (prod/stage/test/dev)
- Intelligent naming for better readability
- Hierarchical layout support
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from replimap.graph.environment import EnvironmentDetector
from replimap.graph.filters import GraphFilter
from replimap.graph.grouper import GroupingConfig, ResourceGroup, ResourceGrouper
from replimap.graph.naming import ResourceNamer
from replimap.graph.visualizer import (
    RESOURCE_VISUALS,
    GraphEdge,
    GraphNode,
    VisualizationGraph,
)

if TYPE_CHECKING:
    from replimap.core import GraphEngine
    from replimap.core.models import ResourceNode

logger = logging.getLogger(__name__)


@dataclass
class BuilderConfig:
    """
    Configuration for graph building.

    Combines filter and grouping settings.

    Attributes:
        filter: Resource filter configuration
        grouping: Resource grouping configuration
        include_metadata: Include detailed metadata in output
    """

    filter: GraphFilter = field(default_factory=GraphFilter.default)
    grouping: GroupingConfig = field(default_factory=GroupingConfig)
    include_metadata: bool = True

    @classmethod
    def simplified(cls) -> BuilderConfig:
        """Create config for simplified (default) view."""
        return cls()

    @classmethod
    def full(cls) -> BuilderConfig:
        """Create config showing all resources."""
        return cls(
            filter=GraphFilter.show_everything(),
            grouping=GroupingConfig.disabled(),
        )

    @classmethod
    def security_view(cls) -> BuilderConfig:
        """Create config focused on security."""
        return cls(
            filter=GraphFilter.security_focused(),
            grouping=GroupingConfig(enabled=False),
        )


class GraphBuilder:
    """
    Builds filtered and grouped visualization graphs.

    Takes a GraphEngine and produces a VisualizationGraph with
    filtering and grouping applied for improved readability.
    """

    def __init__(self, config: BuilderConfig | None = None) -> None:
        """
        Initialize the builder.

        Args:
            config: Builder configuration (default creates BuilderConfig())
        """
        self.config = config or BuilderConfig()
        self._grouper = ResourceGrouper(self.config.grouping)
        self._env_detector = EnvironmentDetector()
        self._namer = ResourceNamer()

    def build(
        self,
        graph: GraphEngine,
        vpc_id: str | None = None,
    ) -> VisualizationGraph:
        """
        Build a visualization graph from a GraphEngine.

        Applies filtering and grouping to simplify the output.

        Args:
            graph: Source graph engine
            vpc_id: Optional VPC to filter by

        Returns:
            Simplified visualization graph
        """
        # Get all resources
        all_resources = graph.get_all_resources()
        logger.info(f"Building graph from {len(all_resources)} resources")

        # Filter by VPC if specified
        if vpc_id:
            all_resources = self._filter_by_vpc(all_resources, graph, vpc_id)
            logger.info(f"After VPC filter: {len(all_resources)} resources")

        # Apply resource filter
        filtered_resources = self.config.filter.filter_resources(all_resources)
        hidden_counts = self.config.filter.get_hidden_count(all_resources)
        logger.info(
            f"After filter: {len(filtered_resources)} visible, "
            f"{sum(hidden_counts.values())} hidden"
        )

        # Apply grouping
        ungrouped, groups = self._grouper.group_resources(filtered_resources)
        logger.info(
            f"After grouping: {len(ungrouped)} individual, {len(groups)} groups"
        )

        # Build visualization graph
        nodes: list[GraphNode] = []
        edges: list[GraphEdge] = []
        node_ids: set[str] = set()

        # Add ungrouped resources as nodes
        for resource in ungrouped:
            node = self._resource_to_node(resource)
            nodes.append(node)
            node_ids.add(resource.id)

        # Add groups as nodes
        for group in groups:
            node = self._group_to_node(group)
            nodes.append(node)
            node_ids.add(group.group_id)

        # Build edges
        edges = self._build_edges(ungrouped, groups, graph, node_ids)

        # Build metadata
        metadata = self._build_metadata(
            all_resources, filtered_resources, ungrouped, groups, hidden_counts
        )

        return VisualizationGraph(
            nodes=nodes,
            edges=edges,
            metadata=metadata,
        )

    def _filter_by_vpc(
        self,
        resources: list[ResourceNode],
        graph: GraphEngine,
        vpc_id: str,
    ) -> list[ResourceNode]:
        """Filter resources to those belonging to a VPC."""

        vpc_resource_ids: set[str] = {vpc_id}

        # Find resources directly in the VPC
        for resource in resources:
            config = resource.config
            if config.get("vpc_id") == vpc_id:
                vpc_resource_ids.add(resource.id)

        # Add resources that depend on VPC resources
        for resource in resources:
            for dep_id in resource.dependencies:
                if dep_id in vpc_resource_ids:
                    vpc_resource_ids.add(resource.id)

        return [r for r in resources if r.id in vpc_resource_ids]

    def _resource_to_node(self, resource: ResourceNode) -> GraphNode:
        """Convert a ResourceNode to a GraphNode with environment and naming."""
        resource_type_str = str(resource.resource_type)
        visuals = RESOURCE_VISUALS.get(
            resource_type_str,
            {"icon": "RES", "color": "#6b7280", "group": "other"},
        )

        properties = self._extract_key_properties(resource)

        # Get basic name
        raw_name = resource.original_name or resource.terraform_name or resource.id

        # Build a temporary node dict for environment detection and naming
        temp_node = {
            "id": resource.id,
            "name": raw_name,
            "type": resource_type_str,
            "properties": {
                **properties,
                "tags": dict(resource.tags) if resource.tags else {},
            },
        }

        # Detect environment
        env_info = self._env_detector.detect(temp_node)

        # Get display name
        display = self._namer.get_display_name(temp_node)

        # Create the node
        node = GraphNode(
            id=resource.id,
            resource_type=resource_type_str,
            name=display.short_name,
            properties=properties,
            icon=visuals["icon"],
            color=visuals["color"],
            group=visuals["group"],
        )

        # Add extended properties for the new features
        node.properties["environment"] = env_info.name
        node.properties["env_color"] = env_info.color
        node.properties["full_name"] = display.full_name
        if display.service_name:
            node.properties["service_name"] = display.service_name

        return node

    def _group_to_node(self, group: ResourceGroup) -> GraphNode:
        """Convert a ResourceGroup to a GraphNode."""
        visuals = RESOURCE_VISUALS.get(
            group.resource_type,
            {"icon": "GRP", "color": "#6b7280", "group": "other"},
        )

        # Use a lighter/muted version of the color for groups
        color = self._lighten_color(visuals["color"])

        return GraphNode(
            id=group.group_id,
            resource_type=group.resource_type,
            name=group.label,
            properties={
                "count": group.count,
                "is_group": True,
                "scope_id": group.scope_id,
                **group.properties,
            },
            icon=f"[{group.count}]",  # Show count as icon
            color=color,
            group=visuals["group"],
        )

    def _lighten_color(self, hex_color: str) -> str:
        """Lighten a hex color for group display."""
        # Simple approach: add transparency suffix
        if hex_color.startswith("#") and len(hex_color) == 7:
            return hex_color + "80"  # 50% opacity
        return hex_color

    def _extract_key_properties(self, resource: ResourceNode) -> dict[str, Any]:
        """Extract key properties for display."""
        props: dict[str, Any] = {}
        config = resource.config

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

    def _build_edges(
        self,
        resources: list[ResourceNode],
        groups: list[ResourceGroup],
        graph: GraphEngine,
        visible_node_ids: set[str],
    ) -> list[GraphEdge]:
        """Build edges for the visualization graph."""
        edges: list[GraphEdge] = []
        seen_edges: set[tuple[str, str]] = set()

        # Create lookup for group membership
        member_to_group: dict[str, str] = {}
        for group in groups:
            for member_id in group.member_ids:
                member_to_group[member_id] = group.group_id

        # Add edges from individual resources
        for resource in resources:
            source_id = resource.id
            for dep_id in resource.dependencies:
                target_id = self._resolve_target(
                    dep_id, member_to_group, visible_node_ids
                )
                if target_id and (source_id, target_id) not in seen_edges:
                    edges.append(
                        GraphEdge(
                            source=source_id,
                            target=target_id,
                            label="",
                            edge_type="dependency",
                        )
                    )
                    seen_edges.add((source_id, target_id))

        # Add edges from groups (based on member dependencies)
        for group in groups:
            source_id = group.group_id
            group_deps: set[str] = set()

            for member_id in group.member_ids:
                member_resource = graph.get_resource(member_id)
                if member_resource:
                    for dep_id in member_resource.dependencies:
                        target_id = self._resolve_target(
                            dep_id, member_to_group, visible_node_ids
                        )
                        if target_id and target_id != source_id:
                            group_deps.add(target_id)

            for target_id in group_deps:
                if (source_id, target_id) not in seen_edges:
                    edges.append(
                        GraphEdge(
                            source=source_id,
                            target=target_id,
                            label="",
                            edge_type="dependency",
                        )
                    )
                    seen_edges.add((source_id, target_id))

        return edges

    def _resolve_target(
        self,
        dep_id: str,
        member_to_group: dict[str, str],
        visible_node_ids: set[str],
    ) -> str | None:
        """Resolve a dependency target to a visible node."""
        # If target is visible, use it directly
        if dep_id in visible_node_ids:
            return dep_id

        # If target is in a group, use the group
        if dep_id in member_to_group:
            group_id = member_to_group[dep_id]
            if group_id in visible_node_ids:
                return group_id

        # Target is not visible
        return None

    def _build_metadata(
        self,
        all_resources: list[ResourceNode],
        filtered_resources: list[ResourceNode],
        ungrouped: list[ResourceNode],
        groups: list[ResourceGroup],
        hidden_counts: dict[str, int],
    ) -> dict[str, Any]:
        """Build metadata for the visualization graph."""
        total_grouped = sum(g.count for g in groups)

        metadata: dict[str, Any] = {
            "total_resources": len(all_resources),
            "visible_resources": len(filtered_resources),
            "hidden_resources": len(all_resources) - len(filtered_resources),
            "ungrouped_count": len(ungrouped),
            "group_count": len(groups),
            "grouped_resources": total_grouped,
            "node_count": len(ungrouped) + len(groups),
            "simplification": {
                "filter_applied": not self.config.filter.show_all,
                "grouping_applied": self.config.grouping.enabled,
                "hidden_by_type": hidden_counts,
            },
        }

        if groups:
            metadata["groups"] = [
                {
                    "id": g.group_id,
                    "type": g.resource_type,
                    "count": g.count,
                    "label": g.label,
                }
                for g in groups
            ]

        return metadata

    def get_simplification_summary(
        self,
        graph: GraphEngine,
        vpc_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Get summary of how much simplification would occur.

        Useful for showing users what will be hidden/grouped.

        Args:
            graph: Source graph engine
            vpc_id: Optional VPC filter

        Returns:
            Summary of simplification effects
        """
        all_resources = graph.get_all_resources()

        if vpc_id:
            all_resources = self._filter_by_vpc(all_resources, graph, vpc_id)

        filtered = self.config.filter.filter_resources(all_resources)
        hidden_counts = self.config.filter.get_hidden_count(all_resources)

        ungrouped, groups = self._grouper.group_resources(filtered)
        group_summary = self._grouper.get_grouping_summary(ungrouped, groups)

        original_count = len(all_resources)
        final_count = len(ungrouped) + len(groups)
        reduction = original_count - final_count

        return {
            "original_count": original_count,
            "after_filtering": len(filtered),
            "hidden_count": len(all_resources) - len(filtered),
            "hidden_by_type": hidden_counts,
            "after_grouping": final_count,
            "reduction": reduction,
            "reduction_percent": (
                round(reduction / original_count * 100, 1) if original_count > 0 else 0
            ),
            "grouping": group_summary,
            "filter_summary": self.config.filter.get_summary(),
        }
