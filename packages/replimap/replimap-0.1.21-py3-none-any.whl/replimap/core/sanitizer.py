"""
Security-Critical Sanitization Layer for RepliMap.

This middleware MUST run between Scanner and Graph/Cache to redact
sensitive data BEFORE storage. This is distinct from the Transformer
which runs later during Terraform generation.

The difference:
- This module: Runs IMMEDIATELY after scan, before cache/graph storage
- Transformer: Runs during clone/export, operates on already-stored data

CRITICAL: If you skip this middleware, sensitive data like EC2 UserData,
Lambda environment variables, and connection strings will be stored
in the cache files on disk.

PERFORMANCE: Uses targeted approach - only scans high-risk fields
to avoid O(N*M) regex scanning of all fields.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

REDACTED = "[REDACTED]"

# Valid base64-encoded placeholder for UserData fields
# Decodes to: "#!/bin/bash\necho 'REDACTED BY REPLIMAP - Replace with actual user data'"
REDACTED_USERDATA_BASE64 = "IyEvYmluL2Jhc2gKZWNobyAnUkVEQUNURUQgQlkgUkVQTElNQVAgLSBSZXBsYWNlIHdpdGggYWN0dWFsIHVzZXIgZGF0YSc="

# Fields that require base64-encoded redaction (UserData, etc.)
BASE64_FIELDS: frozenset[str] = frozenset(
    [
        "userdata",
        "user_data",
        "userData",
        "UserData",
    ]
)

# Fields that ALWAYS contain secrets - redact entire value
HIGH_RISK_FIELDS: frozenset[str] = frozenset(
    [
        # EC2
        "userdata",
        "user_data",
        "userData",
        "UserData",
        # Lambda/ECS
        "environment",
        "Environment",
        "secrets",
        "Secrets",
        # Database
        "password",
        "Password",
        "master_password",
        "MasterPassword",
        "MasterUserPassword",
        "connectionstring",
        "connectionString",
        "ConnectionString",
        # Generic secrets
        "privatekey",
        "private_key",
        "PrivateKey",
        "credentials",
        "Credentials",
    ]
)

# Fields that MIGHT contain secrets - scan content
MEDIUM_RISK_FIELDS: frozenset[str] = frozenset(
    [
        "policy",
        "Policy",
        "PolicyDocument",
        "template",
        "Template",
        "TemplateBody",
        "script",
        "Script",
        "command",
        "Command",
        "commands",
        "Commands",
        "bootstrap",
        "Bootstrap",
    ]
)

# Fields that are SAFE - never scan (performance optimization)
SAFE_FIELDS: frozenset[str] = frozenset(
    [
        # IDs
        "arn",
        "Arn",
        "ARN",
        "id",
        "Id",
        "ID",
        "instanceId",
        "InstanceId",
        "vpcId",
        "VpcId",
        "subnetId",
        "SubnetId",
        "securityGroupId",
        "SecurityGroupId",
        "GroupId",
        "groupId",
        # Status/State
        "status",
        "Status",
        "State",
        "state",
        # Types
        "type",
        "Type",
        "InstanceType",
        "instanceType",
        "ResourceType",
        # Location
        "region",
        "Region",
        "availabilityZone",
        "AvailabilityZone",
        "az",
        "AZ",
        # Timestamps
        "createTime",
        "CreateTime",
        "LaunchTime",
        "launchTime",
        "modifyTime",
        "ModifyTime",
        # Tags (user-controlled but typically safe)
        "tags",
        "Tags",
        # Network basics
        "cidrBlock",
        "CidrBlock",
        "cidr_block",
        "ipAddress",
        "IpAddress",
        "PrivateIpAddress",
        "PublicIpAddress",
    ]
)

# Patterns for content scanning (only used on medium-risk fields)
SECRET_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),  # AWS Access Key ID
    re.compile(r"ASIA[0-9A-Z]{16}"),  # AWS Temporary Access Key
    re.compile(r"(?i)(password|passwd|pwd)\s*[=:]\s*\S+"),  # Password assignments
    re.compile(
        r"(?i)(secret|api_key|apikey|api-key)\s*[=:]\s*\S+"
    ),  # Secret assignments
    re.compile(
        r"(?i)(postgres|mysql|mongodb|redis)://[^@\s]+@"
    ),  # DB connection strings
    re.compile(r"(?i)sk[-_]live[-_][a-zA-Z0-9]+"),  # Stripe live keys
    re.compile(r"(?i)sk[-_]test[-_][a-zA-Z0-9]+"),  # Stripe test keys
    re.compile(r"(?i)ghp_[a-zA-Z0-9]+"),  # GitHub personal tokens
    re.compile(r"(?i)gho_[a-zA-Z0-9]+"),  # GitHub OAuth tokens
    re.compile(r"(?i)xox[baprs]-[a-zA-Z0-9-]+"),  # Slack tokens
    re.compile(r"-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"),  # Private keys
]

# Suspicious key patterns (for unknown fields)
SUSPICIOUS_KEY_PATTERNS = [
    "password",
    "secret",
    "key",
    "token",
    "credential",
    "auth",
    "private",
    "apikey",
    "api_key",
]


@dataclass
class SanitizationResult:
    """Result of sanitization operation."""

    data: Any
    redacted_count: int = 0
    redacted_fields: list[str] = field(default_factory=list)
    skipped_fields: int = 0  # Performance metric


class Sanitizer:
    """
    Sanitizes sensitive data from AWS API responses.

    Performance-optimized: Only scans fields likely to contain secrets.
    This is O(N) where N is the number of fields, not O(N*M) where M
    is the number of regex patterns.

    Usage:
        sanitizer = Sanitizer()
        result = sanitizer.sanitize(aws_response)
        clean_data = result.data

        if result.redacted_count > 0:
            logger.info(f"Redacted {result.redacted_count} sensitive fields")
    """

    def __init__(self) -> None:
        """Initialize the sanitizer."""
        self._redacted_fields: list[str] = []
        self._redacted_count: int = 0
        self._skipped_count: int = 0

    def sanitize(self, data: Any, path: str = "") -> Any:
        """
        Recursively sanitize data structure.

        Args:
            data: Data to sanitize (dict, list, or scalar)
            path: Current path for logging (e.g., "Instance.UserData")

        Returns:
            Sanitized data with secrets redacted
        """
        if isinstance(data, dict):
            return self._sanitize_dict(data, path)
        elif isinstance(data, list):
            return [self.sanitize(item, f"{path}[{i}]") for i, item in enumerate(data)]
        else:
            return data

    def _sanitize_dict(self, data: dict, path: str) -> dict:
        """Sanitize a dictionary."""
        result = {}

        for key, value in data.items():
            current_path = f"{path}.{key}" if path else key

            # HIGH RISK: Always redact entire value
            if key in HIGH_RISK_FIELDS or key.lower() in {
                f.lower() for f in HIGH_RISK_FIELDS
            }:
                if value:  # Don't redact empty values
                    result[key] = self._redact_high_risk(value, current_path)
                else:
                    result[key] = value

            # MEDIUM RISK: Scan content for secrets
            elif key in MEDIUM_RISK_FIELDS or key.lower() in {
                f.lower() for f in MEDIUM_RISK_FIELDS
            }:
                result[key] = self._scan_and_redact(value, current_path)

            # SAFE: Skip entirely (performance optimization)
            elif key in SAFE_FIELDS or key.lower() in {f.lower() for f in SAFE_FIELDS}:
                self._skipped_count += 1
                result[key] = value

            # UNKNOWN: Recurse but check key name for suspicion
            else:
                if isinstance(value, (dict, list)):
                    result[key] = self.sanitize(value, current_path)
                else:
                    # Check if key NAME looks suspicious
                    if self._is_suspicious_key(key):
                        if value:
                            result[key] = REDACTED
                            self._record_redaction(current_path)
                        else:
                            result[key] = value
                    else:
                        result[key] = value

        return result

    def _redact_high_risk(self, value: Any, path: str) -> Any:
        """Redact high-risk fields entirely."""
        self._record_redaction(path)

        # Check if this is a UserData field that needs valid base64
        path_lower = path.lower()
        is_userdata = any(field.lower() in path_lower for field in BASE64_FIELDS)

        if isinstance(value, dict):
            # For Environment.Variables, redact each value but keep keys
            # This preserves the structure for debugging
            if any(k in value for k in ["Variables", "variables"]):
                vars_key = "Variables" if "Variables" in value else "variables"
                return {vars_key: dict.fromkeys(value.get(vars_key, {}), REDACTED)}
            # For other dicts, just replace entirely
            return REDACTED
        elif isinstance(value, str):
            # UserData fields need valid base64 to avoid terraform apply errors
            if is_userdata:
                return REDACTED_USERDATA_BASE64
            return REDACTED
        elif isinstance(value, list):
            return REDACTED
        return REDACTED

    def _scan_and_redact(self, value: Any, path: str) -> Any:
        """Scan medium-risk fields for secret patterns."""
        if isinstance(value, str):
            for pattern in SECRET_PATTERNS:
                if pattern.search(value):
                    self._record_redaction(path)
                    return REDACTED
            return value
        elif isinstance(value, dict):
            return self.sanitize(value, path)
        elif isinstance(value, list):
            return [
                self._scan_and_redact(item, f"{path}[{i}]")
                for i, item in enumerate(value)
            ]
        return value

    def _is_suspicious_key(self, key: str) -> bool:
        """Check if key name suggests sensitive content."""
        key_lower = key.lower()
        return any(s in key_lower for s in SUSPICIOUS_KEY_PATTERNS)

    def _record_redaction(self, path: str) -> None:
        """Record a redaction for logging."""
        self._redacted_count += 1
        self._redacted_fields.append(path)

    def get_result(self, data: Any) -> SanitizationResult:
        """
        Sanitize data and return result with metrics.

        This is the preferred entry point as it provides metrics
        about what was sanitized.

        Args:
            data: Data to sanitize

        Returns:
            SanitizationResult with sanitized data and metrics
        """
        self._redacted_count = 0
        self._redacted_fields = []
        self._skipped_count = 0

        sanitized = self.sanitize(data)

        return SanitizationResult(
            data=sanitized,
            redacted_count=self._redacted_count,
            redacted_fields=self._redacted_fields.copy(),
            skipped_fields=self._skipped_count,
        )


def sanitize_resource_config(config: dict[str, Any]) -> dict[str, Any]:
    """
    Convenience function to sanitize a resource configuration dict.

    Args:
        config: Resource configuration from AWS API

    Returns:
        Sanitized configuration
    """
    sanitizer = Sanitizer()
    result = sanitizer.get_result(config)

    if result.redacted_count > 0:
        logger.debug(
            f"Sanitized {result.redacted_count} sensitive fields: "
            f"{result.redacted_fields[:5]}{'...' if len(result.redacted_fields) > 5 else ''}"
        )

    return result.data


def sanitize_scan_response(
    response: dict[str, Any], service: str = "unknown"
) -> dict[str, Any]:
    """
    Sanitize an AWS API response before caching.

    This should be called immediately after receiving data from AWS
    and BEFORE storing in cache or graph.

    Args:
        response: Raw AWS API response
        service: AWS service name (for logging)

    Returns:
        Sanitized response safe for storage
    """
    sanitizer = Sanitizer()
    result = sanitizer.get_result(response)

    if result.redacted_count > 0:
        logger.info(
            f"[{service}] Redacted {result.redacted_count} sensitive fields "
            f"from scan response"
        )

    return result.data
