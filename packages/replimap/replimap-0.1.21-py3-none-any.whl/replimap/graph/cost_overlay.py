"""
Cost overlay for infrastructure visualization.

Provides cost estimates for AWS resources based on:
- Instance types and sizes
- Storage volumes
- Data transfer estimates
- Regional pricing variations

Task 10: Heat map overlay showing cost per resource/container.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class CostTier(Enum):
    """Cost tier classification for visual representation."""

    LOW = "low"  # < $50/mo
    MEDIUM = "medium"  # $50-200/mo
    HIGH = "high"  # $200-500/mo
    CRITICAL = "critical"  # > $500/mo


@dataclass
class CostEstimate:
    """Cost estimate for a resource."""

    monthly: float
    tier: CostTier
    components: dict[str, float]
    confidence: str  # "high", "medium", "low"
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "monthly": self.monthly,
            "formatted": f"${self.monthly:,.2f}",
            "tier": self.tier.value,
            "components": self.components,
            "confidence": self.confidence,
            "notes": self.notes,
        }


# Base hourly rates for EC2 instance types (us-east-1 on-demand)
EC2_HOURLY_RATES: dict[str, float] = {
    # General purpose
    "t2.micro": 0.0116,
    "t2.small": 0.023,
    "t2.medium": 0.0464,
    "t2.large": 0.0928,
    "t2.xlarge": 0.1856,
    "t3.micro": 0.0104,
    "t3.small": 0.0208,
    "t3.medium": 0.0416,
    "t3.large": 0.0832,
    "t3.xlarge": 0.1664,
    "m5.large": 0.096,
    "m5.xlarge": 0.192,
    "m5.2xlarge": 0.384,
    "m5.4xlarge": 0.768,
    "m6i.large": 0.096,
    "m6i.xlarge": 0.192,
    "m6i.2xlarge": 0.384,
    # Compute optimized
    "c5.large": 0.085,
    "c5.xlarge": 0.17,
    "c5.2xlarge": 0.34,
    "c5.4xlarge": 0.68,
    "c6i.large": 0.085,
    "c6i.xlarge": 0.17,
    # Memory optimized
    "r5.large": 0.126,
    "r5.xlarge": 0.252,
    "r5.2xlarge": 0.504,
    "r5.4xlarge": 1.008,
    "r6i.large": 0.126,
    "r6i.xlarge": 0.252,
}

# RDS hourly rates (us-east-1, single-AZ)
RDS_HOURLY_RATES: dict[str, float] = {
    "db.t3.micro": 0.017,
    "db.t3.small": 0.034,
    "db.t3.medium": 0.068,
    "db.t3.large": 0.136,
    "db.m5.large": 0.171,
    "db.m5.xlarge": 0.342,
    "db.m5.2xlarge": 0.684,
    "db.m5.4xlarge": 1.368,
    "db.r5.large": 0.24,
    "db.r5.xlarge": 0.48,
    "db.r5.2xlarge": 0.96,
    "db.r6i.large": 0.24,
    "db.r6i.xlarge": 0.48,
}

# ElastiCache hourly rates
ELASTICACHE_HOURLY_RATES: dict[str, float] = {
    "cache.t3.micro": 0.017,
    "cache.t3.small": 0.034,
    "cache.t3.medium": 0.068,
    "cache.m5.large": 0.142,
    "cache.m5.xlarge": 0.284,
    "cache.r5.large": 0.19,
    "cache.r5.xlarge": 0.38,
}

# Storage costs per GB-month
STORAGE_COSTS: dict[str, float] = {
    "gp2": 0.10,
    "gp3": 0.08,
    "io1": 0.125,
    "io2": 0.125,
    "st1": 0.045,
    "sc1": 0.025,
    "standard": 0.05,
    "s3_standard": 0.023,
    "s3_ia": 0.0125,
    "s3_glacier": 0.004,
}

# Lambda costs
LAMBDA_COST_PER_GB_SECOND = 0.0000166667
LAMBDA_COST_PER_REQUEST = 0.0000002

# ALB/NLB monthly base cost
ALB_MONTHLY_BASE = 22.0
NLB_MONTHLY_BASE = 22.0


def get_tier(monthly_cost: float) -> CostTier:
    """Determine cost tier from monthly cost."""
    if monthly_cost < 50:
        return CostTier.LOW
    elif monthly_cost < 200:
        return CostTier.MEDIUM
    elif monthly_cost < 500:
        return CostTier.HIGH
    else:
        return CostTier.CRITICAL


class CostCalculator:
    """
    Calculate cost estimates for AWS resources.

    Uses conservative estimates based on on-demand pricing.
    Actual costs may vary based on reserved instances, savings plans, etc.
    """

    def __init__(self, region: str = "us-east-1") -> None:
        """Initialize with region for pricing variations."""
        self.region = region
        # Regional multipliers (rough estimates)
        self.regional_multipliers: dict[str, float] = {
            "us-east-1": 1.0,
            "us-east-2": 1.0,
            "us-west-1": 1.1,
            "us-west-2": 1.0,
            "eu-west-1": 1.1,
            "eu-central-1": 1.15,
            "ap-southeast-1": 1.15,
            "ap-northeast-1": 1.2,
        }
        self.multiplier = self.regional_multipliers.get(region, 1.0)

    def estimate_resource_cost(self, node: dict[str, Any]) -> CostEstimate | None:
        """
        Estimate monthly cost for a resource node.

        Args:
            node: Resource node dictionary with type and properties

        Returns:
            CostEstimate or None if cost cannot be estimated
        """
        resource_type = node.get("type", "")
        properties = node.get("properties", {})

        if resource_type == "aws_instance":
            return self._estimate_ec2(properties)
        elif resource_type == "aws_db_instance":
            return self._estimate_rds(properties)
        elif resource_type == "aws_elasticache_cluster":
            return self._estimate_elasticache(properties)
        elif resource_type == "aws_lambda_function":
            return self._estimate_lambda(properties)
        elif resource_type == "aws_lb":
            return self._estimate_lb(properties)
        elif resource_type == "aws_s3_bucket":
            return self._estimate_s3(properties)
        elif resource_type == "aws_ebs_volume":
            return self._estimate_ebs(properties)
        elif resource_type == "aws_nat_gateway":
            return self._estimate_nat_gateway(properties)

        return None

    def _estimate_ec2(self, props: dict[str, Any]) -> CostEstimate:
        """Estimate EC2 instance cost."""
        instance_type = props.get("instance_type", "t3.medium")
        hourly_rate = EC2_HOURLY_RATES.get(instance_type, 0.1)

        # Assume running 730 hours/month
        compute_cost = hourly_rate * 730 * self.multiplier

        # Estimate EBS storage (if root volume info available)
        storage_cost = 0.0
        root_volume_size = props.get("root_block_device", {}).get("volume_size", 30)
        volume_type = props.get("root_block_device", {}).get("volume_type", "gp3")
        storage_cost = root_volume_size * STORAGE_COSTS.get(volume_type, 0.08)

        total = compute_cost + storage_cost

        return CostEstimate(
            monthly=round(total, 2),
            tier=get_tier(total),
            components={
                "compute": round(compute_cost, 2),
                "storage": round(storage_cost, 2),
            },
            confidence="medium",
            notes=f"Based on {instance_type} on-demand pricing",
        )

    def _estimate_rds(self, props: dict[str, Any]) -> CostEstimate:
        """Estimate RDS instance cost."""
        instance_class = props.get("instance_class", "db.t3.medium")
        hourly_rate = RDS_HOURLY_RATES.get(instance_class, 0.068)

        compute_cost = hourly_rate * 730 * self.multiplier

        # Storage cost
        storage_gb = props.get("allocated_storage", 100)
        storage_type = props.get("storage_type", "gp3")
        storage_cost = storage_gb * STORAGE_COSTS.get(storage_type, 0.08)

        # Multi-AZ doubles the compute cost
        if props.get("multi_az"):
            compute_cost *= 2
            storage_cost *= 2

        total = compute_cost + storage_cost

        return CostEstimate(
            monthly=round(total, 2),
            tier=get_tier(total),
            components={
                "compute": round(compute_cost, 2),
                "storage": round(storage_cost, 2),
            },
            confidence="medium",
            notes=f"Based on {instance_class}"
            + (" Multi-AZ" if props.get("multi_az") else ""),
        )

    def _estimate_elasticache(self, props: dict[str, Any]) -> CostEstimate:
        """Estimate ElastiCache cost."""
        node_type = props.get("node_type", "cache.t3.medium")
        num_nodes = props.get("num_cache_nodes", 1)
        hourly_rate = ELASTICACHE_HOURLY_RATES.get(node_type, 0.068)

        compute_cost = hourly_rate * 730 * num_nodes * self.multiplier

        return CostEstimate(
            monthly=round(compute_cost, 2),
            tier=get_tier(compute_cost),
            components={"compute": round(compute_cost, 2)},
            confidence="medium",
            notes=f"{num_nodes}x {node_type}",
        )

    def _estimate_lambda(self, props: dict[str, Any]) -> CostEstimate:
        """Estimate Lambda function cost (based on typical usage)."""
        memory_mb = props.get("memory_size", 128)
        memory_gb = memory_mb / 1024

        # Estimate monthly invocations (this is highly variable)
        # Default to low estimate of 100k invocations/month, 100ms avg
        estimated_invocations = 100000
        avg_duration_ms = 100

        request_cost = estimated_invocations * LAMBDA_COST_PER_REQUEST
        compute_cost = (
            estimated_invocations
            * (avg_duration_ms / 1000)
            * memory_gb
            * LAMBDA_COST_PER_GB_SECOND
        )

        total = request_cost + compute_cost

        return CostEstimate(
            monthly=round(total, 2),
            tier=get_tier(total),
            components={
                "requests": round(request_cost, 2),
                "compute": round(compute_cost, 2),
            },
            confidence="low",
            notes=f"Estimate based on 100k invocations/month, {memory_mb}MB",
        )

    def _estimate_lb(self, props: dict[str, Any]) -> CostEstimate:
        """Estimate Load Balancer cost."""
        lb_type = props.get("load_balancer_type", "application")

        base_cost = ALB_MONTHLY_BASE if lb_type == "application" else NLB_MONTHLY_BASE

        # LCU costs vary greatly by traffic - use conservative estimate
        lcu_estimate = 10.0  # Low traffic estimate

        total = (base_cost + lcu_estimate) * self.multiplier

        return CostEstimate(
            monthly=round(total, 2),
            tier=get_tier(total),
            components={
                "base": round(base_cost * self.multiplier, 2),
                "lcu": round(lcu_estimate * self.multiplier, 2),
            },
            confidence="low",
            notes=f"{lb_type.upper()} with estimated low traffic",
        )

    def _estimate_s3(self, props: dict[str, Any]) -> CostEstimate:
        """Estimate S3 bucket cost."""
        # S3 costs are highly variable - provide low estimate
        # Assume 100GB standard storage
        storage_gb = 100
        storage_cost = storage_gb * STORAGE_COSTS["s3_standard"]

        return CostEstimate(
            monthly=round(storage_cost, 2),
            tier=get_tier(storage_cost),
            components={"storage": round(storage_cost, 2)},
            confidence="low",
            notes="Estimate based on 100GB standard storage",
        )

    def _estimate_ebs(self, props: dict[str, Any]) -> CostEstimate:
        """Estimate EBS volume cost."""
        volume_size = props.get("size", 100)
        volume_type = props.get("type", "gp3")

        storage_cost = (
            volume_size * STORAGE_COSTS.get(volume_type, 0.08) * self.multiplier
        )

        # IOPS costs for io1/io2
        iops_cost = 0.0
        if volume_type in ("io1", "io2"):
            iops = props.get("iops", 3000)
            iops_cost = iops * 0.065  # per IOPS-month

        total = storage_cost + iops_cost

        return CostEstimate(
            monthly=round(total, 2),
            tier=get_tier(total),
            components={
                "storage": round(storage_cost, 2),
                "iops": round(iops_cost, 2),
            },
            confidence="high",
            notes=f"{volume_size}GB {volume_type}",
        )

    def _estimate_nat_gateway(self, props: dict[str, Any]) -> CostEstimate:
        """Estimate NAT Gateway cost."""
        # Base hourly rate
        hourly_cost = 0.045 * 730 * self.multiplier

        # Data processing estimate (highly variable)
        # Assume 100GB/month processed
        data_cost = 100 * 0.045

        total = hourly_cost + data_cost

        return CostEstimate(
            monthly=round(total, 2),
            tier=get_tier(total),
            components={
                "hourly": round(hourly_cost, 2),
                "data_processing": round(data_cost, 2),
            },
            confidence="medium",
            notes="Based on 100GB/month data processing",
        )


def enrich_nodes_with_cost(
    nodes: list[dict[str, Any]], region: str = "us-east-1"
) -> list[dict[str, Any]]:
    """
    Add cost estimates to all nodes.

    Args:
        nodes: List of resource nodes
        region: AWS region for pricing

    Returns:
        Nodes with cost property added
    """
    calculator = CostCalculator(region)

    for node in nodes:
        cost = calculator.estimate_resource_cost(node)
        if cost:
            node["cost"] = cost.to_dict()

    return nodes


def calculate_container_cost(
    nodes: list[dict[str, Any]], container_id: str | None = None
) -> dict[str, Any]:
    """
    Calculate total cost for a container (VPC, Subnet, etc).

    Args:
        nodes: List of resource nodes with costs
        container_id: VPC/Subnet ID to filter by, or None for all

    Returns:
        Cost summary for the container
    """
    total = 0.0
    by_type: dict[str, float] = {}
    by_tier: dict[str, int] = {"low": 0, "medium": 0, "high": 0, "critical": 0}

    for node in nodes:
        # Filter by container if specified
        if container_id:
            node_vpc = node.get("properties", {}).get("vpc_id")
            if node_vpc != container_id:
                continue

        cost = node.get("cost", {})
        monthly = cost.get("monthly", 0)
        if monthly > 0:
            total += monthly
            resource_type = node.get("type", "unknown")
            by_type[resource_type] = by_type.get(resource_type, 0) + monthly

            tier = cost.get("tier", "low")
            by_tier[tier] = by_tier.get(tier, 0) + 1

    return {
        "total_monthly": round(total, 2),
        "formatted": f"${total:,.2f}/mo",
        "by_type": {
            k: round(v, 2) for k, v in sorted(by_type.items(), key=lambda x: -x[1])
        },
        "by_tier": by_tier,
        "tier": get_tier(total).value,
    }


def generate_cost_overlay_js() -> str:
    """Generate JavaScript for cost overlay visualization."""
    return """
    let showCostOverlay = false;

    function toggleCostOverlay() {
        showCostOverlay = !showCostOverlay;
        updateCostVisualization();
    }

    function updateCostVisualization() {
        if (!showCostOverlay) {
            node.select('circle')
                .style('fill', d => getNodeColor(d));
            return;
        }

        // Color nodes by cost tier
        const tierColors = {
            'low': '#22c55e',      // Green
            'medium': '#eab308',   // Yellow
            'high': '#f97316',     // Orange
            'critical': '#dc2626'  // Red
        };

        node.select('circle')
            .style('fill', d => {
                const tier = d.cost?.tier || 'low';
                return tierColors[tier] || tierColors.low;
            });

        // Update legend
        updateCostLegend();
    }

    function updateCostLegend() {
        let legend = d3.select('#costLegend');
        if (legend.empty()) {
            legend = d3.select('#graph')
                .append('div')
                .attr('id', 'costLegend')
                .attr('class', 'cost-legend');
        }

        if (!showCostOverlay) {
            legend.style('display', 'none');
            return;
        }

        legend.style('display', 'block')
            .html(`
                <h4>Monthly Cost</h4>
                <div class="legend-item"><span class="legend-color" style="background:#22c55e"></span> < $50</div>
                <div class="legend-item"><span class="legend-color" style="background:#eab308"></span> $50-200</div>
                <div class="legend-item"><span class="legend-color" style="background:#f97316"></span> $200-500</div>
                <div class="legend-item"><span class="legend-color" style="background:#dc2626"></span> > $500</div>
            `);
    }
    """


def generate_cost_overlay_css() -> str:
    """Generate CSS for cost overlay."""
    return """
    .cost-legend {
        position: absolute;
        top: 80px;
        right: 20px;
        background: rgba(30, 41, 59, 0.95);
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 12px;
        font-size: 12px;
    }

    .cost-legend h4 {
        margin: 0 0 8px 0;
        font-size: 11px;
        text-transform: uppercase;
        color: #64748b;
    }

    .legend-item {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 4px;
        color: #94a3b8;
    }

    .legend-color {
        width: 12px;
        height: 12px;
        border-radius: 3px;
    }

    .cost-breakdown {
        background: rgba(30, 41, 59, 0.8);
        border-radius: 6px;
        padding: 12px;
        margin-bottom: 12px;
    }

    .cost-breakdown h4 {
        margin: 0 0 8px 0;
        font-size: 11px;
        text-transform: uppercase;
        color: #64748b;
    }

    .cost-value {
        font-size: 24px;
        font-weight: 700;
        color: #f1f5f9;
    }

    .cost-value.tier-low { color: #22c55e; }
    .cost-value.tier-medium { color: #eab308; }
    .cost-value.tier-high { color: #f97316; }
    .cost-value.tier-critical { color: #dc2626; }
    """
