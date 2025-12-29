"""
Calculate blast radius impact scores.

Determines the severity and scope of impact when a resource
is deleted or modified.
"""

from __future__ import annotations

import logging

import networkx as nx

from replimap.blast.models import (
    BlastNode,
    BlastRadiusResult,
    BlastZone,
    DependencyEdge,
    ImpactLevel,
)

logger = logging.getLogger(__name__)


# Base impact scores by resource type (0-100)
RESOURCE_IMPACT_SCORES: dict[str, int] = {
    # Core infrastructure - CRITICAL
    "aws_vpc": 100,
    "aws_db_instance": 95,
    "aws_rds_cluster": 95,
    "aws_elasticache_cluster": 90,
    # Compute - HIGH
    "aws_instance": 80,
    "aws_ecs_service": 85,
    "aws_ecs_cluster": 85,
    "aws_lambda_function": 75,
    "aws_eks_cluster": 90,
    "aws_autoscaling_group": 85,
    "aws_launch_template": 70,
    # Network - HIGH
    "aws_lb": 85,
    "aws_nat_gateway": 80,
    "aws_internet_gateway": 85,
    "aws_subnet": 70,
    "aws_route_table": 60,
    "aws_vpc_endpoint": 65,
    # Security - HIGH
    "aws_security_group": 75,
    "aws_iam_role": 70,
    "aws_iam_policy": 65,
    # Storage - MEDIUM
    "aws_s3_bucket": 65,
    "aws_ebs_volume": 60,
    "aws_efs_file_system": 70,
    # Database supporting - MEDIUM
    "aws_db_subnet_group": 55,
    "aws_db_parameter_group": 50,
    "aws_elasticache_subnet_group": 55,
    # Load balancing - MEDIUM
    "aws_lb_target_group": 60,
    "aws_lb_listener": 55,
    # Messaging - MEDIUM
    "aws_sqs_queue": 55,
    "aws_sns_topic": 50,
    # Supporting - LOW
    "aws_route": 30,
    "aws_route_table_association": 35,
    "aws_cloudwatch_log_group": 30,
    "aws_cloudwatch_metric_alarm": 25,
    "aws_eip": 40,
    # Default
    "_default": 50,
}


class ImpactCalculator:
    """
    Calculate impact scores for blast radius analysis.
    """

    def __init__(
        self,
        graph: nx.DiGraph,
        nodes: dict[str, BlastNode],
        edges: list[DependencyEdge] | None = None,
    ) -> None:
        self.graph = graph
        self.nodes = nodes
        self.edges = edges or []

    def calculate_blast_radius(
        self,
        center_id: str,
        max_depth: int = 10,
    ) -> BlastRadiusResult:
        """
        Calculate blast radius from a center resource.

        Args:
            center_id: ID of the resource to analyze
            max_depth: Maximum depth to traverse

        Returns:
            BlastRadiusResult with all affected resources
        """
        if center_id not in self.nodes:
            raise ValueError(f"Resource {center_id} not found in graph")

        center = self.nodes[center_id]

        # Find all resources that depend on the center (reverse traversal)
        affected = self._find_dependents(center_id, max_depth)

        # Organize into zones by depth
        zones = self._organize_into_zones(affected)

        # Calculate impact scores
        self._calculate_scores(affected)

        # Recalculate zone scores after individual scores
        for zone in zones:
            zone.total_impact_score = sum(r.impact_score for r in zone.resources)

        # Determine overall impact
        overall_impact, overall_score = self._calculate_overall_impact(affected)

        # Get relevant edges
        affected_edges = self._get_affected_edges(affected)

        # Generate safe deletion order
        safe_order = self._calculate_safe_deletion_order(center_id, affected)

        # Generate warnings
        warnings = self._generate_warnings(center, affected)

        return BlastRadiusResult(
            center_resource=center,
            zones=zones,
            affected_resources=list(affected.values()),
            edges=affected_edges,
            total_affected=len(affected),
            max_depth=max(z.depth for z in zones) if zones else 0,
            overall_impact=overall_impact,
            overall_score=overall_score,
            safe_deletion_order=safe_order,
            warnings=warnings,
        )

    def _find_dependents(
        self,
        center_id: str,
        max_depth: int,
    ) -> dict[str, BlastNode]:
        """Find all resources that depend on the center."""
        affected: dict[str, BlastNode] = {}
        visited: set[str] = set()
        queue: list[tuple[str, int]] = [(center_id, 0)]  # (resource_id, depth)

        while queue:
            current_id, depth = queue.pop(0)

            if current_id in visited or depth > max_depth:
                continue

            visited.add(current_id)

            if current_id in self.nodes:
                # Create a copy of the node to avoid modifying the original
                original = self.nodes[current_id]
                node = BlastNode(
                    id=original.id,
                    type=original.type,
                    name=original.name,
                    arn=original.arn,
                    region=original.region,
                    depends_on=list(original.depends_on),
                    depended_by=list(original.depended_by),
                )
                node.depth = depth
                affected[current_id] = node

                # Find resources that depend on this one
                for dependent_id in original.depended_by:
                    if dependent_id not in visited:
                        queue.append((dependent_id, depth + 1))

        return affected

    def _organize_into_zones(
        self,
        affected: dict[str, BlastNode],
    ) -> list[BlastZone]:
        """Organize affected resources into zones by depth."""
        zones_dict: dict[int, list[BlastNode]] = {}

        for node in affected.values():
            if node.depth not in zones_dict:
                zones_dict[node.depth] = []
            zones_dict[node.depth].append(node)

        zones: list[BlastZone] = []
        for depth in sorted(zones_dict.keys()):
            resources = zones_dict[depth]
            total_score = sum(r.impact_score for r in resources)
            zones.append(
                BlastZone(
                    depth=depth,
                    resources=resources,
                    total_impact_score=total_score,
                )
            )

        return zones

    def _calculate_scores(self, affected: dict[str, BlastNode]) -> None:
        """Calculate impact scores for all affected resources."""
        for node in affected.values():
            base_score = RESOURCE_IMPACT_SCORES.get(
                node.type, RESOURCE_IMPACT_SCORES["_default"]
            )

            # Reduce score by depth (further = less immediate impact)
            depth_factor = max(0.3, 1.0 - (node.depth * 0.15))

            # Increase score by number of dependents
            dependent_factor = 1.0 + (len(node.depended_by) * 0.05)

            node.impact_score = int(base_score * depth_factor * dependent_factor)
            node.impact_score = min(100, node.impact_score)

            # Set impact level
            node.impact_level = self._score_to_level(node.impact_score)

    def _score_to_level(self, score: int) -> ImpactLevel:
        """Convert score to impact level."""
        if score >= 80:
            return ImpactLevel.CRITICAL
        elif score >= 60:
            return ImpactLevel.HIGH
        elif score >= 40:
            return ImpactLevel.MEDIUM
        elif score >= 20:
            return ImpactLevel.LOW
        else:
            return ImpactLevel.NONE

    def _calculate_overall_impact(
        self,
        affected: dict[str, BlastNode],
    ) -> tuple[ImpactLevel, int]:
        """Calculate overall impact level and score."""
        if not affected:
            return ImpactLevel.NONE, 0

        # Use the maximum score among affected resources
        max_score = max(r.impact_score for r in affected.values())

        # Factor in the count of affected resources
        count_factor = min(1.5, 1.0 + (len(affected) * 0.02))
        overall_score = int(max_score * count_factor)
        overall_score = min(100, overall_score)

        return self._score_to_level(overall_score), overall_score

    def _get_affected_edges(
        self,
        affected: dict[str, BlastNode],
    ) -> list[DependencyEdge]:
        """Get edges that involve affected resources."""
        affected_ids = set(affected.keys())
        return [
            edge
            for edge in self.edges
            if edge.source_id in affected_ids or edge.target_id in affected_ids
        ]

    def _calculate_safe_deletion_order(
        self,
        center_id: str,
        affected: dict[str, BlastNode],
    ) -> list[str]:
        """
        Calculate safe deletion order.

        Delete dependents first, then the resource itself.
        """
        if not affected:
            return []

        # Create subgraph of affected resources
        affected_ids = list(affected.keys())

        try:
            # Create subgraph
            subgraph = self.graph.subgraph(affected_ids).copy()

            # Reverse topological sort (delete leaves first)
            order = list(nx.topological_sort(subgraph))
            order.reverse()

            return order
        except nx.NetworkXUnfeasible:
            # Cycle detected - just return by depth (most dependent first)
            return sorted(affected_ids, key=lambda x: -affected[x].depth)

    def _generate_warnings(
        self,
        center: BlastNode,
        affected: dict[str, BlastNode],
    ) -> list[str]:
        """Generate warnings about the blast radius."""
        warnings: list[str] = []

        # High impact warning
        critical_count = len(
            [r for r in affected.values() if r.impact_level == ImpactLevel.CRITICAL]
        )
        if critical_count > 0:
            warnings.append(f"{critical_count} CRITICAL resources will be affected")

        # Database warning
        db_affected = [r for r in affected.values() if "db" in r.type.lower()]
        if db_affected:
            warnings.append(
                f"{len(db_affected)} database(s) will be affected - ensure backups exist"
            )

        # Production warning (heuristic: resources with "prod" in name)
        prod_affected = [r for r in affected.values() if "prod" in r.name.lower()]
        if prod_affected:
            warnings.append(f"{len(prod_affected)} production resource(s) detected")

        # Large blast radius
        if len(affected) > 20:
            warnings.append(f"Large blast radius: {len(affected)} resources affected")

        # VPC deletion warning
        if center.type == "aws_vpc":
            warnings.append("Deleting a VPC will destroy all contained resources")

        # Security group with many dependents
        if center.type == "aws_security_group" and len(center.depended_by) > 5:
            warnings.append(
                f"Security group is used by {len(center.depended_by)} resources"
            )

        return warnings
