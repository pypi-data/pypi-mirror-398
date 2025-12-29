"""
Renderers for RepliMap.

Renderers convert the resource graph to output formats:
- Terraform HCL (Free+)
- CloudFormation YAML (Solo+)
- Pulumi Python (Pro+)

Level 2-5 enhancements available via EnhancedTerraformRenderer.
"""

# Level 2-5 Enhanced Components
from .audit_annotator import AuditAnnotator, AuditFinding, SecurityCheckRunner
from .base import BaseRenderer
from .cloudformation import CloudFormationRenderer
from .file_router import FileRoute, FileStructure, SemanticFileRouter
from .import_generator import ImportBlockGenerator, ImportMapping
from .name_generator import NameRegistry, SmartNameGenerator
from .pulumi import PulumiRenderer
from .refactoring import (
    ModuleMovedBlockGenerator,
    MovedBlock,
    RefactoringEngine,
    RefactoringResult,
    ResourceMapping,
    StateManifest,
)
from .terraform import TerraformRenderer
from .terraform_v2 import EnhancedTerraformRenderer, create_renderer
from .variable_extractor import ExtractedVariable, VariableExtractor

__all__ = [
    # Base renderers
    "BaseRenderer",
    "CloudFormationRenderer",
    "PulumiRenderer",
    "TerraformRenderer",
    # Enhanced Terraform renderer (recommended)
    "EnhancedTerraformRenderer",
    "create_renderer",
    # Naming
    "SmartNameGenerator",
    "NameRegistry",
    # Import/Refactoring
    "ImportBlockGenerator",
    "ImportMapping",
    "RefactoringEngine",
    "RefactoringResult",
    "ResourceMapping",
    "MovedBlock",
    "StateManifest",
    "ModuleMovedBlockGenerator",
    # File routing
    "SemanticFileRouter",
    "FileRoute",
    "FileStructure",
    # Variables
    "VariableExtractor",
    "ExtractedVariable",
    # Audit
    "AuditAnnotator",
    "AuditFinding",
    "SecurityCheckRunner",
]
