"""
Sanitization Transformer for RepliMap.

Removes sensitive data from resource configurations:
- Passwords, secrets, keys
- AWS account IDs (replaced with variables)
- Hardcoded ARNs
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any

from .base import BaseTransformer

if TYPE_CHECKING:
    from replimap.core import GraphEngine


logger = logging.getLogger(__name__)

# Patterns for sensitive field names
SENSITIVE_FIELD_PATTERNS = [
    r"password",
    r"secret",
    r"key",
    r"token",
    r"credential",
    r"auth",
    r"private",
    r"api_key",
    r"access_key",
    r"secret_key",
]

# Compile patterns for efficiency
SENSITIVE_REGEX = re.compile("|".join(SENSITIVE_FIELD_PATTERNS), re.IGNORECASE)

# Pattern for AWS account IDs (12 digits)
ACCOUNT_ID_PATTERN = re.compile(r"\b\d{12}\b")

# Pattern for ARNs
ARN_PATTERN = re.compile(r"arn:aws:[a-z0-9-]+:[a-z0-9-]*:\d{12}:[^\s\"',}]+")


class SanitizationTransformer(BaseTransformer):
    """
    Removes or replaces sensitive data in resource configurations.

    This transformer:
    1. Removes fields containing 'password', 'secret', 'key', etc.
    2. Replaces AWS account IDs with ${var.aws_account_id}
    3. Removes hardcoded ARNs or replaces account IDs within them

    The goal is to generate Terraform code that doesn't contain
    production secrets or hardcoded account-specific values.
    """

    name = "SanitizationTransformer"

    def __init__(
        self,
        remove_sensitive: bool = True,
        replace_account_ids: bool = True,
        account_id_replacement: str = "${var.aws_account_id}",
    ) -> None:
        """
        Initialize the sanitizer.

        Args:
            remove_sensitive: Whether to remove sensitive fields
            replace_account_ids: Whether to replace AWS account IDs
            account_id_replacement: String to replace account IDs with
        """
        self.remove_sensitive = remove_sensitive
        self.replace_account_ids = replace_account_ids
        self.account_id_replacement = account_id_replacement
        self._sanitized_count = 0
        self._replaced_count = 0

    def transform(self, graph: GraphEngine) -> GraphEngine:
        """
        Sanitize all resources in the graph.

        Args:
            graph: The GraphEngine to transform

        Returns:
            The same GraphEngine with sanitized configurations
        """
        self._sanitized_count = 0
        self._replaced_count = 0

        for resource in graph.iter_resources():
            # Sanitize config
            resource.config = self._sanitize_dict(resource.config)

            # Sanitize tags (but be less aggressive - keep Name tags)
            resource.tags = self._sanitize_tags(resource.tags)

            # Sanitize ARN
            if resource.arn:
                resource.arn = self._replace_account_id_in_string(resource.arn)

        logger.info(
            f"Sanitized {self._sanitized_count} sensitive fields, "
            f"replaced {self._replaced_count} account IDs"
        )

        return graph

    def _sanitize_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Recursively sanitize a dictionary.

        Args:
            data: Dictionary to sanitize

        Returns:
            Sanitized dictionary
        """
        result: dict[str, Any] = {}

        for key, value in data.items():
            # Check if this is a sensitive field
            if self.remove_sensitive and self._is_sensitive_key(key):
                logger.debug(f"Removing sensitive field: {key}")
                self._sanitized_count += 1
                continue

            # Recursively process nested structures
            if isinstance(value, dict):
                result[key] = self._sanitize_dict(value)
            elif isinstance(value, list):
                result[key] = self._sanitize_list(value)
            elif isinstance(value, str):
                result[key] = self._sanitize_string(value)
            else:
                result[key] = value

        return result

    def _sanitize_list(self, data: list[Any]) -> list[Any]:
        """
        Recursively sanitize a list.

        Args:
            data: List to sanitize

        Returns:
            Sanitized list
        """
        result: list[Any] = []

        for item in data:
            if isinstance(item, dict):
                result.append(self._sanitize_dict(item))
            elif isinstance(item, list):
                result.append(self._sanitize_list(item))
            elif isinstance(item, str):
                result.append(self._sanitize_string(item))
            else:
                result.append(item)

        return result

    def _sanitize_string(self, value: str) -> str:
        """
        Sanitize a string value.

        Args:
            value: String to sanitize

        Returns:
            Sanitized string
        """
        if self.replace_account_ids:
            value = self._replace_account_id_in_string(value)
        return value

    def _sanitize_tags(self, tags: dict[str, str]) -> dict[str, str]:
        """
        Sanitize tags dictionary.

        More conservative than config sanitization - we want to keep
        most tags but still check for secrets.

        Args:
            tags: Tags dictionary

        Returns:
            Sanitized tags
        """
        result = {}

        for key, value in tags.items():
            # Check for obvious secret values in tags
            if self.remove_sensitive and self._looks_like_secret_value(value):
                logger.debug(f"Removing tag with secret value: {key}")
                self._sanitized_count += 1
                continue

            # Replace account IDs in tag values
            if self.replace_account_ids:
                value = self._replace_account_id_in_string(value)

            result[key] = value

        return result

    def _is_sensitive_key(self, key: str) -> bool:
        """Check if a key name indicates sensitive data."""
        return bool(SENSITIVE_REGEX.search(key))

    def _looks_like_secret_value(self, value: str) -> bool:
        """
        Check if a value looks like a secret.

        Heuristics:
        - Contains patterns like "sk_", "pk_", "AKIA" (AWS keys)
        - High entropy random strings
        """
        secret_prefixes = ["sk_", "pk_", "AKIA", "ASIA"]
        return any(value.startswith(prefix) for prefix in secret_prefixes)

    def _replace_account_id_in_string(self, value: str) -> str:
        """
        Replace AWS account IDs in a string.

        Args:
            value: String that may contain account IDs

        Returns:
            String with account IDs replaced
        """

        # Replace in ARNs first (more specific)
        def replace_arn(match: re.Match) -> str:
            arn = match.group(0)
            new_arn = ACCOUNT_ID_PATTERN.sub(self.account_id_replacement, arn)
            if new_arn != arn:
                self._replaced_count += 1
            return new_arn

        result = ARN_PATTERN.sub(replace_arn, value)

        # Then replace standalone account IDs
        # Be careful not to replace things that look like timestamps or other numbers
        if ACCOUNT_ID_PATTERN.search(result):
            # Only replace if it looks like an account ID context
            # (e.g., after : or / in an ARN-like string)
            result = re.sub(
                r"(:|/|^)(\d{12})(?=:|/|$|\s)",
                lambda m: m.group(1) + self.account_id_replacement,
                result,
            )

        return result
