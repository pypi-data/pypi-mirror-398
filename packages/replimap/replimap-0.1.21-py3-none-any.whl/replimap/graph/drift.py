"""
Drift detection and visualization for infrastructure graphs.

Detects and visualizes resources that have drifted from their
Terraform-defined state. Drift can occur when:
- Resources are modified outside of Terraform
- State file is out of sync with actual infrastructure
- Manual changes were made via console or CLI

Task 13: Drift visualization.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DriftStatus(Enum):
    """Status of resource drift."""

    IN_SYNC = "in_sync"  # No drift detected
    DRIFTED = "drifted"  # Resource attributes changed
    DELETED = "deleted"  # Resource deleted outside TF
    ORPHANED = "orphaned"  # In state but not in config
    NEW = "new"  # In config but not yet applied


class DriftSeverity(Enum):
    """Severity of detected drift."""

    LOW = "low"  # Cosmetic changes (tags, descriptions)
    MEDIUM = "medium"  # Configuration changes (settings, parameters)
    HIGH = "high"  # Security-related changes
    CRITICAL = "critical"  # Destructive changes


# Attributes that indicate security-relevant drift
SECURITY_ATTRIBUTES = {
    "ingress",
    "egress",
    "security_groups",
    "iam_role",
    "iam_policy",
    "kms_key_id",
    "encryption",
    "public",
    "publicly_accessible",
    "acl",
}

# Attributes that are cosmetic only
COSMETIC_ATTRIBUTES = {
    "tags",
    "description",
    "name_prefix",
}


@dataclass
class DriftedAttribute:
    """A single drifted attribute."""

    attribute: str
    expected: Any
    actual: Any
    severity: DriftSeverity

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "attribute": self.attribute,
            "expected": str(self.expected)[:100],  # Truncate long values
            "actual": str(self.actual)[:100],
            "severity": self.severity.value,
        }


@dataclass
class DriftResult:
    """Result of drift detection for a resource."""

    resource_id: str
    resource_name: str
    resource_type: str
    status: DriftStatus
    drifted_attributes: list[DriftedAttribute] = field(default_factory=list)
    overall_severity: DriftSeverity = DriftSeverity.LOW
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "resource_id": self.resource_id,
            "resource_name": self.resource_name,
            "resource_type": self.resource_type,
            "status": self.status.value,
            "drifted_attributes": [a.to_dict() for a in self.drifted_attributes],
            "overall_severity": self.overall_severity.value,
            "drift_count": len(self.drifted_attributes),
            "summary": self.summary,
        }


class DriftDetector:
    """
    Detect drift between Terraform state and actual resources.

    Compares expected (from Terraform state) vs actual (from API/plan)
    to identify configuration drift.
    """

    def __init__(
        self,
        expected_state: dict[str, dict[str, Any]],
        actual_state: dict[str, dict[str, Any]],
    ) -> None:
        """
        Initialize drift detector.

        Args:
            expected_state: Dictionary mapping resource_id -> expected attributes
            actual_state: Dictionary mapping resource_id -> actual attributes
        """
        self.expected_state = expected_state
        self.actual_state = actual_state

    def detect_all(self) -> list[DriftResult]:
        """
        Detect drift for all resources.

        Returns:
            List of DriftResult for resources with drift
        """
        results: list[DriftResult] = []

        # Check expected resources for drift or deletion
        for resource_id, expected in self.expected_state.items():
            actual = self.actual_state.get(resource_id)

            if actual is None:
                # Resource deleted outside Terraform
                result = DriftResult(
                    resource_id=resource_id,
                    resource_name=expected.get("name", resource_id),
                    resource_type=expected.get("type", "unknown"),
                    status=DriftStatus.DELETED,
                    overall_severity=DriftSeverity.CRITICAL,
                    summary="Resource was deleted outside of Terraform",
                )
                results.append(result)
            else:
                # Check for attribute drift
                drifted = self._compare_attributes(expected, actual)
                if drifted:
                    severity = self._calculate_severity(drifted)
                    result = DriftResult(
                        resource_id=resource_id,
                        resource_name=expected.get("name", resource_id),
                        resource_type=expected.get("type", "unknown"),
                        status=DriftStatus.DRIFTED,
                        drifted_attributes=drifted,
                        overall_severity=severity,
                        summary=self._generate_summary(drifted),
                    )
                    results.append(result)

        # Check for orphaned resources (in actual but not expected)
        for resource_id, actual in self.actual_state.items():
            if resource_id not in self.expected_state:
                result = DriftResult(
                    resource_id=resource_id,
                    resource_name=actual.get("name", resource_id),
                    resource_type=actual.get("type", "unknown"),
                    status=DriftStatus.ORPHANED,
                    overall_severity=DriftSeverity.MEDIUM,
                    summary="Resource exists but is not in Terraform state",
                )
                results.append(result)

        return results

    def _compare_attributes(
        self, expected: dict[str, Any], actual: dict[str, Any]
    ) -> list[DriftedAttribute]:
        """Compare attributes and return list of drifted ones."""
        drifted: list[DriftedAttribute] = []

        # Compare all expected attributes
        for key, expected_value in expected.items():
            if key in ("id", "arn", "name", "type"):
                continue  # Skip identity fields

            actual_value = actual.get(key)

            if not self._values_equal(expected_value, actual_value):
                severity = self._attribute_severity(key)
                drifted.append(
                    DriftedAttribute(
                        attribute=key,
                        expected=expected_value,
                        actual=actual_value,
                        severity=severity,
                    )
                )

        return drifted

    def _values_equal(self, expected: Any, actual: Any) -> bool:
        """Compare two values for equality, handling None and type differences."""
        if expected is None and actual is None:
            return True
        if expected is None or actual is None:
            return False

        # Handle dict comparison
        if isinstance(expected, dict) and isinstance(actual, dict):
            if set(expected.keys()) != set(actual.keys()):
                return False
            return all(
                self._values_equal(expected[k], actual[k]) for k in expected.keys()
            )

        # Handle list comparison (order-insensitive for some cases)
        if isinstance(expected, list) and isinstance(actual, list):
            if len(expected) != len(actual):
                return False
            # Sort and compare for simple types
            try:
                return sorted(expected) == sorted(actual)
            except TypeError:
                # Fall back to order-sensitive comparison
                return expected == actual

        return expected == actual

    def _attribute_severity(self, attribute: str) -> DriftSeverity:
        """Determine severity based on attribute name."""
        attr_lower = attribute.lower()

        # Check for security-related
        for sec_attr in SECURITY_ATTRIBUTES:
            if sec_attr in attr_lower:
                return DriftSeverity.HIGH

        # Check for cosmetic
        for cos_attr in COSMETIC_ATTRIBUTES:
            if cos_attr in attr_lower:
                return DriftSeverity.LOW

        return DriftSeverity.MEDIUM

    def _calculate_severity(self, drifted: list[DriftedAttribute]) -> DriftSeverity:
        """Calculate overall severity from drifted attributes."""
        if not drifted:
            return DriftSeverity.LOW

        severities = [d.severity for d in drifted]

        if DriftSeverity.CRITICAL in severities:
            return DriftSeverity.CRITICAL
        if DriftSeverity.HIGH in severities:
            return DriftSeverity.HIGH
        if DriftSeverity.MEDIUM in severities:
            return DriftSeverity.MEDIUM

        return DriftSeverity.LOW

    def _generate_summary(self, drifted: list[DriftedAttribute]) -> str:
        """Generate human-readable summary of drift."""
        if not drifted:
            return "No drift detected"

        count = len(drifted)
        high_count = sum(
            1
            for d in drifted
            if d.severity in (DriftSeverity.HIGH, DriftSeverity.CRITICAL)
        )

        if high_count > 0:
            return f"{count} attribute(s) drifted, {high_count} security-related"

        return f"{count} attribute(s) drifted"


def detect_drift_from_plan(plan_changes: list[dict[str, Any]]) -> list[DriftResult]:
    """
    Detect drift from Terraform plan output.

    Parses plan changes to identify resources with drift.

    Args:
        plan_changes: List of change objects from terraform plan

    Returns:
        List of DriftResult
    """
    results: list[DriftResult] = []

    for change in plan_changes:
        if change.get("action") == "no-op":
            continue

        resource_id = change.get("resource_id", change.get("address", ""))
        resource_type = change.get("type", "unknown")
        resource_name = change.get("name", resource_id)

        # Parse change details
        before = change.get("before", {}) or {}
        after = change.get("after", {}) or {}

        if change.get("action") == "delete":
            result = DriftResult(
                resource_id=resource_id,
                resource_name=resource_name,
                resource_type=resource_type,
                status=DriftStatus.DELETED,
                overall_severity=DriftSeverity.CRITICAL,
                summary="Resource will be deleted",
            )
        elif change.get("action") == "create":
            result = DriftResult(
                resource_id=resource_id,
                resource_name=resource_name,
                resource_type=resource_type,
                status=DriftStatus.NEW,
                overall_severity=DriftSeverity.LOW,
                summary="New resource will be created",
            )
        else:
            # Update - find changed attributes
            drifted: list[DriftedAttribute] = []
            changed_attrs = change.get("changed_attributes", [])

            for attr in changed_attrs:
                before_val = before.get(attr)
                after_val = after.get(attr)

                if before_val != after_val:
                    # Determine if this is drift (before != expected) or planned change
                    severity = DriftSeverity.MEDIUM
                    for sec_attr in SECURITY_ATTRIBUTES:
                        if sec_attr in attr.lower():
                            severity = DriftSeverity.HIGH
                            break

                    drifted.append(
                        DriftedAttribute(
                            attribute=attr,
                            expected=before_val,
                            actual=after_val,
                            severity=severity,
                        )
                    )

            overall = DriftSeverity.LOW
            if any(d.severity == DriftSeverity.HIGH for d in drifted):
                overall = DriftSeverity.HIGH
            elif drifted:
                overall = DriftSeverity.MEDIUM

            result = DriftResult(
                resource_id=resource_id,
                resource_name=resource_name,
                resource_type=resource_type,
                status=DriftStatus.DRIFTED,
                drifted_attributes=drifted,
                overall_severity=overall,
                summary=f"{len(drifted)} attribute(s) will change",
            )

        results.append(result)

    return results


def enrich_nodes_with_drift(
    nodes: list[dict[str, Any]],
    drift_results: list[DriftResult],
) -> list[dict[str, Any]]:
    """
    Add drift information to nodes.

    Args:
        nodes: List of resource nodes
        drift_results: List of drift detection results

    Returns:
        Nodes with drift property added
    """
    drift_map = {r.resource_id: r for r in drift_results}

    for node in nodes:
        node_id = node.get("id")
        if node_id and node_id in drift_map:
            result = drift_map[node_id]
            node["drift"] = result.to_dict()
        else:
            node["drift"] = {
                "status": DriftStatus.IN_SYNC.value,
                "drift_count": 0,
            }

    return nodes


def generate_drift_visualization_js() -> str:
    """Generate JavaScript for drift visualization."""
    return """
    let showDriftHighlight = false;

    function toggleDriftHighlight() {
        showDriftHighlight = !showDriftHighlight;
        updateDriftVisualization();
    }

    function updateDriftVisualization() {
        const driftColors = {
            'in_sync': null,  // Use default color
            'drifted': '#f97316',  // Orange
            'deleted': '#dc2626',  // Red
            'orphaned': '#a855f7', // Purple
            'new': '#22c55e'       // Green
        };

        node.select('circle')
            .style('stroke', d => {
                if (!showDriftHighlight) return null;
                const status = d.drift?.status || 'in_sync';
                return driftColors[status];
            })
            .style('stroke-width', d => {
                if (!showDriftHighlight) return null;
                const status = d.drift?.status || 'in_sync';
                return status !== 'in_sync' ? '3px' : null;
            })
            .style('stroke-dasharray', d => {
                if (!showDriftHighlight) return null;
                const status = d.drift?.status || 'in_sync';
                return status === 'drifted' ? '4,2' : null;
            });

        // Add drift badges
        if (showDriftHighlight) {
            node.each(function(d) {
                const status = d.drift?.status || 'in_sync';
                if (status !== 'in_sync') {
                    const g = d3.select(this);
                    if (g.select('.drift-badge').empty()) {
                        g.append('circle')
                            .attr('class', 'drift-badge')
                            .attr('r', 6)
                            .attr('cx', 12)
                            .attr('cy', -12)
                            .attr('fill', driftColors[status]);

                        if (d.drift?.drift_count > 0) {
                            g.append('text')
                                .attr('class', 'drift-count')
                                .attr('x', 12)
                                .attr('y', -9)
                                .attr('text-anchor', 'middle')
                                .attr('fill', 'white')
                                .attr('font-size', '8px')
                                .text(d.drift.drift_count);
                        }
                    }
                }
            });
        } else {
            node.selectAll('.drift-badge, .drift-count').remove();
        }

        updateDriftLegend();
    }

    function updateDriftLegend() {
        let legend = d3.select('#driftLegend');
        if (legend.empty()) {
            legend = d3.select('#graph')
                .append('div')
                .attr('id', 'driftLegend')
                .attr('class', 'drift-legend');
        }

        if (!showDriftHighlight) {
            legend.style('display', 'none');
            return;
        }

        legend.style('display', 'block')
            .html(`
                <h4>Drift Status</h4>
                <div class="legend-item"><span class="legend-color" style="background:#f97316"></span> Drifted</div>
                <div class="legend-item"><span class="legend-color" style="background:#dc2626"></span> Deleted</div>
                <div class="legend-item"><span class="legend-color" style="background:#a855f7"></span> Orphaned</div>
                <div class="legend-item"><span class="legend-color" style="background:#22c55e"></span> New</div>
            `);
    }
    """


def generate_drift_visualization_css() -> str:
    """Generate CSS for drift visualization."""
    return """
    .drift-legend {
        position: absolute;
        top: 140px;
        right: 20px;
        background: rgba(30, 41, 59, 0.95);
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 12px;
        font-size: 12px;
    }

    .drift-legend h4 {
        margin: 0 0 8px 0;
        font-size: 11px;
        text-transform: uppercase;
        color: #64748b;
    }

    .node.drifted circle {
        stroke: #f97316;
        stroke-width: 3px;
        stroke-dasharray: 4,2;
    }

    .node.deleted circle {
        stroke: #dc2626;
        stroke-width: 3px;
    }

    .node.orphaned circle {
        stroke: #a855f7;
        stroke-width: 3px;
    }

    .node.new circle {
        stroke: #22c55e;
        stroke-width: 3px;
    }

    .drift-details {
        background: rgba(249, 115, 22, 0.1);
        border-left: 3px solid #f97316;
        padding: 8px 12px;
        margin-top: 12px;
        border-radius: 4px;
    }

    .drift-details h5 {
        margin: 0 0 8px 0;
        font-size: 11px;
        color: #f97316;
        text-transform: uppercase;
    }

    .drift-attr {
        font-size: 11px;
        margin-bottom: 4px;
        color: #94a3b8;
    }

    .drift-attr .attr-name {
        color: #f1f5f9;
        font-weight: 500;
    }
    """
