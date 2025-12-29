"""
Link classification for different view modes.

Classifies links into:
- DEPENDENCY: Infrastructure dependencies (SG, Subnet, VPC)
- TRAFFIC: Network traffic flow (ALB -> TG -> EC2 -> RDS)
- BOTH: Links that represent both
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class LinkType(Enum):
    """Types of links in the infrastructure graph."""

    DEPENDENCY = "dependency"
    TRAFFIC = "traffic"
    BOTH = "both"


# Classification rules based on source/target resource types
LINK_CLASSIFICATION: dict[tuple[str, str], LinkType] = {
    # Traffic flow links - data flows between these
    ("aws_lb", "aws_lb_target_group"): LinkType.TRAFFIC,
    ("aws_lb_target_group", "aws_instance"): LinkType.TRAFFIC,
    ("aws_lb_target_group", "aws_autoscaling_group"): LinkType.TRAFFIC,
    ("aws_instance", "aws_db_instance"): LinkType.TRAFFIC,
    ("aws_instance", "aws_elasticache_cluster"): LinkType.TRAFFIC,
    ("aws_instance", "aws_sqs_queue"): LinkType.TRAFFIC,
    ("aws_lambda_function", "aws_sqs_queue"): LinkType.TRAFFIC,
    ("aws_lambda_function", "aws_dynamodb_table"): LinkType.TRAFFIC,
    ("aws_lambda_function", "aws_s3_bucket"): LinkType.TRAFFIC,
    ("aws_lambda_function", "aws_db_instance"): LinkType.TRAFFIC,
    ("aws_instance", "aws_s3_bucket"): LinkType.TRAFFIC,
    ("aws_ecs_service", "aws_lb_target_group"): LinkType.TRAFFIC,
    ("aws_ecs_task_definition", "aws_ecr_repository"): LinkType.TRAFFIC,
    # Pure dependency links - infrastructure relationships
    ("aws_instance", "aws_security_group"): LinkType.DEPENDENCY,
    ("aws_instance", "aws_subnet"): LinkType.DEPENDENCY,
    ("aws_instance", "aws_iam_role"): LinkType.DEPENDENCY,
    ("aws_instance", "aws_key_pair"): LinkType.DEPENDENCY,
    ("aws_db_instance", "aws_security_group"): LinkType.DEPENDENCY,
    ("aws_db_instance", "aws_db_subnet_group"): LinkType.DEPENDENCY,
    ("aws_db_instance", "aws_db_parameter_group"): LinkType.DEPENDENCY,
    ("aws_db_instance", "aws_kms_key"): LinkType.DEPENDENCY,
    ("aws_lb", "aws_security_group"): LinkType.DEPENDENCY,
    ("aws_lb", "aws_subnet"): LinkType.DEPENDENCY,
    ("aws_subnet", "aws_vpc"): LinkType.DEPENDENCY,
    ("aws_subnet", "aws_route_table"): LinkType.DEPENDENCY,
    ("aws_security_group", "aws_vpc"): LinkType.DEPENDENCY,
    ("aws_autoscaling_group", "aws_launch_template"): LinkType.DEPENDENCY,
    ("aws_autoscaling_group", "aws_subnet"): LinkType.DEPENDENCY,
    ("aws_lambda_function", "aws_iam_role"): LinkType.DEPENDENCY,
    ("aws_lambda_function", "aws_security_group"): LinkType.DEPENDENCY,
    ("aws_lambda_function", "aws_subnet"): LinkType.DEPENDENCY,
    ("aws_elasticache_cluster", "aws_security_group"): LinkType.DEPENDENCY,
    ("aws_elasticache_cluster", "aws_elasticache_subnet_group"): LinkType.DEPENDENCY,
    ("aws_nat_gateway", "aws_subnet"): LinkType.DEPENDENCY,
    ("aws_nat_gateway", "aws_eip"): LinkType.DEPENDENCY,
    ("aws_internet_gateway", "aws_vpc"): LinkType.DEPENDENCY,
    ("aws_route_table", "aws_vpc"): LinkType.DEPENDENCY,
    ("aws_route", "aws_route_table"): LinkType.DEPENDENCY,
    ("aws_vpc_endpoint", "aws_vpc"): LinkType.DEPENDENCY,
    ("aws_vpc_endpoint", "aws_security_group"): LinkType.DEPENDENCY,
    ("aws_ecs_service", "aws_ecs_cluster"): LinkType.DEPENDENCY,
    ("aws_ecs_service", "aws_ecs_task_definition"): LinkType.DEPENDENCY,
    # Both (security controls traffic)
    ("aws_security_group", "aws_security_group"): LinkType.BOTH,  # SG references
    ("aws_security_group_rule", "aws_security_group"): LinkType.BOTH,
}


def classify_link(source_type: str, target_type: str) -> LinkType:
    """
    Classify a link based on source and target types.

    Args:
        source_type: Resource type of the source node
        target_type: Resource type of the target node

    Returns:
        LinkType classification
    """
    key = (source_type, target_type)
    if key in LINK_CLASSIFICATION:
        return LINK_CLASSIFICATION[key]

    # Reverse lookup
    reverse_key = (target_type, source_type)
    if reverse_key in LINK_CLASSIFICATION:
        return LINK_CLASSIFICATION[reverse_key]

    # Default to dependency
    return LinkType.DEPENDENCY


def enrich_links_with_classification(
    links: list[dict[str, Any]], node_map: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    """
    Add link_type to all links.

    Args:
        links: List of link dictionaries
        node_map: Mapping of node_id -> node dict

    Returns:
        Links with link_type added
    """
    for link in links:
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

        source_type = node_map.get(source_id, {}).get("type", "")
        target_type = node_map.get(target_id, {}).get("type", "")

        link["link_type"] = classify_link(source_type, target_type).value

    return links


def get_traffic_flow_links(links: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Get only traffic flow links."""
    return [
        link
        for link in links
        if link.get("link_type") in (LinkType.TRAFFIC.value, LinkType.BOTH.value)
    ]


def get_dependency_links(links: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Get only dependency links."""
    return [
        link
        for link in links
        if link.get("link_type") in (LinkType.DEPENDENCY.value, LinkType.BOTH.value)
    ]


def generate_view_toggle_html() -> str:
    """Generate HTML for view mode toggle."""
    return """
    <div class="view-toggle">
        <span class="toggle-label">View:</span>
        <button class="toggle-btn active" data-view="all">All</button>
        <button class="toggle-btn" data-view="traffic">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M5 12h14M12 5l7 7-7 7"/>
            </svg>
            Traffic Flow
        </button>
        <button class="toggle-btn" data-view="dependency">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="3"/>
                <path d="M12 2v4M12 18v4M2 12h4M18 12h4"/>
            </svg>
            Dependencies
        </button>
    </div>
    """


def generate_view_toggle_js() -> str:
    """Generate JavaScript for view mode toggle."""
    return """
    let currentViewType = 'all';

    document.querySelectorAll('.toggle-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.toggle-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            currentViewType = this.dataset.view;
            filterByViewType();
        });
    });

    function filterByViewType() {
        link.style('display', l => {
            if (currentViewType === 'all') return null;
            return l.link_type === currentViewType || l.link_type === 'both' ? null : 'none';
        });

        // Update link styling based on type
        link.attr('stroke', l => {
            if (l.link_type === 'traffic') return '#22c55e';  // Green for traffic
            if (l.link_type === 'dependency') return '#6366f1';  // Purple for dependency
            return '#475569';  // Gray for both/unknown
        });

        link.attr('marker-end', l => {
            // Only traffic links get arrows
            return l.link_type === 'traffic' ? 'url(#arrowhead-traffic)' : null;
        });
    }
    """


def generate_view_toggle_css() -> str:
    """Generate CSS for view mode toggle."""
    return """
    .view-toggle {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 12px;
        padding-bottom: 12px;
        border-bottom: 1px solid #334155;
    }

    .toggle-label {
        font-size: 11px;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
    }

    .toggle-btn {
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 500;
        border: 1px solid #475569;
        background: #1e293b;
        color: #94a3b8;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 4px;
        transition: all 0.2s;
    }

    .toggle-btn:hover {
        background: #334155;
        color: #f1f5f9;
    }

    .toggle-btn.active {
        background: #6366f1;
        border-color: #6366f1;
        color: white;
    }

    .toggle-btn svg {
        width: 12px;
        height: 12px;
    }

    /* Link type colors */
    .link.traffic {
        stroke: #22c55e;
    }

    .link.dependency {
        stroke: #6366f1;
    }
    """
