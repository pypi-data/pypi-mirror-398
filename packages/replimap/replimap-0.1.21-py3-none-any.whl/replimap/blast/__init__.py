"""
Blast Radius module for RepliMap.

DEPRECATED: This module has been renamed to 'dependencies'.
All imports are re-exported from the new location for backward compatibility.

See replimap.dependencies for the new API.
"""

import warnings

# Issue deprecation warning when this module is imported
warnings.warn(
    "The 'replimap.blast' module is deprecated. "
    "Use 'replimap.dependencies' instead. "
    "This module will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export everything from dependencies module for backward compatibility
from replimap.dependencies import (  # noqa: E402
    DISCLAIMER_FULL,
    DISCLAIMER_SHORT,
    RESOURCE_IMPACT_SCORES,
    STANDARD_LIMITATIONS,
    # Backward compatibility names
    BlastNode,
    BlastRadiusReporter,
    BlastRadiusResult,
    BlastZone,
    DependencyEdge,
    # New names also available
    DependencyExplorerReporter,
    DependencyExplorerResult,
    DependencyGraphBuilder,
    DependencyType,
    DependencyZone,
    ImpactCalculator,
    ImpactLevel,
    ResourceNode,
)

__all__ = [
    # Deprecated names (still work)
    "BlastNode",
    "BlastRadiusResult",
    "BlastZone",
    "BlastRadiusReporter",
    # Core classes
    "DependencyGraphBuilder",
    "ImpactCalculator",
    "DependencyEdge",
    "DependencyType",
    "ImpactLevel",
    # Constants
    "RESOURCE_IMPACT_SCORES",
    "DISCLAIMER_FULL",
    "DISCLAIMER_SHORT",
    "STANDARD_LIMITATIONS",
    # New names
    "ResourceNode",
    "DependencyExplorerResult",
    "DependencyZone",
    "DependencyExplorerReporter",
]
