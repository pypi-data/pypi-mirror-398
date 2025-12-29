"""
Orphaned resource detection for infrastructure graphs.

Identifies resources that appear to be unused or orphaned:
- No incoming or outgoing dependencies
- Security groups with no attachments
- Volumes not attached to instances
- Target groups with no targets
- Subnets with no resources

Task 14: Orphaned resource detection.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from typing import Any


class OrphanReason(Enum):
    """Reason a resource is considered orphaned."""

    NO_CONNECTIONS = "no_connections"  # No links in or out
    NO_ATTACHMENTS = "no_attachments"  # SG/Volume not attached
    NO_TARGETS = "no_targets"  # Target group empty
    NO_RESOURCES = "no_resources"  # Subnet/VPC empty
    NO_REFERENCES = "no_references"  # IAM/KMS not referenced
    UNREACHABLE = "unreachable"  # Not connected to any entry point


class OrphanSeverity(Enum):
    """Severity/importance of the orphan finding."""

    INFO = "info"  # Might be intentional (backup, DR)
    LOW = "low"  # Unused but minimal cost
    MEDIUM = "medium"  # Unused with some cost
    HIGH = "high"  # Unused with significant cost


# Resource types that are expected to have attachments
ATTACHMENT_RESOURCES = {
    "aws_security_group": "No instances/resources using this security group",
    "aws_ebs_volume": "Volume not attached to any instance",
    "aws_iam_role": "Role not assumed by any resource",
    "aws_iam_policy": "Policy not attached to any role/user",
    "aws_kms_key": "Key not used by any resource",
    "aws_lb_target_group": "Target group has no targets",
    "aws_key_pair": "Key pair not used by any instance",
}

# Resource types that should contain other resources
CONTAINER_RESOURCES = {
    "aws_vpc": "VPC contains no resources",
    "aws_subnet": "Subnet contains no instances",
    "aws_ecs_cluster": "Cluster has no services",
}

# Cost estimates for orphaned resources (monthly)
ORPHAN_COST_ESTIMATES: dict[str, float] = {
    "aws_ebs_volume": 10.0,  # ~100GB gp3
    "aws_eip": 3.60,  # Unused EIP
    "aws_nat_gateway": 32.0,  # Base cost
    "aws_lb": 16.0,  # Minimum ALB cost
    "aws_db_instance": 50.0,  # Minimum RDS
    "aws_elasticache_cluster": 20.0,  # Minimum cache
    "aws_elasticsearch_domain": 30.0,  # Minimum ES
}


@dataclass
class OrphanedResource:
    """A detected orphaned resource."""

    resource_id: str
    resource_name: str
    resource_type: str
    reason: OrphanReason
    severity: OrphanSeverity
    estimated_monthly_cost: float
    message: str
    recommendation: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.resource_id,
            "name": self.resource_name,
            "type": self.resource_type,
            "reason": self.reason.value,
            "severity": self.severity.value,
            "estimated_monthly_cost": self.estimated_monthly_cost,
            "message": self.message,
            "recommendation": self.recommendation,
        }


class OrphanDetector:
    """
    Detect orphaned resources in infrastructure.

    Analyzes the dependency graph to find resources that:
    - Have no dependencies (isolated)
    - Are not referenced by any other resource
    - Appear to be unused based on type-specific rules
    """

    def __init__(
        self,
        nodes: list[dict[str, Any]],
        links: list[dict[str, Any]],
    ) -> None:
        """
        Initialize the detector.

        Args:
            nodes: List of resource nodes
            links: List of dependency links
        """
        self.nodes = nodes
        self.links = links
        self.node_map: dict[str, dict[str, Any]] = {n["id"]: n for n in nodes}

        # Build connection tracking
        self.incoming: dict[str, set[str]] = defaultdict(set)
        self.outgoing: dict[str, set[str]] = defaultdict(set)

        self._build_connection_maps()

    def _build_connection_maps(self) -> None:
        """Build maps of incoming/outgoing connections."""
        for link in self.links:
            source_id = self._get_id(link.get("source"))
            target_id = self._get_id(link.get("target"))

            if source_id and target_id:
                self.outgoing[source_id].add(target_id)
                self.incoming[target_id].add(source_id)

    def _get_id(self, value: Any) -> str | None:
        """Extract ID from link source/target."""
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            return value.get("id")
        return None

    def detect_all(self) -> list[OrphanedResource]:
        """
        Detect all orphaned resources.

        Returns:
            List of OrphanedResource findings
        """
        orphans: list[OrphanedResource] = []

        for node in self.nodes:
            node_id = node.get("id")
            if not node_id:
                continue

            orphan = self._check_orphan(node)
            if orphan:
                orphans.append(orphan)

        # Sort by severity and cost
        orphans.sort(
            key=lambda o: (
                list(OrphanSeverity).index(o.severity),
                -o.estimated_monthly_cost,
            )
        )

        return orphans

    def _check_orphan(self, node: dict[str, Any]) -> OrphanedResource | None:
        """Check if a node is orphaned."""
        node_id = node.get("id")
        resource_type = node.get("type", "")

        # Skip summary nodes
        if node.get("is_summary"):
            return None

        # Check for completely isolated nodes
        if not self.incoming.get(node_id) and not self.outgoing.get(node_id):
            # Some resources are expected to be standalone
            if resource_type not in ("aws_vpc", "aws_s3_bucket"):
                return self._create_orphan(
                    node,
                    OrphanReason.NO_CONNECTIONS,
                    "Resource has no connections to other resources",
                )

        # Type-specific checks
        if resource_type in ATTACHMENT_RESOURCES:
            return self._check_attachment_orphan(node)

        if resource_type in CONTAINER_RESOURCES:
            return self._check_container_orphan(node)

        # Check for unused elastic IPs
        if resource_type == "aws_eip":
            return self._check_eip_orphan(node)

        return None

    def _check_attachment_orphan(self, node: dict[str, Any]) -> OrphanedResource | None:
        """Check if an attachment-type resource is orphaned."""
        node_id = node.get("id")
        resource_type = node.get("type", "")

        # Check for incoming connections (resources using this)
        if not self.incoming.get(node_id):
            message = ATTACHMENT_RESOURCES.get(
                resource_type, "Resource not referenced by any other resource"
            )
            return self._create_orphan(
                node,
                OrphanReason.NO_ATTACHMENTS,
                message,
            )

        return None

    def _check_container_orphan(self, node: dict[str, Any]) -> OrphanedResource | None:
        """Check if a container resource has no children."""
        node_id = node.get("id")
        resource_type = node.get("type", "")

        # For VPCs and subnets, check for resources inside them
        if resource_type in ("aws_vpc", "aws_subnet"):
            contained = self._count_contained_resources(node_id, resource_type)
            if contained == 0:
                message = CONTAINER_RESOURCES.get(
                    resource_type, "Container has no resources"
                )
                return self._create_orphan(
                    node,
                    OrphanReason.NO_RESOURCES,
                    message,
                    severity=OrphanSeverity.INFO,  # Empty containers are low concern
                )

        return None

    def _count_contained_resources(self, container_id: str, container_type: str) -> int:
        """Count resources contained in a VPC/Subnet."""
        count = 0
        for node in self.nodes:
            if node.get("id") == container_id:
                continue

            props = node.get("properties", {})

            if container_type == "aws_vpc":
                if props.get("vpc_id") == container_id:
                    count += 1
            elif container_type == "aws_subnet":
                if props.get("subnet_id") == container_id:
                    count += 1
                # Also check subnet_ids list
                subnet_ids = props.get("subnet_ids", [])
                if container_id in subnet_ids:
                    count += 1

        return count

    def _check_eip_orphan(self, node: dict[str, Any]) -> OrphanedResource | None:
        """Check if an Elastic IP is unused."""
        node_id = node.get("id")

        # EIPs should be attached to something
        if not self.incoming.get(node_id):
            return self._create_orphan(
                node,
                OrphanReason.NO_ATTACHMENTS,
                "Elastic IP not associated with any instance or NAT gateway",
                severity=OrphanSeverity.MEDIUM,  # Unused EIPs cost money
            )

        return None

    def _create_orphan(
        self,
        node: dict[str, Any],
        reason: OrphanReason,
        message: str,
        severity: OrphanSeverity | None = None,
    ) -> OrphanedResource:
        """Create an OrphanedResource from a node."""
        resource_type = node.get("type", "")

        if severity is None:
            severity = self._determine_severity(resource_type)

        cost = ORPHAN_COST_ESTIMATES.get(resource_type, 0.0)
        recommendation = self._get_recommendation(resource_type, reason)

        return OrphanedResource(
            resource_id=node.get("id", ""),
            resource_name=node.get("name", node.get("id", "")),
            resource_type=resource_type,
            reason=reason,
            severity=severity,
            estimated_monthly_cost=cost,
            message=message,
            recommendation=recommendation,
        )

    def _determine_severity(self, resource_type: str) -> OrphanSeverity:
        """Determine severity based on resource type and cost."""
        # High cost resources
        if resource_type in (
            "aws_db_instance",
            "aws_elasticache_cluster",
            "aws_nat_gateway",
            "aws_lb",
        ):
            return OrphanSeverity.HIGH

        # Medium cost
        if resource_type in ("aws_ebs_volume", "aws_eip"):
            return OrphanSeverity.MEDIUM

        # Low cost / informational
        if resource_type in ("aws_security_group", "aws_iam_role"):
            return OrphanSeverity.LOW

        return OrphanSeverity.INFO

    def _get_recommendation(self, resource_type: str, reason: OrphanReason) -> str:
        """Get recommendation for addressing the orphan."""
        recommendations = {
            ("aws_security_group", OrphanReason.NO_ATTACHMENTS): (
                "Consider removing this security group if no longer needed, "
                "or attach it to relevant resources."
            ),
            ("aws_ebs_volume", OrphanReason.NO_ATTACHMENTS): (
                "Attach this volume to an instance, or delete it if the data "
                "is no longer needed. Consider creating a snapshot first."
            ),
            ("aws_eip", OrphanReason.NO_ATTACHMENTS): (
                "Associate this EIP with an instance or NAT gateway, "
                "or release it to avoid charges."
            ),
            ("aws_lb", OrphanReason.NO_CONNECTIONS): (
                "Configure target groups and listeners, or delete the load balancer "
                "if no longer needed."
            ),
            ("aws_iam_role", OrphanReason.NO_ATTACHMENTS): (
                "Review if this role is needed. Unused IAM roles should be removed "
                "for security hygiene."
            ),
        }

        key = (resource_type, reason)
        if key in recommendations:
            return recommendations[key]

        if reason == OrphanReason.NO_CONNECTIONS:
            return "Review this resource to determine if it's still needed."

        return "Consider reviewing and removing unused resources."


def detect_orphans(
    nodes: list[dict[str, Any]],
    links: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Convenience function to detect orphaned resources.

    Args:
        nodes: List of resource nodes
        links: List of dependency links

    Returns:
        List of orphan findings as dictionaries
    """
    detector = OrphanDetector(nodes, links)
    orphans = detector.detect_all()
    return [o.to_dict() for o in orphans]


def enrich_nodes_with_orphan_status(
    nodes: list[dict[str, Any]],
    links: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Add orphan status to nodes.

    Args:
        nodes: List of resource nodes
        links: List of dependency links

    Returns:
        Nodes with is_orphan and orphan_info properties
    """
    detector = OrphanDetector(nodes, links)
    orphans = detector.detect_all()

    orphan_map = {o.resource_id: o for o in orphans}

    for node in nodes:
        node_id = node.get("id")
        if node_id and node_id in orphan_map:
            orphan = orphan_map[node_id]
            node["is_orphan"] = True
            node["orphan_info"] = orphan.to_dict()
        else:
            node["is_orphan"] = False

    return nodes


def calculate_orphan_costs(orphans: list[OrphanedResource]) -> dict[str, Any]:
    """
    Calculate total potential savings from orphaned resources.

    Args:
        orphans: List of orphaned resources

    Returns:
        Cost summary
    """
    total = sum(o.estimated_monthly_cost for o in orphans)
    by_type: dict[str, float] = defaultdict(float)
    by_severity: dict[str, int] = defaultdict(int)

    for orphan in orphans:
        by_type[orphan.resource_type] += orphan.estimated_monthly_cost
        by_severity[orphan.severity.value] += 1

    return {
        "total_monthly_savings": round(total, 2),
        "annual_savings": round(total * 12, 2),
        "orphan_count": len(orphans),
        "by_type": dict(sorted(by_type.items(), key=lambda x: -x[1])),
        "by_severity": dict(by_severity),
    }


def generate_orphan_visualization_js() -> str:
    """Generate JavaScript for orphan visualization."""
    return """
    let showOrphans = false;

    function toggleOrphanHighlight() {
        showOrphans = !showOrphans;
        updateOrphanVisualization();
    }

    function updateOrphanVisualization() {
        node.classed('orphaned-resource', d => showOrphans && d.is_orphan);

        if (showOrphans) {
            node.filter(d => d.is_orphan)
                .select('circle')
                .style('stroke', '#a855f7')
                .style('stroke-width', '3px')
                .style('stroke-dasharray', '5,3');
        } else {
            node.select('circle')
                .style('stroke', null)
                .style('stroke-width', null)
                .style('stroke-dasharray', null);
        }

        updateOrphanPanel();
    }

    function updateOrphanPanel() {
        let panel = d3.select('#orphanPanel');
        if (panel.empty()) {
            panel = d3.select('#graph')
                .append('div')
                .attr('id', 'orphanPanel')
                .attr('class', 'orphan-panel');
        }

        if (!showOrphans) {
            panel.style('display', 'none');
            return;
        }

        const orphans = graphData.nodes.filter(n => n.is_orphan);
        const totalCost = orphans.reduce((sum, n) =>
            sum + (n.orphan_info?.estimated_monthly_cost || 0), 0);

        panel.style('display', 'block')
            .html(`
                <h4>Orphaned Resources</h4>
                <div class="orphan-stats">
                    <div class="orphan-stat">
                        <span class="orphan-count">${orphans.length}</span>
                        <span class="orphan-label">Resources</span>
                    </div>
                    <div class="orphan-stat">
                        <span class="orphan-cost">$${totalCost.toFixed(2)}</span>
                        <span class="orphan-label">Est. Monthly</span>
                    </div>
                </div>
                <div class="orphan-list">
                    ${orphans.slice(0, 5).map(o => `
                        <div class="orphan-item">
                            <span class="orphan-name">${o.name}</span>
                            <span class="orphan-type">${o.type.replace('aws_', '')}</span>
                        </div>
                    `).join('')}
                    ${orphans.length > 5 ? `<div class="orphan-more">+${orphans.length - 5} more</div>` : ''}
                </div>
            `);
    }
    """


def generate_orphan_visualization_css() -> str:
    """Generate CSS for orphan visualization."""
    return """
    .orphan-panel {
        position: absolute;
        bottom: 80px;
        right: 20px;
        background: rgba(30, 41, 59, 0.95);
        border: 2px solid #a855f7;
        border-radius: 12px;
        padding: 16px;
        width: 240px;
        display: none;
        z-index: 100;
    }

    .orphan-panel h4 {
        margin: 0 0 12px 0;
        color: #a855f7;
        font-size: 14px;
    }

    .orphan-stats {
        display: flex;
        gap: 16px;
        margin-bottom: 12px;
    }

    .orphan-stat {
        text-align: center;
    }

    .orphan-count, .orphan-cost {
        font-size: 20px;
        font-weight: 700;
        display: block;
        color: #f1f5f9;
    }

    .orphan-cost {
        color: #a855f7;
    }

    .orphan-label {
        font-size: 10px;
        color: #64748b;
        text-transform: uppercase;
    }

    .orphan-list {
        border-top: 1px solid #334155;
        padding-top: 12px;
    }

    .orphan-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 4px 0;
        font-size: 11px;
    }

    .orphan-name {
        color: #f1f5f9;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        max-width: 140px;
    }

    .orphan-type {
        color: #64748b;
        font-size: 10px;
    }

    .orphan-more {
        color: #64748b;
        font-size: 11px;
        font-style: italic;
        padding-top: 4px;
    }

    .node.orphaned-resource circle {
        stroke: #a855f7;
        stroke-width: 3px;
        stroke-dasharray: 5,3;
    }
    """
