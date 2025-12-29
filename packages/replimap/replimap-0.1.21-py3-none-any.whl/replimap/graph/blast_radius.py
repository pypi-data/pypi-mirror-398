"""
Blast radius analysis for infrastructure graphs.

Calculates the impact of changes or failures in infrastructure:
- Direct dependencies: Resources immediately affected
- Indirect dependencies: Resources affected through cascading failures
- Impact scoring: Severity assessment based on affected resource types

Task 11: Blast radius calculation as Python module.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ImpactSeverity(Enum):
    """Severity level for blast radius impact."""

    LOW = "low"  # Internal resources, no user impact
    MEDIUM = "medium"  # Some services affected
    HIGH = "high"  # Multiple services affected
    CRITICAL = "critical"  # User-facing services affected


# Resource criticality weights for impact scoring
RESOURCE_CRITICALITY: dict[str, float] = {
    # User-facing (highest criticality)
    "aws_lb": 1.0,
    "aws_cloudfront_distribution": 1.0,
    "aws_api_gateway_rest_api": 1.0,
    "aws_route53_record": 0.9,
    # Compute (high criticality)
    "aws_instance": 0.8,
    "aws_ecs_service": 0.8,
    "aws_lambda_function": 0.8,
    "aws_autoscaling_group": 0.8,
    # Data (high criticality)
    "aws_db_instance": 0.9,
    "aws_rds_cluster": 0.9,
    "aws_dynamodb_table": 0.9,
    "aws_elasticache_cluster": 0.7,
    "aws_s3_bucket": 0.6,
    # Infrastructure (medium criticality)
    "aws_vpc": 0.5,
    "aws_subnet": 0.4,
    "aws_security_group": 0.4,
    "aws_nat_gateway": 0.5,
    "aws_internet_gateway": 0.6,
    # Low criticality
    "aws_iam_role": 0.3,
    "aws_iam_policy": 0.2,
    "aws_kms_key": 0.4,
}


@dataclass
class AffectedResource:
    """A resource affected by blast radius."""

    id: str
    name: str
    resource_type: str
    depth: int  # 0 = source, 1 = direct, 2+ = indirect
    impact_path: list[str]  # Path from source to this resource
    criticality: float

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.resource_type,
            "depth": self.depth,
            "impact_path": self.impact_path,
            "criticality": self.criticality,
        }


@dataclass
class BlastRadiusResult:
    """Result of blast radius analysis."""

    source_id: str
    source_name: str
    source_type: str
    direct: list[AffectedResource] = field(default_factory=list)
    indirect: list[AffectedResource] = field(default_factory=list)
    impact_score: float = 0.0
    severity: ImpactSeverity = ImpactSeverity.LOW
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "source": {
                "id": self.source_id,
                "name": self.source_name,
                "type": self.source_type,
            },
            "direct": [r.to_dict() for r in self.direct],
            "indirect": [r.to_dict() for r in self.indirect],
            "total_affected": len(self.direct) + len(self.indirect),
            "impact_score": round(self.impact_score, 2),
            "severity": self.severity.value,
            "summary": self.summary,
        }


class BlastRadiusCalculator:
    """
    Calculate blast radius for infrastructure nodes.

    Traces dependencies to find all resources that would be
    affected by a change or failure in the source resource.
    """

    def __init__(
        self,
        nodes: list[dict[str, Any]],
        links: list[dict[str, Any]],
        max_depth: int = 5,
    ) -> None:
        """
        Initialize the calculator.

        Args:
            nodes: List of resource nodes
            links: List of dependency links
            max_depth: Maximum traversal depth (prevents infinite loops)
        """
        self.nodes = nodes
        self.links = links
        self.max_depth = max_depth

        # Build lookup structures
        self.node_map: dict[str, dict[str, Any]] = {n["id"]: n for n in nodes}
        self.dependents: dict[str, list[str]] = defaultdict(list)  # who depends on this
        self.dependencies: dict[str, list[str]] = defaultdict(
            list
        )  # what this depends on

        self._build_dependency_graph()

    def _build_dependency_graph(self) -> None:
        """Build reverse dependency lookup."""
        for link in self.links:
            source_id = self._get_id(link.get("source"))
            target_id = self._get_id(link.get("target"))

            if source_id and target_id:
                # source depends on target -> target failure affects source
                self.dependents[target_id].append(source_id)
                self.dependencies[source_id].append(target_id)

    def _get_id(self, value: Any) -> str | None:
        """Extract ID from link source/target."""
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            return value.get("id")
        return None

    def calculate(self, source_id: str) -> BlastRadiusResult:
        """
        Calculate blast radius for a source resource.

        Args:
            source_id: ID of the resource to analyze

        Returns:
            BlastRadiusResult with affected resources and impact analysis
        """
        source_node = self.node_map.get(source_id, {})

        result = BlastRadiusResult(
            source_id=source_id,
            source_name=source_node.get("name", source_id),
            source_type=source_node.get("type", "unknown"),
        )

        # BFS to find affected resources
        visited: set[str] = {source_id}
        queue: list[tuple[str, int, list[str]]] = [(source_id, 0, [source_id])]

        while queue:
            current_id, depth, path = queue.pop(0)

            if depth >= self.max_depth:
                continue

            # Find resources that depend on current
            for dependent_id in self.dependents.get(current_id, []):
                if dependent_id in visited:
                    continue

                visited.add(dependent_id)
                dependent_node = self.node_map.get(dependent_id, {})
                new_path = path + [dependent_id]

                affected = AffectedResource(
                    id=dependent_id,
                    name=dependent_node.get("name", dependent_id),
                    resource_type=dependent_node.get("type", "unknown"),
                    depth=depth + 1,
                    impact_path=new_path,
                    criticality=RESOURCE_CRITICALITY.get(
                        dependent_node.get("type", ""), 0.3
                    ),
                )

                if depth == 0:
                    result.direct.append(affected)
                else:
                    result.indirect.append(affected)

                queue.append((dependent_id, depth + 1, new_path))

        # Calculate impact score and severity
        result.impact_score = self._calculate_impact_score(result)
        result.severity = self._determine_severity(result)
        result.summary = self._generate_summary(result)

        return result

    def _calculate_impact_score(self, result: BlastRadiusResult) -> float:
        """
        Calculate overall impact score (0-100).

        Based on:
        - Number of affected resources
        - Criticality of affected resources
        - Depth of impact (direct vs indirect)
        """
        score = 0.0

        # Direct impacts weighted more heavily
        for affected in result.direct:
            score += affected.criticality * 10

        # Indirect impacts
        for affected in result.indirect:
            # Reduce weight by depth
            depth_factor = 1 / (affected.depth + 1)
            score += affected.criticality * 5 * depth_factor

        # Normalize to 0-100 scale
        return min(100, score)

    def _determine_severity(self, result: BlastRadiusResult) -> ImpactSeverity:
        """Determine severity level from impact analysis."""
        # Check for user-facing resources
        user_facing_types = {
            "aws_lb",
            "aws_cloudfront_distribution",
            "aws_api_gateway_rest_api",
            "aws_route53_record",
        }

        all_affected = result.direct + result.indirect

        for affected in all_affected:
            if affected.resource_type in user_facing_types:
                return ImpactSeverity.CRITICAL

        # Check for data resources
        data_types = {
            "aws_db_instance",
            "aws_rds_cluster",
            "aws_dynamodb_table",
        }

        for affected in all_affected:
            if affected.resource_type in data_types:
                return ImpactSeverity.HIGH

        # Check by count
        total = len(all_affected)
        if total > 10:
            return ImpactSeverity.HIGH
        if total > 3:
            return ImpactSeverity.MEDIUM

        return ImpactSeverity.LOW

    def _generate_summary(self, result: BlastRadiusResult) -> str:
        """Generate human-readable summary."""
        total = len(result.direct) + len(result.indirect)

        if total == 0:
            return "No downstream dependencies detected."

        summary_parts = [f"{total} resource(s) affected"]

        if result.direct:
            summary_parts.append(f"{len(result.direct)} direct")

        if result.indirect:
            summary_parts.append(f"{len(result.indirect)} indirect")

        # Note critical types
        critical_types: set[str] = set()
        for affected in result.direct + result.indirect:
            if affected.criticality >= 0.8:
                critical_types.add(affected.resource_type.replace("aws_", ""))

        if critical_types:
            summary_parts.append(f"Critical: {', '.join(sorted(critical_types))}")

        return ". ".join(summary_parts) + "."

    def calculate_all(self) -> dict[str, BlastRadiusResult]:
        """
        Calculate blast radius for all nodes.

        Returns:
            Dictionary mapping node_id to BlastRadiusResult
        """
        results: dict[str, BlastRadiusResult] = {}

        for node in self.nodes:
            node_id = node.get("id")
            if node_id:
                results[node_id] = self.calculate(node_id)

        return results

    def find_high_impact_nodes(
        self, threshold: float = 50.0
    ) -> list[tuple[str, BlastRadiusResult]]:
        """
        Find nodes with high blast radius.

        Args:
            threshold: Minimum impact score to include

        Returns:
            List of (node_id, result) tuples sorted by impact
        """
        all_results = self.calculate_all()

        high_impact = [
            (node_id, result)
            for node_id, result in all_results.items()
            if result.impact_score >= threshold
        ]

        return sorted(high_impact, key=lambda x: -x[1].impact_score)


def calculate_blast_radius(
    nodes: list[dict[str, Any]],
    links: list[dict[str, Any]],
    source_id: str,
    max_depth: int = 5,
) -> dict[str, Any]:
    """
    Convenience function to calculate blast radius for a single node.

    Args:
        nodes: List of resource nodes
        links: List of dependency links
        source_id: ID of the resource to analyze
        max_depth: Maximum traversal depth

    Returns:
        Dictionary with blast radius analysis
    """
    calculator = BlastRadiusCalculator(nodes, links, max_depth)
    result = calculator.calculate(source_id)
    return result.to_dict()


def enrich_nodes_with_blast_radius(
    nodes: list[dict[str, Any]],
    links: list[dict[str, Any]],
    max_depth: int = 5,
) -> list[dict[str, Any]]:
    """
    Add blast radius summary to all nodes.

    Args:
        nodes: List of resource nodes
        links: List of dependency links
        max_depth: Maximum traversal depth

    Returns:
        Nodes with blast_radius property added
    """
    calculator = BlastRadiusCalculator(nodes, links, max_depth)

    for node in nodes:
        node_id = node.get("id")
        if node_id:
            result = calculator.calculate(node_id)
            node["blast_radius"] = {
                "direct_count": len(result.direct),
                "indirect_count": len(result.indirect),
                "total": len(result.direct) + len(result.indirect),
                "impact_score": round(result.impact_score, 2),
                "severity": result.severity.value,
            }

    return nodes


def find_critical_nodes(
    nodes: list[dict[str, Any]],
    links: list[dict[str, Any]],
    top_n: int = 10,
) -> list[dict[str, Any]]:
    """
    Find the most critical nodes based on blast radius.

    Args:
        nodes: List of resource nodes
        links: List of dependency links
        top_n: Number of top nodes to return

    Returns:
        List of critical nodes with full blast radius analysis
    """
    calculator = BlastRadiusCalculator(nodes, links)
    high_impact = calculator.find_high_impact_nodes(threshold=0)

    results = []
    for node_id, result in high_impact[:top_n]:
        node = calculator.node_map.get(node_id, {})
        results.append(
            {
                "node": node,
                "blast_radius": result.to_dict(),
            }
        )

    return results
