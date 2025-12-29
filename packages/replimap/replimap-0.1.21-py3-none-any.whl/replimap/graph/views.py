"""
Multi-level view system for infrastructure graphs.

Supports:
- Overview mode (VPC-level summary)
- Detail mode (resources within a VPC)
- Full mode (all resources)
- Drill-down navigation

This enables progressive disclosure - starting with a high-level
overview and drilling down into details as needed.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from replimap.graph.naming import get_type_plural_name


class ViewMode(str, Enum):
    """View mode for graph visualization."""

    OVERVIEW = "overview"  # VPC-level summary
    VPC_DETAIL = "vpc_detail"  # Resources within a VPC
    FULL = "full"  # All resources visible


@dataclass
class ViewState:
    """Current view state for navigation."""

    mode: ViewMode = ViewMode.OVERVIEW
    focus_vpc: str | None = None
    focus_subnet: str | None = None
    expanded_groups: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "mode": self.mode.value,
            "focus_vpc": self.focus_vpc,
            "focus_subnet": self.focus_subnet,
            "expanded_groups": self.expanded_groups,
        }


@dataclass
class VPCSummary:
    """Summary data for a VPC in overview mode."""

    id: str
    name: str
    resource_count: int
    subnet_count: int
    environments: list[str]
    resource_types: dict[str, int]  # type -> count
    connected_vpcs: list[str]

    def to_node_dict(self) -> dict[str, Any]:
        """Convert to a node dictionary for the graph."""
        return {
            "id": f"summary_{self.id}",
            "type": "vpc_summary",
            "name": self.name,
            "icon": "VPC",
            "color": "#10b981",
            "group": "network",
            "is_summary": True,
            "expandable": True,
            "properties": {
                "vpc_id": self.id,
                "resource_count": self.resource_count,
                "subnet_count": self.subnet_count,
                "environments": self.environments,
                "resource_types": self.resource_types,
            },
        }


@dataclass
class GlobalCategorySummary:
    """Summary data for a category of global resources."""

    category: str
    count: int
    resource_type: str
    color: str
    group: str

    def to_node_dict(self) -> dict[str, Any]:
        """Convert to a node dictionary for the graph."""
        return {
            "id": f"global_{self.category.lower().replace(' ', '_')}",
            "type": "global_summary",
            "name": f"{self.count} {self.category}",
            "icon": f"[{self.count}]",
            "color": self.color,
            "group": self.group,
            "is_summary": True,
            "expandable": True,
            "properties": {
                "count": self.count,
                "category": self.category,
                "resource_type": self.resource_type,
            },
        }


class ViewManager:
    """
    Manages view state and generates appropriate node/link subsets.

    Supports three view modes:
    - Overview: Shows VPCs as single nodes with resource counts
    - VPC Detail: Shows resources within a single VPC
    - Full: Shows all resources
    """

    # Global resource category mappings
    GLOBAL_CATEGORIES: dict[str, dict[str, str]] = {
        "aws_s3_bucket": {
            "category": "S3 Buckets",
            "color": "#ec4899",
            "group": "storage",
        },
        "aws_sqs_queue": {
            "category": "SQS Queues",
            "color": "#f472b6",
            "group": "messaging",
        },
        "aws_sns_topic": {
            "category": "SNS Topics",
            "color": "#fb7185",
            "group": "messaging",
        },
        "aws_iam_role": {
            "category": "IAM Roles",
            "color": "#eab308",
            "group": "security",
        },
        "aws_iam_policy": {
            "category": "IAM Policies",
            "color": "#facc15",
            "group": "security",
        },
        "aws_kms_key": {
            "category": "KMS Keys",
            "color": "#a855f7",
            "group": "security",
        },
        "aws_lambda_function": {
            "category": "Lambda Functions",
            "color": "#f97316",
            "group": "compute",
        },
    }

    def __init__(
        self,
        all_nodes: list[dict[str, Any]],
        all_links: list[dict[str, Any]],
    ) -> None:
        """
        Initialize the view manager.

        Args:
            all_nodes: Complete list of nodes
            all_links: Complete list of links
        """
        self.all_nodes = all_nodes
        self.all_links = all_links
        self.state = ViewState()

        # Pre-process: group nodes by VPC
        self.vpc_groups = self._group_by_vpc()
        self.global_resources = self._get_global_resources()
        self.vpc_connections = self._find_vpc_connections()

    def get_current_view(
        self,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """
        Get nodes and links for current view state.

        Returns:
            Tuple of (visible_nodes, visible_links)
        """
        if self.state.mode == ViewMode.OVERVIEW:
            return self._get_overview_view()
        elif self.state.mode == ViewMode.VPC_DETAIL:
            return self._get_vpc_detail_view(self.state.focus_vpc)
        else:
            return self.all_nodes, self.all_links

    def get_overview_data(
        self,
    ) -> dict[str, Any]:
        """
        Get data specifically for overview mode rendering.

        Returns:
            Dictionary with summary nodes and links for overview
        """
        nodes, links = self._get_overview_view()
        return {
            "nodes": nodes,
            "links": links,
            "vpc_summaries": [
                self._create_vpc_summary(vpc_id).to_node_dict()
                for vpc_id in self.vpc_groups.keys()
            ],
            "global_summaries": [
                summary.to_node_dict() for summary in self._create_global_summaries()
            ],
        }

    def _get_overview_view(
        self,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """
        Generate overview with VPCs as main nodes.

        Returns simplified graph with:
        - One node per VPC (with resource count)
        - One node per global service category
        - Links between VPCs (if resources communicate)
        """
        nodes: list[dict[str, Any]] = []
        links: list[dict[str, Any]] = []

        # Add VPC summary nodes
        for vpc_id in self.vpc_groups:
            summary = self._create_vpc_summary(vpc_id)
            nodes.append(summary.to_node_dict())

        # Add global resource category summaries
        for category_summary in self._create_global_summaries():
            nodes.append(category_summary.to_node_dict())

        # Add inter-VPC links
        for vpc_id, connected_vpcs in self.vpc_connections.items():
            for connected_vpc in connected_vpcs:
                links.append(
                    {
                        "source": f"summary_{vpc_id}",
                        "target": f"summary_{connected_vpc}",
                        "type": "vpc_connection",
                        "label": "",
                    }
                )

        return nodes, links

    def _get_vpc_detail_view(
        self,
        vpc_id: str | None,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Get detailed view of a single VPC."""
        if not vpc_id or vpc_id not in self.vpc_groups:
            return [], []

        vpc_data = self.vpc_groups[vpc_id]
        nodes = list(vpc_data["resources"])

        # Add the VPC node itself if it exists
        vpc_node = next(
            (n for n in self.all_nodes if n["id"] == vpc_id),
            None,
        )
        if vpc_node:
            nodes.append(vpc_node)

        # Filter links to only include resources in this VPC
        resource_ids = {r["id"] for r in nodes}
        links = [
            link
            for link in self.all_links
            if self._get_link_source(link) in resource_ids
            or self._get_link_target(link) in resource_ids
        ]

        return nodes, links

    def navigate_to(self, target_id: str) -> ViewState:
        """
        Navigate to a specific view.

        Args:
            target_id: ID of target to navigate to

        Returns:
            Updated ViewState
        """
        if target_id.startswith("summary_"):
            vpc_id = target_id.replace("summary_", "")
            self.state = ViewState(
                mode=ViewMode.VPC_DETAIL,
                focus_vpc=vpc_id,
            )
        elif target_id == "overview":
            self.state = ViewState(mode=ViewMode.OVERVIEW)
        elif target_id.startswith("global_"):
            # Stay in overview but could expand in future
            pass
        else:
            # Navigate to full view focused on this resource
            self.state = ViewState(mode=ViewMode.FULL)

        return self.state

    def _group_by_vpc(self) -> dict[str, dict[str, Any]]:
        """Group all resources by their VPC."""
        groups: dict[str, dict[str, Any]] = {}

        for node in self.all_nodes:
            vpc_id = node.get("properties", {}).get("vpc_id")

            if node.get("type") == "aws_vpc":
                vpc_id = node["id"]

            if not vpc_id:
                continue

            if vpc_id not in groups:
                groups[vpc_id] = {
                    "name": self._get_vpc_name(vpc_id),
                    "resources": [],
                    "subnets": set(),
                    "environments": set(),
                }

            if node.get("type") != "aws_vpc":
                groups[vpc_id]["resources"].append(node)

            subnet_id = node.get("properties", {}).get("subnet_id")
            if subnet_id:
                groups[vpc_id]["subnets"].add(subnet_id)

            env = node.get("environment")
            if env and env != "unknown":
                groups[vpc_id]["environments"].add(env)

        return groups

    def _get_global_resources(self) -> list[dict[str, Any]]:
        """Get resources not in any VPC."""
        return [
            n
            for n in self.all_nodes
            if not n.get("properties", {}).get("vpc_id") and n.get("type") != "aws_vpc"
        ]

    def _find_vpc_connections(self) -> dict[str, set[str]]:
        """Find connections between VPCs based on resource links."""
        connections: dict[str, set[str]] = defaultdict(set)

        # Build resource to VPC map
        resource_to_vpc: dict[str, str] = {}
        for node in self.all_nodes:
            vpc_id = node.get("properties", {}).get("vpc_id")
            if node.get("type") == "aws_vpc":
                vpc_id = node["id"]
            if vpc_id:
                resource_to_vpc[node["id"]] = vpc_id

        # Find cross-VPC links
        for link in self.all_links:
            source_id = self._get_link_source(link)
            target_id = self._get_link_target(link)

            source_vpc = resource_to_vpc.get(source_id)
            target_vpc = resource_to_vpc.get(target_id)

            if source_vpc and target_vpc and source_vpc != target_vpc:
                connections[source_vpc].add(target_vpc)

        return connections

    def _create_vpc_summary(self, vpc_id: str) -> VPCSummary:
        """Create summary data for a VPC."""
        vpc_data = self.vpc_groups.get(vpc_id, {})
        resources = vpc_data.get("resources", [])

        # Count resources by type
        type_counts: dict[str, int] = defaultdict(int)
        for r in resources:
            resource_type = r.get("type", "unknown")
            type_counts[resource_type] += 1

        return VPCSummary(
            id=vpc_id,
            name=vpc_data.get("name", vpc_id),
            resource_count=len(resources),
            subnet_count=len(vpc_data.get("subnets", set())),
            environments=sorted(vpc_data.get("environments", set())),
            resource_types=dict(type_counts),
            connected_vpcs=list(self.vpc_connections.get(vpc_id, set())),
        )

    def _create_global_summaries(self) -> list[GlobalCategorySummary]:
        """Create summary nodes for global resources by category."""
        by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)

        for resource in self.global_resources:
            resource_type = resource.get("type", "unknown")
            by_type[resource_type].append(resource)

        summaries: list[GlobalCategorySummary] = []

        for resource_type, resources in by_type.items():
            if resource_type in self.GLOBAL_CATEGORIES:
                cat_info = self.GLOBAL_CATEGORIES[resource_type]
                summaries.append(
                    GlobalCategorySummary(
                        category=cat_info["category"],
                        count=len(resources),
                        resource_type=resource_type,
                        color=cat_info["color"],
                        group=cat_info["group"],
                    )
                )
            else:
                # Generic category
                category_name = get_type_plural_name(resource_type, len(resources))
                summaries.append(
                    GlobalCategorySummary(
                        category=category_name,
                        count=len(resources),
                        resource_type=resource_type,
                        color="#6b7280",
                        group="other",
                    )
                )

        return summaries

    def _get_vpc_name(self, vpc_id: str) -> str:
        """Get VPC name from ID or tags."""
        # Find VPC node
        for node in self.all_nodes:
            if node["id"] == vpc_id and node.get("type") == "aws_vpc":
                return node.get("name", vpc_id)

        # Try to extract from ID patterns
        vpc_lower = vpc_id.lower()
        if "prod" in vpc_lower:
            return "prod VPC"
        if "public" in vpc_lower:
            return "public VPC"
        if "stage" in vpc_lower or "staging" in vpc_lower:
            return "stage VPC"
        if "test" in vpc_lower:
            return "test VPC"
        if "dev" in vpc_lower:
            return "dev VPC"

        return vpc_id

    def _get_link_source(self, link: dict[str, Any]) -> str:
        """Get source ID from link (handles D3 object format)."""
        source = link.get("source", "")
        if isinstance(source, dict):
            return source.get("id", "")
        return source

    def _get_link_target(self, link: dict[str, Any]) -> str:
        """Get target ID from link (handles D3 object format)."""
        target = link.get("target", "")
        if isinstance(target, dict):
            return target.get("id", "")
        return target


def generate_view_navigation_html() -> str:
    """Generate HTML for view navigation."""
    return """
    <div class="view-nav" id="viewNav" style="display: none;">
        <button class="back-btn" id="backToOverview">
            <span class="back-arrow">&#x25C0;</span> Back to Overview
        </button>
        <span class="current-view" id="currentViewLabel"></span>
    </div>
    """


def generate_view_navigation_js() -> str:
    """Generate JavaScript for view navigation."""
    return """
    // View management state
    let currentViewMode = 'overview';
    let focusVpcId = null;

    // Show overview mode (VPC summaries)
    function showOverview() {
        currentViewMode = 'overview';
        focusVpcId = null;

        document.getElementById('viewNav').style.display = 'none';

        // Show only summary nodes
        node.style('display', d => d.is_summary ? null : 'none');

        // Show only summary-to-summary links
        link.style('display', l => {
            const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
            const targetId = typeof l.target === 'object' ? l.target.id : l.target;
            const sourceNode = graphData.nodes.find(n => n.id === sourceId);
            const targetNode = graphData.nodes.find(n => n.id === targetId);
            return (sourceNode?.is_summary && targetNode?.is_summary) ? null : 'none';
        });

        // Hide container boxes
        if (typeof containerBoxes !== 'undefined') {
            containerBoxes.style('display', 'none');
        }

        // Fit view to visible content
        zoomToFit();
    }

    // Drill into a VPC
    function drillIntoVpc(vpcId) {
        currentViewMode = 'vpc_detail';
        focusVpcId = vpcId;

        // Show navigation bar
        const viewNav = document.getElementById('viewNav');
        viewNav.style.display = 'flex';

        // Update label
        const vpcNode = graphData.nodes.find(n =>
            n.id === vpcId || n.id === 'summary_' + vpcId
        );
        const vpcName = vpcNode?.name || vpcNode?.properties?.vpc_id || vpcId;
        document.getElementById('currentViewLabel').textContent = vpcName;

        // Show resources in this VPC
        node.style('display', d => {
            // Show if this is the VPC or a resource in the VPC
            if (d.id === vpcId) return null;
            if (d.properties?.vpc_id === vpcId) return null;
            // Hide summaries
            if (d.is_summary) return 'none';
            return 'none';
        });

        // Show relevant links
        link.style('display', l => {
            const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
            const targetId = typeof l.target === 'object' ? l.target.id : l.target;

            const sourceNode = graphData.nodes.find(n => n.id === sourceId);
            const targetNode = graphData.nodes.find(n => n.id === targetId);

            const sourceVpc = sourceNode?.properties?.vpc_id;
            const targetVpc = targetNode?.properties?.vpc_id;

            return (sourceVpc === vpcId || targetVpc === vpcId) ? null : 'none';
        });

        // Show container boxes for this VPC
        if (typeof containerBoxes !== 'undefined') {
            containerBoxes.style('display', d => {
                return (d.id === vpcId || d.parent_id === vpcId) ? null : 'none';
            });
        }

        // Fit view to visible content
        zoomToFit();
    }

    // Show full view (all resources)
    function showFullView() {
        currentViewMode = 'full';
        focusVpcId = null;

        document.getElementById('viewNav').style.display = 'flex';
        document.getElementById('currentViewLabel').textContent = 'All Resources';

        // Show all nodes except summaries
        node.style('display', d => d.is_summary ? 'none' : null);

        // Show all links
        link.style('display', null);

        // Show all container boxes
        if (typeof containerBoxes !== 'undefined') {
            containerBoxes.style('display', null);
        }

        zoomToFit();
    }

    // Fit view to visible content
    function zoomToFit() {
        const visibleNodes = graphData.nodes.filter(d => {
            const nodeEl = document.querySelector(`[data-node-id="${CSS.escape(d.id)}"]`);
            return nodeEl && getComputedStyle(nodeEl).display !== 'none';
        });

        if (visibleNodes.length === 0) return;

        const xs = visibleNodes.map(d => d.x);
        const ys = visibleNodes.map(d => d.y);
        const padding = 100;

        const minX = Math.min(...xs) - padding;
        const maxX = Math.max(...xs) + padding;
        const minY = Math.min(...ys) - padding;
        const maxY = Math.max(...ys) + padding;

        const width = maxX - minX;
        const height = maxY - minY;
        const scale = Math.min(
            window.innerWidth / width,
            window.innerHeight / height,
            2
        ) * 0.9;

        const tx = (window.innerWidth - width * scale) / 2 - minX * scale;
        const ty = (window.innerHeight - height * scale) / 2 - minY * scale;

        svg.transition()
            .duration(500)
            .call(zoom.transform, d3.zoomIdentity.translate(tx, ty).scale(scale));
    }

    // Handle summary node clicks for drill-down
    function handleSummaryClick(d) {
        if (d.is_summary && d.expandable) {
            if (d.type === 'vpc_summary') {
                drillIntoVpc(d.properties.vpc_id);
            } else if (d.type === 'global_summary') {
                // Could expand global categories in future
            }
        }
    }

    // Back to overview handler
    document.getElementById('backToOverview')?.addEventListener('click', showOverview);

    // Initialize in overview mode if data supports it
    function initializeView() {
        const hasSummaryNodes = graphData.nodes.some(n => n.is_summary);
        if (hasSummaryNodes) {
            showOverview();
        }
    }
    """


def generate_view_styles() -> str:
    """Generate CSS for view navigation."""
    return """
    /* View Navigation */
    .view-nav {
        position: absolute;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: rgba(30, 41, 59, 0.95);
        border-radius: 8px;
        padding: 8px 16px;
        display: flex;
        align-items: center;
        gap: 12px;
        border: 1px solid #334155;
        z-index: 100;
    }

    .back-btn {
        padding: 6px 12px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 500;
        border: 1px solid #6366f1;
        background: transparent;
        color: #6366f1;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 6px;
        transition: all 0.2s;
    }

    .back-btn:hover {
        background: #6366f1;
        color: white;
    }

    .back-arrow {
        font-size: 10px;
    }

    .current-view {
        font-size: 14px;
        font-weight: 600;
        color: #f1f5f9;
    }

    /* Summary nodes have different style */
    .node.summary circle {
        stroke-dasharray: 6,3;
        stroke-width: 3px;
    }

    .node.summary:hover circle {
        stroke-dasharray: none;
        cursor: pointer;
    }

    /* VPC summary specific */
    .node.vpc-summary circle {
        fill: rgba(16, 185, 129, 0.3);
        stroke: #10b981;
    }

    /* Global summary specific */
    .node.global-summary circle {
        fill: rgba(99, 102, 241, 0.3);
        stroke: #6366f1;
    }

    /* Inter-VPC links */
    .link.vpc-connection {
        stroke: #6366f1;
        stroke-width: 3px;
        stroke-dasharray: 8,4;
        stroke-opacity: 0.8;
    }

    /* Quick insights panel */
    .insights-panel {
        position: absolute;
        bottom: 80px;
        left: 20px;
        background: rgba(30, 41, 59, 0.95);
        border-radius: 12px;
        padding: 12px 16px;
        max-width: 280px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
        border: 1px solid #334155;
        z-index: 100;
    }

    .insights-panel h4 {
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        color: #64748b;
        margin-bottom: 8px;
    }

    .insight-item {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 12px;
        padding: 4px 0;
        color: #e2e8f0;
    }

    .insight-icon {
        width: 16px;
        text-align: center;
    }
    """
