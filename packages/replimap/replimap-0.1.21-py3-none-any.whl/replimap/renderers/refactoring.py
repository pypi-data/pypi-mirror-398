"""
Refactoring Engine for RepliMap.

Generate Terraform `moved` blocks for safe Brownfield adoption.

This is the Level 3 upgrade that enables safe Brownfield adoption.
Instead of skipping imports (which causes Create/Delete disasters),
we generate `moved` blocks for seamless address refactoring.

The Seven Laws of Sovereign Code:
5. Refactor, Don't Recreate - Use moved blocks, never destroy to rename.

Requires: Terraform 1.1+ for moved blocks

The Fatal Flaw in Level 2 "Skip Import":
- State has: aws_instance.web → i-123 (legacy name)
- RepliMap generates: aws_instance.web_a1b2 → i-123 (deterministic name)
- Level 2 Approach (WRONG): "i-123 is already managed, skip import"
- Result: terraform plan shows "Destroy web, Create web_a1b2" = DISASTER!

The Level 3 Solution:
- Generate `moved { from = aws_instance.web to = aws_instance.web_a1b2 }`
- Result: terraform plan shows "Resource has moved" = PERFECT!
"""

from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from replimap.core.config import RepliMapConfig
    from replimap.renderers.import_generator import ImportMapping

logger = logging.getLogger(__name__)


@dataclass
class ResourceMapping:
    """Maps an AWS ID to both legacy and new Terraform addresses."""

    aws_id: str
    resource_type: str
    legacy_address: str | None  # From existing state (e.g., "aws_instance.web")
    new_address: str  # Our deterministic name (e.g., "aws_instance.web_a1b2")
    attributes: dict[str, Any] = field(default_factory=dict)

    @property
    def needs_move(self) -> bool:
        """True if resource exists in state with different name."""
        return (
            self.legacy_address is not None and self.legacy_address != self.new_address
        )

    @property
    def needs_import(self) -> bool:
        """True if resource is not in state at all."""
        return self.legacy_address is None


@dataclass
class MovedBlock:
    """A Terraform moved block."""

    from_address: str
    to_address: str

    def render(self) -> str:
        """Render the moved block as HCL."""
        return f"""moved {{
  from = {self.from_address}
  to   = {self.to_address}
}}"""


@dataclass
class RefactoringResult:
    """Result of refactoring analysis."""

    moves: list[MovedBlock] = field(default_factory=list)
    imports: list[ImportMapping] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def summary(self) -> str:
        """Generate a human-readable summary."""
        lines = [
            "Refactoring Analysis:",
            f"  - {len(self.moves)} resources to move (rename in state)",
            f"  - {len(self.imports)} resources to import (new adoption)",
            f"  - {len(self.unchanged)} resources unchanged",
        ]
        if self.errors:
            lines.append(f"  - {len(self.errors)} errors")
        return "\n".join(lines)

    @property
    def has_changes(self) -> bool:
        """True if there are moves or imports to process."""
        return bool(self.moves or self.imports)


class StateManifest:
    """
    Parse and cache Terraform state for refactoring analysis.

    Loads the existing Terraform state and builds a mapping of
    AWS IDs to Terraform addresses, enabling detection of
    renamed resources.
    """

    def __init__(self, working_dir: str | Path = ".") -> None:
        """
        Initialize the state manifest.

        Args:
            working_dir: Directory containing Terraform configuration
        """
        self.working_dir = Path(working_dir)
        self._id_to_address: dict[str, str] = {}
        self._address_to_id: dict[str, str] = {}
        self._loaded = False

    def load(self) -> bool:
        """
        Load state from terraform show -json.

        Returns:
            True if state was loaded successfully
        """
        try:
            result = subprocess.run(
                ["terraform", "show", "-json"],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                # No state or can't read - greenfield deployment
                logger.info("No existing Terraform state found (greenfield deployment)")
                return False

            state = json.loads(result.stdout)
            self._parse_state(state)
            self._loaded = True
            logger.info(f"Loaded state manifest: {len(self._id_to_address)} resources")
            return True

        except subprocess.TimeoutExpired:
            logger.warning("terraform show timed out")
            return False
        except json.JSONDecodeError:
            logger.warning("Invalid JSON from terraform show")
            return False
        except FileNotFoundError:
            logger.warning("terraform not found in PATH")
            return False
        except Exception as e:
            logger.warning(f"Failed to load state: {e}")
            return False

    def _parse_state(self, state: dict[str, Any]) -> None:
        """
        Parse state JSON to build aws_id -> address mapping.

        Args:
            state: Parsed terraform show -json output
        """
        values = state.get("values", {})
        root_module = values.get("root_module", {})

        self._parse_module(root_module, "")

        # Parse child modules
        for child in root_module.get("child_modules", []):
            module_address = child.get("address", "")
            self._parse_module(child, module_address)

    def _parse_module(self, module: dict[str, Any], module_address: str) -> None:
        """
        Parse a module's resources.

        Args:
            module: Module data from state
            module_address: Full module address prefix
        """
        for resource in module.get("resources", []):
            if resource.get("mode") != "managed":
                continue

            address = resource.get("address", "")
            values = resource.get("values", {})

            # Extract AWS ID
            aws_id = values.get("id") or values.get("arn")

            if aws_id and address:
                self._id_to_address[aws_id] = address
                self._address_to_id[address] = aws_id

    def get_address_for_id(self, aws_id: str) -> str | None:
        """Get the Terraform address for an AWS ID."""
        return self._id_to_address.get(aws_id)

    def get_id_for_address(self, address: str) -> str | None:
        """Get the AWS ID for a Terraform address."""
        return self._address_to_id.get(address)

    def is_managed(self, aws_id: str) -> bool:
        """Check if an AWS ID is in the current state."""
        return aws_id in self._id_to_address

    def get_all_ids(self) -> set[str]:
        """Get all AWS IDs in the state."""
        return set(self._id_to_address.keys())

    @property
    def is_loaded(self) -> bool:
        """Check if state was successfully loaded."""
        return self._loaded

    @property
    def resource_count(self) -> int:
        """Number of resources in state."""
        return len(self._id_to_address)


class RefactoringEngine:
    """
    Generate `moved` blocks for safe Brownfield refactoring.

    This engine solves the "Legacy Name vs Deterministic Name" problem:
    - State has resources with human-created names (web, db, cache)
    - RepliMap generates deterministic names (web_a1b2, db_c3d4)
    - Without moved blocks: Terraform destroys and recreates
    - With moved blocks: Terraform seamlessly renames

    Usage:
        engine = RefactoringEngine(working_dir="./terraform")
        result = engine.analyze(resources)

        # Generate appropriate files
        result.moves   → moves.tf
        result.imports → imports.tf
    """

    def __init__(
        self,
        working_dir: str | Path = ".",
        config: RepliMapConfig | None = None,
    ) -> None:
        """
        Initialize the refactoring engine.

        Args:
            working_dir: Directory containing Terraform configuration
            config: User configuration
        """
        self.working_dir = Path(working_dir)
        self.config = config
        self.state_manifest = StateManifest(working_dir)

    def analyze(self, resources: list[Any]) -> RefactoringResult:
        """
        Analyze resources and determine what needs moving vs importing.

        Args:
            resources: List of ResourceNode objects

        Returns:
            RefactoringResult with moves and imports lists
        """
        # Import here to avoid circular imports
        from replimap.renderers.import_generator import ImportMapping

        result = RefactoringResult()

        # Try to load existing state
        has_state = self.state_manifest.load()

        if not has_state:
            # Greenfield deployment - everything needs import
            logger.info("Greenfield deployment: all resources need import")
            for resource in resources:
                new_address = f"{resource.resource_type}.{resource.terraform_name}"
                result.imports.append(
                    ImportMapping(
                        terraform_address=new_address,
                        aws_id=resource.id,
                        resource_type=str(resource.resource_type),
                        attributes=resource.config,
                    )
                )
            return result

        # Brownfield deployment - analyze each resource
        for resource in resources:
            new_address = f"{resource.resource_type}.{resource.terraform_name}"
            legacy_address = self.state_manifest.get_address_for_id(resource.id)

            mapping = ResourceMapping(
                aws_id=resource.id,
                resource_type=str(resource.resource_type),
                legacy_address=legacy_address,
                new_address=new_address,
                attributes=resource.config,
            )

            if mapping.needs_move:
                # Resource exists with different name - generate moved block
                result.moves.append(
                    MovedBlock(
                        from_address=legacy_address,
                        to_address=new_address,
                    )
                )
                logger.debug(f"Move: {legacy_address} -> {new_address}")
            elif mapping.needs_import:
                # Resource not in state - generate import block
                result.imports.append(
                    ImportMapping(
                        terraform_address=new_address,
                        aws_id=resource.id,
                        resource_type=str(resource.resource_type),
                        attributes=resource.config,
                    )
                )
                logger.debug(f"Import: {new_address} <- {resource.id}")
            else:
                # Resource exists with same name - no action needed
                result.unchanged.append(new_address)
                logger.debug(f"Unchanged: {new_address}")

        return result

    def generate_moved_file(
        self,
        moves: list[MovedBlock],
        output_path: Path,
    ) -> None:
        """
        Generate moves.tf file with all moved blocks.

        Args:
            moves: List of MovedBlock objects
            output_path: Path to write the moves.tf file
        """
        if not moves:
            logger.info("No moved blocks to generate")
            return

        lines = [
            "# ═══════════════════════════════════════════════════════════════════════════════",
            "# Auto-generated by RepliMap",
            "# These blocks safely rename resources without destroying them",
            "# ═══════════════════════════════════════════════════════════════════════════════",
            "#",
            "# Requires Terraform 1.1+",
            "#",
            "# When you run 'terraform plan', you should see:",
            "#   # aws_instance.old_name has moved to aws_instance.new_name",
            "#",
            "# This is SAFE - no resources will be destroyed or recreated.",
            "#",
            "# After applying, you can remove this file - the moves are one-time operations.",
            "#",
            "# ═══════════════════════════════════════════════════════════════════════════════",
            "",
        ]

        for move in moves:
            lines.append(move.render())
            lines.append("")

        output_path.write_text("\n".join(lines))
        logger.info(f"Wrote moves.tf: {len(moves)} moved blocks")

    def generate_files(
        self,
        result: RefactoringResult,
        output_dir: Path,
    ) -> dict[str, Path]:
        """
        Generate all refactoring files (moves.tf and imports.tf).

        Args:
            result: Refactoring analysis result
            output_dir: Directory to write files

        Returns:
            Dictionary of generated file paths
        """
        from replimap.renderers.import_generator import ImportBlockGenerator

        generated: dict[str, Path] = {}

        # Generate moves.tf
        if result.moves:
            moves_path = output_dir / "moves.tf"
            self.generate_moved_file(result.moves, moves_path)
            generated["moves.tf"] = moves_path

        # Generate imports.tf
        if result.imports:
            import_gen = ImportBlockGenerator(config=self.config)
            imports_path = output_dir / "imports.tf"
            import_gen.generate_import_file(result.imports, imports_path)
            generated["imports.tf"] = imports_path

            # Also generate legacy import script
            script_path = output_dir / "import.sh"
            import_gen.generate_import_script(result.imports, script_path)
            generated["import.sh"] = script_path

        return generated


class ModuleMovedBlockGenerator:
    """
    Generate moved blocks for migrating resources INTO local modules.

    Level 5 Enhancement: When extracting related resources into a local module,
    generate moved blocks that change the address from root to module.

    Example:
        moved {
          from = aws_vpc.production_a1b2
          to   = module.vpc_production.aws_vpc.this
        }
    """

    def generate_module_moves(
        self,
        module_name: str,
        resources: list[tuple[str, str, str]],
    ) -> list[MovedBlock]:
        """
        Generate moved blocks for module extraction.

        Args:
            module_name: Name of the local module
            resources: List of (resource_type, old_name, new_name_in_module)

        Returns:
            List of MovedBlock objects
        """
        moves = []

        for resource_type, old_name, new_name in resources:
            moves.append(
                MovedBlock(
                    from_address=f"{resource_type}.{old_name}",
                    to_address=f"module.{module_name}.{resource_type}.{new_name}",
                )
            )

        return moves

    def generate_module_moves_file(
        self,
        module_moves: dict[str, list[MovedBlock]],
        output_path: Path,
    ) -> None:
        """
        Generate module-moves.tf file.

        Args:
            module_moves: Dict mapping module name to its moved blocks
            output_path: Path to write the file
        """
        if not module_moves:
            return

        lines = [
            "# ═══════════════════════════════════════════════════════════════════════════════",
            "# Auto-generated by RepliMap",
            "# These blocks move resources INTO local modules",
            "# ═══════════════════════════════════════════════════════════════════════════════",
            "#",
            "# Requires Terraform 1.1+",
            "#",
            "# After applying, resources will be organized into local modules",
            "# while maintaining their AWS state.",
            "#",
            "# ═══════════════════════════════════════════════════════════════════════════════",
            "",
        ]

        for module_name, moves in module_moves.items():
            lines.append(f"# Module: {module_name}")
            lines.append("")
            for move in moves:
                lines.append(move.render())
                lines.append("")

        output_path.write_text("\n".join(lines))
        logger.info(
            f"Wrote module-moves.tf: {sum(len(m) for m in module_moves.values())} moves"
        )
