"""
RepliMap CLI Entry Point.

Usage:
    replimap scan --profile <aws-profile> --region <region> [--output graph.json]
    replimap clone --profile <source-profile> --region <region> --output-dir ./terraform
    replimap license activate <key>
    replimap license status
"""

from __future__ import annotations

import configparser
import hashlib
import json
import logging
import os
import time
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from replimap.audit.checkov_runner import CheckovResults

import boto3
import typer
from botocore.exceptions import ClientError, NoCredentialsError, ProfileNotFound
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
)
from rich.prompt import Confirm, Prompt
from rich.table import Table

from replimap import __version__
from replimap.core import (
    GraphEngine,
    ScanCache,
    ScanFilter,
    SelectionStrategy,
    apply_filter_to_graph,
    apply_selection,
    build_subgraph_from_selection,
    update_cache_from_graph,
)
from replimap.licensing import (
    Feature,
    LicenseStatus,
    LicenseValidationError,
    check_audit_ci_mode_allowed,
    check_audit_fix_allowed,
    check_drift_allowed,
    check_scan_allowed,
    get_scans_remaining,
)
from replimap.licensing.manager import get_license_manager
from replimap.licensing.tracker import get_usage_tracker
from replimap.renderers import TerraformRenderer
from replimap.scanners.base import run_all_scanners
from replimap.transformers import create_default_pipeline

# Credential cache directory
CACHE_DIR = Path.home() / ".replimap" / "cache"
CREDENTIAL_CACHE_FILE = CACHE_DIR / "credentials.json"
CREDENTIAL_CACHE_TTL = timedelta(hours=12)  # Cache MFA credentials for 12 hours

# Initialize rich console
console = Console()

# Configure logging with rich handler
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console, rich_tracebacks=True)],
)
logger = logging.getLogger("replimap")

# Create Typer app
app = typer.Typer(
    name="replimap",
    help="AWS Environment Replication Tool - Clone your production to staging in minutes",
    add_completion=False,
    rich_markup_mode="rich",
    context_settings={"help_option_names": ["-h", "--help"]},
)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"[bold cyan]RepliMap[/] v{__version__}")
        raise typer.Exit()


def get_available_profiles() -> list[str]:
    """Get list of available AWS profiles from config."""
    profiles = ["default"]
    config_path = Path.home() / ".aws" / "config"
    credentials_path = Path.home() / ".aws" / "credentials"

    for path in [config_path, credentials_path]:
        if path.exists():
            config = configparser.ConfigParser()
            config.read(path)
            for section in config.sections():
                # Config file uses "profile xxx" format, credentials uses just "xxx"
                if section.startswith("profile "):
                    profiles.append(section.replace("profile ", ""))
                elif section != "default":
                    profiles.append(section)

    return sorted(set(profiles))


def get_profile_region(profile: str | None) -> str | None:
    """
    Get the default region for a profile from AWS config.

    Args:
        profile: AWS profile name

    Returns:
        Region string if found, None otherwise
    """
    config_path = Path.home() / ".aws" / "config"
    if not config_path.exists():
        return None

    config = configparser.ConfigParser()
    config.read(config_path)

    # Determine section name
    if profile and profile != "default":
        section = f"profile {profile}"
    else:
        section = "default"

    if section in config and "region" in config[section]:
        return config[section]["region"]

    # Also check environment variable
    return os.environ.get("AWS_DEFAULT_REGION")


def get_credential_cache_key(profile: str | None) -> str:
    """Generate a cache key for credentials."""
    key = f"profile:{profile or 'default'}"
    return hashlib.md5(key.encode(), usedforsecurity=False).hexdigest()


def get_cached_credentials(profile: str | None) -> dict | None:
    """
    Get cached credentials if valid.

    Returns cached session credentials to avoid repeated MFA prompts.
    """
    if not CREDENTIAL_CACHE_FILE.exists():
        return None

    try:
        with open(CREDENTIAL_CACHE_FILE) as f:
            cache = json.load(f)

        cache_key = get_credential_cache_key(profile)
        if cache_key not in cache:
            return None

        entry = cache[cache_key]
        expires_at = datetime.fromisoformat(entry["expires_at"])

        if datetime.now() >= expires_at:
            return None

        return entry["credentials"]
    except (json.JSONDecodeError, KeyError, ValueError):
        return None


def save_cached_credentials(
    profile: str | None,
    credentials: dict,
    expiration: datetime | None = None,
) -> None:
    """Save credentials to cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    cache = {}
    if CREDENTIAL_CACHE_FILE.exists():
        try:
            with open(CREDENTIAL_CACHE_FILE) as f:
                cache = json.load(f)
        except json.JSONDecodeError:
            cache = {}

    cache_key = get_credential_cache_key(profile)

    # Use provided expiration or default TTL
    if expiration:
        expires_at = expiration
    else:
        expires_at = datetime.now() + CREDENTIAL_CACHE_TTL

    cache[cache_key] = {
        "credentials": credentials,
        "expires_at": expires_at.isoformat(),
        "profile": profile,
    }

    with open(CREDENTIAL_CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)

    # Secure the cache file
    os.chmod(CREDENTIAL_CACHE_FILE, 0o600)


def clear_credential_cache(profile: str | None = None) -> None:
    """Clear credential cache for a profile or all profiles."""
    if not CREDENTIAL_CACHE_FILE.exists():
        return

    if profile is None:
        # Clear all
        CREDENTIAL_CACHE_FILE.unlink()
        return

    try:
        with open(CREDENTIAL_CACHE_FILE) as f:
            cache = json.load(f)

        cache_key = get_credential_cache_key(profile)
        if cache_key in cache:
            del cache[cache_key]

        with open(CREDENTIAL_CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)
    except (json.JSONDecodeError, KeyError):
        pass


def get_aws_session(
    profile: str | None, region: str, use_cache: bool = True
) -> boto3.Session:
    """
    Create a boto3 session with the specified profile and region.

    Supports credential caching to avoid repeated MFA prompts.

    Args:
        profile: AWS profile name (optional)
        region: AWS region
        use_cache: Whether to use credential caching (default: True)

    Returns:
        Configured boto3 Session

    Raises:
        typer.Exit: If credentials are invalid
    """
    # Try cached credentials first (for MFA sessions)
    if use_cache:
        cached = get_cached_credentials(profile)
        if cached:
            try:
                session = boto3.Session(
                    aws_access_key_id=cached["access_key"],
                    aws_secret_access_key=cached["secret_key"],
                    aws_session_token=cached.get("session_token"),
                    region_name=region,
                )
                sts = session.client("sts")
                identity = sts.get_caller_identity()
                console.print(
                    f"[green]Authenticated[/] as [bold]{identity['Arn']}[/] "
                    f"[dim](cached credentials)[/]"
                )
                return session
            except (ClientError, NoCredentialsError):
                # Cache invalid, continue with normal auth
                clear_credential_cache(profile)

    try:
        session = boto3.Session(profile_name=profile, region_name=region)

        # Verify credentials work
        sts = session.client("sts")
        identity = sts.get_caller_identity()

        # Cache the credentials if they're temporary (MFA)
        credentials = session.get_credentials()
        if credentials and use_cache:
            frozen = credentials.get_frozen_credentials()
            if frozen.token:  # Has session token = temporary credentials
                save_cached_credentials(
                    profile,
                    {
                        "access_key": frozen.access_key,
                        "secret_key": frozen.secret_key,
                        "session_token": frozen.token,
                    },
                )
                console.print(
                    f"[green]Authenticated[/] as [bold]{identity['Arn']}[/] "
                    f"[dim](credentials cached for 12h)[/]"
                )
            else:
                console.print(
                    f"[green]Authenticated[/] as [bold]{identity['Arn']}[/] "
                    f"(Account: {identity['Account']})"
                )
        else:
            console.print(
                f"[green]Authenticated[/] as [bold]{identity['Arn']}[/] "
                f"(Account: {identity['Account']})"
            )

        return session

    except ProfileNotFound:
        available = get_available_profiles()
        console.print(
            Panel(
                f"[red]Profile '{profile}' not found.[/]\n\n"
                f"Available profiles: [cyan]{', '.join(available)}[/]\n\n"
                "Configure a new profile with: [bold]aws configure --profile <name>[/]",
                title="Profile Not Found",
                border_style="red",
            )
        )
        raise typer.Exit(1)

    except NoCredentialsError:
        console.print(
            Panel(
                "[red]No AWS credentials found.[/]\n\n"
                "Configure credentials with:\n"
                "  [bold]aws configure[/] (for default profile)\n"
                "  [bold]aws configure --profile <name>[/] (for named profile)\n\n"
                "Or set environment variables:\n"
                "  [dim]AWS_ACCESS_KEY_ID[/]\n"
                "  [dim]AWS_SECRET_ACCESS_KEY[/]\n"
                "  [dim]AWS_SESSION_TOKEN[/] (optional)",
                title="Authentication Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        if error_code == "ExpiredToken":
            clear_credential_cache(profile)
            console.print(
                Panel(
                    "[yellow]Session token expired.[/]\n\n"
                    "Please re-authenticate. Your cached credentials have been cleared.",
                    title="Session Expired",
                    border_style="yellow",
                )
            )
        else:
            console.print(
                Panel(
                    f"[red]AWS authentication failed:[/]\n{e}",
                    title="Authentication Error",
                    border_style="red",
                )
            )
        raise typer.Exit(1)


def print_graph_stats(graph: GraphEngine) -> None:
    """Print graph statistics in a rich table."""
    stats = graph.statistics()

    table = Table(title="Graph Statistics", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="dim")
    table.add_column("Value", justify="right")

    table.add_row("Total Resources", str(stats["total_resources"]))
    table.add_row("Total Dependencies", str(stats["total_dependencies"]))

    if stats["resources_by_type"]:
        table.add_section()
        for rtype, count in sorted(stats["resources_by_type"].items()):
            table.add_row(f"  {rtype}", str(count))

    console.print(table)

    if stats["has_cycles"]:
        console.print(
            "[yellow]Warning:[/] Dependency graph contains cycles!",
            style="bold yellow",
        )


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-V",
        help="Enable verbose logging",
    ),
) -> None:
    """RepliMap - AWS Environment Replication Tool."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)


@app.command()
def scan(
    profile: str | None = typer.Option(
        None,
        "--profile",
        "-p",
        help="AWS profile name (uses 'default' if not specified)",
    ),
    region: str | None = typer.Option(
        None,
        "--region",
        "-r",
        help="AWS region to scan (uses profile's region or us-east-1)",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output path for graph JSON (optional)",
    ),
    interactive: bool = typer.Option(
        False,
        "--interactive",
        "-i",
        help="Interactive mode - prompt for missing options",
    ),
    no_cache: bool = typer.Option(
        False,
        "--no-cache",
        help="Don't use cached credentials (re-authenticate)",
    ),
    # New graph-based selection options
    scope: str | None = typer.Option(
        None,
        "--scope",
        "-s",
        help="Selection scope: vpc:<id>, vpc-name:<pattern>, or VPC ID directly",
    ),
    entry: str | None = typer.Option(
        None,
        "--entry",
        "-e",
        help="Entry point: tag:Key=Value, <type>:<name>, or resource ID",
    ),
    config: Path | None = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to YAML selection config file",
    ),
    # Legacy filter options (still supported for backwards compatibility)
    vpc: str | None = typer.Option(
        None,
        "--vpc",
        help="[Legacy] Filter by VPC ID(s), comma-separated",
    ),
    vpc_name: str | None = typer.Option(
        None,
        "--vpc-name",
        help="[Legacy] Filter by VPC name pattern (supports wildcards)",
    ),
    types: str | None = typer.Option(
        None,
        "--types",
        "-t",
        help="[Legacy] Filter by resource types, comma-separated",
    ),
    tag: list[str] | None = typer.Option(
        None,
        "--tag",
        help="Select by tag (Key=Value), can be repeated",
    ),
    exclude_types: str | None = typer.Option(
        None,
        "--exclude-types",
        help="Exclude resource types, comma-separated",
    ),
    exclude_tag: list[str] | None = typer.Option(
        None,
        "--exclude-tag",
        help="Exclude by tag (Key=Value), can be repeated",
    ),
    exclude_patterns: str | None = typer.Option(
        None,
        "--exclude-patterns",
        help="Exclude by name patterns, comma-separated (supports wildcards)",
    ),
    # Scan cache options
    use_scan_cache: bool = typer.Option(
        False,
        "--cache",
        help="Use scan result cache for faster incremental scans",
    ),
    refresh_cache: bool = typer.Option(
        False,
        "--refresh-cache",
        help="Force refresh of scan cache (re-scan all resources)",
    ),
) -> None:
    """
    Scan AWS resources and build dependency graph.

    The region is determined in this order:
    1. --region flag (if provided)
    2. Profile's configured region (from ~/.aws/config)
    3. AWS_DEFAULT_REGION environment variable
    4. us-east-1 (fallback)

    Examples:
        replimap scan --profile prod
        replimap scan --profile prod --region us-west-2
        replimap scan -i  # Interactive mode
        replimap scan --profile prod --output graph.json

    Selection Examples (Graph-Based - Recommended):
        replimap scan --profile prod --scope vpc:vpc-12345678
        replimap scan --profile prod --scope vpc-name:Production*
        replimap scan --profile prod --entry alb:my-app-alb
        replimap scan --profile prod --entry tag:Application=MyApp
        replimap scan --profile prod --tag Environment=Production

    Filter Examples (Legacy, still supported):
        replimap scan --profile prod --vpc vpc-12345678
        replimap scan --profile prod --types vpc,subnet,ec2,rds
        replimap scan --profile prod --exclude-types sns,sqs

    Advanced Examples:
        replimap scan --profile prod --scope vpc:vpc-123 --exclude-patterns "test-*"
        replimap scan --profile prod --config selection.yaml

    Cache Examples:
        replimap scan --profile prod --cache  # Use cached results
        replimap scan --profile prod --cache --refresh-cache  # Force refresh
    """
    # Interactive mode - prompt for missing options
    if interactive:
        if not profile:
            available = get_available_profiles()
            console.print("\n[bold]Available AWS Profiles:[/]")
            for i, p in enumerate(available, 1):
                console.print(f"  {i}. {p}")
            console.print()
            profile = Prompt.ask(
                "Select profile",
                default="default",
                choices=available,
            )

    # Determine region: flag > profile config > env var > default
    effective_region = region
    region_source = "flag"

    if not effective_region:
        profile_region = get_profile_region(profile)
        if profile_region:
            effective_region = profile_region
            region_source = f"profile '{profile or 'default'}'"
        else:
            effective_region = "us-east-1"
            region_source = "default"

    if interactive and not region:
        console.print(
            f"\n[dim]Detected region: {effective_region} (from {region_source})[/]"
        )
        if not Confirm.ask("Use this region?", default=True):
            effective_region = Prompt.ask("Enter region", default=effective_region)
            region_source = "user input"

    # Check license and quotas
    manager = get_license_manager()
    tracker = get_usage_tracker()
    features = manager.current_features

    # Check scan frequency limit (NOT resource count - resources are unlimited!)
    gate_result = check_scan_allowed()
    if not gate_result.allowed:
        console.print(gate_result.prompt)
        raise typer.Exit(1)

    # Show plan badge with dev mode indicator
    if manager.is_dev_mode:
        plan_badge = "[yellow](dev mode)[/]"
    else:
        plan_badge = f"[dim]({manager.current_plan.value})[/]"

    console.print(
        Panel(
            f"[bold]RepliMap Scanner[/] v{__version__} {plan_badge}\n"
            f"Region: [cyan]{effective_region}[/] [dim](from {region_source})[/]"
            + (
                f"\nProfile: [cyan]{profile}[/]"
                if profile
                else "\nProfile: [cyan]default[/]"
            ),
            title="Configuration",
            border_style="cyan",
        )
    )

    # Get AWS session
    session = get_aws_session(profile, effective_region, use_cache=not no_cache)

    # Get account ID for cache key
    account_id = "unknown"
    if use_scan_cache:
        try:
            sts = session.client("sts")
            account_id = sts.get_caller_identity()["Account"]
        except Exception as e:
            logger.debug(f"Could not get AWS account ID for cache key: {e}")

    # Initialize graph
    graph = GraphEngine()

    # Load scan cache if enabled
    scan_cache: ScanCache | None = None
    cached_count = 0

    if use_scan_cache and not refresh_cache:
        scan_cache = ScanCache.load(
            account_id=account_id,
            region=effective_region,
        )
        stats = scan_cache.get_stats()
        cached_count = stats["total_resources"]
        if cached_count > 0:
            console.print(f"[dim]Loaded {cached_count} resources from cache[/]")
            # Populate graph from cache
            from replimap.core import populate_graph_from_cache

            populate_graph_from_cache(scan_cache, graph)

    # Run all registered scanners with progress
    # Use parallel scanning if license allows (ASYNC_SCANNING feature)
    use_parallel = features.has_feature(Feature.ASYNC_SCANNING)
    scan_mode = "parallel" if use_parallel else "sequential"
    scan_start = time.time()

    # If using cache and we have cached data, show that we're doing incremental scan
    if cached_count > 0:
        console.print("[dim]Performing incremental scan for updated resources...[/]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Scanning AWS resources ({scan_mode})...", total=None)
        results = run_all_scanners(
            session, effective_region, graph, parallel=use_parallel
        )
        progress.update(task, completed=True)
    scan_duration = time.time() - scan_start

    # Update scan cache with new results
    if use_scan_cache:
        if scan_cache is None:
            scan_cache = ScanCache(
                account_id=account_id,
                region=effective_region,
            )
        update_cache_from_graph(scan_cache, graph)
        cache_path = scan_cache.save()
        console.print(f"[dim]Scan cache saved to {cache_path}[/]")

    # Apply selection or filters
    # Check if new graph-based selection is being used
    use_new_selection = scope or entry or config

    if use_new_selection:
        # Load config from YAML if provided
        if config and config.exists():
            import yaml

            with open(config) as f:
                config_data = yaml.safe_load(f)
            selection_strategy = SelectionStrategy.from_dict(
                config_data.get("selection", {})
            )
        else:
            # Build strategy from CLI args
            selection_strategy = SelectionStrategy.from_cli_args(
                scope=scope,
                entry=entry,
                tag=tag,
                exclude_types=exclude_types,
                exclude_patterns=exclude_patterns,
            )

        if not selection_strategy.is_empty():
            console.print(
                f"\n[dim]Applying selection: {selection_strategy.describe()}[/]"
            )
            pre_select_count = graph.statistics()["total_resources"]

            # Apply graph-based selection
            selection_result = apply_selection(graph, selection_strategy)

            # Build subgraph from selection
            graph = build_subgraph_from_selection(graph, selection_result)

            post_select_count = graph.statistics()["total_resources"]
            console.print(
                f"[dim]Selected: {post_select_count} of {pre_select_count} resources "
                f"({selection_result.summary()['clone']} to clone, "
                f"{selection_result.summary()['reference']} to reference)[/]"
            )

    else:
        # Legacy filter support (backwards compatibility)
        scan_filter = ScanFilter.from_cli_args(
            vpc=vpc,
            vpc_name=vpc_name,
            types=types,
            tags=tag,
            exclude_types=exclude_types,
            exclude_tags=exclude_tag,
        )

        if not scan_filter.is_empty():
            console.print(f"\n[dim]Applying filters: {scan_filter.describe()}[/]")
            pre_filter_count = graph.statistics()["total_resources"]
            removed_count = apply_filter_to_graph(
                graph, scan_filter, retain_dependencies=True
            )
            console.print(
                f"[dim]Filtered: {pre_filter_count} → {pre_filter_count - removed_count} resources[/]"
            )

    # Get resource stats (no limits - resources are unlimited!)
    stats = graph.statistics()
    resource_count = stats["total_resources"]

    # Record usage
    tracker.record_scan(
        scan_id=str(uuid.uuid4()),
        region=effective_region,
        resource_count=resource_count,
        resource_types=stats.get("resources_by_type", {}),
        duration_seconds=scan_duration,
        profile=profile,
        success=True,
    )

    # Report results
    console.print()

    failed = [name for name, err in results.items() if err is not None]
    succeeded = [name for name, err in results.items() if err is None]

    if succeeded:
        console.print(f"[green]Completed:[/] {', '.join(succeeded)}")
    if failed:
        console.print(f"[red]Failed:[/] {', '.join(failed)}")
        for name, err in results.items():
            if err:
                console.print(f"  [red]-[/] {name}: {err}")

    # Print statistics
    console.print()
    print_graph_stats(graph)

    # Show remaining scans for FREE users
    remaining = get_scans_remaining()
    if remaining >= 0:
        console.print(
            f"\n[dim]Scans remaining this month: {remaining}/{features.max_scans_per_month}[/dim]"
        )

    # Save output if requested
    if output:
        graph.save(output)
        console.print(f"\n[green]Graph saved to[/] {output}")

    console.print()


@app.command()
def clone(
    profile: str | None = typer.Option(
        None,
        "--profile",
        "-p",
        help="AWS source profile name",
    ),
    region: str | None = typer.Option(
        None,
        "--region",
        "-r",
        help="AWS region to scan (uses profile's region or us-east-1)",
    ),
    output_dir: Path = typer.Option(
        Path("./terraform"),
        "--output-dir",
        "-o",
        help="Output directory for generated files",
    ),
    output_format: str = typer.Option(
        "terraform",
        "--format",
        "-f",
        help="Output format: 'terraform' (Free+), 'cloudformation' (Solo+), 'pulumi' (Pro+)",
    ),
    mode: str = typer.Option(
        "dry-run",
        "--mode",
        "-m",
        help="Mode: 'dry-run' (preview) or 'generate' (create files)",
    ),
    downsize: bool = typer.Option(
        True,
        "--downsize/--no-downsize",
        help="Enable instance downsizing for cost savings",
    ),
    rename_pattern: str | None = typer.Option(
        None,
        "--rename-pattern",
        help="Renaming pattern, e.g., 'prod:stage'",
    ),
    interactive: bool = typer.Option(
        False,
        "--interactive",
        "-i",
        help="Interactive mode - prompt for missing options",
    ),
    no_cache: bool = typer.Option(
        False,
        "--no-cache",
        help="Don't use cached credentials (re-authenticate)",
    ),
    dev_mode: bool = typer.Option(
        False,
        "--dev-mode",
        "--dev",
        help="[SOLO+] Optimize resources for dev/staging (generates right-sizer.auto.tfvars)",
    ),
    dev_strategy: str = typer.Option(
        "conservative",
        "--dev-strategy",
        help="Right-Sizer strategy: 'conservative' (default) or 'aggressive'",
    ),
) -> None:
    """
    Clone AWS environment to Infrastructure-as-Code.

    The region is determined in this order:
    1. --region flag (if provided)
    2. Profile's configured region (from ~/.aws/config)
    3. AWS_DEFAULT_REGION environment variable
    4. us-east-1 (fallback)

    Output formats:
    - terraform: Terraform HCL (Free tier and above)
    - cloudformation: AWS CloudFormation YAML (Solo plan and above)
    - pulumi: Pulumi Python (Pro plan and above)

    Examples:
        replimap clone --profile prod --mode dry-run
        replimap clone --profile prod --format terraform --mode generate
        replimap clone -i  # Interactive mode
        replimap clone --profile prod --format cloudformation -o ./cfn
    """
    from replimap.licensing.gates import FeatureNotAvailableError
    from replimap.renderers import CloudFormationRenderer, PulumiRenderer

    # Interactive mode - prompt for missing options
    if interactive:
        if not profile:
            available = get_available_profiles()
            console.print("\n[bold]Available AWS Profiles:[/]")
            for i, p in enumerate(available, 1):
                console.print(f"  {i}. {p}")
            console.print()
            profile = Prompt.ask(
                "Select profile",
                default="default",
                choices=available,
            )

    # Determine region: flag > profile config > env var > default
    effective_region = region
    region_source = "flag"

    if not effective_region:
        profile_region = get_profile_region(profile)
        if profile_region:
            effective_region = profile_region
            region_source = f"profile '{profile or 'default'}'"
        else:
            effective_region = "us-east-1"
            region_source = "default"

    if interactive and not region:
        console.print(
            f"\n[dim]Detected region: {effective_region} (from {region_source})[/]"
        )
        if not Confirm.ask("Use this region?", default=True):
            effective_region = Prompt.ask("Enter region", default=effective_region)

    # Validate output format
    valid_formats = ("terraform", "cloudformation", "pulumi")
    if output_format not in valid_formats:
        console.print(
            f"[red]Error:[/] Invalid format '{output_format}'. "
            f"Use one of: {', '.join(valid_formats)}"
        )
        raise typer.Exit(1)

    if interactive:
        console.print(f"\n[dim]Current format: {output_format}[/]")
        if not Confirm.ask("Use this format?", default=True):
            output_format = Prompt.ask(
                "Select format",
                default="terraform",
                choices=list(valid_formats),
            )

    # Get the appropriate renderer
    format_info = {
        "terraform": ("Terraform HCL", "Free+"),
        "cloudformation": ("CloudFormation YAML", "Solo+"),
        "pulumi": ("Pulumi Python", "Pro+"),
    }
    format_name, plan_required = format_info[output_format]

    manager = get_license_manager()
    plan_badge = f"[dim]({manager.current_plan.value})[/]"

    console.print(
        Panel(
            f"[bold]RepliMap Clone[/] v{__version__} {plan_badge}\n"
            f"Region: [cyan]{effective_region}[/] [dim](from {region_source})[/]\n"
            f"Profile: [cyan]{profile or 'default'}[/]\n"
            f"Format: [cyan]{format_name}[/] ({plan_required})\n"
            f"Mode: [cyan]{mode}[/]\n"
            f"Output: [cyan]{output_dir}[/]\n"
            f"Downsize: [cyan]{downsize}[/]"
            + (f"\nRename: [cyan]{rename_pattern}[/]" if rename_pattern else ""),
            title="Configuration",
            border_style="cyan",
        )
    )

    if mode not in ("dry-run", "generate"):
        console.print(
            f"[red]Error:[/] Invalid mode '{mode}'. Use 'dry-run' or 'generate'."
        )
        raise typer.Exit(1)

    # Get AWS session
    session = get_aws_session(profile, effective_region, use_cache=not no_cache)

    # Initialize graph
    graph = GraphEngine()

    # Run all scanners with progress
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Scanning AWS resources...", total=None)
        run_all_scanners(session, effective_region, graph)
        progress.update(task, completed=True)

    stats = graph.statistics()
    console.print(
        f"[green]Found[/] {stats['total_resources']} resources "
        f"with {stats['total_dependencies']} dependencies"
    )

    # Apply transformations
    console.print()

    # Determine if Right-Sizer will handle optimization
    # If Right-Sizer is active, skip legacy DownsizeTransformer to prevent conflict
    # (DownsizeTransformer would downsize resources, then Right-Sizer would see
    # already-downsized resources and have nothing to optimize)
    effective_downsize = downsize
    if dev_mode and output_format == "terraform":
        from replimap.licensing.gates import check_right_sizer_allowed

        rightsizer_result = check_right_sizer_allowed()
        if rightsizer_result.allowed:
            # Right-Sizer will handle optimization - skip DownsizeTransformer
            effective_downsize = False
            console.print(
                "[dim]ℹ️  DownsizeTransformer skipped (Right-Sizer will handle optimization)[/dim]"
            )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Applying transformations...", total=None)
        pipeline = create_default_pipeline(
            downsize=effective_downsize,
            rename_pattern=rename_pattern,
            sanitize=True,
        )
        graph = pipeline.execute(graph)
        progress.update(task, completed=True)

    console.print(f"[green]Applied[/] {len(pipeline)} transformers")

    # Select renderer based on format
    if output_format == "terraform":
        renderer = TerraformRenderer()
    elif output_format == "cloudformation":
        renderer = CloudFormationRenderer()
    else:  # pulumi
        renderer = PulumiRenderer()

    # Preview
    preview = renderer.preview(graph)

    # Show output files table
    console.print()
    table = Table(title="Output Files", show_header=True, header_style="bold cyan")
    table.add_column("File", style="dim")
    table.add_column("Resources", justify="right")

    for filename, resources in sorted(preview.items()):
        table.add_row(filename, str(len(resources)))

    console.print(table)

    if mode == "dry-run":
        console.print()
        console.print(
            Panel(
                "[yellow]This is a dry-run.[/]\n"
                "Use [bold]--mode generate[/] to create files.",
                border_style="yellow",
            )
        )
    else:
        console.print()
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(
                    f"Generating {format_name} files...", total=None
                )
                written = renderer.render(graph, output_dir)
                progress.update(task, completed=True)

            console.print(
                Panel(
                    f"[green]Generated {len(written)} files[/] in [bold]{output_dir}[/]",
                    border_style="green",
                )
            )

            # ═══════════════════════════════════════════════════════════════════
            # RIGHT-SIZER INTEGRATION (After Terraform generation)
            # ═══════════════════════════════════════════════════════════════════
            if dev_mode and output_format == "terraform":
                from replimap.cost.rightsizer import (
                    DowngradeStrategy,
                    RightSizerClient,
                    check_and_prompt_upgrade,
                    right_sizer_success_panel,
                )

                # Check license first
                if not check_and_prompt_upgrade():
                    # User doesn't have Solo+ license, prompt shown
                    console.print(
                        "\n[yellow]Right-Sizer skipped. Continuing with production defaults.[/yellow]"
                    )
                else:
                    console.print(
                        "\n[cyan]🔄 Analyzing resources for Right-Sizer optimization...[/cyan]\n"
                    )

                    try:
                        # Initialize client
                        rightsizer = RightSizerClient()

                        # Extract resource metadata from graph
                        all_resources = graph.get_all_resources()
                        summaries = rightsizer.extract_resources(
                            all_resources, effective_region
                        )

                        if not summaries:
                            console.print(
                                "[yellow]No rightsizable resources found (EC2, RDS, ElastiCache).[/yellow]"
                            )
                        else:
                            console.print(
                                f"[dim]Analyzing {len(summaries)} resources...[/dim]\n"
                            )

                            # Get suggestions from API
                            strategy = DowngradeStrategy(dev_strategy.lower())
                            result = rightsizer.get_suggestions(summaries, strategy)

                            if result.success and result.suggestions:
                                # 1. Display recommendations table
                                rightsizer.display_suggestions_table(result)

                                # 2. Generate and write tfvars file
                                tfvars_content = rightsizer.generate_tfvars_content(
                                    result.suggestions
                                )
                                tfvars_path = rightsizer.write_tfvars_file(
                                    str(output_dir), tfvars_content
                                )

                                # 3. Display success panel
                                console.print(
                                    right_sizer_success_panel(
                                        original_monthly=result.total_current_monthly,
                                        recommended_monthly=result.total_recommended_monthly,
                                        suggestions_count=result.resources_with_suggestions,
                                        skipped_count=result.resources_skipped,
                                        tfvars_filename=os.path.basename(tfvars_path),
                                    )
                                )

                            elif result.error_message:
                                console.print(
                                    f"\n[red]⚠️  Right-Sizer error: {result.error_message}[/red]"
                                )
                                console.print(
                                    "[yellow]Continuing with production defaults.[/yellow]"
                                )

                            else:
                                console.print(
                                    "[green]✓ All resources are already optimally sized![/green]"
                                )

                    except Exception as e:
                        # Graceful degradation - don't crash the whole clone
                        console.print(f"\n[red]⚠️  Right-Sizer error: {e}[/red]")
                        console.print(
                            "[yellow]Continuing with production defaults.[/yellow]"
                        )

        except FeatureNotAvailableError as e:
            console.print()
            console.print(
                Panel(
                    f"[red]Feature not available:[/] {e}\n\n"
                    f"Upgrade your plan to use {format_name} output:\n"
                    f"[bold]https://replimap.io/upgrade[/]",
                    title="Upgrade Required",
                    border_style="red",
                )
            )
            raise typer.Exit(1)

    console.print()


@app.command()
def load(
    input_file: Path = typer.Argument(
        ...,
        help="Path to graph JSON file",
    ),
) -> None:
    """
    Load and display a saved graph.

    Examples:
        replimap load graph.json
    """
    if not input_file.exists():
        console.print(f"[red]Error:[/] File not found: {input_file}")
        raise typer.Exit(1)

    graph = GraphEngine.load(input_file)

    console.print(
        Panel(
            f"Loaded graph from [bold]{input_file}[/]",
            title="Graph Loaded",
            border_style="green",
        )
    )

    # Print statistics
    print_graph_stats(graph)

    # Show resources table
    console.print()
    table = Table(
        title="Resources (first 20)", show_header=True, header_style="bold cyan"
    )
    table.add_column("Type", style="dim")
    table.add_column("ID")
    table.add_column("Dependencies", justify="right")

    # Use safe dependency order to handle cycles (e.g., mutual SG references)
    for resource in graph.get_safe_dependency_order()[:20]:
        deps = graph.get_dependencies(resource.id)
        table.add_row(
            str(resource.resource_type),
            resource.id,
            str(len(deps)) if deps else "-",
        )

    console.print(table)

    stats = graph.statistics()
    if stats["total_resources"] > 20:
        console.print(f"[dim]... and {stats['total_resources'] - 20} more[/]")

    console.print()


@app.command()
def profiles() -> None:
    """
    List available AWS profiles.

    Shows all configured AWS profiles from ~/.aws/config and ~/.aws/credentials.

    Examples:
        replimap profiles
    """
    available = get_available_profiles()

    table = Table(
        title="Available AWS Profiles", show_header=True, header_style="bold cyan"
    )
    table.add_column("Profile", style="cyan")
    table.add_column("Region", style="dim")
    table.add_column("Status")

    for profile_name in available:
        region = get_profile_region(profile_name) or "[dim]not set[/]"

        # Check if credentials are cached
        cached = get_cached_credentials(profile_name)
        if cached:
            status = "[green]cached[/]"
        else:
            status = "[dim]-[/]"

        table.add_row(profile_name, region, status)

    console.print(table)

    console.print()
    console.print("[dim]Tip: Use --profile <name> to select a profile[/]")
    console.print("[dim]Tip: Use --interactive or -i for guided setup[/]")
    console.print()


# Cache subcommand group
cache_app = typer.Typer(
    name="cache",
    help="Credential cache management",
    rich_markup_mode="rich",
    context_settings={"help_option_names": ["-h", "--help"]},
)
app.add_typer(cache_app, name="cache")


@cache_app.command("clear")
def cache_clear(
    profile: str | None = typer.Option(
        None,
        "--profile",
        "-p",
        help="Clear cache for specific profile (all if not specified)",
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip confirmation",
    ),
) -> None:
    """
    Clear cached AWS credentials.

    Examples:
        replimap cache clear
        replimap cache clear --profile prod
    """
    if not yes:
        if profile:
            confirm = Confirm.ask(f"Clear cached credentials for profile '{profile}'?")
        else:
            confirm = Confirm.ask("Clear all cached credentials?")
        if not confirm:
            console.print("[dim]Cancelled.[/]")
            raise typer.Exit(0)

    clear_credential_cache(profile)

    if profile:
        console.print(f"[green]Cleared cached credentials for profile '{profile}'[/]")
    else:
        console.print("[green]Cleared all cached credentials[/]")


@cache_app.command("status")
def cache_status() -> None:
    """
    Show credential cache status.

    Examples:
        replimap cache status
    """
    if not CREDENTIAL_CACHE_FILE.exists():
        console.print("[dim]No cached credentials.[/]")
        return

    try:
        with open(CREDENTIAL_CACHE_FILE) as f:
            cache = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        console.print("[dim]No cached credentials.[/]")
        return

    if not cache:
        console.print("[dim]No cached credentials.[/]")
        return

    table = Table(
        title="Cached Credentials", show_header=True, header_style="bold cyan"
    )
    table.add_column("Profile")
    table.add_column("Expires", style="dim")
    table.add_column("Status")

    now = datetime.now()
    for _cache_key, entry in cache.items():
        profile_name = entry.get("profile") or "default"
        expires_at = datetime.fromisoformat(entry["expires_at"])

        if now >= expires_at:
            status = "[red]expired[/]"
            expires_str = expires_at.strftime("%Y-%m-%d %H:%M")
        else:
            remaining = expires_at - now
            hours = remaining.seconds // 3600
            minutes = (remaining.seconds % 3600) // 60
            status = f"[green]valid ({hours}h {minutes}m remaining)[/]"
            expires_str = expires_at.strftime("%Y-%m-%d %H:%M")

        table.add_row(profile_name, expires_str, status)

    console.print(table)
    console.print()


# Scan cache subcommand group
scan_cache_app = typer.Typer(
    name="scan-cache",
    help="Scan result cache management",
    rich_markup_mode="rich",
    context_settings={"help_option_names": ["-h", "--help"]},
)
app.add_typer(scan_cache_app, name="scan-cache")


@scan_cache_app.command("status")
def scan_cache_status() -> None:
    """
    Show scan cache status for all regions.

    Examples:
        replimap scan-cache status
    """
    from replimap.core.cache import DEFAULT_CACHE_DIR

    if not DEFAULT_CACHE_DIR.exists():
        console.print("[dim]No scan cache found.[/]")
        return

    cache_files = list(DEFAULT_CACHE_DIR.glob("scan-*.json"))
    if not cache_files:
        console.print("[dim]No scan cache found.[/]")
        return

    table = Table(title="Scan Cache Status", show_header=True, header_style="bold cyan")
    table.add_column("Account")
    table.add_column("Region")
    table.add_column("Resources", justify="right")
    table.add_column("Last Updated", style="dim")

    total_resources = 0
    for cache_file in cache_files:
        try:
            with open(cache_file) as f:
                cache_data = json.load(f)

            metadata = cache_data.get("metadata", {})
            entries = cache_data.get("entries", {})

            account_id = metadata.get("account_id", "unknown")
            region = metadata.get("region", "unknown")
            resource_count = len(entries)
            total_resources += resource_count

            last_updated = metadata.get("last_updated", 0)
            if last_updated:
                updated_str = datetime.fromtimestamp(last_updated).strftime(
                    "%Y-%m-%d %H:%M"
                )
            else:
                updated_str = "unknown"

            # Truncate account ID for display
            account_display = (
                f"{account_id[:4]}...{account_id[-4:]}"
                if len(account_id) > 10
                else account_id
            )

            table.add_row(account_display, region, str(resource_count), updated_str)
        except (json.JSONDecodeError, KeyError):
            continue

    console.print(table)
    console.print(f"\n[dim]Total cached resources: {total_resources}[/]")
    console.print(f"[dim]Cache directory: {DEFAULT_CACHE_DIR}[/]")
    console.print()


@scan_cache_app.command("clear")
def scan_cache_clear(
    region: str | None = typer.Option(
        None,
        "--region",
        "-r",
        help="Clear cache for specific region only",
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip confirmation",
    ),
) -> None:
    """
    Clear scan result cache.

    Examples:
        replimap scan-cache clear
        replimap scan-cache clear --region us-east-1
    """
    from replimap.core.cache import DEFAULT_CACHE_DIR

    if not DEFAULT_CACHE_DIR.exists():
        console.print("[dim]No scan cache to clear.[/]")
        return

    cache_files = list(DEFAULT_CACHE_DIR.glob("scan-*.json"))
    if not cache_files:
        console.print("[dim]No scan cache to clear.[/]")
        return

    # Filter by region if specified
    files_to_delete = []
    for cache_file in cache_files:
        try:
            with open(cache_file) as f:
                cache_data = json.load(f)
            metadata = cache_data.get("metadata", {})
            if region is None or metadata.get("region") == region:
                files_to_delete.append(cache_file)
        except (json.JSONDecodeError, KeyError):
            files_to_delete.append(cache_file)  # Delete corrupt files

    if not files_to_delete:
        console.print(f"[dim]No cache found for region '{region}'.[/]")
        return

    if not yes:
        if region:
            confirm = Confirm.ask(
                f"Clear scan cache for region '{region}'? ({len(files_to_delete)} files)"
            )
        else:
            confirm = Confirm.ask(
                f"Clear all scan cache? ({len(files_to_delete)} files)"
            )
        if not confirm:
            console.print("[dim]Cancelled.[/]")
            raise typer.Exit(0)

    for cache_file in files_to_delete:
        cache_file.unlink()

    console.print(f"[green]Cleared {len(files_to_delete)} cache files.[/]")


@scan_cache_app.command("info")
def scan_cache_info(
    region: str = typer.Argument(
        ...,
        help="Region to show cache info for",
    ),
    account: str | None = typer.Option(
        None,
        "--account",
        "-a",
        help="AWS account ID (uses first found if not specified)",
    ),
) -> None:
    """
    Show detailed cache info for a region.

    Examples:
        replimap scan-cache info us-east-1
    """
    from replimap.core.cache import DEFAULT_CACHE_DIR

    if not DEFAULT_CACHE_DIR.exists():
        console.print("[dim]No scan cache found.[/]")
        raise typer.Exit(1)

    # Find cache file for region
    cache_file = None
    for cf in DEFAULT_CACHE_DIR.glob("scan-*.json"):
        try:
            with open(cf) as f:
                cache_data = json.load(f)
            metadata = cache_data.get("metadata", {})
            if metadata.get("region") == region:
                if account is None or metadata.get("account_id") == account:
                    cache_file = cf
                    break
        except (json.JSONDecodeError, KeyError):
            continue

    if cache_file is None:
        console.print(f"[red]No cache found for region '{region}'.[/]")
        raise typer.Exit(1)

    with open(cache_file) as f:
        cache_data = json.load(f)

    metadata = cache_data.get("metadata", {})
    entries = cache_data.get("entries", {})

    # Count by type
    type_counts: dict[str, int] = {}
    for entry in entries.values():
        resource = entry.get("resource", {})
        rtype = resource.get("resource_type", "unknown")
        type_counts[rtype] = type_counts.get(rtype, 0) + 1

    console.print(
        Panel(
            f"Account: [cyan]{metadata.get('account_id', 'unknown')}[/]\n"
            f"Region: [cyan]{metadata.get('region', 'unknown')}[/]\n"
            f"Total Resources: [bold]{len(entries)}[/]\n"
            f"Created: {datetime.fromtimestamp(metadata.get('created_at', 0)).strftime('%Y-%m-%d %H:%M')}\n"
            f"Last Updated: {datetime.fromtimestamp(metadata.get('last_updated', 0)).strftime('%Y-%m-%d %H:%M')}",
            title="Cache Info",
            border_style="cyan",
        )
    )

    if type_counts:
        console.print()
        table = Table(
            title="Cached Resources by Type",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Resource Type", style="dim")
        table.add_column("Count", justify="right")

        for rtype, count in sorted(
            type_counts.items(), key=lambda x: x[1], reverse=True
        ):
            table.add_row(rtype, str(count))

        console.print(table)

    console.print()


# License subcommand group
license_app = typer.Typer(
    name="license",
    help="License management commands",
    rich_markup_mode="rich",
    context_settings={"help_option_names": ["-h", "--help"]},
)
app.add_typer(license_app, name="license")


@license_app.command("activate")
def license_activate(
    license_key: str = typer.Argument(
        ...,
        help="License key (format: RM-XXXX-XXXX-XXXX-XXXX)",
    ),
) -> None:
    """
    Activate a license key.

    Examples:
        replimap license activate RM-7P0A-QB0G-ADFS-2TWU
    """
    manager = get_license_manager()

    try:
        license_obj = manager.activate(license_key)
        console.print(
            Panel(
                f"[green]License activated successfully![/]\n\n"
                f"Plan: [bold cyan]{license_obj.plan.value.upper()}[/]\n"
                f"Email: {license_obj.email}\n"
                f"Expires: {license_obj.expires_at.strftime('%Y-%m-%d') if license_obj.expires_at else 'Never'}",
                title="License Activated",
                border_style="green",
            )
        )
    except LicenseValidationError as e:
        console.print(
            Panel(
                f"[red]License activation failed:[/]\n{e}",
                title="Activation Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)


@license_app.command("status")
def license_status() -> None:
    """
    Show current license status.

    Examples:
        replimap license status
    """
    manager = get_license_manager()
    status, message = manager.validate()
    license_obj = manager.current_license
    features = manager.current_features

    # Status panel
    if status == LicenseStatus.VALID:
        status_color = "green"
        status_icon = "[green]Valid[/]"
    elif status == LicenseStatus.EXPIRED:
        status_color = "red"
        status_icon = "[red]Expired[/]"
    else:
        status_color = "yellow"
        status_icon = f"[yellow]{status.value}[/]"

    plan_name = manager.current_plan.value.upper()
    if license_obj:
        info = (
            f"Plan: [bold cyan]{plan_name}[/]\n"
            f"Status: {status_icon}\n"
            f"Email: {license_obj.email}\n"
            f"Expires: {license_obj.expires_at.strftime('%Y-%m-%d') if license_obj.expires_at else 'Never'}"
        )
    else:
        info = (
            f"Plan: [bold cyan]{plan_name}[/]\n"
            f"Status: {status_icon}\n"
            f"[dim]No license key activated. Using free tier.[/]"
        )

    console.print(
        Panel(
            info,
            title="License Status",
            border_style=status_color,
        )
    )

    # Features table
    console.print()
    table = Table(title="Plan Features", show_header=True, header_style="bold cyan")
    table.add_column("Feature", style="dim")
    table.add_column("Available", justify="center")

    feature_display = [
        (Feature.UNLIMITED_RESOURCES, "Unlimited Resources"),
        (Feature.ASYNC_SCANNING, "Async Scanning"),
        (Feature.MULTI_ACCOUNT, "Multi-Account Support"),
        (Feature.CUSTOM_TEMPLATES, "Custom Templates"),
        (Feature.WEB_DASHBOARD, "Web Dashboard"),
        (Feature.COLLABORATION, "Team Collaboration"),
        (Feature.SSO, "SSO Integration"),
        (Feature.AUDIT_LOGS, "Audit Logs"),
    ]

    for feature, display_name in feature_display:
        available = features.has_feature(feature)
        icon = "[green]Yes[/]" if available else "[dim]No[/]"
        table.add_row(display_name, icon)

    console.print(table)

    # Limits
    console.print()
    limits_table = Table(
        title="Usage Limits", show_header=True, header_style="bold cyan"
    )
    limits_table.add_column("Limit", style="dim")
    limits_table.add_column("Value", justify="right")

    limits_table.add_row(
        "Resources per Scan",
        str(features.max_resources_per_scan)
        if features.max_resources_per_scan
        else "Unlimited",
    )
    limits_table.add_row(
        "Scans per Month",
        str(features.max_scans_per_month)
        if features.max_scans_per_month
        else "Unlimited",
    )
    limits_table.add_row(
        "AWS Accounts",
        str(features.max_aws_accounts) if features.max_aws_accounts else "Unlimited",
    )

    console.print(limits_table)

    # Usage stats
    tracker = get_usage_tracker()
    stats = tracker.get_stats()

    if stats.total_scans > 0:
        console.print()
        usage_table = Table(
            title="Usage This Month", show_header=True, header_style="bold cyan"
        )
        usage_table.add_column("Metric", style="dim")
        usage_table.add_column("Value", justify="right")

        usage_table.add_row("Scans", str(stats.scans_this_month))
        usage_table.add_row("Resources Scanned", str(stats.resources_this_month))
        usage_table.add_row("Regions Used", str(len(stats.unique_regions)))

        console.print(usage_table)

    console.print()


@license_app.command("deactivate")
def license_deactivate(
    confirm: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip confirmation",
    ),
) -> None:
    """
    Deactivate the current license.

    Examples:
        replimap license deactivate --yes
    """
    manager = get_license_manager()

    if manager.current_license is None:
        console.print("[yellow]No license is currently active.[/]")
        raise typer.Exit(0)

    if not confirm:
        confirm = typer.confirm("Are you sure you want to deactivate your license?")
        if not confirm:
            console.print("[dim]Cancelled.[/]")
            raise typer.Exit(0)

    manager.deactivate()
    console.print("[green]License deactivated.[/] You are now on the free tier.")


@license_app.command("usage")
def license_usage() -> None:
    """
    Show detailed usage statistics.

    Examples:
        replimap license usage
    """
    tracker = get_usage_tracker()
    stats = tracker.get_stats()

    console.print(
        Panel(
            f"Total Scans: [bold]{stats.total_scans}[/]\n"
            f"Total Resources Scanned: [bold]{stats.total_resources_scanned}[/]\n"
            f"Unique Regions: [bold]{len(stats.unique_regions)}[/]\n"
            f"Last Scan: [bold]{stats.last_scan.strftime('%Y-%m-%d %H:%M') if stats.last_scan else 'Never'}[/]",
            title="Usage Overview",
            border_style="cyan",
        )
    )

    # Recent scans
    recent = tracker.get_recent_scans(10)
    if recent:
        console.print()
        table = Table(title="Recent Scans", show_header=True, header_style="bold cyan")
        table.add_column("Date", style="dim")
        table.add_column("Region")
        table.add_column("Resources", justify="right")
        table.add_column("Duration", justify="right")

        for scan in recent:
            table.add_row(
                scan.timestamp.strftime("%Y-%m-%d %H:%M"),
                scan.region,
                str(scan.resource_count),
                f"{scan.duration_seconds:.1f}s",
            )

        console.print(table)

    # Resource type breakdown
    if stats.resource_type_counts:
        console.print()
        type_table = Table(
            title="Resources by Type", show_header=True, header_style="bold cyan"
        )
        type_table.add_column("Resource Type", style="dim")
        type_table.add_column("Count", justify="right")

        for rtype, count in sorted(
            stats.resource_type_counts.items(),
            key=lambda x: x[1],
            reverse=True,
        ):
            type_table.add_row(rtype, str(count))

        console.print(type_table)

    console.print()


# =============================================================================
# AUDIT COMMAND
# =============================================================================


def _output_audit_json(
    results: CheckovResults,
    output_path: Path,
    region: str,
    profile: str | None,
    vpc_id: str | None,
) -> Path:
    """
    Output audit results as JSON.

    Args:
        results: Checkov scan results
        output_path: Base path for output (will change extension to .json)
        region: AWS region
        profile: AWS profile name
        vpc_id: VPC ID if specified

    Returns:
        Path to the generated JSON file
    """
    import json
    from datetime import datetime

    from replimap.audit.fix_suggestions import FIX_SUGGESTIONS
    from replimap.audit.soc2_mapping import get_soc2_mapping

    # Build SOC2 summary
    soc2_summary: dict = {}
    for f in results.findings:
        if f.check_result != "FAILED":
            continue
        mapping = get_soc2_mapping(f.check_id)
        if mapping:
            control = mapping.control
            if control not in soc2_summary:
                soc2_summary[control] = {
                    "control": control,
                    "category": mapping.category,
                    "count": 0,
                    "checks": [],
                }
            soc2_summary[control]["count"] += 1
            if f.check_id not in soc2_summary[control]["checks"]:
                soc2_summary[control]["checks"].append(f.check_id)

    # Build JSON output
    json_output = {
        "summary": {
            "score": results.score,
            "grade": results.grade,
            "passed": results.passed,
            "failed": results.failed,
            "skipped": results.skipped,
            "total": results.total,
            "high_severity_count": len(results.high_severity),
        },
        "metadata": {
            "account_id": "N/A",  # Would need to pass this through
            "region": region,
            "profile": profile,
            "vpc_id": vpc_id,
            "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        "severity_breakdown": {
            "critical": len(results.findings_by_severity["CRITICAL"]),
            "high": len(results.findings_by_severity["HIGH"]),
            "medium": len(results.findings_by_severity["MEDIUM"]),
            "low": len(results.findings_by_severity["LOW"]),
        },
        "findings": [
            {
                "check_id": f.check_id,
                "check_name": f.check_name,
                "severity": f.severity,
                "result": f.check_result,
                "resource": f.resource,
                "file_path": f.file_path,
                "line_range": list(f.file_line_range),
                "soc2_mapping": (
                    {
                        "control": m.control,
                        "category": m.category,
                        "description": m.description,
                    }
                    if (m := get_soc2_mapping(f.check_id))
                    else None
                ),
                "has_fix_suggestion": f.check_id in FIX_SUGGESTIONS,
                "guideline": f.guideline,
            }
            for f in results.findings
            if f.check_result == "FAILED"
        ],
        "soc2_summary": soc2_summary,
    }

    # Determine output path
    json_path = output_path.with_suffix(".json")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(json_output, indent=2))

    return json_path


def _generate_remediation(results: CheckovResults, output_dir: Path) -> None:
    """
    Generate Terraform remediation code from audit results.

    Args:
        results: Checkov scan results containing findings
        output_dir: Directory to write remediation files
    """
    from replimap.audit.remediation import RemediationGenerator

    console.print()
    console.print(
        Panel(
            "[bold blue]🔧 Generating Remediation Code[/bold blue]\n\n"
            f"Output: [cyan]{output_dir}[/]",
            border_style="blue",
        )
    )

    generator = RemediationGenerator(results.findings, output_dir)
    plan = generator.generate()

    if plan.files:
        # Write all files
        plan.write_all(output_dir)

        console.print()
        console.print(
            Panel(
                f"[bold]Remediation Generated[/bold]\n\n"
                f"[green]✓ Files:[/] {len(plan.files)}\n"
                f"[green]✓ Coverage:[/] {plan.coverage_percent}%\n"
                f"[dim]Skipped:[/] {plan.skipped_findings} (no template available)",
                title="🔧 Remediation Summary",
                border_style="green",
            )
        )

        # Show by severity
        by_severity = plan.files_by_severity()
        from replimap.audit.remediation.models import RemediationSeverity

        severity_info = []
        if by_severity[RemediationSeverity.CRITICAL]:
            severity_info.append(
                f"[red]CRITICAL: {len(by_severity[RemediationSeverity.CRITICAL])}[/]"
            )
        if by_severity[RemediationSeverity.HIGH]:
            severity_info.append(
                f"[orange1]HIGH: {len(by_severity[RemediationSeverity.HIGH])}[/]"
            )
        if by_severity[RemediationSeverity.MEDIUM]:
            severity_info.append(
                f"[yellow]MEDIUM: {len(by_severity[RemediationSeverity.MEDIUM])}[/]"
            )
        if by_severity[RemediationSeverity.LOW]:
            severity_info.append(
                f"[green]LOW: {len(by_severity[RemediationSeverity.LOW])}[/]"
            )

        if severity_info:
            console.print(f"  Fixes by severity: {' | '.join(severity_info)}")

        console.print()
        console.print(f"[green]✓ Remediation:[/] {output_dir.absolute()}")
        console.print(f"[green]✓ README:[/] {output_dir.absolute()}/README.md")

        if plan.has_imports:
            console.print(
                f"[yellow]⚠ Import script:[/] {output_dir.absolute()}/import.sh"
            )
            console.print()
            console.print(
                "[dim]Some fixes require terraform import. "
                "Run import.sh before terraform apply.[/dim]"
            )

        if plan.warnings:
            console.print()
            for warning in plan.warnings:
                console.print(f"[yellow]⚠[/] {warning}")
    else:
        console.print()
        console.print(
            "[yellow]No remediation templates available for the detected findings.[/yellow]"
        )


@app.command()
def audit(
    profile: str | None = typer.Option(
        None,
        "--profile",
        "-p",
        help="AWS profile name",
    ),
    region: str | None = typer.Option(
        None,
        "--region",
        "-r",
        help="AWS region to audit",
    ),
    vpc: str | None = typer.Option(
        None,
        "--vpc",
        "-v",
        help="VPC ID to scope the audit (optional)",
    ),
    output: Path = typer.Option(
        Path("./audit_report.html"),
        "--output",
        "-o",
        help="Path for HTML/JSON report",
    ),
    terraform_dir: Path = typer.Option(
        Path("./audit_output"),
        "--terraform-dir",
        "-t",
        help="Directory for generated Terraform files",
    ),
    open_report: bool = typer.Option(
        True,
        "--open/--no-open",
        help="Open report in browser after generation",
    ),
    no_cache: bool = typer.Option(
        False,
        "--no-cache",
        help="Don't use cached credentials",
    ),
    fail_on_high: bool = typer.Option(
        False,
        "--fail-on-high",
        help="Exit with code 1 if HIGH/CRITICAL issues found (for CI/CD)",
    ),
    fail_on_score: int | None = typer.Option(
        None,
        "--fail-on-score",
        help="Exit with code 1 if score below threshold (e.g., --fail-on-score 70)",
    ),
    output_format: str = typer.Option(
        "html",
        "--format",
        "-f",
        help="Output format: html or json",
    ),
    fix: bool = typer.Option(
        False,
        "--fix",
        help="Generate Terraform remediation code for findings",
    ),
    fix_output: Path = typer.Option(
        Path("./remediation"),
        "--fix-output",
        help="Directory for remediation Terraform files",
    ),
) -> None:
    """
    Run security audit on AWS infrastructure.

    Scans your AWS environment, generates a forensic Terraform snapshot,
    runs Checkov security analysis, and produces an HTML report with
    findings mapped to SOC2 controls.

    Requires Checkov to be installed: pip install checkov

    Examples:
        replimap audit --region us-east-1
        replimap audit -p prod -r ap-southeast-2 -v vpc-abc123
        replimap audit -r us-west-2 --no-open
        replimap audit -r us-east-1 --fail-on-high --no-open  # CI/CD mode
        replimap audit -r us-east-1 --fail-on-score 70 --no-open
        replimap audit -r us-east-1 --format json
        replimap audit -r us-east-1 --fix --fix-output ./remediation
    """
    import webbrowser

    from replimap.audit import AuditEngine, CheckovNotInstalledError

    # Determine region
    effective_region = region
    region_source = "flag"

    if not effective_region:
        profile_region = get_profile_region(profile)
        if profile_region:
            effective_region = profile_region
            region_source = f"profile '{profile or 'default'}'"
        else:
            effective_region = "us-east-1"
            region_source = "default"

    console.print()
    console.print(
        Panel(
            f"[bold blue]🔒 RepliMap Security Audit[/bold blue]\n\n"
            f"Region: [cyan]{effective_region}[/] [dim](from {region_source})[/]\n"
            f"Profile: [cyan]{profile or 'default'}[/]\n"
            + (f"VPC: [cyan]{vpc}[/]\n" if vpc else "")
            + f"Output: [cyan]{output}[/]\n"
            f"Terraform: [cyan]{terraform_dir}[/]",
            border_style="blue",
        )
    )

    # Get AWS session
    session = get_aws_session(profile, effective_region, use_cache=not no_cache)

    # Check Checkov is installed
    try:
        engine = AuditEngine(
            session=session,
            region=effective_region,
            profile=profile,
            vpc_id=vpc,
        )
    except CheckovNotInstalledError:
        console.print()
        console.print(
            Panel(
                "[red]Checkov is not installed.[/]\n\n"
                "Install Checkov with:\n"
                "  [bold]pipx install checkov[/]  (recommended)\n\n"
                "Or:\n"
                "  [bold]pip install checkov[/]",
                title="Missing Dependency",
                border_style="red",
            )
        )
        raise typer.Exit(1)

    # Run audit
    console.print()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Scanning AWS resources...", total=None)

        try:
            results, report_path = engine.run(
                output_dir=terraform_dir,
                report_path=output,
            )
        except Exception as e:
            progress.stop()
            console.print()
            console.print(
                Panel(
                    f"[red]Audit failed:[/]\n{e}",
                    title="Error",
                    border_style="red",
                )
            )
            raise typer.Exit(1)

        progress.update(task, completed=True)

    # Handle JSON output format
    if output_format.lower() == "json":
        json_path = _output_audit_json(results, output, effective_region, profile, vpc)
        console.print()
        console.print(f"[green]✓ JSON Report:[/] {json_path.absolute()}")
        console.print(f"[green]✓ Terraform:[/] {terraform_dir.absolute()}")
    else:
        # Display results for HTML format
        console.print()

        # Score with color
        if results.score >= 80:
            score_color = "green"
        elif results.score >= 60:
            score_color = "yellow"
        else:
            score_color = "red"

        console.print(
            Panel(
                f"[bold]Security Score: [{score_color}]{results.score}%[/] (Grade: {results.grade})[/bold]\n\n"
                f"[green]✓ Passed:[/] {results.passed}\n"
                f"[red]✗ Failed:[/] {results.failed}\n"
                f"[dim]○ Skipped:[/] {results.skipped}",
                title="📊 Audit Results",
                border_style=score_color,
            )
        )

        # High severity warning
        if results.high_severity:
            console.print()
            console.print(
                f"[bold red]⚠️  {len(results.high_severity)} High/Critical severity issues require attention![/bold red]"
            )
            for finding in results.high_severity[:5]:
                console.print(f"  [red]•[/] {finding.check_id}: {finding.check_name}")
            if len(results.high_severity) > 5:
                console.print(
                    f"  [dim]... and {len(results.high_severity) - 5} more[/dim]"
                )

        # Output paths
        console.print()
        console.print(f"[green]✓ Report:[/] {report_path.absolute()}")
        console.print(f"[green]✓ Terraform:[/] {terraform_dir.absolute()}")

        # Open report in browser (only for HTML format)
        if open_report:
            console.print()
            console.print("[dim]Opening report in browser...[/dim]")
            webbrowser.open(f"file://{report_path.absolute()}")

    # Generate remediation if requested (SOLO+ feature)
    if fix:
        fix_gate = check_audit_fix_allowed()
        if not fix_gate.allowed:
            console.print(fix_gate.prompt)
            raise typer.Exit(1)
        if results.findings:
            _generate_remediation(results, fix_output)

    # CI/CD checks (PRO+ feature)
    exit_code = 0

    if fail_on_high or fail_on_score is not None:
        ci_gate = check_audit_ci_mode_allowed()
        if not ci_gate.allowed:
            console.print(ci_gate.prompt)
            raise typer.Exit(1)

    if fail_on_high and results.high_severity:
        console.print()
        console.print(
            f"[bold red]❌ CI/CD FAILED: {len(results.high_severity)} HIGH/CRITICAL issues found[/bold red]"
        )
        for f in results.high_severity[:5]:
            console.print(f"   • {f.check_id}: {f.check_name}")
        if len(results.high_severity) > 5:
            console.print(f"   ... and {len(results.high_severity) - 5} more")
        exit_code = 1

    if fail_on_score is not None and results.score < fail_on_score:
        console.print()
        console.print(
            f"[bold red]❌ CI/CD FAILED: Score {results.score} below threshold {fail_on_score}[/bold red]"
        )
        exit_code = 1

    if exit_code == 0 and (fail_on_high or fail_on_score is not None):
        console.print()
        console.print("[bold green]✓ CI/CD PASSED[/bold green]")

    console.print()

    if exit_code != 0:
        raise typer.Exit(exit_code)


# =============================================================================
# GRAPH VISUALIZATION COMMAND
# =============================================================================


@app.command()
def graph(
    profile: str | None = typer.Option(
        None,
        "--profile",
        "-p",
        help="AWS profile name",
    ),
    region: str | None = typer.Option(
        None,
        "--region",
        "-r",
        help="AWS region to visualize",
    ),
    vpc: str | None = typer.Option(
        None,
        "--vpc",
        "-v",
        help="VPC ID to scope the visualization (optional)",
    ),
    output: Path = typer.Option(
        Path("./infrastructure_graph.html"),
        "--output",
        "-o",
        help="Path for output file",
    ),
    output_format: str = typer.Option(
        "html",
        "--format",
        "-f",
        help="Output format: html (interactive D3.js), mermaid, or json",
    ),
    open_graph: bool = typer.Option(
        True,
        "--open/--no-open",
        help="Open graph in browser after generation (HTML only)",
    ),
    no_cache: bool = typer.Option(
        False,
        "--no-cache",
        help="Don't use cached credentials",
    ),
    # Graph simplification options
    show_all: bool = typer.Option(
        False,
        "--all",
        "-a",
        help="Show all resources (disable filtering)",
    ),
    show_sg_rules: bool = typer.Option(
        False,
        "--sg-rules",
        help="Show security group rules (hidden by default)",
    ),
    show_routes: bool = typer.Option(
        False,
        "--routes",
        help="Show routes and route tables (hidden by default)",
    ),
    no_collapse: bool = typer.Option(
        False,
        "--no-collapse",
        help="Disable resource grouping (show all individual resources)",
    ),
    security_view: bool = typer.Option(
        False,
        "--security",
        help="Security-focused view (show SGs, IAM, KMS)",
    ),
) -> None:
    """
    Generate visual dependency graph of AWS infrastructure.

    Scans your AWS environment and generates an interactive visualization
    showing resources and their dependencies.

    By default, the graph is simplified for readability:
    - Noisy resources (SG rules, routes) are hidden
    - Large groups of similar resources are collapsed

    Output formats:
    - html: Interactive D3.js force-directed graph (default)
    - mermaid: Mermaid diagram syntax for documentation
    - json: Raw JSON data for integration

    Examples:
        replimap graph --region us-east-1
        replimap graph -p prod -r us-west-2 -v vpc-abc123
        replimap graph -r us-east-1 --all           # Show everything
        replimap graph -r us-east-1 --sg-rules      # Include SG rules
        replimap graph -r us-east-1 --routes        # Include routes
        replimap graph -r us-east-1 --no-collapse   # No grouping
        replimap graph -r us-east-1 --security      # Security focus
        replimap graph -r us-east-1 --format mermaid -o docs/graph.md
    """
    import webbrowser

    from replimap.graph import GraphVisualizer, OutputFormat

    # Determine region
    effective_region = region
    region_source = "flag"

    if not effective_region:
        profile_region = get_profile_region(profile)
        if profile_region:
            effective_region = profile_region
            region_source = f"profile '{profile or 'default'}'"
        else:
            effective_region = "us-east-1"
            region_source = "default"

    # Parse output format
    try:
        fmt = OutputFormat(output_format.lower())
    except ValueError:
        console.print(
            f"[red]Error:[/] Invalid format '{output_format}'. "
            f"Use one of: html, mermaid, json"
        )
        raise typer.Exit(1)

    # Build filter summary
    filter_parts = []
    if show_all:
        filter_parts.append("all resources")
    else:
        filter_parts.append("simplified")
        if show_sg_rules:
            filter_parts.append("+SG rules")
        if show_routes:
            filter_parts.append("+routes")
        if security_view:
            filter_parts.append("+security focus")
    if no_collapse:
        filter_parts.append("no grouping")

    filter_desc = ", ".join(filter_parts)

    console.print()
    console.print(
        Panel(
            f"[bold cyan]📊 RepliMap Graph Visualizer[/bold cyan]\n\n"
            f"Region: [cyan]{effective_region}[/] [dim](from {region_source})[/]\n"
            f"Profile: [cyan]{profile or 'default'}[/]\n"
            + (f"VPC: [cyan]{vpc}[/]\n" if vpc else "")
            + f"Format: [cyan]{fmt.value}[/]\n"
            f"Filter: [cyan]{filter_desc}[/]\n"
            f"Output: [cyan]{output}[/]",
            border_style="cyan",
        )
    )

    # Get AWS session
    session = get_aws_session(profile, effective_region, use_cache=not no_cache)

    # Configure filter based on options
    effective_show_sg_rules = show_sg_rules or security_view
    effective_show_routes = show_routes

    # Run visualization
    console.print()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Scanning AWS resources...", total=None)

        try:
            visualizer = GraphVisualizer(
                session=session,
                region=effective_region,
                profile=profile,
            )

            result = visualizer.generate(
                vpc_id=vpc,
                output_format=fmt,
                output_path=output,
                show_all=show_all,
                show_sg_rules=effective_show_sg_rules,
                show_routes=effective_show_routes,
                no_collapse=no_collapse,
            )

            progress.update(task, completed=True)
        except Exception as e:
            progress.stop()
            console.print()
            console.print(
                Panel(
                    f"[red]Graph generation failed:[/]\n{e}",
                    title="Error",
                    border_style="red",
                )
            )
            raise typer.Exit(1)

    # Output result
    console.print()
    if isinstance(result, Path):
        console.print(f"[green]✓ Graph generated:[/] {result.absolute()}")

        # Open in browser for HTML
        if open_graph and fmt == OutputFormat.HTML:
            console.print()
            console.print("[dim]Opening graph in browser...[/dim]")
            webbrowser.open(f"file://{result.absolute()}")
    else:
        # Content returned for stdout mode
        console.print(result)

    console.print()


# =============================================================================
# DRIFT DETECTION COMMAND
# =============================================================================


@app.command()
def drift(
    profile: str | None = typer.Option(
        None,
        "--profile",
        "-p",
        help="AWS profile name",
    ),
    region: str | None = typer.Option(
        None,
        "--region",
        "-r",
        help="AWS region to scan",
    ),
    state: Path | None = typer.Option(
        None,
        "--state",
        "-s",
        help="Path to terraform.tfstate file",
    ),
    state_bucket: str | None = typer.Option(
        None,
        "--state-bucket",
        help="S3 bucket for remote state",
    ),
    state_key: str | None = typer.Option(
        None,
        "--state-key",
        help="S3 key for remote state",
    ),
    vpc: str | None = typer.Option(
        None,
        "--vpc",
        "-v",
        help="VPC ID to scope the scan (optional)",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path (HTML or JSON)",
    ),
    output_format: str = typer.Option(
        "console",
        "--format",
        "-f",
        help="Output format: console, html, or json",
    ),
    fail_on_drift: bool = typer.Option(
        False,
        "--fail-on-drift",
        help="Exit with code 1 if any drift detected (for CI/CD)",
    ),
    fail_on_high: bool = typer.Option(
        False,
        "--fail-on-high",
        help="Exit with code 1 only for HIGH/CRITICAL drift (for CI/CD)",
    ),
    open_report: bool = typer.Option(
        True,
        "--open/--no-open",
        help="Open HTML report in browser after generation",
    ),
    no_cache: bool = typer.Option(
        False,
        "--no-cache",
        help="Don't use cached credentials",
    ),
) -> None:
    """
    Detect infrastructure drift between Terraform state and AWS.

    Compares your Terraform state file against the actual AWS resources
    to identify changes made outside of Terraform (console, CLI, etc).

    State Sources:
    - Local file: --state ./terraform.tfstate
    - S3 remote: --state-bucket my-bucket --state-key path/terraform.tfstate

    Output formats:
    - console: Rich terminal output (default)
    - html: Professional HTML report
    - json: Machine-readable JSON

    Examples:
        # Local state file
        replimap drift -r us-east-1 -s ./terraform.tfstate

        # Remote S3 state
        replimap drift -r us-east-1 --state-bucket my-tf-state --state-key prod/terraform.tfstate

        # Generate HTML report
        replimap drift -r us-east-1 -s ./terraform.tfstate -f html -o drift-report.html

        # CI/CD mode - fail on any drift
        replimap drift -r us-east-1 -s ./terraform.tfstate --fail-on-drift --no-open

        # CI/CD mode - fail only on high severity
        replimap drift -r us-east-1 -s ./terraform.tfstate --fail-on-high --no-open
    """
    import webbrowser

    from replimap.drift import DriftEngine, DriftReporter

    # Check drift feature access (Pro+ feature)
    drift_gate = check_drift_allowed()
    if not drift_gate.allowed:
        console.print(drift_gate.prompt)
        raise typer.Exit(1)

    # Determine region
    effective_region = region
    region_source = "flag"

    if not effective_region:
        profile_region = get_profile_region(profile)
        if profile_region:
            effective_region = profile_region
            region_source = f"profile '{profile or 'default'}'"
        else:
            effective_region = "us-east-1"
            region_source = "default"

    # Validate inputs
    if not state and not (state_bucket and state_key):
        console.print(
            Panel(
                "[red]Either --state or --state-bucket/--state-key is required.[/]\n\n"
                "Examples:\n"
                "  [bold]replimap drift -r us-east-1 -s ./terraform.tfstate[/]\n"
                "  [bold]replimap drift -r us-east-1 --state-bucket my-bucket --state-key prod/terraform.tfstate[/]",
                title="Missing State Source",
                border_style="red",
            )
        )
        raise typer.Exit(1)

    # Determine state source for display
    if state:
        state_display = str(state)
    else:
        state_display = f"s3://{state_bucket}/{state_key}"

    console.print()
    console.print(
        Panel(
            f"[bold orange1]RepliMap Drift Detector[/bold orange1]\n\n"
            f"Region: [cyan]{effective_region}[/] [dim](from {region_source})[/]\n"
            f"Profile: [cyan]{profile or 'default'}[/]\n"
            + (f"VPC: [cyan]{vpc}[/]\n" if vpc else "")
            + f"State: [cyan]{state_display}[/]\n"
            f"Format: [cyan]{output_format}[/]",
            border_style="orange1",
        )
    )

    # Get AWS session
    session = get_aws_session(profile, effective_region, use_cache=not no_cache)

    # Build remote backend config if using S3
    remote_backend = None
    if state_bucket and state_key:
        remote_backend = {
            "bucket": state_bucket,
            "key": state_key,
            "region": effective_region,
        }

    # Run drift detection
    console.print()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Detecting drift...", total=None)

        try:
            engine = DriftEngine(
                session=session,
                region=effective_region,
                profile=profile,
            )

            report = engine.detect(
                state_path=state,
                remote_backend=remote_backend,
                vpc_id=vpc,
            )

            progress.update(task, completed=True)

        except FileNotFoundError as e:
            progress.stop()
            console.print()
            console.print(
                Panel(
                    f"[red]State file not found:[/]\n{e}",
                    title="Error",
                    border_style="red",
                )
            )
            raise typer.Exit(1)
        except Exception as e:
            progress.stop()
            console.print()
            console.print(
                Panel(
                    f"[red]Drift detection failed:[/]\n{e}",
                    title="Error",
                    border_style="red",
                )
            )
            raise typer.Exit(1)

    # Generate output
    reporter = DriftReporter()

    # Console output (always show summary)
    if output_format == "console" or not output:
        console.print()
        if report.has_drift:
            console.print(
                Panel(
                    f"[bold red]DRIFT DETECTED[/bold red]\n\n"
                    f"[red]Total drifts:[/] {report.drifted_resources}\n"
                    f"[green]  Added (not in TF):[/] {report.added_resources}\n"
                    f"[red]  Removed (deleted):[/] {report.removed_resources}\n"
                    f"[yellow]  Modified:[/] {report.modified_resources}",
                    border_style="red",
                )
            )

            # Show high priority drifts
            critical_high = report.critical_drifts + report.high_drifts
            if critical_high:
                console.print()
                console.print("[bold red]High Priority Drifts:[/bold red]")
                for d in critical_high[:5]:
                    drift_icon = {"added": "+", "removed": "-", "modified": "~"}.get(
                        d.drift_type.value, "?"
                    )
                    console.print(
                        f"  [{d.severity.value.upper()}] [{drift_icon}] {d.resource_type}: {d.resource_id}"
                    )
                if len(critical_high) > 5:
                    console.print(f"  [dim]... and {len(critical_high) - 5} more[/dim]")
        else:
            console.print(
                Panel(
                    f"[bold green]NO DRIFT[/bold green]\n\n"
                    f"Your AWS resources match your Terraform state.\n"
                    f"Total resources checked: {report.total_resources}",
                    border_style="green",
                )
            )

    # HTML output
    if output_format == "html" or (output and output.suffix == ".html"):
        output_path = output or Path("./drift-report.html")
        reporter.to_html(report, output_path)
        console.print()
        console.print(f"[green]HTML report:[/] {output_path.absolute()}")
        if open_report:
            console.print("[dim]Opening report in browser...[/dim]")
            webbrowser.open(f"file://{output_path.absolute()}")

    # JSON output
    if output_format == "json" or (output and output.suffix == ".json"):
        output_path = output or Path("./drift-report.json")
        reporter.to_json(report, output_path)
        console.print()
        console.print(f"[green]JSON report:[/] {output_path.absolute()}")

    # CI/CD exit codes
    exit_code = 0

    if fail_on_drift and report.has_drift:
        console.print()
        console.print(
            f"[bold red]CI/CD FAILED: {report.drifted_resources} drift(s) detected[/bold red]"
        )
        exit_code = 1

    if fail_on_high and (report.critical_drifts or report.high_drifts):
        high_count = len(report.critical_drifts) + len(report.high_drifts)
        console.print()
        console.print(
            f"[bold red]CI/CD FAILED: {high_count} HIGH/CRITICAL drift(s)[/bold red]"
        )
        exit_code = 1

    if exit_code == 0 and (fail_on_drift or fail_on_high):
        console.print()
        console.print("[bold green]CI/CD PASSED: No significant drift[/bold green]")

    console.print()
    console.print(f"[dim]Scan completed in {report.scan_duration_seconds}s[/dim]")
    console.print()

    if exit_code != 0:
        raise typer.Exit(exit_code)


# =============================================================================
# DEPENDENCY EXPLORER COMMAND (formerly Blast Radius)
# =============================================================================


@app.command()
def deps(
    resource_id: str = typer.Argument(
        ...,
        help="Resource ID to analyze (e.g., vpc-12345, sg-abc123)",
    ),
    profile: str | None = typer.Option(
        None,
        "--profile",
        "-p",
        help="AWS profile name",
    ),
    region: str | None = typer.Option(
        None,
        "--region",
        "-r",
        help="AWS region to scan",
    ),
    vpc: str | None = typer.Option(
        None,
        "--vpc",
        "-v",
        help="VPC ID to scope the scan (optional)",
    ),
    max_depth: int = typer.Option(
        10,
        "--depth",
        "-d",
        help="Maximum depth to traverse",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path (HTML or JSON)",
    ),
    output_format: str = typer.Option(
        "console",
        "--format",
        "-f",
        help="Output format: console, tree, table, html, or json",
    ),
    open_report: bool = typer.Option(
        True,
        "--open/--no-open",
        help="Open HTML report in browser after generation",
    ),
    show_disclaimer: bool = typer.Option(
        True,
        "--disclaimer/--no-disclaimer",
        help="Show disclaimer about limitations",
    ),
    no_cache: bool = typer.Option(
        False,
        "--no-cache",
        help="Don't use cached credentials",
    ),
) -> None:
    """
    Explore dependencies for a resource.

    Shows what resources MAY be affected if you modify or delete a resource.
    This analysis is based on AWS API metadata only.

    IMPORTANT: Application-level dependencies (hardcoded IPs, DNS,
    config files) are NOT detected. Always validate all dependencies
    before making infrastructure changes.

    This is a Pro+ feature.

    Output formats:
    - console: Rich terminal output with summary (default)
    - tree: Tree view of dependencies
    - table: Table of affected resources
    - html: Interactive HTML report with D3.js visualization
    - json: Machine-readable JSON

    Examples:
        # Explore dependencies for a security group
        replimap deps sg-12345 -r us-east-1

        # Show as tree view
        replimap deps vpc-abc123 -r us-east-1 --format tree

        # Generate HTML visualization
        replimap deps i-xyz789 -r us-east-1 -f html -o deps.html

        # Limit depth of analysis
        replimap deps vpc-12345 -r us-east-1 --depth 3
    """
    import webbrowser

    from replimap.dependencies import (
        DISCLAIMER_SHORT,
        DependencyExplorerReporter,
        DependencyGraphBuilder,
        ImpactCalculator,
    )
    from replimap.licensing import check_deps_allowed

    # Check deps feature access (Pro+ feature)
    deps_gate = check_deps_allowed()
    if not deps_gate.allowed:
        console.print(deps_gate.prompt)
        raise typer.Exit(1)

    # Determine region
    effective_region = region
    region_source = "flag"

    if not effective_region:
        profile_region = get_profile_region(profile)
        if profile_region:
            effective_region = profile_region
            region_source = f"profile '{profile or 'default'}'"
        else:
            effective_region = "us-east-1"
            region_source = "default"

    console.print()
    console.print(
        Panel(
            f"[bold blue]Dependency Explorer[/bold blue]\n\n"
            f"Resource: [cyan]{resource_id}[/]\n"
            f"Region: [cyan]{effective_region}[/] [dim](from {region_source})[/]\n"
            f"Profile: [cyan]{profile or 'default'}[/]\n"
            + (f"VPC: [cyan]{vpc}[/]\n" if vpc else "")
            + f"Max Depth: [cyan]{max_depth}[/]\n\n"
            f"[dim]{DISCLAIMER_SHORT}[/dim]",
            border_style="blue",
        )
    )

    # Get AWS session
    session = get_aws_session(profile, effective_region, use_cache=not no_cache)

    # Scan resources
    console.print()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Scanning AWS resources...", total=None)

        try:
            # Create graph and run scanners
            graph = GraphEngine()
            run_all_scanners(
                session=session,
                region=effective_region,
                graph=graph,
            )

            # Apply VPC filter if specified
            if vpc:
                from replimap.core import ScanFilter, apply_filter_to_graph

                filter_config = ScanFilter(
                    vpc_ids=[vpc],
                    include_vpc_resources=True,
                )
                graph = apply_filter_to_graph(graph, filter_config)

            progress.update(task, description="Building dependency graph...")

            # Build dependency graph
            builder = DependencyGraphBuilder()
            dep_graph = builder.build_from_graph_engine(graph, effective_region)

            progress.update(task, description="Exploring dependencies...")

            # Explore dependencies
            calculator = ImpactCalculator(
                dep_graph,
                builder.get_nodes(),
                builder.get_edges(),
            )

            try:
                result = calculator.calculate_blast_radius(resource_id, max_depth)
            except ValueError:
                progress.stop()
                console.print()
                console.print(
                    Panel(
                        f"[red]Resource not found:[/] {resource_id}\n\n"
                        f"Make sure the resource ID is correct and exists in region {effective_region}.\n\n"
                        f"[dim]Available resources: {len(builder.get_nodes())}[/]",
                        title="Error",
                        border_style="red",
                    )
                )
                raise typer.Exit(1)

            progress.update(task, completed=True)

        except Exception as e:
            progress.stop()
            console.print()
            console.print(
                Panel(
                    f"[red]Dependency exploration failed:[/]\n{e}",
                    title="Error",
                    border_style="red",
                )
            )
            logger.exception("Dependency exploration failed")
            raise typer.Exit(1)

    # Report results
    reporter = DependencyExplorerReporter()
    console.print()

    if output_format == "tree":
        reporter.to_tree(result)
    elif output_format == "table":
        reporter.to_table(result)
    elif output_format == "json":
        output_path = output or Path("./deps.json")
        reporter.to_json(result, output_path)
    elif output_format == "html":
        output_path = output or Path("./deps.html")
        reporter.to_html(result, output_path)
        if open_report:
            console.print()
            console.print("[dim]Opening report in browser...[/dim]")
            webbrowser.open(f"file://{output_path.absolute()}")
    else:
        # Default: console output
        reporter.to_console(result)

    # Also export if output path specified but format is console
    if output and output_format == "console":
        if output.suffix == ".html":
            reporter.to_html(result, output)
            if open_report:
                console.print()
                console.print("[dim]Opening report in browser...[/dim]")
                webbrowser.open(f"file://{output.absolute()}")
        elif output.suffix == ".json":
            reporter.to_json(result, output)

    console.print()


# Backward compatibility alias for blast command
@app.command(hidden=True)
def blast(
    resource_id: str = typer.Argument(...),
    profile: str | None = typer.Option(None, "--profile", "-p"),
    region: str | None = typer.Option(None, "--region", "-r"),
    vpc: str | None = typer.Option(None, "--vpc", "-v"),
    max_depth: int = typer.Option(10, "--depth", "-d"),
    output: Path | None = typer.Option(None, "--output", "-o"),
    output_format: str = typer.Option("console", "--format", "-f"),
    open_report: bool = typer.Option(True, "--open/--no-open"),
    no_cache: bool = typer.Option(False, "--no-cache"),
) -> None:
    """Deprecated: Use 'replimap deps' instead."""
    console.print(
        "[yellow]Note: 'replimap blast' is deprecated. "
        "Use 'replimap deps' instead.[/yellow]\n"
    )
    deps(
        resource_id=resource_id,
        profile=profile,
        region=region,
        vpc=vpc,
        max_depth=max_depth,
        output=output,
        output_format=output_format,
        open_report=open_report,
        show_disclaimer=True,
        no_cache=no_cache,
    )


# =============================================================================
# COST ESTIMATOR COMMAND
# =============================================================================


@app.command()
def cost(
    profile: str | None = typer.Option(
        None,
        "--profile",
        "-p",
        help="AWS profile name",
    ),
    region: str | None = typer.Option(
        None,
        "--region",
        "-r",
        help="AWS region to scan",
    ),
    vpc: str | None = typer.Option(
        None,
        "--vpc",
        "-v",
        help="VPC ID to scope the scan (optional)",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path (HTML, JSON, CSV, or Markdown)",
    ),
    output_format: str = typer.Option(
        "console",
        "--format",
        "-f",
        help="Output format: console, table, html, json, csv, or markdown",
    ),
    open_report: bool = typer.Option(
        True,
        "--open/--no-open",
        help="Open HTML report in browser after generation",
    ),
    no_cache: bool = typer.Option(
        False,
        "--no-cache",
        help="Don't use cached credentials",
    ),
    acknowledge: bool = typer.Option(
        False,
        "--acknowledge",
        "-y",
        help="Acknowledge that this is an estimate only (skip confirmation for exports)",
    ),
) -> None:
    """
    Estimate monthly AWS costs for your infrastructure.

    ⚠️ IMPORTANT: These are rough estimates only. Actual AWS costs may differ
    by 20-40% depending on usage patterns, data transfer, and pricing agreements.

    Provides cost breakdown by category, resource, and region with
    optimization recommendations.

    This is a Pro+ feature.

    Output formats:
    - console: Rich terminal output with summary (default)
    - table: Full table of all resource costs
    - html: Interactive HTML report with charts
    - json: Machine-readable JSON
    - csv: Spreadsheet-compatible CSV
    - markdown: Markdown report

    Examples:
        # Estimate costs for current region
        replimap cost -r us-east-1

        # Estimate costs for a specific VPC
        replimap cost -r us-east-1 --vpc vpc-12345

        # Export to HTML report
        replimap cost -r us-east-1 -f html -o cost-report.html

        # Export with acknowledgment (skip prompt)
        replimap cost -r us-east-1 -f json -o costs.json --acknowledge
    """
    import webbrowser

    from replimap.cost import CostEstimator, CostReporter
    from replimap.licensing import check_cost_allowed

    # Check cost feature access (Pro+ feature)
    cost_gate = check_cost_allowed()
    if not cost_gate.allowed:
        console.print(cost_gate.prompt)
        raise typer.Exit(1)

    # Determine region
    effective_region = region
    region_source = "flag"

    if not effective_region:
        profile_region = get_profile_region(profile)
        if profile_region:
            effective_region = profile_region
            region_source = f"profile '{profile or 'default'}'"
        else:
            effective_region = "us-east-1"
            region_source = "default"

    console.print()
    console.print(
        Panel(
            f"[bold green]Cost Estimator[/bold green]\n\n"
            f"Region: [cyan]{effective_region}[/] [dim](from {region_source})[/]\n"
            f"Profile: [cyan]{profile or 'default'}[/]\n"
            + (f"VPC: [cyan]{vpc}[/]\n" if vpc else ""),
            border_style="green",
        )
    )

    # Get AWS session
    session = get_aws_session(profile, effective_region, use_cache=not no_cache)

    # Scan resources
    console.print()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Scanning AWS resources...", total=None)

        try:
            # Create graph and run scanners
            graph = GraphEngine()
            run_all_scanners(
                session=session,
                region=effective_region,
                graph=graph,
            )

            # Apply VPC filter if specified
            if vpc:
                from replimap.core import ScanFilter, apply_filter_to_graph

                filter_config = ScanFilter(
                    vpc_ids=[vpc],
                    include_vpc_resources=True,
                )
                graph = apply_filter_to_graph(graph, filter_config)

            progress.update(task, description="Estimating costs...")

            # Estimate costs
            estimator = CostEstimator(effective_region)
            estimate = estimator.estimate_from_graph_engine(graph)

            progress.update(task, completed=True)

        except Exception as e:
            progress.stop()
            console.print()
            console.print(
                Panel(
                    f"[red]Cost estimation failed:[/]\n{e}",
                    title="Error",
                    border_style="red",
                )
            )
            logger.exception("Cost estimation failed")
            raise typer.Exit(1)

    # Report results
    reporter = CostReporter()
    console.print()

    # Helper function to confirm export
    def confirm_export() -> bool:
        """Ask user to acknowledge estimate disclaimer before export."""
        if acknowledge:
            return True

        console.print()
        console.print("[yellow]⚠️ Before exporting, please acknowledge:[/yellow]")
        console.print("   This estimate is for planning purposes only.")
        console.print("   Actual costs may differ by 20-40%.")
        console.print("   Data transfer, API calls, and other fees are NOT included.")
        console.print()

        return typer.confirm("I understand this is an estimate only. Export anyway?")

    if output_format == "table":
        reporter.to_table(estimate)
    elif output_format == "json":
        output_path = output or Path("./cost-estimate.json")
        if confirm_export():
            reporter.to_json(estimate, output_path)
    elif output_format == "csv":
        output_path = output or Path("./cost-estimate.csv")
        if confirm_export():
            reporter.to_csv(estimate, output_path)
    elif output_format == "html":
        output_path = output or Path("./cost-estimate.html")
        if confirm_export():
            reporter.to_html(estimate, output_path)
            if open_report:
                console.print()
                console.print("[dim]Opening report in browser...[/dim]")
                webbrowser.open(f"file://{output_path.absolute()}")
    elif output_format in ("md", "markdown"):
        output_path = output or Path("./cost-estimate.md")
        if confirm_export():
            reporter.to_markdown(estimate, output_path)
    else:
        # Default: console output
        reporter.to_console(estimate)

    # Also export if output path specified but format is console
    if output and output_format == "console":
        if not confirm_export():
            console.print()
            return

        if output.suffix == ".html":
            reporter.to_html(estimate, output)
            if open_report:
                console.print()
                console.print("[dim]Opening report in browser...[/dim]")
                webbrowser.open(f"file://{output.absolute()}")
        elif output.suffix == ".json":
            reporter.to_json(estimate, output)
        elif output.suffix == ".csv":
            reporter.to_csv(estimate, output)
        elif output.suffix == ".md":
            reporter.to_markdown(estimate, output)

    console.print()


# =============================================================================
# UPGRADE COMMAND GROUP
# =============================================================================

upgrade_app = typer.Typer(
    help="Upgrade your RepliMap plan",
    no_args_is_help=True,
)
app.add_typer(upgrade_app, name="upgrade")


PRICING_URL = "https://replimap.dev/pricing"
CHECKOUT_URLS = {
    "solo": "https://replimap.dev/checkout/solo",
    "pro": "https://replimap.dev/checkout/pro",
    "team": "https://replimap.dev/checkout/team",
    "enterprise": "https://replimap.dev/contact",
}


def _show_upgrade_info(plan_name: str) -> None:
    """Show upgrade information and open browser."""
    import webbrowser

    from replimap.licensing.models import Plan, get_plan_features

    plan_map = {
        "solo": Plan.SOLO,
        "pro": Plan.PRO,
        "team": Plan.TEAM,
        "enterprise": Plan.ENTERPRISE,
    }

    plan = plan_map.get(plan_name.lower())
    if not plan:
        console.print(f"[red]Unknown plan: {plan_name}[/]")
        raise typer.Exit(1)

    config = get_plan_features(plan)

    console.print()
    console.print(
        Panel(
            f"[bold blue]{config.plan.value.upper()} Plan[/bold blue]\n\n"
            f"[dim]Price:[/] ${config.price_monthly}/month\n"
            f"       ${config.price_annual_monthly}/month (billed annually)",
            border_style="blue",
        )
    )

    console.print("\n[bold]Features:[/bold]\n")

    if config.max_scans_per_month is None:
        console.print("  [green]✓[/] Unlimited scans")

    if config.clone_download_enabled:
        console.print("  [green]✓[/] Download Terraform code")

    if config.audit_visible_findings is None:
        console.print("  [green]✓[/] Full audit reports")

    if config.audit_ci_mode:
        console.print("  [green]✓[/] CI/CD integration")

    if config.drift_enabled:
        console.print("  [green]✓[/] Drift detection")

    if config.drift_watch_enabled:
        console.print("  [green]✓[/] Drift watch mode")

    if config.drift_alerts_enabled:
        console.print("  [green]✓[/] Alert notifications")

    if config.cost_enabled:
        console.print("  [green]✓[/] Cost estimation")

    if config.deps_enabled:
        console.print("  [green]✓[/] Dependency exploration")

    if config.max_aws_accounts is None or config.max_aws_accounts > 1:
        accounts = (
            "Unlimited"
            if config.max_aws_accounts is None
            else str(config.max_aws_accounts)
        )
        console.print(f"  [green]✓[/] {accounts} AWS accounts")

    console.print()

    url = CHECKOUT_URLS.get(plan_name.lower(), PRICING_URL)
    console.print(f"[dim]Opening {url}...[/dim]")
    webbrowser.open(url)


@upgrade_app.command("solo")
def upgrade_solo() -> None:
    """Upgrade to Solo plan ($29/mo)."""
    _show_upgrade_info("solo")


@upgrade_app.command("pro")
def upgrade_pro() -> None:
    """Upgrade to Pro plan ($79/mo)."""
    _show_upgrade_info("pro")


@upgrade_app.command("team")
def upgrade_team() -> None:
    """Upgrade to Team plan ($149/mo)."""
    _show_upgrade_info("team")


@upgrade_app.command("enterprise")
def upgrade_enterprise() -> None:
    """Contact us for Enterprise plan."""
    _show_upgrade_info("enterprise")


@upgrade_app.callback(invoke_without_command=True)
def upgrade_default(ctx: typer.Context) -> None:
    """Show available plans."""
    if ctx.invoked_subcommand is None:
        import webbrowser

        console.print()
        console.print(
            Panel(
                "[bold blue]RepliMap Plans[/bold blue]\n\n"
                "[dim]Solo[/]     $29/mo  - Download code, full reports\n"
                "[dim]Pro[/]      $79/mo  - Drift detection, CI/CD mode\n"
                "[dim]Team[/]    $149/mo  - Watch mode, alerts, dependency explorer\n"
                "[dim]Enterprise[/] Custom - SSO, audit logs, SLA",
                border_style="blue",
            )
        )
        console.print()
        console.print("Usage: [bold]replimap upgrade <plan>[/]\n")
        console.print("  [dim]replimap upgrade solo[/]")
        console.print("  [dim]replimap upgrade pro[/]")
        console.print("  [dim]replimap upgrade team[/]")
        console.print()
        console.print(f"[dim]Opening {PRICING_URL}...[/dim]")
        webbrowser.open(PRICING_URL)


# =============================================================================
# REMEDIATE COMMAND
# =============================================================================


@app.command()
def remediate(
    input_file: Path = typer.Argument(
        ...,
        help="Path to audit JSON file (from: replimap audit --format json)",
    ),
    output: Path = typer.Option(
        Path("./remediation"),
        "--output",
        "-o",
        help="Directory for remediation Terraform files",
    ),
) -> None:
    """
    Generate Terraform remediation code from an audit JSON file.

    This command reads a JSON audit report (generated by `replimap audit --format json`)
    and generates Terraform code to fix the detected security issues.

    Examples:
        replimap remediate audit_report.json
        replimap remediate audit_report.json --output ./fixes
    """
    from replimap.audit.checkov_runner import CheckovFinding
    from replimap.audit.remediation import RemediationGenerator
    from replimap.audit.remediation.models import RemediationSeverity

    if not input_file.exists():
        console.print(f"[red]Error: File not found: {input_file}[/]")
        raise typer.Exit(1)

    console.print()
    console.print(
        Panel(
            f"[bold blue]🔧 RepliMap Remediation Generator[/bold blue]\n\n"
            f"Input: [cyan]{input_file}[/]\n"
            f"Output: [cyan]{output}[/]",
            border_style="blue",
        )
    )

    # Load the audit JSON
    try:
        data = json.loads(input_file.read_text())
    except json.JSONDecodeError as e:
        console.print(f"[red]Error: Invalid JSON file: {e}[/]")
        raise typer.Exit(1)

    # Extract findings from JSON
    findings: list[CheckovFinding] = []
    for f in data.get("findings", []):
        try:
            finding = CheckovFinding(
                check_id=f.get("check_id", "UNKNOWN"),
                check_name=f.get("check_name", "Unknown"),
                severity=f.get("severity", "MEDIUM"),
                resource=f.get("resource", "Unknown"),
                file_path=f.get("file_path", ""),
                file_line_range=tuple(f.get("line_range", [0, 0])),
                guideline=f.get("guideline"),
            )
            findings.append(finding)
        except Exception as e:
            console.print(f"[yellow]Warning: Skipping malformed finding: {e}[/]")

    if not findings:
        console.print("[yellow]No findings to remediate.[/yellow]")
        raise typer.Exit(0)

    console.print(f"\n[dim]Found {len(findings)} findings in audit report...[/dim]")

    # Generate remediation
    generator = RemediationGenerator(findings, output)
    plan = generator.generate()

    if plan.files:
        # Write all files
        plan.write_all(output)

        console.print()
        console.print(
            Panel(
                f"[bold]Remediation Generated[/bold]\n\n"
                f"[green]✓ Files:[/] {len(plan.files)}\n"
                f"[green]✓ Coverage:[/] {plan.coverage_percent}%\n"
                f"[dim]Skipped:[/] {plan.skipped_findings} (no template available)",
                title="🔧 Remediation Summary",
                border_style="green",
            )
        )

        # Show by severity
        by_severity = plan.files_by_severity()

        severity_info = []
        if by_severity[RemediationSeverity.CRITICAL]:
            severity_info.append(
                f"[red]CRITICAL: {len(by_severity[RemediationSeverity.CRITICAL])}[/]"
            )
        if by_severity[RemediationSeverity.HIGH]:
            severity_info.append(
                f"[orange1]HIGH: {len(by_severity[RemediationSeverity.HIGH])}[/]"
            )
        if by_severity[RemediationSeverity.MEDIUM]:
            severity_info.append(
                f"[yellow]MEDIUM: {len(by_severity[RemediationSeverity.MEDIUM])}[/]"
            )
        if by_severity[RemediationSeverity.LOW]:
            severity_info.append(
                f"[green]LOW: {len(by_severity[RemediationSeverity.LOW])}[/]"
            )

        if severity_info:
            console.print(f"  Fixes by severity: {' | '.join(severity_info)}")

        console.print()
        console.print(f"[green]✓ Remediation:[/] {output.absolute()}")
        console.print(f"[green]✓ README:[/] {output.absolute()}/README.md")

        if plan.has_imports:
            console.print(f"[yellow]⚠ Import script:[/] {output.absolute()}/import.sh")
            console.print()
            console.print(
                "[dim]Some fixes require terraform import. "
                "Run import.sh before terraform apply.[/dim]"
            )

        if plan.warnings:
            console.print()
            for warning in plan.warnings:
                console.print(f"[yellow]⚠[/] {warning}")
    else:
        console.print()
        console.print(
            "[yellow]No remediation templates available for the detected findings.[/yellow]"
        )

    console.print()


# =============================================================================
# SNAPSHOT COMMANDS
# =============================================================================

# Create snapshot subcommand group
snapshot_app = typer.Typer(help="Infrastructure snapshots for change tracking")


@snapshot_app.command("save")
def snapshot_save(
    profile: str | None = typer.Option(
        None,
        "--profile",
        "-p",
        help="AWS profile name",
    ),
    region: str | None = typer.Option(
        None,
        "--region",
        "-r",
        help="AWS region to snapshot",
    ),
    name: str = typer.Option(
        ...,
        "--name",
        "-n",
        help="Snapshot name",
    ),
    vpc: str | None = typer.Option(
        None,
        "--vpc",
        "-v",
        help="VPC ID to scope the snapshot (optional)",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Custom output file path",
    ),
    no_cache: bool = typer.Option(
        False,
        "--no-cache",
        help="Don't use cached credentials",
    ),
) -> None:
    """
    Save an infrastructure snapshot.

    Captures the current state of AWS resources for future comparison.
    Perfect for change management evidence and SOC2 compliance.

    Examples:
        replimap snapshot save -r us-east-1 -n "before-migration"
        replimap snapshot save -r us-east-1 -n "prod-baseline" -v vpc-abc123
        replimap snapshot save -r us-west-2 -n "weekly-backup" -o ./snapshots/weekly.json
    """
    from replimap.core import GraphEngine
    from replimap.scanners.base import run_all_scanners
    from replimap.snapshot import InfraSnapshot, ResourceSnapshot, SnapshotStore

    # Determine region
    effective_region = region
    region_source = "flag"

    if not effective_region:
        profile_region = get_profile_region(profile)
        if profile_region:
            effective_region = profile_region
            region_source = f"profile '{profile or 'default'}'"
        else:
            effective_region = "us-east-1"
            region_source = "default"

    console.print()
    console.print(
        Panel(
            f"[bold blue]📸 Creating Infrastructure Snapshot[/bold blue]\n\n"
            f"Name: [cyan]{name}[/]\n"
            f"Region: [cyan]{effective_region}[/] [dim](from {region_source})[/]\n"
            f"Profile: [cyan]{profile or 'default'}[/]"
            + (f"\nVPC: [cyan]{vpc}[/]" if vpc else ""),
            border_style="blue",
        )
    )

    # Get AWS session
    session = get_aws_session(profile, effective_region, use_cache=not no_cache)

    # Scan resources
    console.print()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Scanning infrastructure...", total=None)

        graph = GraphEngine()
        run_all_scanners(session, effective_region, graph)

        progress.update(task, completed=True)

    # Filter by VPC if specified
    if vpc:
        filtered_resources = []
        for resource in graph.get_all_resources():
            resource_vpc = resource.config.get("vpc_id") or resource.config.get("VpcId")
            if (
                resource_vpc == vpc
                or resource.id == vpc
                or vpc in resource.dependencies
            ):
                filtered_resources.append(resource)
        resources = filtered_resources
    else:
        resources = graph.get_all_resources()

    console.print(f"[dim]Found {len(resources)} resources[/dim]")

    # Create resource snapshots
    resource_snapshots = []
    for r in resources:
        rs = ResourceSnapshot(
            id=r.id,
            type=str(r.resource_type),
            arn=r.arn,
            name=r.original_name,
            region=effective_region,
            config=r.config,
            tags=r.tags,
        )
        resource_snapshots.append(rs)

    # Create snapshot
    snapshot = InfraSnapshot(
        name=name,
        region=effective_region,
        vpc_id=vpc,
        profile=profile or "default",
        resources=resource_snapshots,
    )

    # Save snapshot
    if output:
        snapshot.save(output)
        filepath = output
    else:
        store = SnapshotStore()
        filepath = store.save(snapshot)

    console.print()
    console.print(
        Panel(
            f"[bold]Snapshot Saved[/bold]\n\n"
            f"[green]✓ Name:[/] {snapshot.name}\n"
            f"[green]✓ Resources:[/] {snapshot.resource_count}\n"
            f"[green]✓ Created:[/] {snapshot.created_at[:19]}\n"
            f"[green]✓ Path:[/] {filepath}",
            title="📸 Snapshot Complete",
            border_style="green",
        )
    )

    # Show resource breakdown
    by_type = snapshot.resource_types()
    if by_type:
        console.print()
        console.print("[bold]Resources by Type:[/bold]")
        for rtype, count in sorted(by_type.items(), key=lambda x: -x[1])[:10]:
            console.print(f"  {rtype}: {count}")
        if len(by_type) > 10:
            console.print(f"  [dim]... and {len(by_type) - 10} more types[/dim]")


@snapshot_app.command("list")
def snapshot_list(
    region: str | None = typer.Option(
        None,
        "--region",
        "-r",
        help="Filter by region",
    ),
) -> None:
    """
    List saved snapshots.

    Examples:
        replimap snapshot list
        replimap snapshot list -r us-east-1
    """
    from replimap.snapshot import SnapshotStore

    store = SnapshotStore()
    snapshots = store.list(region=region)

    if not snapshots:
        console.print("[dim]No snapshots found[/dim]")
        return

    table = Table(title="Saved Snapshots")
    table.add_column("Name")
    table.add_column("Region")
    table.add_column("Resources", justify="right")
    table.add_column("Created")

    for snap in snapshots:
        table.add_row(
            snap["name"],
            snap.get("region", "-"),
            str(snap.get("resource_count", 0)),
            snap.get("created_at", "-")[:19],
        )

    console.print(table)


@snapshot_app.command("show")
def snapshot_show(
    name: str = typer.Argument(..., help="Snapshot name or path"),
) -> None:
    """
    Show snapshot details.

    Examples:
        replimap snapshot show "before-migration"
        replimap snapshot show ./snapshots/baseline.json
    """
    from replimap.snapshot import SnapshotStore

    store = SnapshotStore()
    snapshot = store.load(name)

    if not snapshot:
        console.print(f"[red]Snapshot not found: {name}[/red]")
        raise typer.Exit(1)

    console.print()
    console.print(f"[bold]Snapshot: {snapshot.name}[/bold]")
    console.print()
    console.print(f"Created: {snapshot.created_at[:19]}")
    console.print(f"Region: {snapshot.region}")
    console.print(f"Profile: {snapshot.profile}")
    if snapshot.vpc_id:
        console.print(f"VPC: {snapshot.vpc_id}")
    console.print(f"Resources: {snapshot.resource_count}")
    console.print(f"Version: {snapshot.version}")

    # Count by type
    by_type = snapshot.resource_types()
    if by_type:
        console.print()
        console.print("[bold]Resources by Type:[/bold]")
        for rtype, count in sorted(by_type.items(), key=lambda x: -x[1]):
            console.print(f"  {rtype}: {count}")


@snapshot_app.command("diff")
def snapshot_diff(
    profile: str | None = typer.Option(
        None,
        "--profile",
        "-p",
        help="AWS profile name",
    ),
    region: str | None = typer.Option(
        None,
        "--region",
        "-r",
        help="AWS region to scan",
    ),
    baseline: str = typer.Option(
        ...,
        "--baseline",
        "-b",
        help="Baseline snapshot name or path",
    ),
    current: str | None = typer.Option(
        None,
        "--current",
        "-c",
        help="Current snapshot name (default: scan current state)",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path",
    ),
    output_format: str = typer.Option(
        "console",
        "--format",
        "-f",
        help="Output format: console, json, markdown, html",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-V",
        help="Show detailed attribute changes",
    ),
    fail_on_change: bool = typer.Option(
        False,
        "--fail-on-change",
        help="Exit with code 1 if any changes detected (for CI/CD)",
    ),
    fail_on_critical: bool = typer.Option(
        False,
        "--fail-on-critical",
        help="Exit with code 1 only for critical/high changes (for CI/CD)",
    ),
    no_cache: bool = typer.Option(
        False,
        "--no-cache",
        help="Don't use cached credentials",
    ),
) -> None:
    """
    Compare snapshots to find infrastructure changes.

    Compare a baseline snapshot to either the current AWS state or another
    saved snapshot. Perfect for change management and SOC2 evidence.

    Examples:
        # Compare baseline to current AWS state
        replimap snapshot diff -r us-east-1 -b "before-migration"

        # Compare two saved snapshots
        replimap snapshot diff -r us-east-1 -b "v1" -c "v2"

        # Export for SOC2 evidence
        replimap snapshot diff -r us-east-1 -b "baseline" -o changes.md -f markdown

        # CI/CD mode - fail on any change
        replimap snapshot diff -r us-east-1 -b "baseline" --fail-on-change
    """
    from replimap.core import GraphEngine
    from replimap.scanners.base import run_all_scanners
    from replimap.snapshot import (
        InfraSnapshot,
        ResourceSnapshot,
        SnapshotDiffer,
        SnapshotReporter,
        SnapshotStore,
    )

    store = SnapshotStore()

    # Load baseline
    baseline_snap = store.load(baseline)
    if not baseline_snap:
        console.print(f"[red]Baseline snapshot not found: {baseline}[/red]")
        raise typer.Exit(1)

    # Use baseline's region if not specified
    if not region:
        region = baseline_snap.region

    console.print()
    console.print(
        Panel(
            f"[bold blue]📸 Comparing Infrastructure Snapshots[/bold blue]\n\n"
            f"Baseline: [cyan]{baseline_snap.name}[/] ({baseline_snap.created_at[:19]})\n"
            f"Region: [cyan]{region}[/]",
            border_style="blue",
        )
    )

    # Get current state
    if current:
        current_snap = store.load(current)
        if not current_snap:
            console.print(f"[red]Current snapshot not found: {current}[/red]")
            raise typer.Exit(1)
        console.print(
            f"Current: [cyan]{current_snap.name}[/] ({current_snap.created_at[:19]})"
        )
    else:
        # Scan current state
        console.print()
        console.print("[dim]Scanning current infrastructure...[/dim]")

        session = get_aws_session(profile, region, use_cache=not no_cache)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Scanning...", total=None)

            graph = GraphEngine()
            run_all_scanners(session, region, graph)

            progress.update(task, completed=True)

        # Filter by VPC if baseline was scoped
        if baseline_snap.vpc_id:
            filtered_resources = []
            for resource in graph.get_all_resources():
                resource_vpc = resource.config.get("vpc_id") or resource.config.get(
                    "VpcId"
                )
                if (
                    resource_vpc == baseline_snap.vpc_id
                    or resource.id == baseline_snap.vpc_id
                    or baseline_snap.vpc_id in resource.dependencies
                ):
                    filtered_resources.append(resource)
            resources = filtered_resources
        else:
            resources = graph.get_all_resources()

        resource_snapshots = [
            ResourceSnapshot(
                id=r.id,
                type=str(r.resource_type),
                arn=r.arn,
                name=r.original_name,
                region=region,
                config=r.config,
                tags=r.tags,
            )
            for r in resources
        ]

        current_snap = InfraSnapshot(
            name="current",
            region=region,
            vpc_id=baseline_snap.vpc_id,
            resources=resource_snapshots,
        )

    # Perform diff
    console.print()
    differ = SnapshotDiffer()
    diff_result = differ.diff(baseline_snap, current_snap)

    # Report
    reporter = SnapshotReporter()

    if output_format == "console":
        reporter.to_console(diff_result, verbose=verbose)
    elif output_format == "json":
        output_path = output or Path("snapshot_diff.json")
        reporter.to_json(diff_result, output_path)
    elif output_format in ("md", "markdown"):
        output_path = output or Path("snapshot_diff.md")
        reporter.to_markdown(diff_result, output_path)
    elif output_format == "html":
        output_path = output or Path("snapshot_diff.html")
        reporter.to_html(diff_result, output_path)
    else:
        reporter.to_console(diff_result, verbose=verbose)
        if output:
            reporter.to_json(diff_result, output)

    # CI/CD checks
    exit_code = 0

    if fail_on_change and diff_result.has_changes:
        console.print()
        console.print(
            f"[bold red]❌ CI/CD FAILED: {diff_result.total_changes} changes detected[/bold red]"
        )
        exit_code = 1

    if fail_on_critical and diff_result.has_critical_changes:
        console.print()
        console.print(
            f"[bold red]❌ CI/CD FAILED: {len(diff_result.critical_changes)} critical/high changes detected[/bold red]"
        )
        exit_code = 1

    if exit_code == 0 and (fail_on_change or fail_on_critical):
        console.print()
        console.print("[bold green]✓ CI/CD PASSED[/bold green]")

    console.print()

    if exit_code != 0:
        raise typer.Exit(exit_code)


@snapshot_app.command("delete")
def snapshot_delete(
    name: str = typer.Argument(..., help="Snapshot name to delete"),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Skip confirmation",
    ),
) -> None:
    """
    Delete a saved snapshot.

    Examples:
        replimap snapshot delete "old-snapshot"
        replimap snapshot delete "old-snapshot" --force
    """
    from replimap.snapshot import SnapshotStore

    store = SnapshotStore()

    if not store.exists(name):
        console.print(f"[red]Snapshot not found: {name}[/red]")
        raise typer.Exit(1)

    if not force:
        if not Confirm.ask(f"Delete snapshot '{name}'?"):
            console.print("[dim]Cancelled[/dim]")
            raise typer.Exit(0)

    if store.delete(name):
        console.print(f"[green]✓ Deleted snapshot: {name}[/green]")
    else:
        console.print(f"[red]Failed to delete snapshot: {name}[/red]")
        raise typer.Exit(1)


# Register snapshot command group
app.add_typer(snapshot_app, name="snapshot")


def cli() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    cli()
