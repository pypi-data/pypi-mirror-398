"""
Smart Name Generator for RepliMap.

Generates deterministic, AWS-compliant resource names using hash-based
naming to ensure consistency across scans.

The Seven Laws of Sovereign Code:
1. Determinism is Absolute - Same input MUST yield same output. Always.
2. Entropy is the Enemy - Manual maintenance lists grow stale daily.

This module implements Law 1 by generating names based on resource AWS IDs
(immutable) rather than scan order (non-deterministic).
"""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from replimap.core.config import RepliMapConfig

logger = logging.getLogger(__name__)


# AWS Resource Name Length Limits
# LEVEL 2 INSIGHT: This is still a hardcoded list!
# We keep a MINIMAL core set and use CONSERVATIVE defaults for unknown types.
# Users can override via .replimap.yaml config file.
AWS_NAME_LIMITS: dict[str, int] = {
    # Only the most common resources with SHORT limits
    # Unknown resources use conservative default (32)
    "aws_elb": 32,
    "aws_alb": 32,
    "aws_lb": 32,
    "aws_elasticache_cluster": 50,
    "aws_rds_cluster": 63,
    "aws_db_instance": 63,
    "aws_s3_bucket": 63,
    "aws_lambda_function": 64,
    "aws_iam_role": 64,
    "aws_iam_policy": 128,
    "aws_sqs_queue": 80,
    "aws_sns_topic": 256,
    "aws_dynamodb_table": 255,
    "aws_kinesis_stream": 128,
    "aws_cloudwatch_log_group": 512,
    # CONSERVATIVE DEFAULT for unknown types
    # Better to be too short (truncate) than too long (fail)
    "_default": 32,  # Changed from 64 to 32 for safety!
}


@dataclass
class NameGeneratorConfig:
    """Configuration for the name generator."""

    hash_length: int = 8
    limits: dict[str, int] = field(default_factory=lambda: AWS_NAME_LIMITS.copy())
    # Base62 characters for denser hash encoding
    base62_chars: str = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


class SmartNameGenerator:
    """
    Generate deterministic, AWS-compliant resource names.

    Level 2 Improvements:
    - Conservative defaults (32 chars) for unknown resources
    - User-configurable overrides via .replimap.yaml
    - Minimal hardcoded list (only short-limit resources)

    The $100 Bet: Would I bet $100 that this generates the same name
    for the same resource across multiple scans? YES.

    Usage:
        generator = SmartNameGenerator()

        # ELB with 32 char limit
        name = generator.generate(
            resource_id="arn:aws:elasticloadbalancing:...",
            original_name="my-very-long-application-load-balancer",
            resource_type="aws_lb"
        )
        # Result: "my_very_long_applic_a1B2c3D4" (32 chars)
    """

    def __init__(
        self,
        config: NameGeneratorConfig | None = None,
        user_config: RepliMapConfig | None = None,
    ) -> None:
        """
        Initialize the name generator.

        Args:
            config: Generator configuration (defaults provided)
            user_config: User configuration from .replimap.yaml
        """
        self.config = config or NameGeneratorConfig()

        # Load user overrides from .replimap.yaml
        if user_config:
            self._apply_user_config(user_config)

    def _apply_user_config(self, user_config: RepliMapConfig) -> None:
        """Apply user-defined name limits from configuration."""
        user_limits = user_config.get("naming", {}).get("limits", {})
        if user_limits:
            self.config.limits.update(user_limits)
            logger.info(f"Applied user naming limits: {list(user_limits.keys())}")

    def generate(
        self,
        resource_id: str,
        original_name: str,
        resource_type: str,
    ) -> str:
        """
        Generate smart resource name.

        DETERMINISM GUARANTEE: Same resource_id + resource_type = same output.
        The original_name affects readability but the hash ensures uniqueness.

        Args:
            resource_id: AWS resource ID (e.g., i-0abc123) or ARN
            original_name: Human-readable name (e.g., "WebServer")
            resource_type: Terraform resource type (e.g., "aws_instance")

        Returns:
            Deterministic, length-compliant Terraform resource name
        """
        # Get length limit for this resource type
        max_length = self.config.limits.get(
            resource_type, self.config.limits.get("_default", 32)
        )

        # Generate deterministic hash (Base62 for density)
        id_hash = self._generate_short_hash(resource_id)

        # Sanitize original name
        clean_name = self._sanitize_name(original_name)

        # Calculate available space for name
        # Format: {name}_{hash}
        separator_length = 1  # underscore
        available_for_name = max_length - self.config.hash_length - separator_length

        # Handle edge case where limit is too small
        if available_for_name < 1:
            # Just use the hash
            return id_hash[:max_length]

        # Truncate name if needed, preserving start for readability
        if len(clean_name) > available_for_name:
            clean_name = clean_name[:available_for_name]
            # Remove trailing underscore if truncation created one
            clean_name = clean_name.rstrip("_")

        # Combine name and hash
        if clean_name:
            final_name = f"{clean_name}_{id_hash}"
        else:
            final_name = f"resource_{id_hash}"

        # Ensure valid Terraform identifier
        final_name = self._ensure_valid_identifier(final_name)

        # Final validation
        if len(final_name) > max_length:
            # Fallback: just use hash with prefix
            final_name = f"r_{id_hash}"[:max_length]

        return final_name

    def _generate_short_hash(self, resource_id: str) -> str:
        """
        Generate short, dense hash using Base62.

        Base62 (a-z, A-Z, 0-9) is denser than hex:
        - 8 hex chars = 32 bits of entropy
        - 6 base62 chars ≈ 35 bits of entropy

        Args:
            resource_id: AWS resource ID or ARN

        Returns:
            Short hash string
        """
        # SHA256 for good distribution
        sha = hashlib.sha256(resource_id.encode("utf-8")).digest()

        # Convert to base62 for density
        # Take first 6 bytes (48 bits) and encode
        num = int.from_bytes(sha[:6], "big")

        result = ""
        chars = self.config.base62_chars

        while num > 0 and len(result) < self.config.hash_length:
            result = chars[num % 62] + result
            num //= 62

        # Pad if needed
        result = result.zfill(self.config.hash_length)

        return result[: self.config.hash_length]

    def _sanitize_name(self, name: str) -> str:
        """
        Ensure name is valid Terraform identifier.

        Args:
            name: Original name (may contain invalid chars)

        Returns:
            Sanitized name safe for Terraform
        """
        if not name:
            return ""

        # Replace invalid chars with underscore
        sanitized = re.sub(r"[^a-zA-Z0-9_]", "_", name)

        # Collapse multiple underscores
        sanitized = re.sub(r"_+", "_", sanitized)

        # Remove leading/trailing underscores
        sanitized = sanitized.strip("_")

        # Lowercase for consistency
        return sanitized.lower()

    def _ensure_valid_identifier(self, name: str) -> str:
        """
        Ensure the name is a valid Terraform identifier.

        Terraform identifiers must start with a letter or underscore.

        Args:
            name: Name to validate

        Returns:
            Valid Terraform identifier
        """
        if not name:
            return "resource"

        # Ensure starts with letter or underscore
        if name and not name[0].isalpha() and name[0] != "_":
            name = f"r_{name}"

        return name

    def generate_unique_name(
        self,
        resource_id: str,
        original_name: str,
        resource_type: str,
        existing_names: set[str],
    ) -> str:
        """
        Generate a unique name, handling collisions.

        In rare cases, two different resources could have the same name
        (e.g., same Name tag). This method handles that by appending
        a numeric suffix.

        Args:
            resource_id: AWS resource ID
            original_name: Human-readable name
            resource_type: Terraform resource type
            existing_names: Set of names already in use

        Returns:
            Unique Terraform resource name
        """
        base_name = self.generate(resource_id, original_name, resource_type)

        if base_name not in existing_names:
            return base_name

        # Handle collision by appending counter
        counter = 1
        while True:
            candidate = f"{base_name}_{counter}"
            if candidate not in existing_names:
                logger.warning(
                    f"Name collision detected for {resource_id}: "
                    f"{base_name} -> {candidate}"
                )
                return candidate
            counter += 1


class NameRegistry:
    """
    Registry for tracking generated names and preventing collisions.

    This class maintains a mapping from resource IDs to their generated
    names, ensuring consistency and detecting collisions.
    """

    def __init__(self, generator: SmartNameGenerator | None = None) -> None:
        """
        Initialize the name registry.

        Args:
            generator: Name generator to use (creates default if None)
        """
        self.generator = generator or SmartNameGenerator()
        self._id_to_name: dict[str, str] = {}
        self._name_to_id: dict[str, str] = {}
        self._type_names: dict[str, set[str]] = {}

    def register(
        self,
        resource_id: str,
        original_name: str,
        resource_type: str,
    ) -> str:
        """
        Register a resource and get its unique name.

        If the resource was already registered, returns the same name.
        This ensures determinism across multiple calls.

        Args:
            resource_id: AWS resource ID
            original_name: Human-readable name
            resource_type: Terraform resource type

        Returns:
            Unique Terraform resource name
        """
        # Check if already registered
        if resource_id in self._id_to_name:
            return self._id_to_name[resource_id]

        # Get existing names for this resource type
        if resource_type not in self._type_names:
            self._type_names[resource_type] = set()

        existing_names = self._type_names[resource_type]

        # Generate unique name
        name = self.generator.generate_unique_name(
            resource_id, original_name, resource_type, existing_names
        )

        # Register the mapping
        self._id_to_name[resource_id] = name
        self._name_to_id[f"{resource_type}.{name}"] = resource_id
        self._type_names[resource_type].add(name)

        return name

    def get_name(self, resource_id: str) -> str | None:
        """Get the registered name for a resource ID."""
        return self._id_to_name.get(resource_id)

    def get_id(self, resource_type: str, name: str) -> str | None:
        """Get the resource ID for a registered name."""
        return self._name_to_id.get(f"{resource_type}.{name}")

    def is_registered(self, resource_id: str) -> bool:
        """Check if a resource ID is registered."""
        return resource_id in self._id_to_name

    def get_all_names(self, resource_type: str) -> set[str]:
        """Get all registered names for a resource type."""
        return self._type_names.get(resource_type, set()).copy()

    def clear(self) -> None:
        """Clear all registrations."""
        self._id_to_name.clear()
        self._name_to_id.clear()
        self._type_names.clear()
