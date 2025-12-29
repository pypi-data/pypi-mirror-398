"""
Right-Sizer Module.

Calls the Backend API to get optimization suggestions and generates
a Terraform .auto.tfvars file for applying overrides.

CRITICAL: Uses replimap.core.naming to ensure variable names match Generator.

The Seven Laws of Sovereign Code:
1. Operate Autonomously - The tool should work offline when possible
3. Simplicity is the Ultimate Sophistication - Minimal dependencies
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import httpx
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# CRITICAL: Use the SAME naming module as Generator
from replimap.core.naming import get_variable_name

logger = logging.getLogger(__name__)

# API Configuration
REPLIMAP_API_BASE = os.environ.get(
    "REPLIMAP_API_URL",
    "https://replimap-api.davidlu1001.workers.dev",
)
RIGHTSIZER_ENDPOINT = f"{REPLIMAP_API_BASE}/v1/rightsizer/suggestions"
API_TIMEOUT = 30.0
MAX_RESOURCES_PER_REQUEST = 100  # Backend limit

console = Console()


class DowngradeStrategy(str, Enum):
    """Optimization strategy for Right-Sizer."""

    CONSERVATIVE = "conservative"
    AGGRESSIVE = "aggressive"


# Mapping of resource types to their primary "size" attribute
RESOURCE_SIZE_ATTRIBUTE: dict[str, str] = {
    "aws_instance": "instance_type",
    "aws_db_instance": "instance_class",
    "aws_elasticache_cluster": "node_type",
    "aws_elasticache_replication_group": "node_type",
    "aws_launch_template": "instance_type",
}


@dataclass
class ResourceSummary:
    """Resource metadata to send to API."""

    resource_id: str
    resource_type: str
    instance_type: str
    region: str
    multi_az: bool | None = None
    storage_type: str | None = None
    storage_size_gb: int | None = None
    iops: int | None = None

    def to_api_dict(self) -> dict[str, Any]:
        """Convert to API request format (metadata only, no secrets)."""
        data: dict[str, Any] = {
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "instance_type": self.instance_type,
            "region": self.region,
        }
        if self.multi_az is not None:
            data["multi_az"] = self.multi_az
        if self.storage_type:
            data["storage_type"] = self.storage_type
        if self.storage_size_gb:
            data["storage_size_gb"] = self.storage_size_gb
        if self.iops:
            data["iops"] = self.iops
        return data


@dataclass
class SavingsBreakdown:
    """Breakdown of savings by category."""

    instance: float = 0.0
    storage: float = 0.0
    multi_az: float = 0.0


@dataclass
class ResourceSuggestion:
    """Single resource optimization suggestion from API."""

    resource_id: str
    resource_type: str
    original_type: str
    original_monthly_cost: float
    recommended_type: str
    recommended_monthly_cost: float
    monthly_savings: float
    annual_savings: float
    savings_percentage: float
    savings_breakdown: SavingsBreakdown
    actions: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    confidence: str = "high"
    recommended_storage_type: str | None = None
    recommended_multi_az: bool | None = None


@dataclass
class SkippedResource:
    """Resource that was skipped with reason."""

    resource_id: str
    resource_type: str
    instance_type: str
    reason: str


@dataclass
class RightSizerResult:
    """Complete result from Right-Sizer API."""

    success: bool
    suggestions: list[ResourceSuggestion]
    skipped: list[SkippedResource]
    total_resources: int
    resources_with_suggestions: int
    resources_skipped: int
    total_current_monthly: float
    total_recommended_monthly: float
    total_monthly_savings: float
    total_annual_savings: float
    savings_percentage: float
    savings_breakdown: SavingsBreakdown
    strategy_used: str
    error_message: str | None = None


class RightSizerClient:
    """Client for the Right-Sizer API."""

    SUPPORTED_RESOURCE_TYPES = {
        "aws_instance",
        "aws_db_instance",
        "aws_elasticache_cluster",
        "aws_elasticache_replication_group",
        # Note: aws_launch_template is NOT supported by the backend API
    }

    def __init__(self) -> None:
        """Initialize the Right-Sizer client."""
        from replimap.licensing.manager import get_license_manager

        self.manager = get_license_manager()

    def _get_license_key(self) -> str | None:
        """Get the current license key."""
        license_info = self.manager.current_license  # Property, not method
        return license_info.license_key if license_info else None

    def extract_resources(
        self,
        scanned_resources: list[Any],
        region: str,
    ) -> list[ResourceSummary]:
        """
        Extract resource metadata from scanned resources.

        SECURITY: Only extracts metadata (type, region), never secrets or tags.
        """
        summaries = []

        for resource in scanned_resources:
            # Get resource type (ResourceNode uses 'resource_type', not 'type')
            resource_type = getattr(resource, "resource_type", None)
            if resource_type:
                resource_type = (
                    resource_type.value
                    if hasattr(resource_type, "value")
                    else str(resource_type)
                )

            if not resource_type or resource_type not in self.SUPPORTED_RESOURCE_TYPES:
                continue

            # Get attributes/config
            attrs = (
                getattr(resource, "attributes", None)
                or getattr(resource, "config", {})
                or {}
            )
            if hasattr(attrs, "__dict__"):
                attrs = attrs.__dict__

            # Get instance type (different attribute names for different resources)
            instance_type = (
                attrs.get("instance_type")
                or attrs.get("instance_class")
                or attrs.get("node_type")
            )

            if not instance_type:
                continue

            # Get resource name
            resource_name = (
                getattr(resource, "terraform_name", None)
                or getattr(resource, "name", None)
                or getattr(resource, "id", None)
                or str(id(resource))
            )

            summary = ResourceSummary(
                resource_id=str(resource_name),
                resource_type=resource_type,
                instance_type=instance_type,
                region=region,
                multi_az=attrs.get("multi_az"),
                storage_type=attrs.get("storage_type"),
                storage_size_gb=attrs.get("allocated_storage"),
                iops=attrs.get("iops"),
            )
            summaries.append(summary)

        return summaries

    def get_suggestions(
        self,
        resources: list[ResourceSummary],
        strategy: DowngradeStrategy = DowngradeStrategy.CONSERVATIVE,
    ) -> RightSizerResult:
        """Get optimization suggestions from API (sync version)."""
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If already in async context, run in thread pool
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run, self.get_suggestions_async(resources, strategy)
                    )
                    return future.result()
            return asyncio.run(self.get_suggestions_async(resources, strategy))
        except RuntimeError:
            return asyncio.run(self.get_suggestions_async(resources, strategy))

    async def get_suggestions_async(
        self,
        resources: list[ResourceSummary],
        strategy: DowngradeStrategy = DowngradeStrategy.CONSERVATIVE,
    ) -> RightSizerResult:
        """Get optimization suggestions from API (async version)."""
        if not resources:
            return self._error_result("No rightsizable resources found")

        license_key = self._get_license_key()
        if not license_key:
            return self._error_result("No active license key")

        # Batch resources if exceeding API limit
        if len(resources) > MAX_RESOURCES_PER_REQUEST:
            return await self._get_suggestions_batched(resources, strategy, license_key)

        return await self._get_suggestions_single(resources, strategy, license_key)

    async def _get_suggestions_batched(
        self,
        resources: list[ResourceSummary],
        strategy: DowngradeStrategy,
        license_key: str,
    ) -> RightSizerResult:
        """Get suggestions for resources in batches (when > 100 resources)."""
        # Split into batches
        batches = [
            resources[i : i + MAX_RESOURCES_PER_REQUEST]
            for i in range(0, len(resources), MAX_RESOURCES_PER_REQUEST)
        ]

        logger.info(
            f"Batching {len(resources)} resources into {len(batches)} API requests "
            f"(max {MAX_RESOURCES_PER_REQUEST} per request)"
        )

        # Process all batches
        results: list[RightSizerResult] = []
        for i, batch in enumerate(batches):
            logger.debug(
                f"Processing batch {i + 1}/{len(batches)} ({len(batch)} resources)"
            )
            result = await self._get_suggestions_single(batch, strategy, license_key)

            if not result.success:
                # If any batch fails, return the error
                return result

            results.append(result)

        # Merge all results
        return self._merge_results(results, strategy)

    def _merge_results(
        self, results: list[RightSizerResult], strategy: DowngradeStrategy
    ) -> RightSizerResult:
        """Merge multiple RightSizerResult objects into one."""
        all_suggestions: list[ResourceSuggestion] = []
        all_skipped: list[SkippedResource] = []
        total_current = 0.0
        total_recommended = 0.0
        breakdown = SavingsBreakdown(instance=0, storage=0, multi_az=0)

        for result in results:
            all_suggestions.extend(result.suggestions)
            all_skipped.extend(result.skipped)
            total_current += result.total_current_monthly
            total_recommended += result.total_recommended_monthly
            breakdown.instance += result.savings_breakdown.instance
            breakdown.storage += result.savings_breakdown.storage
            breakdown.multi_az += result.savings_breakdown.multi_az

        total_savings = total_current - total_recommended
        savings_pct = (total_savings / total_current * 100) if total_current > 0 else 0

        return RightSizerResult(
            success=True,
            suggestions=all_suggestions,
            skipped=all_skipped,
            total_resources=len(all_suggestions) + len(all_skipped),
            resources_with_suggestions=len(all_suggestions),
            resources_skipped=len(all_skipped),
            total_current_monthly=round(total_current, 2),
            total_recommended_monthly=round(total_recommended, 2),
            total_monthly_savings=round(total_savings, 2),
            total_annual_savings=round(total_savings * 12, 2),
            savings_percentage=round(savings_pct, 1),
            savings_breakdown=SavingsBreakdown(
                instance=round(breakdown.instance, 2),
                storage=round(breakdown.storage, 2),
                multi_az=round(breakdown.multi_az, 2),
            ),
            strategy_used=strategy.value,
        )

    async def _get_suggestions_single(
        self,
        resources: list[ResourceSummary],
        strategy: DowngradeStrategy,
        license_key: str,
    ) -> RightSizerResult:
        """Get suggestions for a single batch of resources."""
        # Prepare request (only metadata, no secrets)
        request_body = {
            "resources": [r.to_api_dict() for r in resources],
            "strategy": strategy.value,
        }

        # Debug: Log sample of resources being sent
        logger.debug(
            f"Sending {len(resources)} resources to Right-Sizer API. "
            f"Sample: {request_body['resources'][:2] if request_body['resources'] else 'empty'}"
        )

        try:
            async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
                response = await client.post(
                    RIGHTSIZER_ENDPOINT,
                    json=request_body,
                    headers={
                        "Authorization": f"Bearer {license_key}",
                        "Content-Type": "application/json",
                    },
                )

                if response.status_code == 401:
                    return self._error_result("Invalid or expired license key")

                if response.status_code == 403:
                    data = response.json()
                    return self._error_result(
                        data.get("message", "Right-Sizer requires Solo plan or higher")
                    )

                if response.status_code == 429:
                    return self._error_result(
                        "Rate limit exceeded. Please try again later."
                    )

                if response.status_code == 400:
                    # Bad request - try to extract error details
                    try:
                        data = response.json()
                        error_msg = data.get(
                            "error", data.get("message", "Invalid request")
                        )
                        return self._error_result(f"API validation error: {error_msg}")
                    except (json.JSONDecodeError, KeyError):
                        return self._error_result("API error: Invalid request format")

                if response.status_code != 200:
                    # Try to extract error message from response
                    try:
                        data = response.json()
                        error_msg = data.get(
                            "error", data.get("message", f"HTTP {response.status_code}")
                        )
                        return self._error_result(f"API error: {error_msg}")
                    except (json.JSONDecodeError, KeyError):
                        return self._error_result(
                            f"API error: HTTP {response.status_code}"
                        )

                data = response.json()
                return self._parse_response(data)

        except httpx.TimeoutException:
            return self._error_result("API request timed out. Please try again.")
        except httpx.RequestError as e:
            return self._error_result(f"Network error: {e!s}")
        except json.JSONDecodeError:
            return self._error_result("Invalid response from API")

    def _parse_response(self, data: dict[str, Any]) -> RightSizerResult:
        """Parse API response into RightSizerResult."""
        suggestions = []
        for s in data.get("suggestions", []):
            breakdown = s.get("savings_breakdown", {})
            suggestion = ResourceSuggestion(
                resource_id=s["resource_id"],
                resource_type=s["resource_type"],
                original_type=s["current"]["instance_type"],
                original_monthly_cost=s["current"]["monthly_cost"],
                recommended_type=s["recommended"]["instance_type"],
                recommended_monthly_cost=s["recommended"]["monthly_cost"],
                monthly_savings=s["monthly_savings"],
                annual_savings=s["annual_savings"],
                savings_percentage=s["savings_percentage"],
                savings_breakdown=SavingsBreakdown(
                    instance=breakdown.get("instance", 0),
                    storage=breakdown.get("storage", 0),
                    multi_az=breakdown.get("multi_az", 0),
                ),
                actions=s.get("actions", []),
                warnings=s.get("warnings", []),
                confidence=s.get("confidence", "high"),
                recommended_storage_type=s["recommended"].get("storage_type"),
                recommended_multi_az=s["recommended"].get("multi_az"),
            )
            suggestions.append(suggestion)

        skipped = [
            SkippedResource(
                resource_id=sk["resource_id"],
                resource_type=sk["resource_type"],
                instance_type=sk["instance_type"],
                reason=sk["reason"],
            )
            for sk in data.get("skipped", [])
        ]

        summary = data.get("summary", {})
        breakdown = summary.get("savings_breakdown", {})

        return RightSizerResult(
            success=data.get("success", False),
            suggestions=suggestions,
            skipped=skipped,
            total_resources=summary.get("total_resources", 0),
            resources_with_suggestions=summary.get("resources_with_suggestions", 0),
            resources_skipped=summary.get("resources_skipped", 0),
            total_current_monthly=summary.get("total_current_monthly", 0),
            total_recommended_monthly=summary.get("total_recommended_monthly", 0),
            total_monthly_savings=summary.get("total_monthly_savings", 0),
            total_annual_savings=summary.get("total_annual_savings", 0),
            savings_percentage=summary.get("savings_percentage", 0),
            savings_breakdown=SavingsBreakdown(
                instance=breakdown.get("instance", 0),
                storage=breakdown.get("storage", 0),
                multi_az=breakdown.get("multi_az", 0),
            ),
            strategy_used=data.get("strategy_used", "conservative"),
        )

    def _error_result(self, message: str) -> RightSizerResult:
        """Create an error result."""
        return RightSizerResult(
            success=False,
            suggestions=[],
            skipped=[],
            total_resources=0,
            resources_with_suggestions=0,
            resources_skipped=0,
            total_current_monthly=0,
            total_recommended_monthly=0,
            total_monthly_savings=0,
            total_annual_savings=0,
            savings_percentage=0,
            savings_breakdown=SavingsBreakdown(),
            strategy_used="",
            error_message=message,
        )

    def generate_tfvars_content(self, suggestions: list[ResourceSuggestion]) -> str:
        """
        Generate HCL content for right-sizer.auto.tfvars.

        CRITICAL: Uses replimap.core.naming.get_variable_name to ensure
        variable names match exactly what Generator produces.
        """
        lines = []
        lines.append(
            "# ============================================================================"
        )
        lines.append("# Auto-generated by RepliMap Right-Sizer")
        lines.append(
            "# These values override production defaults for dev/staging environments"
        )
        lines.append("# Delete this file to revert to production configuration")
        lines.append(
            "# ============================================================================"
        )
        lines.append("")

        total_savings = sum(s.monthly_savings for s in suggestions)
        lines.append(
            f"# Estimated Savings: ${total_savings:,.2f}/month (${total_savings * 12:,.2f}/year)"
        )
        lines.append("# Generated by Right-Sizer")
        lines.append("")

        for s in suggestions:
            lines.append(f"# {s.resource_type}.{s.resource_id}")
            lines.append(
                f"# {s.original_type} → {s.recommended_type} (saves ${s.monthly_savings:.2f}/mo)"
            )

            # Get the correct attribute name for this resource type
            size_attr = RESOURCE_SIZE_ATTRIBUTE.get(s.resource_type, "instance_type")

            # Use the SAME naming function as Generator
            size_var = get_variable_name(s.resource_type, s.resource_id, size_attr)
            lines.append(f'{size_var} = "{s.recommended_type}"')

            # RDS-specific: storage_type and multi_az
            if s.resource_type == "aws_db_instance":
                if s.recommended_storage_type:
                    storage_var = get_variable_name(
                        s.resource_type, s.resource_id, "storage_type"
                    )
                    lines.append(f'{storage_var} = "{s.recommended_storage_type}"')

                if s.recommended_multi_az is not None:
                    multi_az_var = get_variable_name(
                        s.resource_type, s.resource_id, "multi_az"
                    )
                    lines.append(
                        f"{multi_az_var} = {str(s.recommended_multi_az).lower()}"
                    )

            lines.append("")

        return "\n".join(lines)

    def write_tfvars_file(self, output_dir: str, content: str) -> str:
        """Write the tfvars file to the output directory."""
        path = os.path.join(output_dir, "right-sizer.auto.tfvars")
        with open(path, "w") as f:
            f.write(content)
        return path

    def display_suggestions_table(self, result: RightSizerResult) -> None:
        """Display suggestions in a rich table."""
        if not result.suggestions:
            console.print("[yellow]No optimization suggestions available.[/yellow]")
            return

        table = Table(
            title="💰 Right-Sizer Recommendations",
            show_header=True,
            header_style="bold cyan",
        )

        table.add_column("Resource", style="dim", max_width=25)
        table.add_column("Type", max_width=12)
        table.add_column("Current", style="red")
        table.add_column("Recommended", style="green")
        table.add_column("Monthly Savings", style="bold green", justify="right")
        table.add_column("Confidence")

        for s in result.suggestions:
            confidence_style = {"high": "green", "medium": "yellow", "low": "red"}.get(
                s.confidence, "white"
            )

            # Shorten resource type for display
            short_type = s.resource_type.replace("aws_", "").replace("_", " ")[:12]

            table.add_row(
                s.resource_id[:23],
                short_type,
                s.original_type,
                s.recommended_type,
                f"${s.monthly_savings:,.2f}",
                f"[{confidence_style}]{s.confidence}[/{confidence_style}]",
            )

        console.print(table)

        # Show skipped resources if any
        if result.skipped:
            console.print(
                f"\n[dim]ℹ️  Skipped {len(result.skipped)} resources (already optimal):[/dim]"
            )
            for sk in result.skipped[:5]:
                console.print(f"  [dim]• {sk.resource_id}: {sk.reason}[/dim]")
            if len(result.skipped) > 5:
                console.print(f"  [dim]  ... and {len(result.skipped) - 5} more[/dim]")


def right_sizer_success_panel(
    original_monthly: float,
    recommended_monthly: float,
    suggestions_count: int,
    skipped_count: int,
    tfvars_filename: str,
) -> Panel:
    """Generate success panel after Right-Sizer completes."""
    monthly_savings = original_monthly - recommended_monthly
    annual_savings = monthly_savings * 12
    savings_pct = (
        (monthly_savings / original_monthly * 100) if original_monthly > 0 else 0
    )

    content = f"""[bold green]✅ Right-Sizer Analysis Complete[/bold green]

[bold]Resources Analyzed:[/bold] {suggestions_count + skipped_count}
[bold]Optimizations Applied:[/bold] {suggestions_count}
[bold]Skipped (already optimal):[/bold] {skipped_count}

┌─────────────────────────────────────────────────────┐
│  [bold]Cost Comparison[/bold]                                   │
├─────────────────────────────────────────────────────┤
│  Original (Production):     [red]${original_monthly:>10,.2f}/mo[/red]  │
│  Optimized (Dev/Staging):   [green]${recommended_monthly:>10,.2f}/mo[/green]  │
├─────────────────────────────────────────────────────┤
│  [bold]Monthly Savings:[/bold]            [bold green]${monthly_savings:>10,.2f}[/bold green]     │
│  [bold]Annual Savings:[/bold]             [bold green]${annual_savings:>10,.2f}[/bold green]     │
│  [bold]Savings Percentage:[/bold]         [bold green]{savings_pct:>10.0f}%[/bold green]     │
└─────────────────────────────────────────────────────┘

[dim]Overrides written to: {tfvars_filename}[/dim]
[dim]Delete that file to revert to production defaults.[/dim]"""

    return Panel(
        content,
        title="[bold]💰 Right-Sizer Savings Report[/bold]",
        border_style="green",
        padding=(1, 2),
    )


def check_and_prompt_upgrade() -> bool:
    """Check if Right-Sizer is allowed and show upgrade prompt if not."""
    from replimap.licensing.gates import check_right_sizer_allowed

    result = check_right_sizer_allowed()

    if not result.allowed:
        if result.prompt:
            console.print(result.prompt)
        return False

    return True
