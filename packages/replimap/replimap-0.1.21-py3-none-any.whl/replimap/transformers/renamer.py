"""
Renaming Transformer for RepliMap.

Applies environment-specific renaming to resources:
- Replaces 'prod' with 'staging' in names and tags
- Uses regex for case-insensitive matching
- Preserves original names for reference
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any

from .base import BaseTransformer

if TYPE_CHECKING:
    from replimap.core import GraphEngine


logger = logging.getLogger(__name__)


# Default replacement patterns
DEFAULT_REPLACEMENTS: dict[str, str] = {
    "production": "staging",
    "prod": "stage",
    "prd": "stg",
}


class RenamingTransformer(BaseTransformer):
    """
    Applies environment-specific renaming to resources.

    This transformer:
    1. Replaces environment names in resource names/tags
    2. Uses case-insensitive regex matching
    3. Applies to Name tags, terraform names, and config fields

    The goal is to clearly distinguish staging resources from
    production and avoid naming conflicts.
    """

    name = "RenamingTransformer"

    def __init__(
        self,
        replacements: dict[str, str] | None = None,
        case_insensitive: bool = True,
        rename_s3_buckets: bool = True,
        s3_suffix: str = "",
    ) -> None:
        """
        Initialize the renamer.

        Args:
            replacements: Mapping of old strings to new strings
            case_insensitive: Whether to match case-insensitively
            rename_s3_buckets: Whether to rename S3 buckets
            s3_suffix: Suffix to add to S3 bucket names for uniqueness
        """
        self.replacements = replacements or DEFAULT_REPLACEMENTS
        self.case_insensitive = case_insensitive
        self.rename_s3_buckets = rename_s3_buckets
        self.s3_suffix = s3_suffix
        self._renamed_count = 0

        # Pre-compile regex patterns
        self._patterns: list[tuple[re.Pattern, str]] = []
        for old, new in self.replacements.items():
            flags = re.IGNORECASE if case_insensitive else 0
            # Use word boundaries to avoid partial matches
            pattern = re.compile(rf"\b{re.escape(old)}\b", flags)
            self._patterns.append((pattern, new))

    def transform(self, graph: GraphEngine) -> GraphEngine:
        """
        Apply renaming to all resources in the graph.

        Args:
            graph: The GraphEngine to transform

        Returns:
            The same GraphEngine with renamed resources
        """
        self._renamed_count = 0

        for resource in graph.iter_resources():
            # Rename tags
            resource.tags = self._rename_dict(resource.tags)

            # Rename terraform_name
            if resource.terraform_name:
                new_name = self._rename_string(resource.terraform_name)
                if new_name != resource.terraform_name:
                    resource.terraform_name = new_name

            # Rename config fields
            resource.config = self._rename_config(resource.config)

            # Update original_name for display purposes
            if resource.original_name:
                new_original = self._rename_string(resource.original_name)
                if new_original != resource.original_name:
                    resource.config["_original_name"] = resource.original_name
                    resource.original_name = new_original

        logger.info(f"Applied {self._renamed_count} renames")

        return graph

    def _rename_string(self, value: str) -> str:
        """
        Apply all replacement patterns to a string.

        Args:
            value: String to rename

        Returns:
            Renamed string
        """
        result = value
        for pattern, replacement in self._patterns:
            new_result = pattern.sub(replacement, result)
            if new_result != result:
                self._renamed_count += 1
            result = new_result
        return result

    def _rename_dict(self, data: dict[str, str]) -> dict[str, str]:
        """
        Apply renaming to dictionary values.

        Args:
            data: Dictionary with string values

        Returns:
            Dictionary with renamed values
        """
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self._rename_string(value)
            else:
                result[key] = value
        return result

    def _rename_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """
        Recursively apply renaming to config dictionary.

        Only renames specific fields that represent names:
        - name, bucket, identifier
        - db_name, group_name
        - Keys containing 'name' in their path

        Args:
            config: Configuration dictionary

        Returns:
            Configuration with renamed values
        """
        result: dict[str, Any] = {}

        # Fields that should be renamed
        name_fields = {
            "name",
            "bucket",
            "identifier",
            "db_name",
            "group_name",
            "description",
        }

        for key, value in config.items():
            if isinstance(value, str):
                # Only rename specific name-like fields
                if key in name_fields or "name" in key.lower():
                    result[key] = self._rename_string(value)
                else:
                    result[key] = value
            elif isinstance(value, dict):
                result[key] = self._rename_config(value)
            elif isinstance(value, list):
                result[key] = self._rename_list(value)
            else:
                result[key] = value

        return result

    def _rename_list(self, data: list[Any]) -> list[Any]:
        """
        Recursively apply renaming to list elements.

        Args:
            data: List to process

        Returns:
            List with renamed elements
        """
        result: list[Any] = []
        for item in data:
            if isinstance(item, dict):
                result.append(self._rename_config(item))
            elif isinstance(item, list):
                result.append(self._rename_list(item))
            else:
                # Don't rename arbitrary string items in lists
                result.append(item)
        return result

    @classmethod
    def from_pattern(cls, pattern: str) -> RenamingTransformer:
        """
        Create a transformer from a pattern string.

        Pattern format: "old1:new1,old2:new2"
        Example: "prod:stage,production:staging"

        Args:
            pattern: Comma-separated old:new pairs

        Returns:
            Configured RenamingTransformer
        """
        replacements = {}
        for pair in pattern.split(","):
            if ":" in pair:
                old, new = pair.split(":", 1)
                replacements[old.strip()] = new.strip()

        return cls(replacements=replacements)
