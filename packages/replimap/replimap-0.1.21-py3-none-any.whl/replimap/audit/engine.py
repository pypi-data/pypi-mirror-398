"""
Audit Engine - Orchestrates the complete audit workflow.

Coordinates scanning, Terraform generation, Checkov analysis, and report generation.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from replimap.audit.checkov_runner import (
    CheckovNotInstalledError,
    CheckovResults,
    CheckovRunner,
)
from replimap.audit.renderer import AuditRenderer
from replimap.audit.reporter import AuditReporter, ReportMetadata
from replimap.core import GraphEngine
from replimap.scanners.base import run_all_scanners

if TYPE_CHECKING:
    from boto3 import Session

logger = logging.getLogger(__name__)


class AuditEngine:
    """
    Orchestrates the complete security audit workflow.

    Workflow:
    1. Scan AWS resources (existing Scanner)
    2. Generate Terraform in AUDIT mode (no transforms)
    3. Run Checkov security scan
    4. Generate HTML report

    Usage:
        engine = AuditEngine(session, region, profile="prod")
        results, report_path = engine.run(
            output_dir=Path("./audit_output"),
            report_path=Path("./audit_report.html")
        )
    """

    def __init__(
        self,
        session: Session,
        region: str,
        profile: str | None = None,
        vpc_id: str | None = None,
    ) -> None:
        """
        Initialize the audit engine.

        Args:
            session: Boto3 session for AWS access
            region: AWS region to audit
            profile: AWS profile name (for metadata)
            vpc_id: Optional VPC ID to scope the audit
        """
        self.session = session
        self.region = region
        self.profile = profile
        self.vpc_id = vpc_id
        self._account_id: str | None = None

    @property
    def account_id(self) -> str:
        """Get the AWS account ID (cached)."""
        if self._account_id is None:
            try:
                sts = self.session.client("sts")
                self._account_id = sts.get_caller_identity()["Account"]
            except Exception:
                self._account_id = "unknown"
        return self._account_id

    def run(
        self,
        output_dir: Path,
        report_path: Path,
        skip_scan: bool = False,
        graph: GraphEngine | None = None,
    ) -> tuple[CheckovResults, Path]:
        """
        Run the complete audit workflow.

        Args:
            output_dir: Directory for generated Terraform files
            report_path: Path for the HTML report
            skip_scan: Skip AWS scanning (use provided graph)
            graph: Pre-scanned graph (optional, used with skip_scan)

        Returns:
            Tuple of (CheckovResults, report_path)

        Raises:
            CheckovNotInstalledError: If Checkov is not installed
        """
        # Verify Checkov is available before starting
        if not CheckovRunner.is_installed():
            raise CheckovNotInstalledError()

        # Step 1: Scan AWS resources
        if skip_scan and graph is not None:
            logger.info("Using provided graph, skipping AWS scan")
        else:
            logger.info(f"Scanning AWS resources in {self.region}")
            graph = self._scan()

        # Step 2: Generate Terraform in AUDIT mode
        logger.info(f"Generating audit Terraform to {output_dir}")
        self._generate_terraform(graph, output_dir)

        # Step 3: Run Checkov scan
        logger.info("Running Checkov security scan")
        runner = CheckovRunner()
        results = runner.scan(output_dir)

        # Step 4: Generate HTML report
        logger.info(f"Generating audit report: {report_path}")
        report = self._generate_report(results, output_dir, report_path)

        logger.info(
            f"Audit complete: Score={results.score}% Grade={results.grade} "
            f"Passed={results.passed} Failed={results.failed}"
        )

        return results, report

    def _scan(self) -> GraphEngine:
        """
        Scan AWS resources.

        Returns:
            GraphEngine containing discovered resources
        """
        graph = GraphEngine()

        # Run all scanners
        run_all_scanners(self.session, self.region, graph)

        # If VPC filter specified, filter the graph
        if self.vpc_id:
            graph = self._filter_by_vpc(graph, self.vpc_id)

        logger.info(
            f"Scan complete: {graph.statistics()['total_resources']} resources found"
        )
        return graph

    def _filter_by_vpc(self, graph: GraphEngine, vpc_id: str) -> GraphEngine:
        """
        Filter graph to only include resources in the specified VPC.

        Args:
            graph: Full resource graph
            vpc_id: VPC ID to filter by

        Returns:
            Filtered graph
        """

        filtered = GraphEngine()

        # Get VPC resource
        vpc_resource = graph.get_resource(vpc_id)
        if vpc_resource:
            filtered.add_resource(vpc_resource)

        # Get all resources that belong to this VPC
        for resource in graph.iter_resources():
            # Skip if already added
            if filtered.get_resource(resource.id):
                continue

            # Check if resource belongs to this VPC
            config = resource.config
            resource_vpc = config.get("vpc_id") or config.get("VpcId")

            if resource_vpc == vpc_id:
                filtered.add_resource(resource)
                continue

            # Check dependencies
            if vpc_id in resource.dependencies:
                filtered.add_resource(resource)
                continue

        logger.info(
            f"VPC filter applied: {filtered.statistics()['total_resources']} resources in {vpc_id}"
        )
        return filtered

    def _generate_terraform(self, graph: GraphEngine, output_dir: Path) -> None:
        """
        Generate raw Terraform files for audit.

        Args:
            graph: Resource graph
            output_dir: Output directory
        """
        renderer = AuditRenderer(
            account_id=self.account_id,
            region=self.region,
        )
        renderer.render(graph, output_dir)

    def _generate_report(
        self,
        results: CheckovResults,
        hcl_dir: Path,
        report_path: Path,
    ) -> Path:
        """
        Generate HTML security report.

        Args:
            results: Checkov scan results
            hcl_dir: Directory with Terraform files
            report_path: Output path for report

        Returns:
            Path to generated report
        """
        metadata = ReportMetadata(
            account_id=self.account_id,
            region=self.region,
            profile=self.profile,
            vpc_id=self.vpc_id,
        )

        reporter = AuditReporter()
        return reporter.generate(results, hcl_dir, report_path, metadata)

    def scan_only(self) -> GraphEngine:
        """
        Scan AWS resources without running audit.

        Useful for previewing what will be audited.

        Returns:
            GraphEngine with discovered resources
        """
        return self._scan()

    def generate_only(self, graph: GraphEngine, output_dir: Path) -> dict[str, Path]:
        """
        Generate Terraform without running Checkov.

        Args:
            graph: Resource graph
            output_dir: Output directory

        Returns:
            Dictionary of written files
        """
        renderer = AuditRenderer(
            account_id=self.account_id,
            region=self.region,
        )
        return renderer.render(graph, output_dir)
