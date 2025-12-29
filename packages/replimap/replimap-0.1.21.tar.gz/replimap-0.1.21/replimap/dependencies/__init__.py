"""
Dependency Explorer module for RepliMap.

Provides dependency analysis for resource modification/deletion:
- What resources may be affected if I modify this?
- What are the AWS API-detected dependencies?
- What should I review before making changes?

IMPORTANT DISCLAIMER:
This analysis is based on AWS API metadata ONLY.
Application-level dependencies CANNOT be detected, including:
- Hardcoded IP addresses in application code
- DNS-based service discovery
- Configuration files referencing other resources
- Cross-account references
- External service integrations

ALWAYS review application logs, code, and configuration
before making any infrastructure changes.

This is a Pro+ feature ($79/mo).
"""

from replimap.dependencies.graph_builder import DependencyGraphBuilder
from replimap.dependencies.impact_calculator import (
    RESOURCE_IMPACT_SCORES,
    ImpactCalculator,
)
from replimap.dependencies.models import (
    DISCLAIMER_FULL,
    DISCLAIMER_SHORT,
    STANDARD_LIMITATIONS,
    # Backward compatibility aliases
    BlastNode,
    BlastRadiusResult,
    BlastZone,
    # New names
    DependencyEdge,
    DependencyExplorerResult,
    DependencyType,
    DependencyZone,
    ImpactLevel,
    ResourceNode,
)
from replimap.dependencies.reporter import (
    # Backward compatibility alias
    BlastRadiusReporter,
    DependencyExplorerReporter,
)

__all__ = [
    # Disclaimer constants
    "DISCLAIMER_FULL",
    "DISCLAIMER_SHORT",
    "STANDARD_LIMITATIONS",
    # New model names
    "ResourceNode",
    "DependencyExplorerResult",
    "DependencyZone",
    "DependencyEdge",
    "DependencyType",
    "ImpactLevel",
    # New class names
    "DependencyGraphBuilder",
    "ImpactCalculator",
    "DependencyExplorerReporter",
    # Constants
    "RESOURCE_IMPACT_SCORES",
    # Backward compatibility aliases (deprecated)
    "BlastNode",
    "BlastRadiusResult",
    "BlastZone",
    "BlastRadiusReporter",
]
