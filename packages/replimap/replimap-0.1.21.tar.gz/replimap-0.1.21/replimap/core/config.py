"""
Configuration loader for RepliMap.

Loads user configuration from .replimap.yaml files, supporting
hierarchical configuration with defaults.

The Seven Laws of Sovereign Code:
6. Mimic the Environment - Respect existing versions, backends, structure.

This module enables user-customizable behavior through .replimap.yaml,
allowing escape hatches for all safety defaults.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# Default configuration values
DEFAULT_CONFIG: dict[str, Any] = {
    "version": "1.0",
    # Naming configuration
    "naming": {
        "hash_length": 8,
        "limits": {},  # User overrides for AWS_NAME_LIMITS
    },
    # Import block configuration
    "import": {
        "formats": {},  # User overrides for import ID formats
        "terraform_version": "1.5",  # Minimum version for import blocks
    },
    # Scope configuration (boundary recognition)
    "scope": {
        # Override default behavior for AWS default resources
        # Set to True to MANAGE (not just reference) default resources
        "manage_defaults": {
            "default_vpc": False,  # Default: read-only (safer)
            "default_security_group": False,
            "default_network_acl": False,
            "default_route_table": False,
        },
        # Resources matching these patterns will be read-only (data sources)
        "read_only": [],
        # Resources matching these patterns will be force-managed (override read_only)
        "force_manage": [],
        # Resources matching these patterns will be skipped entirely
        "skip": [],
    },
    # Drift detection configuration
    "drift": {
        # Additional attributes to ignore in drift detection
        "ignore_attributes": [],
        # Resources to ignore entirely in drift detection
        "ignore_resources": [],
        # Use terraform plan for drift (recommended)
        "use_terraform_plan": True,
    },
    # Module extraction configuration
    "modules": {
        # Enable local module extraction suggestions
        "suggest_extraction": True,
        # Minimum resources to suggest module extraction
        "min_resources_for_module": 3,
    },
    # Audit annotation configuration
    "audit": {
        # Only annotate inline for these severities
        "inline_severities": ["CRITICAL", "HIGH"],
        # Maximum inline findings before summarizing
        "max_inline_findings": 3,
        # Generate full audit report
        "generate_report": True,
    },
    # Output configuration
    "output": {
        # Use semantic file routing (vpc.tf, security.tf, etc.)
        "semantic_files": True,
        # Extract common variables
        "extract_variables": True,
        # Generate moved blocks for refactoring
        "generate_moved_blocks": True,
        # Generate import blocks
        "generate_import_blocks": True,
    },
}


@dataclass
class RepliMapConfig:
    """
    Configuration container for RepliMap.

    Provides type-safe access to configuration values with defaults.
    """

    data: dict[str, Any] = field(default_factory=dict)
    config_path: Path | None = None

    def __post_init__(self) -> None:
        """Merge with defaults."""
        self.data = deep_merge(DEFAULT_CONFIG.copy(), self.data)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by dot-notation key.

        Examples:
            config.get("naming.hash_length")  # Returns 8
            config.get("scope.manage_defaults.default_vpc")  # Returns False

        Args:
            key: Dot-notation key path
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key.split(".")
        value = self.data

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value by dot-notation key.

        Args:
            key: Dot-notation key path
            value: Value to set
        """
        keys = key.split(".")
        data = self.data

        for k in keys[:-1]:
            if k not in data:
                data[k] = {}
            data = data[k]

        data[keys[-1]] = value

    def get_naming_limits(self) -> dict[str, int]:
        """Get naming limits with user overrides."""
        return self.get("naming.limits", {})

    def get_import_formats(self) -> dict[str, str]:
        """Get import ID formats with user overrides."""
        return self.get("import.formats", {})

    def is_default_managed(self, default_type: str) -> bool:
        """
        Check if a default resource type should be managed.

        This is the ESCAPE HATCH - users can override default safety rules.

        Args:
            default_type: One of 'default_vpc', 'default_security_group', etc.

        Returns:
            True if user wants to manage (not just reference) this default
        """
        return bool(self.get(f"scope.manage_defaults.{default_type}", False))

    def get_read_only_patterns(self) -> list[str]:
        """Get patterns for read-only resources."""
        return self.get("scope.read_only", [])

    def get_skip_patterns(self) -> list[str]:
        """Get patterns for skipped resources."""
        return self.get("scope.skip", [])

    def get_force_manage_patterns(self) -> list[str]:
        """Get patterns for force-managed resources."""
        return self.get("scope.force_manage", [])

    def should_use_semantic_files(self) -> bool:
        """Check if semantic file routing is enabled."""
        return bool(self.get("output.semantic_files", True))

    def should_generate_moved_blocks(self) -> bool:
        """Check if moved blocks should be generated."""
        return bool(self.get("output.generate_moved_blocks", True))

    def should_generate_import_blocks(self) -> bool:
        """Check if import blocks should be generated."""
        return bool(self.get("output.generate_import_blocks", True))

    def get_inline_severities(self) -> list[str]:
        """Get severities for inline audit annotations."""
        return self.get("audit.inline_severities", ["CRITICAL", "HIGH"])

    def get_max_inline_findings(self) -> int:
        """Get maximum findings for inline annotation before summarizing."""
        return int(self.get("audit.max_inline_findings", 3))

    def to_dict(self) -> dict[str, Any]:
        """Export configuration as dictionary."""
        return self.data.copy()


class ConfigLoader:
    """
    Load RepliMap configuration from .replimap.yaml files.

    Searches for configuration in the following order:
    1. Explicit path (if provided)
    2. Current working directory
    3. Parent directories (up to root)
    4. User home directory (~/.replimap.yaml)

    Later sources override earlier sources.
    """

    CONFIG_FILENAMES = [".replimap.yaml", ".replimap.yml", "replimap.yaml"]

    def __init__(self, working_dir: str | Path | None = None) -> None:
        """
        Initialize the config loader.

        Args:
            working_dir: Starting directory for config search
        """
        self.working_dir = Path(working_dir or os.getcwd())
        self._config: RepliMapConfig | None = None

    def load(
        self,
        config_path: str | Path | None = None,
        use_defaults: bool = True,
    ) -> RepliMapConfig:
        """
        Load configuration from file(s).

        Args:
            config_path: Explicit config file path (optional)
            use_defaults: Whether to use default values

        Returns:
            Loaded configuration
        """
        config_data: dict[str, Any] = {}
        found_path: Path | None = None

        if config_path:
            # Load from explicit path
            found_path = Path(config_path)
            if found_path.exists():
                config_data = self._load_yaml(found_path)
            else:
                logger.warning(f"Config file not found: {config_path}")
        else:
            # Search for config file
            found_path = self._find_config_file()
            if found_path:
                config_data = self._load_yaml(found_path)
                logger.info(f"Loaded configuration from: {found_path}")

        if not use_defaults:
            self._config = RepliMapConfig(data=config_data, config_path=found_path)
        else:
            # Merge with defaults (default behavior)
            self._config = RepliMapConfig(data=config_data, config_path=found_path)

        return self._config

    def _find_config_file(self) -> Path | None:
        """
        Search for a config file in standard locations.

        Returns:
            Path to config file, or None if not found
        """
        # Check current directory and parents
        current = self.working_dir.resolve()
        root = Path(current.anchor)

        while current != root:
            for filename in self.CONFIG_FILENAMES:
                config_path = current / filename
                if config_path.exists():
                    return config_path
            current = current.parent

        # Check home directory
        home = Path.home()
        for filename in self.CONFIG_FILENAMES:
            config_path = home / filename
            if config_path.exists():
                return config_path

        return None

    def _load_yaml(self, path: Path) -> dict[str, Any]:
        """
        Load YAML file.

        Args:
            path: Path to YAML file

        Returns:
            Parsed YAML content
        """
        try:
            import yaml

            with open(path) as f:
                data = yaml.safe_load(f)
                return data if isinstance(data, dict) else {}
        except ImportError:
            logger.warning("PyYAML not installed. Install with: pip install pyyaml")
            return {}
        except Exception as e:
            logger.warning(f"Failed to load config from {path}: {e}")
            return {}

    @property
    def config(self) -> RepliMapConfig:
        """Get loaded configuration (loads if not already loaded)."""
        if self._config is None:
            self._config = self.load()
        return self._config


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """
    Deep merge two dictionaries.

    Override values take precedence over base values.
    Nested dicts are merged recursively.

    Args:
        base: Base dictionary
        override: Override dictionary

    Returns:
        Merged dictionary
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value

    return result


def generate_example_config() -> str:
    """
    Generate an example .replimap.yaml file content.

    Returns:
        Example configuration as YAML string
    """
    return """# RepliMap Configuration File
# Place this file as .replimap.yaml in your project root or home directory

version: "1.0"

# ═══════════════════════════════════════════════════════════════════════════════
# NAMING CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
naming:
  # Hash length for deterministic naming (default: 8)
  hash_length: 8

  # Override AWS name length limits for specific resource types
  # Default is 32 (conservative). Add custom limits here:
  limits:
    # aws_bedrock_agent: 40
    # aws_custom_resource: 50

# ═══════════════════════════════════════════════════════════════════════════════
# IMPORT BLOCK CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
import:
  # Minimum Terraform version for import blocks (default: 1.5)
  terraform_version: "1.5"

  # Override import ID formats for complex resources
  # Format: resource_type: "format_template"
  formats:
    # aws_security_group_rule: "{sg_id}_{type}_{protocol}_{from}_{to}_{source}"
    # aws_route: "{route_table_id}_{destination}"

# ═══════════════════════════════════════════════════════════════════════════════
# SCOPE CONFIGURATION (Boundary Recognition)
# ═══════════════════════════════════════════════════════════════════════════════
scope:
  # ⚠️ ESCAPE HATCH: Override default safety behavior
  # By default, AWS default resources (Default VPC, Default SG, etc.) are
  # generated as read-only data sources to prevent accidental destruction.
  #
  # Set to true to MANAGE these resources (allows Terraform to modify/destroy)
  manage_defaults:
    default_vpc: false              # Keep as data source (SAFE)
    default_security_group: false   # Keep as data source (SAFE)
    default_network_acl: false      # Keep as data source (SAFE)
    default_route_table: false      # Keep as data source (SAFE)

  # Resources matching these patterns will be READ-ONLY (data sources)
  # Patterns: "tag:Key=Value", "id:resource-id", "id_prefix:prefix"
  read_only:
    # - tag:ManagedBy=SecurityTeam   # Security team's resources
    # - tag:Shared=true               # Shared infrastructure
    # - id_prefix:alias/aws/          # AWS-managed KMS aliases

  # Force-manage specific resources (overrides read_only rules)
  force_manage:
    # - id:vpc-12345678               # I specifically want to manage this VPC

  # Skip these resources entirely (no output generated)
  skip:
    # - tag:TerraformIgnore=true
    # - tag:Environment=legacy

# ═══════════════════════════════════════════════════════════════════════════════
# DRIFT DETECTION CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
drift:
  # Use terraform plan for drift detection (recommended)
  use_terraform_plan: true

  # Additional attributes to ignore in drift detection
  ignore_attributes:
    # - last_modified        # Lambda changes on every deploy
    # - source_code_hash     # Track separately

  # Ignore specific resources entirely in drift detection
  ignore_resources:
    # - aws_cloudwatch_log_group.lambda_logs

# ═══════════════════════════════════════════════════════════════════════════════
# MODULE EXTRACTION CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
modules:
  # Enable local module extraction suggestions
  suggest_extraction: true

  # Minimum related resources to suggest module extraction
  min_resources_for_module: 3

# ═══════════════════════════════════════════════════════════════════════════════
# AUDIT ANNOTATION CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
audit:
  # Only these severities get inline code annotations
  # Lower severities go to file header or report
  inline_severities:
    - CRITICAL
    - HIGH

  # Maximum findings before summarizing (noise control)
  max_inline_findings: 3

  # Generate full audit report (audit-report.md)
  generate_report: true

# ═══════════════════════════════════════════════════════════════════════════════
# OUTPUT CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
output:
  # Use semantic file routing (vpc.tf, security.tf, compute.tf, etc.)
  semantic_files: true

  # Extract common variables (region, environment, etc.)
  extract_variables: true

  # Generate moved blocks for Brownfield refactoring
  generate_moved_blocks: true

  # Generate import blocks for Terraform 1.5+
  generate_import_blocks: true
"""
