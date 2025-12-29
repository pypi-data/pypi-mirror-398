"""
Licensing Models for RepliMap.

Defines the Plan tiers, License structure, and feature configurations.
"""

from __future__ import annotations

import hashlib
import platform
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class LicenseValidationError(Exception):
    """Raised when license validation fails."""

    pass


class Plan(str, Enum):
    """Subscription plan tiers."""

    FREE = "free"
    SOLO = "solo"
    PRO = "pro"
    TEAM = "team"
    ENTERPRISE = "enterprise"

    def __str__(self) -> str:
        return self.value


class LicenseStatus(str, Enum):
    """License validation status."""

    VALID = "valid"
    EXPIRED = "expired"
    INVALID = "invalid"
    SUSPENDED = "suspended"
    MACHINE_MISMATCH = "machine_mismatch"


class Feature(str, Enum):
    """
    Available features that can be gated by plan.

    Gate Philosophy: Gate at OUTPUT, not at SCAN.
    - Scanning is always free (user experiences full value)
    - Gating happens when users try to export/download

    Core Principles:
    - SCAN: Unlimited resources, frequency limited only
    - GRAPH: Full viewing free, watermark on export
    - CLONE: Full generation, download is paid
    - AUDIT: Full scan, detailed findings are paid
    - DRIFT: Fully paid feature
    """

    # Core scanning (always available, frequency limited for FREE)
    SCAN = "scan"
    SCAN_UNLIMITED_FREQUENCY = "scan_unlimited_frequency"
    ASYNC_SCANNING = "async_scanning"

    # Multi-account support
    SINGLE_ACCOUNT = "single_account"
    MULTI_ACCOUNT = "multi_account"
    UNLIMITED_ACCOUNTS = "unlimited_accounts"

    # Clone features (gate at DOWNLOAD, not generation)
    CLONE_GENERATE = "clone_generate"  # Always available
    CLONE_FULL_PREVIEW = "clone_full_preview"  # See all lines
    CLONE_DOWNLOAD = "clone_download"  # Download to disk

    # Graph features (gate at EXPORT, not viewing)
    GRAPH_VIEW = "graph_view"  # Always available
    GRAPH_EXPORT_NO_WATERMARK = "graph_export_no_watermark"

    # Audit features (gate at DETAILS, not scan)
    AUDIT_SCAN = "audit_scan"  # Always available
    AUDIT_FULL_FINDINGS = "audit_full_findings"  # See all findings
    AUDIT_REPORT_EXPORT = "audit_report_export"  # Export HTML/PDF
    AUDIT_CI_MODE = "audit_ci_mode"  # --fail-on-high

    # Drift features (Pro+ only)
    DRIFT_DETECT = "drift_detect"
    DRIFT_WATCH = "drift_watch"
    DRIFT_ALERTS = "drift_alerts"

    # Advanced features
    COST_ESTIMATE = "cost_estimate"
    RIGHT_SIZER = "right_sizer"  # Auto-downsize for dev/staging
    DEPENDENCY_EXPLORER = "dependency_explorer"
    BLAST_RADIUS = "dependency_explorer"  # Backward compatibility alias

    # Transformation features
    BASIC_TRANSFORM = "basic_transform"
    ADVANCED_TRANSFORM = "advanced_transform"
    CUSTOM_TEMPLATES = "custom_templates"

    # Output format features
    TERRAFORM_OUTPUT = "terraform_output"
    CLOUDFORMATION_OUTPUT = "cloudformation_output"
    PULUMI_OUTPUT = "pulumi_output"
    CDK_OUTPUT = "cdk_output"

    # Team features
    WEB_DASHBOARD = "web_dashboard"
    COLLABORATION = "collaboration"
    SHARED_GRAPHS = "shared_graphs"

    # Enterprise features
    SSO = "sso"
    AUDIT_LOGS = "audit_logs"
    PRIORITY_SUPPORT = "priority_support"
    SLA_GUARANTEE = "sla_guarantee"
    CUSTOM_INTEGRATIONS = "custom_integrations"

    # Legacy compatibility (mapped to new features)
    BASIC_SCAN = "basic_scan"
    UNLIMITED_RESOURCES = "unlimited_resources"


@dataclass
class PlanFeatures:
    """
    Feature configuration for a plan tier.

    Gate Philosophy: Gate at OUTPUT, not at SCAN.
    - max_resources_per_scan: DEPRECATED - always None (unlimited)
    - Limits are on OUTPUT actions (download, export, view findings)
    """

    plan: Plan
    price_monthly: int  # USD
    price_annual_monthly: int  # USD, annual price per month

    # Scan limits (frequency only - NO resource count limit!)
    max_scans_per_month: int | None  # None = unlimited
    max_aws_accounts: int | None  # None = unlimited

    # Clone output limits
    clone_preview_lines: int | None  # Lines shown in preview, None = full
    clone_download_enabled: bool  # Can download generated code

    # Audit output limits
    audit_visible_findings: int | None  # Findings shown, None = all
    audit_report_export: bool  # Can export HTML/PDF report
    audit_ci_mode: bool  # Can use --fail-on-high

    # Graph export limits
    graph_export_watermark: bool  # Export has watermark

    # Advanced features
    drift_enabled: bool
    drift_watch_enabled: bool
    drift_alerts_enabled: bool
    cost_enabled: bool
    rightsizer_enabled: bool  # Right-Sizer for dev/staging optimization
    deps_enabled: bool  # Dependency explorer (formerly blast_enabled)

    # Team features
    max_team_members: int | None  # None = unlimited

    # Feature set
    features: set[Feature] = field(default_factory=set)

    # Legacy: kept for backwards compatibility, always None
    max_resources_per_scan: int | None = None  # DEPRECATED: always unlimited

    def has_feature(self, feature: Feature) -> bool:
        """Check if this plan includes a feature."""
        return feature in self.features

    def can_scan_resources(self, count: int) -> bool:
        """
        Check if the plan allows scanning this many resources.

        DEPRECATED: Always returns True. Resources are unlimited.
        Gating happens at output time, not scan time.
        """
        return True  # Always allow scanning

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "plan": str(self.plan),
            "price_monthly": self.price_monthly,
            "price_annual_monthly": self.price_annual_monthly,
            "max_scans_per_month": self.max_scans_per_month,
            "max_aws_accounts": self.max_aws_accounts,
            "clone_preview_lines": self.clone_preview_lines,
            "clone_download_enabled": self.clone_download_enabled,
            "audit_visible_findings": self.audit_visible_findings,
            "audit_report_export": self.audit_report_export,
            "audit_ci_mode": self.audit_ci_mode,
            "graph_export_watermark": self.graph_export_watermark,
            "drift_enabled": self.drift_enabled,
            "drift_watch_enabled": self.drift_watch_enabled,
            "drift_alerts_enabled": self.drift_alerts_enabled,
            "cost_enabled": self.cost_enabled,
            "rightsizer_enabled": self.rightsizer_enabled,
            "deps_enabled": self.deps_enabled,
            "blast_enabled": self.deps_enabled,  # Backward compatibility alias
            "max_team_members": self.max_team_members,
            "features": [str(f) for f in self.features],
            # Legacy field
            "max_resources_per_scan": None,
        }


# =============================================================================
# PLAN FEATURE CONFIGURATIONS
#
# Gate Strategy (核心原则):
# - SCAN: Unlimited resources, limit frequency (3/month for FREE)
# - GRAPH: Full visualization, watermark on export for FREE
# - CLONE: Full generation, block download for FREE
# - AUDIT: Full scan, limit visible findings for FREE
# - DRIFT: Disabled for FREE and SOLO
# =============================================================================

PLAN_FEATURES: dict[Plan, PlanFeatures] = {
    # =========================================================================
    # FREE TIER - Experience everything, pay to export
    # =========================================================================
    Plan.FREE: PlanFeatures(
        plan=Plan.FREE,
        price_monthly=0,
        price_annual_monthly=0,
        # Scan: UNLIMITED resources, limited frequency
        max_scans_per_month=3,
        max_aws_accounts=1,
        # Clone: Generate but NO download
        clone_preview_lines=100,  # Show first 100 lines
        clone_download_enabled=False,
        # Audit: Scan all, show limited findings
        audit_visible_findings=3,  # Show only 3 findings
        audit_report_export=False,
        audit_ci_mode=False,
        # Graph: View all, watermark on export
        graph_export_watermark=True,
        # Advanced: Disabled
        drift_enabled=False,
        drift_watch_enabled=False,
        drift_alerts_enabled=False,
        cost_enabled=False,
        rightsizer_enabled=False,  # Right-Sizer is Solo+
        deps_enabled=False,
        # Team: Solo only
        max_team_members=1,
        features={
            Feature.SCAN,
            Feature.GRAPH_VIEW,
            Feature.CLONE_GENERATE,
            Feature.AUDIT_SCAN,
            Feature.SINGLE_ACCOUNT,
            Feature.BASIC_TRANSFORM,
            Feature.TERRAFORM_OUTPUT,
            # Legacy compatibility
            Feature.BASIC_SCAN,
        },
    ),
    # =========================================================================
    # SOLO TIER ($29/mo) - For individual developers
    # =========================================================================
    Plan.SOLO: PlanFeatures(
        plan=Plan.SOLO,
        price_monthly=29,
        price_annual_monthly=17,
        max_scans_per_month=None,  # Unlimited
        max_aws_accounts=1,
        clone_preview_lines=None,  # Full preview
        clone_download_enabled=True,  # Can download!
        audit_visible_findings=None,  # All findings
        audit_report_export=True,  # Can export
        audit_ci_mode=False,  # CI mode is Pro
        graph_export_watermark=False,  # No watermark
        drift_enabled=False,  # Drift is Pro
        drift_watch_enabled=False,
        drift_alerts_enabled=False,
        cost_enabled=False,
        rightsizer_enabled=True,  # Right-Sizer enabled!
        deps_enabled=False,
        max_team_members=1,
        features={
            Feature.SCAN,
            Feature.SCAN_UNLIMITED_FREQUENCY,
            Feature.GRAPH_VIEW,
            Feature.GRAPH_EXPORT_NO_WATERMARK,
            Feature.CLONE_GENERATE,
            Feature.CLONE_DOWNLOAD,
            Feature.CLONE_FULL_PREVIEW,
            Feature.AUDIT_SCAN,
            Feature.AUDIT_FULL_FINDINGS,
            Feature.AUDIT_REPORT_EXPORT,
            Feature.RIGHT_SIZER,  # Right-Sizer!
            Feature.SINGLE_ACCOUNT,
            Feature.BASIC_TRANSFORM,
            Feature.ADVANCED_TRANSFORM,
            Feature.TERRAFORM_OUTPUT,
            Feature.ASYNC_SCANNING,
            # Legacy compatibility
            Feature.BASIC_SCAN,
            Feature.UNLIMITED_RESOURCES,
        },
    ),
    # =========================================================================
    # PRO TIER ($79/mo) - For teams managing multiple environments
    # =========================================================================
    Plan.PRO: PlanFeatures(
        plan=Plan.PRO,
        price_monthly=79,
        price_annual_monthly=50,
        max_scans_per_month=None,
        max_aws_accounts=3,  # dev/staging/prod
        clone_preview_lines=None,
        clone_download_enabled=True,
        audit_visible_findings=None,
        audit_report_export=True,
        audit_ci_mode=True,  # CI mode enabled!
        graph_export_watermark=False,
        drift_enabled=True,  # Drift enabled!
        drift_watch_enabled=False,  # Watch is Team
        drift_alerts_enabled=False,
        cost_enabled=True,  # Cost enabled!
        rightsizer_enabled=True,  # Right-Sizer enabled!
        deps_enabled=False,
        max_team_members=1,
        features={
            Feature.SCAN,
            Feature.SCAN_UNLIMITED_FREQUENCY,
            Feature.GRAPH_VIEW,
            Feature.GRAPH_EXPORT_NO_WATERMARK,
            Feature.CLONE_GENERATE,
            Feature.CLONE_DOWNLOAD,
            Feature.CLONE_FULL_PREVIEW,
            Feature.AUDIT_SCAN,
            Feature.AUDIT_FULL_FINDINGS,
            Feature.AUDIT_REPORT_EXPORT,
            Feature.AUDIT_CI_MODE,
            Feature.DRIFT_DETECT,
            Feature.COST_ESTIMATE,
            Feature.RIGHT_SIZER,  # Right-Sizer!
            Feature.MULTI_ACCOUNT,
            Feature.BASIC_TRANSFORM,
            Feature.ADVANCED_TRANSFORM,
            Feature.CUSTOM_TEMPLATES,
            Feature.TERRAFORM_OUTPUT,
            Feature.CLOUDFORMATION_OUTPUT,
            Feature.PULUMI_OUTPUT,
            Feature.WEB_DASHBOARD,
            Feature.ASYNC_SCANNING,
            # Legacy compatibility
            Feature.BASIC_SCAN,
            Feature.UNLIMITED_RESOURCES,
        },
    ),
    # =========================================================================
    # TEAM TIER ($149/mo) - For DevOps teams with advanced needs
    # =========================================================================
    Plan.TEAM: PlanFeatures(
        plan=Plan.TEAM,
        price_monthly=149,
        price_annual_monthly=100,
        max_scans_per_month=None,
        max_aws_accounts=10,
        clone_preview_lines=None,
        clone_download_enabled=True,
        audit_visible_findings=None,
        audit_report_export=True,
        audit_ci_mode=True,
        graph_export_watermark=False,
        drift_enabled=True,
        drift_watch_enabled=True,  # Watch mode!
        drift_alerts_enabled=True,  # Alerts!
        cost_enabled=True,
        rightsizer_enabled=True,  # Right-Sizer enabled!
        deps_enabled=True,  # Dependency explorer!
        max_team_members=5,  # 5 members included
        features={
            Feature.SCAN,
            Feature.SCAN_UNLIMITED_FREQUENCY,
            Feature.GRAPH_VIEW,
            Feature.GRAPH_EXPORT_NO_WATERMARK,
            Feature.CLONE_GENERATE,
            Feature.CLONE_DOWNLOAD,
            Feature.CLONE_FULL_PREVIEW,
            Feature.AUDIT_SCAN,
            Feature.AUDIT_FULL_FINDINGS,
            Feature.AUDIT_REPORT_EXPORT,
            Feature.AUDIT_CI_MODE,
            Feature.DRIFT_DETECT,
            Feature.DRIFT_WATCH,
            Feature.DRIFT_ALERTS,
            Feature.COST_ESTIMATE,
            Feature.RIGHT_SIZER,  # Right-Sizer!
            Feature.DEPENDENCY_EXPLORER,
            Feature.MULTI_ACCOUNT,
            Feature.BASIC_TRANSFORM,
            Feature.ADVANCED_TRANSFORM,
            Feature.CUSTOM_TEMPLATES,
            Feature.TERRAFORM_OUTPUT,
            Feature.CLOUDFORMATION_OUTPUT,
            Feature.PULUMI_OUTPUT,
            Feature.CDK_OUTPUT,
            Feature.WEB_DASHBOARD,
            Feature.COLLABORATION,
            Feature.SHARED_GRAPHS,
            Feature.ASYNC_SCANNING,
            # Legacy compatibility
            Feature.BASIC_SCAN,
            Feature.UNLIMITED_RESOURCES,
        },
    ),
    # =========================================================================
    # ENTERPRISE TIER ($399+/mo) - For organizations with compliance needs
    # =========================================================================
    Plan.ENTERPRISE: PlanFeatures(
        plan=Plan.ENTERPRISE,
        price_monthly=399,  # Starting price
        price_annual_monthly=333,
        max_scans_per_month=None,
        max_aws_accounts=None,  # Unlimited
        clone_preview_lines=None,
        clone_download_enabled=True,
        audit_visible_findings=None,
        audit_report_export=True,
        audit_ci_mode=True,
        graph_export_watermark=False,
        drift_enabled=True,
        drift_watch_enabled=True,
        drift_alerts_enabled=True,
        cost_enabled=True,
        rightsizer_enabled=True,  # Right-Sizer enabled!
        deps_enabled=True,
        max_team_members=None,  # Unlimited
        features=set(Feature),  # All features
    ),
}


def get_plan_features(plan: Plan) -> PlanFeatures:
    """Get the feature configuration for a plan."""
    return PLAN_FEATURES[plan]


def has_feature(plan: Plan, feature: Feature) -> bool:
    """Check if a plan has a specific feature."""
    return feature in PLAN_FEATURES[plan].features


def get_upgrade_target(current_plan: Plan, required_feature: Feature) -> Plan | None:
    """
    Find the cheapest plan that has the required feature.

    Args:
        current_plan: User's current plan
        required_feature: Feature they need

    Returns:
        The cheapest plan with the feature, or None if no upgrade available
    """
    plan_order = [Plan.FREE, Plan.SOLO, Plan.PRO, Plan.TEAM, Plan.ENTERPRISE]
    current_idx = plan_order.index(current_plan)

    for plan in plan_order[current_idx + 1 :]:
        if has_feature(plan, required_feature):
            return plan
    return None


def get_plan_for_limit(limit_type: str, required_value: int) -> Plan | None:
    """
    Find the cheapest plan that meets a limit requirement.

    Args:
        limit_type: Type of limit (e.g., "max_aws_accounts")
        required_value: Minimum value needed

    Returns:
        The cheapest plan meeting the requirement
    """
    plan_order = [Plan.FREE, Plan.SOLO, Plan.PRO, Plan.TEAM, Plan.ENTERPRISE]

    for plan in plan_order:
        features = PLAN_FEATURES[plan]
        limit_value = getattr(features, limit_type, None)

        if limit_value is None:  # Unlimited
            return plan
        if limit_value >= required_value:
            return plan

    return Plan.ENTERPRISE


@dataclass
class License:
    """License information for a user/organization."""

    license_key: str
    plan: Plan
    email: str
    organization: str | None = None
    issued_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime | None = None
    machine_fingerprint: str | None = None
    max_machines: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        """Check if the license has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(UTC) > self.expires_at

    @property
    def features(self) -> PlanFeatures:
        """Get the features for this license's plan."""
        return get_plan_features(self.plan)

    def has_feature(self, feature: Feature) -> bool:
        """Check if this license includes a feature."""
        return self.features.has_feature(feature)

    def validate_machine(self, fingerprint: str) -> bool:
        """Validate the machine fingerprint."""
        if self.machine_fingerprint is None:
            return True  # Not bound to machine
        return self.machine_fingerprint == fingerprint

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "license_key": self.license_key,
            "plan": str(self.plan),
            "email": self.email,
            "organization": self.organization,
            "issued_at": self.issued_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "machine_fingerprint": self.machine_fingerprint,
            "max_machines": self.max_machines,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> License:
        """Create License from dictionary."""
        return cls(
            license_key=data["license_key"],
            plan=Plan(data["plan"]),
            email=data["email"],
            organization=data.get("organization"),
            issued_at=datetime.fromisoformat(data["issued_at"]),
            expires_at=(
                datetime.fromisoformat(data["expires_at"])
                if data.get("expires_at")
                else None
            ),
            machine_fingerprint=data.get("machine_fingerprint"),
            max_machines=data.get("max_machines", 1),
            metadata=data.get("metadata", {}),
        )


def get_machine_fingerprint() -> str:
    """
    Generate a unique fingerprint for the current machine.

    Combines multiple system identifiers for a stable fingerprint.
    """
    components = [
        platform.node(),  # Hostname
        platform.machine(),  # Architecture
        platform.system(),  # OS
    ]

    # Try to get MAC address
    try:
        mac = uuid.getnode()
        # Check if MAC is stable (not random) by calling twice
        # uuid.getnode() returns a random value if no real MAC is available
        if mac == uuid.getnode():  # MAC is stable, use it
            components.append(str(mac))
    except OSError:
        # MAC address not available on this platform
        pass

    fingerprint_string = "|".join(components)
    return hashlib.sha256(fingerprint_string.encode()).hexdigest()[:32]
