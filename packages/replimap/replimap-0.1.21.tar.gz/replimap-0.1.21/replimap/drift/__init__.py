"""Drift detection module for RepliMap."""

from replimap.drift.engine import DriftEngine
from replimap.drift.models import (
    AttributeDiff,
    DriftReport,
    DriftSeverity,
    DriftType,
    ResourceDrift,
)
from replimap.drift.plan_engine import (
    PlanBasedDriftEngine,
    PlanChange,
    PlanDriftReporter,
    PlanParser,
    PlanResult,
)
from replimap.drift.reporter import DriftReporter
from replimap.drift.state_parser import TerraformStateParser, TFResource, TFState

__all__ = [
    # Legacy engine (deprecated, uses COMPARABLE_ATTRIBUTES)
    "DriftEngine",
    # New plan-based engine (recommended)
    "PlanBasedDriftEngine",
    "PlanParser",
    "PlanChange",
    "PlanResult",
    "PlanDriftReporter",
    # Original reporter (with to_console, to_json, to_html)
    "DriftReporter",
    # Models
    "DriftType",
    "DriftSeverity",
    "AttributeDiff",
    "ResourceDrift",
    "DriftReport",
    # State parsing
    "TerraformStateParser",
    "TFResource",
    "TFState",
]
