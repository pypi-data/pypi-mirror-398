"""
Feature Gating for RepliMap.

Provides decorators and utilities for gating features based on plan tier.

Gate Philosophy: Gate at OUTPUT, not at SCAN.
- Users experience full value first (unlimited scanning)
- Gating happens at export/download time

Core Principles:
- SCAN: Unlimited resources, frequency limited only
- GRAPH: Full viewing free, watermark on export
- CLONE: Full generation, download is paid
- AUDIT: Full scan, detailed findings are paid
- DRIFT: Fully paid feature
"""

from __future__ import annotations

import functools
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, ParamSpec, TypeVar

from replimap.licensing.models import Feature, Plan, get_plan_features

logger = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")


class FeatureNotAvailableError(Exception):
    """Raised when a feature is not available in the current plan."""

    def __init__(
        self,
        feature: Feature | str,
        current_plan: Plan,
        required_plan: Plan | None = None,
    ) -> None:
        self.feature = feature
        self.current_plan = current_plan
        self.required_plan = required_plan

        message = f"Feature '{feature}' is not available in {current_plan} plan"
        if required_plan:
            message += f". Upgrade to {required_plan} or higher to unlock this feature."

        super().__init__(message)


class ResourceLimitExceededError(Exception):
    """Raised when resource limits are exceeded."""

    def __init__(
        self,
        limit_type: str,
        current: int,
        maximum: int,
        current_plan: Plan,
    ) -> None:
        self.limit_type = limit_type
        self.current = current
        self.maximum = maximum
        self.current_plan = current_plan

        message = (
            f"{limit_type} limit exceeded: {current}/{maximum} "
            f"(current plan: {current_plan})"
        )
        super().__init__(message)


def feature_gate(
    feature: Feature,
    fallback: R | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator to gate a function behind a feature flag.

    Args:
        feature: The feature required to use this function
        fallback: Optional fallback value to return if feature is unavailable

    Returns:
        Decorated function that checks feature availability

    Example:
        @feature_gate(Feature.ASYNC_SCANNING)
        async def run_async_scan():
            ...
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            from replimap.licensing.manager import get_license_manager

            manager = get_license_manager()
            if not manager.current_features.has_feature(feature):
                if fallback is not None:
                    logger.debug(f"Feature {feature} not available, using fallback")
                    return fallback
                raise FeatureNotAvailableError(
                    feature=feature,
                    current_plan=manager.current_plan,
                    required_plan=_get_minimum_plan_for_feature(feature),
                )
            return func(*args, **kwargs)

        return wrapper

    return decorator


def require_plan(
    minimum_plan: Plan,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator to require a minimum plan tier.

    Args:
        minimum_plan: The minimum plan required

    Returns:
        Decorated function that checks plan tier

    Example:
        @require_plan(Plan.PRO)
        def generate_custom_template():
            ...
    """
    plan_order = [Plan.FREE, Plan.SOLO, Plan.PRO, Plan.TEAM, Plan.ENTERPRISE]

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            from replimap.licensing.manager import get_license_manager

            manager = get_license_manager()
            current_plan = manager.current_plan

            current_index = plan_order.index(current_plan)
            required_index = plan_order.index(minimum_plan)

            if current_index < required_index:
                raise FeatureNotAvailableError(
                    feature=func.__name__,
                    current_plan=current_plan,
                    required_plan=minimum_plan,
                )

            return func(*args, **kwargs)

        return wrapper

    return decorator


def check_resource_limit(
    resource_count: int,
    limit_type: str = "resources_per_scan",
) -> None:
    """
    Check if resource count is within plan limits.

    Args:
        resource_count: Number of resources to check
        limit_type: Type of limit to check

    Raises:
        ResourceLimitExceededError: If limit is exceeded
    """
    from replimap.licensing.manager import get_license_manager

    manager = get_license_manager()
    features = manager.current_features

    if limit_type == "resources_per_scan":
        max_limit = features.max_resources_per_scan
    elif limit_type == "scans_per_month":
        max_limit = features.max_scans_per_month
    elif limit_type == "aws_accounts":
        max_limit = features.max_aws_accounts
    else:
        logger.warning(f"Unknown limit type: {limit_type}")
        return

    if max_limit is not None and resource_count > max_limit:
        raise ResourceLimitExceededError(
            limit_type=limit_type,
            current=resource_count,
            maximum=max_limit,
            current_plan=manager.current_plan,
        )


def _get_minimum_plan_for_feature(feature: Feature) -> Plan | None:
    """Get the minimum plan that includes a feature."""
    from replimap.licensing.models import PLAN_FEATURES

    plan_order = [Plan.FREE, Plan.SOLO, Plan.PRO, Plan.TEAM, Plan.ENTERPRISE]

    for plan in plan_order:
        if PLAN_FEATURES[plan].has_feature(feature):
            return plan

    return None


def get_upgrade_prompt(feature: Feature, current_plan: Plan) -> str:
    """
    Generate a helpful upgrade prompt for a missing feature.

    Args:
        feature: The feature that's not available
        current_plan: The user's current plan

    Returns:
        Helpful upgrade message
    """
    required_plan = _get_minimum_plan_for_feature(feature)
    if required_plan is None:
        return f"Feature '{feature}' is not available in any plan."

    required_features = get_plan_features(required_plan)
    price = required_features.price_monthly

    return (
        f"'{feature.value}' requires {required_plan.value} plan (${price}/month).\n"
        f"Upgrade at: https://replimap.io/upgrade"
    )


def is_feature_available(feature: Feature) -> bool:
    """
    Check if a feature is available in the current plan.

    Args:
        feature: The feature to check

    Returns:
        True if feature is available
    """
    from replimap.licensing.manager import get_license_manager

    manager = get_license_manager()
    return manager.current_features.has_feature(feature)


def get_available_features() -> list[Feature]:
    """Get all features available in the current plan."""
    from replimap.licensing.manager import get_license_manager

    manager = get_license_manager()
    return list(manager.current_features.features)


def get_unavailable_features() -> list[Feature]:
    """Get all features NOT available in the current plan."""
    from replimap.licensing.manager import get_license_manager

    manager = get_license_manager()
    all_features = set(Feature)
    available = manager.current_features.features
    return list(all_features - available)


# =============================================================================
# OUTPUT-FOCUSED GATE CHECKS
# =============================================================================


@dataclass
class GateResult:
    """Result of a gate check."""

    allowed: bool
    prompt: str | None = None
    data: dict[str, Any] | None = None


def check_scan_allowed() -> GateResult:
    """
    Check if user can perform a scan.

    Gate: Monthly frequency limit (NOT resource count!)
    Resources are always unlimited - we gate at output time.
    """
    from replimap.licensing.manager import get_license_manager
    from replimap.licensing.prompts import format_scan_limit_prompt
    from replimap.licensing.tracker import get_usage_tracker

    manager = get_license_manager()
    tracker = get_usage_tracker()
    features = manager.current_features

    # Unlimited scans for paid plans
    if features.max_scans_per_month is None:
        return GateResult(allowed=True)

    # Check monthly limit for FREE
    scans_this_month = tracker.get_scans_this_month()
    if scans_this_month >= features.max_scans_per_month:
        # Calculate next reset date
        now = datetime.now()
        next_month = (now.replace(day=1) + timedelta(days=32)).replace(day=1)
        reset_date = next_month.strftime("%B %d, %Y")

        prompt = format_scan_limit_prompt(
            used=scans_this_month,
            limit=features.max_scans_per_month,
            reset_date=reset_date,
        )
        return GateResult(
            allowed=False,
            prompt=prompt,
            data={
                "used": scans_this_month,
                "limit": features.max_scans_per_month,
                "reset_date": reset_date,
            },
        )

    return GateResult(
        allowed=True,
        data={
            "remaining": features.max_scans_per_month - scans_this_month,
            "limit": features.max_scans_per_month,
        },
    )


def get_scans_remaining() -> int:
    """Get remaining scans this month (-1 for unlimited)."""
    from replimap.licensing.manager import get_license_manager
    from replimap.licensing.tracker import get_usage_tracker

    manager = get_license_manager()
    features = manager.current_features

    if features.max_scans_per_month is None:
        return -1

    tracker = get_usage_tracker()
    scans_this_month = tracker.get_scans_this_month()
    return max(0, features.max_scans_per_month - scans_this_month)


def check_clone_download_allowed() -> GateResult:
    """
    Check if user can download generated Terraform code.

    Gate: Download is paid feature. Generation/preview is free.
    """
    from replimap.licensing.manager import get_license_manager
    from replimap.licensing.prompts import get_upgrade_prompt

    manager = get_license_manager()
    features = manager.current_features

    if features.clone_download_enabled:
        return GateResult(allowed=True)

    # FREE users cannot download
    prompt = get_upgrade_prompt(
        "clone_download_blocked",
        {
            "resource_count": 0,  # Will be filled in later
            "lines_count": 0,
            "file_count": 0,
            "preview_lines": features.clone_preview_lines or 100,
            "hours_saved": 0,
            "money_saved": 0,
        },
    )
    return GateResult(allowed=False, prompt=prompt)


def get_clone_preview_lines() -> int | None:
    """Get number of lines to show in preview (None for full)."""
    from replimap.licensing.manager import get_license_manager

    manager = get_license_manager()
    return manager.current_features.clone_preview_lines


def format_clone_output(
    full_code: str,
    resource_count: int,
    file_count: int,
) -> tuple[str, str | None]:
    """
    Format clone output with appropriate preview/gate.

    Args:
        full_code: The complete generated code
        resource_count: Number of resources generated
        file_count: Number of files generated

    Returns:
        (code_to_display, upgrade_prompt_or_none)
    """
    from replimap.licensing.manager import get_license_manager
    from replimap.licensing.prompts import (
        format_clone_blocked_prompt,
        format_clone_preview_footer,
    )

    manager = get_license_manager()
    features = manager.current_features
    preview_limit = features.clone_preview_lines

    lines = full_code.split("\n")
    total_lines = len(lines)

    if preview_limit is None or total_lines <= preview_limit:
        # Full access
        return full_code, None

    # Limited preview
    preview_lines = lines[:preview_limit]
    remaining = total_lines - preview_limit

    # Add truncation footer
    footer = format_clone_preview_footer(
        remaining_lines=remaining,
        preview_lines=preview_limit,
        total_lines=total_lines,
        resource_count=resource_count,
        file_count=file_count,
    )

    preview = "\n".join(preview_lines) + footer

    # Generate upgrade prompt
    prompt = format_clone_blocked_prompt(
        resource_count=resource_count,
        lines_count=total_lines,
        file_count=file_count,
        preview_lines=preview_limit,
    )

    return preview, prompt


def check_audit_export_allowed() -> GateResult:
    """Check if user can export audit report."""
    from replimap.licensing.manager import get_license_manager
    from replimap.licensing.prompts import get_upgrade_prompt

    manager = get_license_manager()
    features = manager.current_features

    if features.audit_report_export:
        return GateResult(allowed=True)

    prompt = get_upgrade_prompt("audit_export_blocked")
    return GateResult(allowed=False, prompt=prompt)


def check_audit_ci_mode_allowed() -> GateResult:
    """Check if user can use --fail-on-high CI mode."""
    from replimap.licensing.manager import get_license_manager
    from replimap.licensing.prompts import get_upgrade_prompt

    manager = get_license_manager()
    features = manager.current_features

    if features.audit_ci_mode:
        return GateResult(allowed=True)

    prompt = get_upgrade_prompt("audit_ci_blocked")
    return GateResult(allowed=False, prompt=prompt)


def check_audit_fix_allowed() -> GateResult:
    """
    Check if user can use --fix to generate remediation code.

    Remediation code generation requires SOLO+ plan since it requires
    seeing all audit findings to generate proper fixes.
    """
    from replimap.licensing.manager import get_license_manager
    from replimap.licensing.prompts import get_upgrade_prompt

    manager = get_license_manager()
    features = manager.current_features

    # --fix requires being able to see all findings (SOLO+)
    if features.audit_visible_findings is None and features.audit_report_export:
        return GateResult(allowed=True)

    prompt = get_upgrade_prompt("audit_fix_blocked")
    return GateResult(allowed=False, prompt=prompt)


def get_audit_visible_findings() -> int | None:
    """Get number of findings to show (None for all)."""
    from replimap.licensing.manager import get_license_manager

    manager = get_license_manager()
    return manager.current_features.audit_visible_findings


def format_audit_findings(
    all_findings: list[Any],
    score: int,
    grade: str,
) -> tuple[list[Any], str | None]:
    """
    Format audit findings with appropriate visibility.

    Args:
        all_findings: List of all findings
        score: Security score (0-100)
        grade: Letter grade (A-F)

    Returns:
        (visible_findings, upgrade_prompt_or_none)
    """
    from replimap.licensing.manager import get_license_manager
    from replimap.licensing.prompts import format_audit_limited_prompt

    manager = get_license_manager()
    features = manager.current_features
    visible_limit = features.audit_visible_findings

    if visible_limit is None:
        # Full access
        return all_findings, None

    # Count by severity
    critical_count = sum(
        1 for f in all_findings if getattr(f, "severity", "") == "CRITICAL"
    )
    high_count = sum(1 for f in all_findings if getattr(f, "severity", "") == "HIGH")
    medium_count = sum(
        1 for f in all_findings if getattr(f, "severity", "") == "MEDIUM"
    )
    low_count = sum(1 for f in all_findings if getattr(f, "severity", "") == "LOW")

    # Limited view
    visible = all_findings[:visible_limit]

    # Count hidden critical findings
    visible_critical = sum(
        1 for f in visible if getattr(f, "severity", "") == "CRITICAL"
    )
    hidden_critical = max(0, critical_count - visible_critical)

    prompt = format_audit_limited_prompt(
        score=score,
        grade=grade,
        critical_count=critical_count,
        high_count=high_count,
        medium_count=medium_count,
        low_count=low_count,
        shown_count=visible_limit,
        total_count=len(all_findings),
        hidden_critical=hidden_critical,
    )

    return visible, prompt


def check_graph_export_watermark() -> bool:
    """Check if graph export should have watermark."""
    from replimap.licensing.manager import get_license_manager

    manager = get_license_manager()
    return manager.current_features.graph_export_watermark


def check_drift_allowed() -> GateResult:
    """Check if user can use drift detection."""
    from replimap.licensing.manager import get_license_manager
    from replimap.licensing.prompts import get_upgrade_prompt

    manager = get_license_manager()
    features = manager.current_features

    if features.drift_enabled:
        return GateResult(allowed=True)

    prompt = get_upgrade_prompt("drift_not_available")
    return GateResult(allowed=False, prompt=prompt)


def check_drift_watch_allowed() -> GateResult:
    """Check if user can use drift watch mode."""
    from replimap.licensing.manager import get_license_manager
    from replimap.licensing.prompts import get_upgrade_prompt

    manager = get_license_manager()
    features = manager.current_features

    if features.drift_watch_enabled:
        return GateResult(allowed=True)

    prompt = get_upgrade_prompt("drift_watch_not_available")
    return GateResult(allowed=False, prompt=prompt)


def check_cost_allowed() -> GateResult:
    """Check if user can use cost estimation."""
    from replimap.licensing.manager import get_license_manager
    from replimap.licensing.prompts import get_upgrade_prompt

    manager = get_license_manager()
    features = manager.current_features

    if features.cost_enabled:
        return GateResult(allowed=True)

    prompt = get_upgrade_prompt("cost_not_available")
    return GateResult(allowed=False, prompt=prompt)


def check_right_sizer_allowed() -> GateResult:
    """
    Check if user can use Right-Sizer (Solo+ feature).

    Right-Sizer automatically downgrades production resources
    to cost-effective sizes for dev/staging environments.
    """
    from replimap.licensing.manager import get_license_manager
    from replimap.licensing.prompts import get_upgrade_prompt

    manager = get_license_manager()
    features = manager.current_features

    if features.rightsizer_enabled:
        return GateResult(allowed=True)

    prompt = get_upgrade_prompt("right_sizer_not_available")
    return GateResult(allowed=False, prompt=prompt)


def check_deps_allowed() -> GateResult:
    """Check if user can use dependency exploration (Pro+ feature)."""
    from replimap.licensing.manager import get_license_manager
    from replimap.licensing.prompts import get_upgrade_prompt

    manager = get_license_manager()
    features = manager.current_features

    if features.deps_enabled:
        return GateResult(allowed=True)

    prompt = get_upgrade_prompt("deps_not_available")
    return GateResult(allowed=False, prompt=prompt)


# Backward compatibility alias
def check_blast_allowed() -> GateResult:
    """Deprecated: Use check_deps_allowed instead."""
    return check_deps_allowed()


def check_multi_account_allowed(account_count: int) -> GateResult:
    """Check if user can use multiple AWS accounts."""
    from replimap.licensing.manager import get_license_manager
    from replimap.licensing.prompts import format_multi_account_prompt

    manager = get_license_manager()
    features = manager.current_features
    limit = features.max_aws_accounts

    if limit is None or account_count <= limit:
        return GateResult(allowed=True)

    # Determine upgrade target
    if limit == 1:
        upgrade_plan = "Pro"
        upgrade_price = 99
    else:
        upgrade_plan = "Team"
        upgrade_price = 199

    prompt = format_multi_account_prompt(
        current_count=account_count,
        limit=limit,
        upgrade_plan=upgrade_plan,
        upgrade_price=upgrade_price,
    )
    return GateResult(allowed=False, prompt=prompt)


def check_output_format_allowed(output_format: str) -> GateResult:
    """
    Check if user can use a specific output format.

    Args:
        output_format: Format string (terraform, cloudformation, pulumi, cdk)
    """
    from replimap.licensing.manager import get_license_manager
    from replimap.licensing.prompts import get_upgrade_prompt

    manager = get_license_manager()
    features = manager.current_features

    format_to_feature = {
        "terraform": Feature.TERRAFORM_OUTPUT,
        "cloudformation": Feature.CLOUDFORMATION_OUTPUT,
        "pulumi": Feature.PULUMI_OUTPUT,
        "cdk": Feature.CDK_OUTPUT,
    }

    feature = format_to_feature.get(output_format.lower())
    if feature is None:
        return GateResult(allowed=False, prompt=f"Unknown format: {output_format}")

    if features.has_feature(feature):
        return GateResult(allowed=True)

    # Get appropriate prompt
    prompt_key = f"{output_format.lower()}_not_available"
    prompt = get_upgrade_prompt(prompt_key)
    return GateResult(allowed=False, prompt=prompt)
