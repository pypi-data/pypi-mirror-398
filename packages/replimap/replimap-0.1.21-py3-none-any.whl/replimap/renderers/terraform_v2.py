"""
Enhanced Terraform Renderer for RepliMap (v2).

Integrates all Level 2-5 enhancements from the Sovereign Engineer Protocol:
- SmartNameGenerator: Deterministic, collision-free naming
- ScopeEngine: Boundary recognition with escape hatches
- SemanticFileRouter: Organized file output
- VariableExtractor: DRY variable extraction
- AuditAnnotator: Noise-controlled security annotations
- ImportBlockGenerator: Terraform 1.5+ import blocks
- RefactoringEngine: Moved blocks for Brownfield adoption
- LocalModuleExtractor: Module pattern detection

The Seven Laws of Sovereign Code:
1. Determinism Above All - Same input = same output. Always.
2. Entropy is the Enemy - Hardcoded values are bugs in disguise.
3. Delegate to Terraform - Don't reinvent what Terraform does well.
4. Schema is Truth - Beautiful code is true code.
5. Refactor, Don't Recreate - Use moved blocks, never destroy to rename.
6. Mimic the Environment - Respect existing versions, backends, structure.
7. Know Thy Boundaries - Default VPC is read-only. Period.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from replimap.core.config import ConfigLoader, RepliMapConfig
from replimap.core.scope import DataSourceRenderer, ScopeEngine

# Import new components
from replimap.renderers.audit_annotator import AuditAnnotator, SecurityCheckRunner
from replimap.renderers.file_router import SemanticFileRouter
from replimap.renderers.import_generator import ImportBlockGenerator, ImportMapping
from replimap.renderers.name_generator import NameRegistry, SmartNameGenerator
from replimap.renderers.refactoring import RefactoringEngine
from replimap.renderers.terraform import TerraformRenderer
from replimap.renderers.variable_extractor import VariableExtractor

if TYPE_CHECKING:
    from replimap.core import GraphEngine
    from replimap.core.models import ResourceNode

logger = logging.getLogger(__name__)


class EnhancedTerraformRenderer(TerraformRenderer):
    """
    Enhanced Terraform Renderer with all Level 2-5 improvements.

    This renderer builds on TerraformRenderer and adds:
    - Deterministic naming via SmartNameGenerator
    - Boundary recognition via ScopeEngine
    - Semantic file routing via SemanticFileRouter
    - Variable extraction via VariableExtractor
    - Security annotations via AuditAnnotator
    - Import blocks via ImportBlockGenerator
    - Moved blocks via RefactoringEngine

    Usage:
        config = ConfigLoader().load()
        renderer = EnhancedTerraformRenderer(config=config)
        files = renderer.render(graph, output_dir)

    Configuration is loaded from .replimap.yaml if present.
    """

    def __init__(
        self,
        template_dir: Path | None = None,
        config: RepliMapConfig | None = None,
        working_dir: Path | None = None,
    ) -> None:
        """
        Initialize the enhanced renderer.

        Args:
            template_dir: Path to Jinja2 templates (defaults to built-in)
            config: User configuration (loads from .replimap.yaml if None)
            working_dir: Working directory for Terraform operations
        """
        super().__init__(template_dir=template_dir)

        # Load configuration
        if config is None:
            loader = ConfigLoader(working_dir=working_dir)
            config = loader.load()
        self.config = config

        self.working_dir = working_dir or Path.cwd()

        # Initialize new components
        self.name_generator = SmartNameGenerator(user_config=config)
        self.name_registry = NameRegistry()
        self.scope_engine = ScopeEngine(config=config)
        self.file_router = SemanticFileRouter()
        self.variable_extractor = VariableExtractor()
        self.security_runner = SecurityCheckRunner()
        self.import_generator = ImportBlockGenerator(config=config)
        self.refactoring_engine = RefactoringEngine(
            working_dir=self.working_dir,
            config=config,
        )
        self.data_source_renderer = DataSourceRenderer()

        # Track resources by scope
        self._managed_resources: list[ResourceNode] = []
        self._readonly_resources: list[ResourceNode] = []
        self._skipped_resources: list[ResourceNode] = []

    def render(self, graph: GraphEngine, output_dir: Path) -> dict[str, Path]:
        """
        Render the graph to Terraform files with all enhancements.

        Args:
            graph: The GraphEngine containing resources
            output_dir: Directory to write .tf files

        Returns:
            Dictionary mapping filenames to their paths
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Rendering Terraform (enhanced) to {output_dir}")

        # Phase 1: Apply deterministic naming
        self._apply_smart_naming(graph)

        # Phase 2: Classify resources by scope
        self._classify_resources(graph)

        # Phase 3: Run security checks
        findings = self.security_runner.run_checks(list(graph.iter_resources()))
        annotator = AuditAnnotator(findings, config=self.config)

        # Phase 4: Extract variables
        variables = self.variable_extractor.analyze(list(graph.iter_resources()))

        # Phase 5: Route resources to files
        file_contents: dict[str, list[str]] = {}

        # Render managed resources
        for resource in self._managed_resources:
            self._render_resource(resource, graph, annotator, file_contents)

        # Render read-only resources as data sources
        if self._readonly_resources:
            data_content = self._render_data_sources()
            if "data.tf" not in file_contents:
                file_contents["data.tf"] = []
            file_contents["data.tf"].append(data_content)

        # Write files
        written_files: dict[str, Path] = {}
        for filename, contents in file_contents.items():
            file_path = output_dir / filename

            # Add file header with audit summary if applicable
            header = annotator.get_file_header_summary()
            if header:
                contents.insert(0, header)

            with open(file_path, "w") as f:
                f.write("\n\n".join(contents))
            written_files[filename] = file_path
            logger.info(f"Wrote {filename} ({len(contents)} resources)")

        # Generate supporting files
        self._generate_versions(output_dir, written_files)
        self._generate_providers(output_dir, written_files)
        self._generate_data_sources(output_dir, written_files)

        # Generate variables with extracted values
        self._generate_enhanced_variables(graph, variables, output_dir, written_files)

        # Generate outputs
        self._generate_outputs(graph, output_dir, written_files)

        # Phase 6: Generate import/refactoring files
        if self.config.should_generate_import_blocks():
            self._generate_import_files(output_dir, written_files)

        if self.config.should_generate_moved_blocks():
            self._generate_moved_files(output_dir, written_files)

        # Generate audit report if configured
        if self.config.get("audit.generate_report", True):
            report_path = output_dir / "audit-report.md"
            annotator.generate_report_file(report_path)
            written_files["audit-report.md"] = report_path

        # Run terraform fmt
        self._run_terraform_fmt(output_dir)

        return written_files

    def _apply_smart_naming(self, graph: GraphEngine) -> None:
        """
        Apply deterministic naming to all resources.

        This replaces the old _ensure_unique_names with SmartNameGenerator.
        Uses NameRegistry to ensure uniqueness and determinism.
        """
        for resource in graph.iter_resources():
            resource_type = str(resource.resource_type)

            # Register the resource and get deterministic name
            new_name = self.name_registry.register(
                resource_id=resource.id,
                original_name=resource.original_name or "",
                resource_type=resource_type,
            )

            # Update the resource
            resource.terraform_name = new_name
            logger.debug(f"Named {resource.id} as {resource_type}.{new_name}")

    def _classify_resources(self, graph: GraphEngine) -> None:
        """
        Classify resources into MANAGED, READ_ONLY, or SKIP.

        This implements the ScopeEngine for boundary recognition.
        """
        self._managed_resources = []
        self._readonly_resources = []
        self._skipped_resources = []

        for resource in graph.iter_resources():
            scope = self.scope_engine.determine_scope(resource)

            if scope.is_managed:
                self._managed_resources.append(resource)
            elif scope.is_read_only:
                self._readonly_resources.append(resource)
            else:
                self._skipped_resources.append(resource)
                logger.info(f"Skipping {resource.id}: {scope.reason}")

        logger.info(
            f"Resource classification: "
            f"{len(self._managed_resources)} managed, "
            f"{len(self._readonly_resources)} read-only, "
            f"{len(self._skipped_resources)} skipped"
        )

    def _render_resource(
        self,
        resource: ResourceNode,
        graph: GraphEngine,
        annotator: AuditAnnotator,
        file_contents: dict[str, list[str]],
    ) -> None:
        """
        Render a single resource with security annotations.

        Args:
            resource: The resource to render
            graph: The graph engine
            annotator: Audit annotator for security findings
            file_contents: Dict to accumulate file contents
        """
        template_name = self.TEMPLATE_MAPPING.get(resource.resource_type)

        # Use semantic file router if enabled
        if self.config.should_use_semantic_files():
            output_file = self.file_router.get_file_for_resource(
                str(resource.resource_type)
            )
        else:
            output_file = self.FILE_MAPPING.get(
                resource.resource_type,
                "main.tf",
            )

        if not template_name:
            logger.warning(f"No template for resource type: {resource.resource_type}")
            return

        try:
            template = self.env.get_template(template_name)
            rendered = template.render(resource=resource, graph=graph)

            # Add security annotations if present
            annotations = annotator.get_inline_annotations(resource.id)
            if annotations:
                rendered = f"{annotations}\n{rendered}"

            if output_file not in file_contents:
                file_contents[output_file] = []
            file_contents[output_file].append(rendered)

        except Exception as e:
            logger.error(f"Error rendering {resource.id}: {e}")

    def _render_data_sources(self) -> str:
        """
        Render read-only resources as data sources.

        Returns:
            HCL content for data sources
        """
        lines = [
            "# ═══════════════════════════════════════════════════════════════════════════════",
            "# READ-ONLY RESOURCES (Data Sources)",
            "# ═══════════════════════════════════════════════════════════════════════════════",
            "#",
            "# These resources are managed externally (Default VPC, shared resources, etc.)",
            "# RepliMap generates data sources to REFERENCE them, not MANAGE them.",
            "#",
            "# To convert to managed resources, update .replimap.yaml:",
            "#   scope:",
            "#     force_manage:",
            "#       - id:<resource-id>",
            "#",
            "# ═══════════════════════════════════════════════════════════════════════════════",
            "",
        ]

        for resource in self._readonly_resources:
            data_block = self.data_source_renderer.render_data_source(resource)
            if data_block:
                lines.append(data_block)
                lines.append("")

        return "\n".join(lines)

    def _generate_enhanced_variables(
        self,
        graph: GraphEngine,
        extracted_vars: list[Any],
        output_dir: Path,
        written_files: dict[str, Path],
    ) -> None:
        """
        Generate variables.tf with extracted variables.

        This replaces the parent's _generate_variables with enhanced extraction.
        """
        # Generate variables file from extractor
        self.variable_extractor.generate_variables_file(
            extracted_vars,
            output_dir / "variables.tf",
        )

        # Generate tfvars with actual values
        self.variable_extractor.generate_tfvars(
            extracted_vars,
            output_dir / "terraform.tfvars",
        )

        written_files["variables.tf"] = output_dir / "variables.tf"
        written_files["terraform.tfvars"] = output_dir / "terraform.tfvars"

        # Also generate the example file using parent method
        self._generate_tfvars_example(graph, output_dir, written_files)

    def _generate_import_files(
        self,
        output_dir: Path,
        written_files: dict[str, Path],
    ) -> None:
        """
        Generate import blocks for managed resources.

        Creates imports.tf with Terraform 1.5+ import blocks.
        """
        mappings: list[ImportMapping] = []

        for resource in self._managed_resources:
            mapping = ImportMapping(
                terraform_address=f"{resource.resource_type}.{resource.terraform_name}",
                aws_id=resource.id,
                resource_type=str(resource.resource_type),
                attributes=resource.config,
            )
            mappings.append(mapping)

        if mappings:
            imports_path = output_dir / "imports.tf"
            self.import_generator.generate_import_file(mappings, imports_path)
            written_files["imports.tf"] = imports_path

            # Also generate legacy import script
            script_path = output_dir / "import.sh"
            self.import_generator.generate_import_script(mappings, script_path)
            written_files["import.sh"] = script_path

    def _generate_moved_files(
        self,
        output_dir: Path,
        written_files: dict[str, Path],
    ) -> None:
        """
        Generate moved blocks for refactoring.

        Analyzes existing Terraform state and generates moved blocks
        for resources that need address changes.
        """
        result = self.refactoring_engine.analyze(self._managed_resources)

        if result.has_changes:
            logger.info(result.summary())

            generated = self.refactoring_engine.generate_files(result, output_dir)
            written_files.update(generated)

    def render_preview(self, graph: GraphEngine) -> dict[str, Any]:
        """
        Preview what would be generated without writing files.

        Returns detailed information about what the render would produce.

        Args:
            graph: The GraphEngine containing resources

        Returns:
            Dictionary with preview information
        """
        # Apply naming
        self._apply_smart_naming(graph)

        # Classify resources
        self._classify_resources(graph)

        # Run security checks
        findings = self.security_runner.run_checks(list(graph.iter_resources()))

        # Extract variables
        variables = self.variable_extractor.analyze(list(graph.iter_resources()))

        # Build preview
        preview: dict[str, Any] = {
            "summary": {
                "total_resources": sum(1 for _ in graph.iter_resources()),
                "managed": len(self._managed_resources),
                "read_only": len(self._readonly_resources),
                "skipped": len(self._skipped_resources),
                "security_findings": len(findings),
                "extracted_variables": len(variables),
            },
            "files": {},
            "resources": {
                "managed": [r.id for r in self._managed_resources],
                "read_only": [r.id for r in self._readonly_resources],
                "skipped": [r.id for r in self._skipped_resources],
            },
            "security": {
                "critical": sum(1 for f in findings if f.severity == "CRITICAL"),
                "high": sum(1 for f in findings if f.severity == "HIGH"),
                "medium": sum(1 for f in findings if f.severity == "MEDIUM"),
                "low": sum(1 for f in findings if f.severity == "LOW"),
            },
            "naming": {
                resource.id: resource.terraform_name
                for resource in graph.iter_resources()
            },
        }

        # Preview file routing
        for resource in self._managed_resources:
            output_file = (
                self.file_router.get_file_for_resource(str(resource.resource_type))
                if self.config.should_use_semantic_files()
                else self.FILE_MAPPING.get(resource.resource_type, "main.tf")
            )
            if output_file not in preview["files"]:
                preview["files"][output_file] = []
            preview["files"][output_file].append(resource.id)

        return preview


def create_renderer(
    working_dir: Path | None = None,
    config_path: Path | None = None,
) -> EnhancedTerraformRenderer:
    """
    Factory function to create an EnhancedTerraformRenderer.

    Convenience function that handles configuration loading.

    Args:
        working_dir: Working directory for Terraform operations
        config_path: Explicit path to .replimap.yaml

    Returns:
        Configured EnhancedTerraformRenderer instance
    """
    loader = ConfigLoader(working_dir=working_dir)
    config = loader.load(config_path=config_path)

    return EnhancedTerraformRenderer(
        config=config,
        working_dir=working_dir,
    )
