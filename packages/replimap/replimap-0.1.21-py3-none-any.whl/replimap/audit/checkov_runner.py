"""
Checkov Security Scanner Integration.

Wraps Checkov CLI to scan Terraform files and parse results.
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


class CheckovNotInstalledError(RuntimeError):
    """Raised when Checkov is not installed."""

    def __init__(self) -> None:
        super().__init__(
            "Checkov is not installed. Install with: pipx install checkov (recommended)\n"
            "Or: pip install checkov"
        )


class CheckovExecutionError(RuntimeError):
    """Raised when Checkov execution fails."""

    pass


@dataclass
class CheckovFinding:
    """Represents a single Checkov security finding."""

    check_id: str  # e.g., "CKV_AWS_19"
    check_name: str  # e.g., "Ensure all data stored in S3 is encrypted"
    severity: str  # LOW | MEDIUM | HIGH | CRITICAL | UNKNOWN
    resource: str  # e.g., "aws_s3_bucket.my_bucket"
    file_path: str  # e.g., "/path/to/s3.tf"
    file_line_range: tuple[int, int]  # (start_line, end_line)
    guideline: str | None = None  # URL to remediation docs

    @property
    def severity_order(self) -> int:
        """Return severity as integer for sorting (higher = more severe)."""
        order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "UNKNOWN": 0}
        return order.get(self.severity, 0)


@dataclass
class CheckovResults:
    """Aggregated results from a Checkov scan."""

    passed: int = 0
    failed: int = 0
    skipped: int = 0
    findings: list[CheckovFinding] = field(default_factory=list)
    scan_directory: Path | None = None
    checkov_version: str | None = None

    @property
    def total(self) -> int:
        """Total number of checks run."""
        return self.passed + self.failed + self.skipped

    @property
    def score(self) -> float:
        """
        Security score from 0-100.

        Calculated as: (passed / (passed + failed)) * 100
        Skipped checks are not included in the score.
        """
        total_evaluated = self.passed + self.failed
        if total_evaluated == 0:
            return 100.0
        return round((self.passed / total_evaluated) * 100, 1)

    @property
    def grade(self) -> str:
        """Letter grade based on score."""
        if self.score >= 90:
            return "A"
        if self.score >= 80:
            return "B"
        if self.score >= 70:
            return "C"
        if self.score >= 60:
            return "D"
        return "F"

    @property
    def high_severity(self) -> list[CheckovFinding]:
        """Return only HIGH and CRITICAL severity findings."""
        return [f for f in self.findings if f.severity in ("HIGH", "CRITICAL")]

    @property
    def findings_by_severity(self) -> dict[str, list[CheckovFinding]]:
        """Group findings by severity."""
        result: dict[str, list[CheckovFinding]] = {
            "CRITICAL": [],
            "HIGH": [],
            "MEDIUM": [],
            "LOW": [],
            "UNKNOWN": [],
        }
        for finding in self.findings:
            result[finding.severity].append(finding)
        return result


# Mapping of Checkov check IDs to severity levels
# Based on common security impact assessments
SEVERITY_MAPPING: dict[str, str] = {
    # CRITICAL - Immediate security risk, data exposure
    "CKV_AWS_20": "CRITICAL",  # S3 public access
    "CKV_AWS_53": "CRITICAL",  # S3 public ACL
    "CKV_AWS_54": "CRITICAL",  # S3 public bucket
    "CKV_AWS_55": "CRITICAL",  # S3 public policy
    "CKV_AWS_56": "CRITICAL",  # S3 public bucket
    "CKV_AWS_57": "CRITICAL",  # S3 public access
    "CKV_AWS_62": "CRITICAL",  # Lambda public
    "CKV_AWS_23": "HIGH",  # SG unrestricted ingress
    "CKV_AWS_24": "CRITICAL",  # SSH open to 0.0.0.0/0
    "CKV_AWS_25": "CRITICAL",  # RDP open to 0.0.0.0/0
    "CKV_AWS_40": "CRITICAL",  # IAM password policy
    "CKV_AWS_41": "CRITICAL",  # Root MFA
    "CKV_AWS_49": "HIGH",  # IAM least privilege
    # HIGH - Significant security concern
    "CKV_AWS_19": "HIGH",  # S3 encryption
    "CKV_AWS_3": "HIGH",  # EBS encryption
    "CKV_AWS_16": "HIGH",  # RDS encryption
    "CKV_AWS_17": "HIGH",  # RDS snapshot encryption
    "CKV_AWS_2": "HIGH",  # ALB HTTPS
    "CKV_AWS_103": "HIGH",  # ALB TLS 1.2
    "CKV_AWS_67": "HIGH",  # CloudTrail enabled
    "CKV_AWS_48": "HIGH",  # VPC Flow Logs
    "CKV_AWS_7": "HIGH",  # KMS key rotation
    "CKV_AWS_79": "HIGH",  # IMDSv2
    "CKV_AWS_83": "HIGH",  # ElastiCache transit encryption
    "CKV_AWS_84": "HIGH",  # ElastiCache at-rest encryption
    # MEDIUM - Should be addressed
    "CKV_AWS_18": "MEDIUM",  # S3 versioning
    "CKV_AWS_21": "MEDIUM",  # S3 logging
    "CKV_AWS_26": "MEDIUM",  # SNS encryption
    "CKV_AWS_27": "MEDIUM",  # SQS encryption
    "CKV_AWS_35": "MEDIUM",  # CloudTrail log validation
    "CKV_AWS_36": "MEDIUM",  # CloudTrail S3 logging
    "CKV_AWS_50": "MEDIUM",  # Lambda X-Ray
    "CKV_AWS_76": "MEDIUM",  # API Gateway logging
    "CKV_AWS_91": "MEDIUM",  # RDS enhanced monitoring
    "CKV_AWS_104": "MEDIUM",  # ALB access logs
    "CKV_AWS_128": "MEDIUM",  # RDS deletion protection
    "CKV_AWS_157": "MEDIUM",  # RDS multi-AZ
    # LOW - Best practice
    "CKV_AWS_4": "LOW",  # EBS snapshot encryption
    "CKV_AWS_5": "LOW",  # DocumentDB backup
    "CKV_AWS_15": "LOW",  # RDS multi-AZ
    "CKV_AWS_28": "LOW",  # DynamoDB backup
    "CKV_AWS_33": "LOW",  # KMS policy
    "CKV_AWS_52": "LOW",  # GuardDuty
    "CKV_AWS_64": "LOW",  # Redshift encryption
    "CKV_AWS_65": "LOW",  # ECR encryption
    "CKV_AWS_78": "LOW",  # Config rule
}


def _get_severity(check_id: str) -> str:
    """Get severity for a check ID, defaulting to MEDIUM if unknown."""
    return SEVERITY_MAPPING.get(check_id, "MEDIUM")


class CheckovRunner:
    """
    Runs Checkov security scanner on Terraform directories.

    Usage:
        runner = CheckovRunner()
        results = runner.scan(Path("./terraform"))
        print(f"Score: {results.score}%")
    """

    def __init__(self, timeout: int = 300) -> None:
        """
        Initialize the Checkov runner.

        Args:
            timeout: Maximum time in seconds for Checkov to run

        Raises:
            CheckovNotInstalledError: If Checkov is not installed
        """
        self.timeout = timeout
        self._checkov_path = shutil.which("checkov")

        if not self._checkov_path:
            raise CheckovNotInstalledError()

    def scan(self, directory: Path) -> CheckovResults:
        """
        Run Checkov scan on a directory.

        Args:
            directory: Path to directory containing Terraform files

        Returns:
            CheckovResults with pass/fail counts and findings

        Raises:
            CheckovExecutionError: If Checkov fails to execute
        """
        if not directory.exists():
            raise CheckovExecutionError(f"Directory does not exist: {directory}")

        logger.info(f"Running Checkov scan on {directory}")

        try:
            # Run checkov with JSON output
            # --quiet: Reduce verbosity
            # --compact: Compact output
            # -o json: JSON output format
            result = subprocess.run(  # noqa: S603
                [
                    "checkov",
                    "-d",
                    str(directory),
                    "-o",
                    "json",
                    "--quiet",
                    "--compact",
                    "--framework",
                    "terraform",
                ],
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )

            # Checkov returns exit code 1 when findings exist, which is expected
            # Parse the JSON output
            return self._parse_output(result.stdout, directory)

        except subprocess.TimeoutExpired:
            raise CheckovExecutionError(
                f"Checkov timed out after {self.timeout} seconds"
            )
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Checkov output: {e}")
            raise CheckovExecutionError(f"Failed to parse Checkov output: {e}")
        except Exception as e:
            raise CheckovExecutionError(f"Checkov execution failed: {e}")

    def _parse_output(self, output: str, directory: Path) -> CheckovResults:
        """
        Parse Checkov JSON output into CheckovResults.

        Args:
            output: Raw JSON output from Checkov
            directory: The scanned directory

        Returns:
            Parsed CheckovResults
        """
        results = CheckovResults(scan_directory=directory)

        if not output.strip():
            logger.warning("Checkov returned empty output")
            return results

        try:
            data = json.loads(output)
        except json.JSONDecodeError:
            # Try to extract JSON from output (sometimes has extra text)
            import re

            json_match = re.search(r"\[?\{.*\}\]?", output, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                logger.warning("Could not parse Checkov output as JSON")
                return results

        # Handle both single and multiple framework results
        if isinstance(data, list):
            check_results = data
        elif isinstance(data, dict):
            check_results = [data]
        else:
            return results

        for check_result in check_results:
            if not isinstance(check_result, dict):
                continue

            # Get summary counts
            summary = check_result.get("summary", {})
            results.passed += summary.get("passed", 0)
            results.failed += summary.get("failed", 0)
            results.skipped += summary.get("skipped", 0)

            # Get version info
            if not results.checkov_version:
                results.checkov_version = check_result.get("check_type")

            # Parse failed checks
            failed_checks = check_result.get("results", {}).get("failed_checks", [])
            for check in failed_checks:
                finding = self._parse_finding(check)
                if finding:
                    results.findings.append(finding)

        # Sort findings by severity (most severe first)
        results.findings.sort(key=lambda f: f.severity_order, reverse=True)

        logger.info(
            f"Checkov scan complete: {results.passed} passed, "
            f"{results.failed} failed, {results.skipped} skipped"
        )

        return results

    def _parse_finding(self, check: dict) -> CheckovFinding | None:
        """
        Parse a single failed check into a CheckovFinding.

        Args:
            check: Dictionary representing a failed check

        Returns:
            CheckovFinding or None if parsing fails
        """
        try:
            check_id = check.get("check_id", "UNKNOWN")
            file_line_range = check.get("file_line_range", [0, 0])

            # Ensure we have a valid tuple for line range
            if isinstance(file_line_range, list) and len(file_line_range) >= 2:
                line_range = (file_line_range[0], file_line_range[1])
            else:
                line_range = (0, 0)

            return CheckovFinding(
                check_id=check_id,
                check_name=check.get("check_name", "Unknown check"),
                severity=_get_severity(check_id),
                resource=check.get("resource", "Unknown resource"),
                file_path=check.get("file_path", ""),
                file_line_range=line_range,
                guideline=check.get("guideline"),
            )
        except Exception as e:
            logger.warning(f"Failed to parse finding: {e}")
            return None

    @staticmethod
    def is_installed() -> bool:
        """Check if Checkov is installed."""
        return shutil.which("checkov") is not None
