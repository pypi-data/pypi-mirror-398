"""
Schema Bootstrapper for RepliMap.

Bootstrap Terraform provider schema for schema-driven intelligence.

The Seven Laws of Sovereign Code:
4. Schema is Truth - Don't hardcode; query the provider schema dynamically.

The Bootstrap Paradox:
- Need schema to generate quality code
- Need terraform init to get schema
- Need .tf files to run init
- Need to generate .tf files... but need schema!

Solution: Create minimal bootstrap environment, init it,
extract the schema, and cache it for the main generation phase.

Level 4 Enhancement: Version-aware bootstrapping that respects
user's existing provider version constraints.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


# Minimal provider configuration for bootstrapping
DEFAULT_BOOTSTRAP_PROVIDER_TF = """
terraform {
  required_version = ">= 1.1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Dummy provider config - won't actually connect to AWS
provider "aws" {
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  # Use a dummy region
  region = "us-east-1"
}
"""


@dataclass
class AttributeSchema:
    """Schema for a single resource attribute."""

    name: str
    computed: bool = False
    optional: bool = False
    required: bool = False
    sensitive: bool = False
    attr_type: str = "string"

    @property
    def is_strictly_computed(self) -> bool:
        """True if attribute is computed and NOT configurable."""
        return self.computed and not self.optional and not self.required


@dataclass
class ResourceSchema:
    """Schema for a resource type."""

    resource_type: str
    attributes: dict[str, AttributeSchema] = field(default_factory=dict)
    block_types: dict[str, Any] = field(default_factory=dict)

    def get_computed_attributes(self) -> set[str]:
        """Get all strictly computed attributes (not configurable)."""
        return {
            name for name, attr in self.attributes.items() if attr.is_strictly_computed
        }

    def get_optional_attributes(self) -> set[str]:
        """Get attributes with provider defaults."""
        return {
            name
            for name, attr in self.attributes.items()
            if attr.computed and attr.optional
        }

    def is_computed(self, attribute: str) -> bool:
        """Check if an attribute is strictly computed."""
        attr = self.attributes.get(attribute)
        return attr.is_strictly_computed if attr else False


@dataclass
class ProviderConstraint:
    """A provider version constraint from user's config."""

    source: str  # e.g., "hashicorp/aws"
    version: str | None  # e.g., "~> 4.0"


class EnvironmentDetector:
    """
    Detect existing Terraform environment configuration.

    Level 4: Before bootstrapping, we analyze the user's existing
    configuration to ensure compatibility.
    """

    # Regex patterns for HCL parsing
    PROVIDER_BLOCK_PATTERN = re.compile(r"required_providers\s*\{([^}]+)\}", re.DOTALL)

    PROVIDER_ENTRY_PATTERN = re.compile(r"(\w+)\s*=\s*\{([^}]+)\}", re.DOTALL)

    SOURCE_PATTERN = re.compile(r'source\s*=\s*"([^"]+)"')
    VERSION_PATTERN = re.compile(r'version\s*=\s*"([^"]+)"')

    BACKEND_PATTERN = re.compile(r'backend\s+"(\w+)"\s*\{([^}]*)\}', re.DOTALL)

    def __init__(self, working_dir: str | Path = ".") -> None:
        """
        Initialize the environment detector.

        Args:
            working_dir: Directory to search for Terraform files
        """
        self.working_dir = Path(working_dir)

    def detect_provider_constraints(self) -> dict[str, ProviderConstraint]:
        """
        Scan user's .tf files for required_providers blocks.

        Returns:
            Dict mapping provider name to its constraints
        """
        constraints: dict[str, ProviderConstraint] = {}

        # Scan all .tf files
        for tf_file in self.working_dir.glob("**/*.tf"):
            try:
                content = tf_file.read_text()
                self._parse_providers(content, constraints)
            except Exception as e:
                logger.debug(f"Error reading {tf_file}: {e}")

        return constraints

    def _parse_providers(
        self,
        content: str,
        constraints: dict[str, ProviderConstraint],
    ) -> None:
        """Parse provider constraints from file content."""
        for match in self.PROVIDER_BLOCK_PATTERN.finditer(content):
            block_content = match.group(1)

            for entry in self.PROVIDER_ENTRY_PATTERN.finditer(block_content):
                provider_name = entry.group(1)
                entry_content = entry.group(2)

                source_match = self.SOURCE_PATTERN.search(entry_content)
                version_match = self.VERSION_PATTERN.search(entry_content)

                if source_match:
                    constraints[provider_name] = ProviderConstraint(
                        source=source_match.group(1),
                        version=version_match.group(1) if version_match else None,
                    )

    def detect_backend(self) -> dict[str, Any] | None:
        """
        Detect if user has a remote backend configured.

        This is critical for Level 4: we can't just read local state
        if state is in S3/Terraform Cloud.

        Returns:
            Backend configuration dict or None
        """
        for tf_file in self.working_dir.glob("**/*.tf"):
            try:
                content = tf_file.read_text()

                match = self.BACKEND_PATTERN.search(content)
                if match:
                    return {
                        "type": match.group(1),
                        "config": match.group(2),
                    }
            except Exception as e:
                logger.debug(f"Failed to parse backend from {tf_file}: {e}")
                continue

        return None

    def has_existing_terraform(self) -> bool:
        """Check if this directory has Terraform configuration."""
        return any(self.working_dir.glob("**/*.tf"))

    def has_terraform_lock(self) -> bool:
        """Check if terraform.lock.hcl exists."""
        return (self.working_dir / ".terraform.lock.hcl").exists()

    def has_terraform_state(self) -> bool:
        """Check if terraform.tfstate exists."""
        return (self.working_dir / "terraform.tfstate").exists()


class SchemaBootstrapper:
    """
    Bootstrap Terraform provider schema.

    Creates a temporary environment to fetch provider schema
    without requiring existing Terraform configuration.

    Workflow:
    1. Create temp directory with minimal provider config
    2. Run terraform init
    3. Run terraform providers schema -json
    4. Cache the result based on provider versions
    5. Return schema for use in generation
    """

    def __init__(self, cache_dir: Path | None = None) -> None:
        """
        Initialize the bootstrapper.

        Args:
            cache_dir: Directory for schema cache
        """
        self.cache_dir = cache_dir or Path.home() / ".replimap" / "schema_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_schema(self, force_refresh: bool = False) -> dict[str, Any]:
        """
        Get provider schema, using cache if available.

        Args:
            force_refresh: Force re-fetch schema

        Returns:
            Parsed schema JSON
        """
        cache_key = self._get_cache_key()
        cache_file = self.cache_dir / f"{cache_key}.json"

        # Try cache first
        if cache_file.exists() and not force_refresh:
            try:
                return json.loads(cache_file.read_text())
            except json.JSONDecodeError:
                logger.warning("Invalid schema cache, refreshing")

        # Bootstrap and fetch schema
        schema = self._bootstrap_and_fetch()

        # Cache the result
        cache_file.write_text(json.dumps(schema, separators=(",", ":")))
        logger.info(f"Cached schema to {cache_file}")

        return schema

    def _get_cache_key(self) -> str:
        """
        Generate cache key based on provider config.

        The key changes when provider versions change.
        """
        return hashlib.sha256(DEFAULT_BOOTSTRAP_PROVIDER_TF.encode()).hexdigest()[:12]

    def _bootstrap_and_fetch(self) -> dict[str, Any]:
        """
        Create temp environment, init, and fetch schema.

        Returns:
            Parsed schema JSON
        """
        with tempfile.TemporaryDirectory(prefix="replimap_bootstrap_") as tmpdir:
            tmppath = Path(tmpdir)

            # Write minimal provider config
            (tmppath / "providers.tf").write_text(DEFAULT_BOOTSTRAP_PROVIDER_TF)

            # Run terraform init
            init_result = subprocess.run(
                ["terraform", "init", "-input=false", "-no-color"],
                cwd=tmppath,
                capture_output=True,
                text=True,
                timeout=120,
            )

            if init_result.returncode != 0:
                raise BootstrapError(f"terraform init failed: {init_result.stderr}")

            # Fetch schema
            schema_result = subprocess.run(
                ["terraform", "providers", "schema", "-json"],
                cwd=tmppath,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if schema_result.returncode != 0:
                raise BootstrapError(
                    f"terraform providers schema failed: {schema_result.stderr}"
                )

            return json.loads(schema_result.stdout)


class VersionAwareBootstrapper(SchemaBootstrapper):
    """
    Level 4 Enhanced Bootstrapper: Respects existing environment.

    Improvements over Level 3:
    1. Detects and uses existing provider version constraints
    2. Warns about remote backends
    3. Caches based on actual version constraints (not just defaults)
    """

    def __init__(
        self,
        working_dir: str | Path = ".",
        cache_dir: Path | None = None,
    ) -> None:
        """
        Initialize the version-aware bootstrapper.

        Args:
            working_dir: Working directory with existing Terraform config
            cache_dir: Directory for schema cache
        """
        super().__init__(cache_dir)
        self.working_dir = Path(working_dir)
        self.detector = EnvironmentDetector(working_dir)
        self.detected_constraints: dict[str, ProviderConstraint] = {}

    def get_schema(self, force_refresh: bool = False) -> dict[str, Any]:
        """
        Get provider schema, respecting user's version constraints.

        Args:
            force_refresh: Force re-fetch schema

        Returns:
            Parsed schema JSON
        """
        # Detect existing constraints FIRST
        self.detected_constraints = self.detector.detect_provider_constraints()

        if self.detected_constraints:
            logger.info(
                f"Detected provider constraints: {list(self.detected_constraints.keys())}"
            )

        # Check for remote backend
        backend = self.detector.detect_backend()
        if backend:
            logger.warning(
                f"Detected remote backend: {backend['type']}. "
                "You may need to run 'terraform init' first to access state."
            )

        # Generate cache key based on ACTUAL constraints (not defaults)
        cache_key = self._get_version_aware_cache_key()
        cache_file = self.cache_dir / f"{cache_key}.json"

        if cache_file.exists() and not force_refresh:
            try:
                return json.loads(cache_file.read_text())
            except json.JSONDecodeError:
                pass

        schema = self._bootstrap_and_fetch()
        cache_file.write_text(json.dumps(schema, separators=(",", ":")))

        return schema

    def _get_version_aware_cache_key(self) -> str:
        """
        Generate cache key based on detected version constraints.

        This ensures we don't use cached 5.x schema for a 4.x environment.
        """
        key_parts = []

        for name, constraint in sorted(self.detected_constraints.items()):
            key_parts.append(f"{name}:{constraint.version or 'latest'}")

        if not key_parts:
            key_parts.append("default")

        key_string = "|".join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()[:12]

    def _generate_providers_tf(self) -> str:
        """
        Generate providers.tf content, respecting user constraints.

        Returns:
            HCL content for providers.tf
        """
        if self.detected_constraints:
            return self._render_detected_constraints()

        logger.info("No existing constraints found, using defaults")
        return DEFAULT_BOOTSTRAP_PROVIDER_TF

    def _render_detected_constraints(self) -> str:
        """Render detected constraints as HCL."""
        provider_entries = []

        for name, constraint in self.detected_constraints.items():
            entry = f'    {name} = {{\n      source  = "{constraint.source}"'

            if constraint.version:
                entry += f'\n      version = "{constraint.version}"'

            entry += "\n    }"
            provider_entries.append(entry)

        return f"""
terraform {{
  required_version = ">= 1.1.0"

  required_providers {{
{chr(10).join(provider_entries)}
  }}
}}

# Dummy provider configs for schema fetching
provider "aws" {{
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  region = "us-east-1"
}}
"""

    def _bootstrap_and_fetch(self) -> dict[str, Any]:
        """
        Create temp environment with user's constraints.

        Returns:
            Parsed schema JSON
        """
        with tempfile.TemporaryDirectory(prefix="replimap_bootstrap_") as tmpdir:
            tmppath = Path(tmpdir)

            # Write provider config (version-aware)
            providers_tf = self._generate_providers_tf()
            (tmppath / "providers.tf").write_text(providers_tf)

            # Run terraform init
            init_result = subprocess.run(
                ["terraform", "init", "-input=false", "-no-color"],
                cwd=tmppath,
                capture_output=True,
                text=True,
                timeout=120,
            )

            if init_result.returncode != 0:
                raise BootstrapError(f"terraform init failed: {init_result.stderr}")

            # Fetch schema
            schema_result = subprocess.run(
                ["terraform", "providers", "schema", "-json"],
                cwd=tmppath,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if schema_result.returncode != 0:
                raise BootstrapError(
                    f"terraform providers schema failed: {schema_result.stderr}"
                )

            return json.loads(schema_result.stdout)


class ProviderSchemaLoader:
    """
    Load and parse Terraform provider schema.

    This is the Level 2 upgrade: instead of hardcoding what's computed,
    we ASK the provider directly.

    Usage:
        loader = ProviderSchemaLoader(working_dir="./terraform")
        loader.load()

        # Now dynamically check any attribute
        if loader.is_computed("aws_instance", "arn"):
            # Skip this in drift detection
    """

    def __init__(self, working_dir: str | Path = ".") -> None:
        """
        Initialize the schema loader.

        Args:
            working_dir: Working directory
        """
        self.working_dir = Path(working_dir)
        self.cache_dir = self.working_dir / ".replimap" / "schema_cache"
        self.schemas: dict[str, ResourceSchema] = {}
        self._loaded = False

    def load(self, force_refresh: bool = False) -> ProviderSchemaLoader:
        """
        Load provider schema.

        Args:
            force_refresh: Force re-fetch schema

        Returns:
            Self for chaining
        """
        if self._loaded and not force_refresh:
            return self

        bootstrapper = VersionAwareBootstrapper(
            working_dir=self.working_dir,
            cache_dir=self.cache_dir,
        )

        try:
            schema_json = bootstrapper.get_schema(force_refresh=force_refresh)
            self._parse_schema_json(schema_json)
            self._loaded = True
            logger.info(f"Loaded schema for {len(self.schemas)} resource types")
        except BootstrapError as e:
            logger.warning(f"Failed to load schema: {e}")
            # Continue with empty schema - will use fallback defaults
        except FileNotFoundError:
            logger.warning("Terraform not found - using fallback defaults")

        return self

    def _parse_schema_json(self, schema_json: dict[str, Any]) -> None:
        """Parse the terraform providers schema JSON."""
        for provider_key, provider_schema in schema_json.get(
            "provider_schemas", {}
        ).items():
            if "aws" not in provider_key:
                continue

            resources = provider_schema.get("resource_schemas", {})

            for resource_type, resource_def in resources.items():
                schema = ResourceSchema(resource_type=resource_type)

                # Parse block attributes
                block = resource_def.get("block", {})
                attributes = block.get("attributes", {})

                for attr_name, attr_def in attributes.items():
                    schema.attributes[attr_name] = AttributeSchema(
                        name=attr_name,
                        computed=attr_def.get("computed", False),
                        optional=attr_def.get("optional", False),
                        required=attr_def.get("required", False),
                        sensitive=attr_def.get("sensitive", False),
                    )

                # Parse block types
                block_types = block.get("block_types", {})
                schema.block_types = block_types

                self.schemas[resource_type] = schema

    def is_computed(self, resource_type: str, attribute: str) -> bool:
        """
        Check if an attribute is strictly computed (not configurable).

        This replaces the hardcoded GLOBAL_COMPUTED_ATTRS list!

        Args:
            resource_type: Terraform resource type
            attribute: Attribute name

        Returns:
            True if attribute is computed and not configurable
        """
        schema = self.schemas.get(resource_type)

        if not schema:
            # Unknown resource type - be conservative, don't filter
            return False

        return schema.is_computed(attribute)

    def get_computed_attrs(self, resource_type: str) -> set[str]:
        """Get all computed attributes for a resource type."""
        schema = self.schemas.get(resource_type)

        if not schema:
            return set()

        return schema.get_computed_attributes()

    def get_schema(self, resource_type: str) -> ResourceSchema | None:
        """Get the full schema for a resource type."""
        return self.schemas.get(resource_type)

    @property
    def is_loaded(self) -> bool:
        """Check if schema is loaded."""
        return self._loaded

    @property
    def resource_count(self) -> int:
        """Number of resource types in schema."""
        return len(self.schemas)


class BootstrapError(Exception):
    """Raised when bootstrap process fails."""

    pass
