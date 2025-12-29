"""
Patterns module for RepliMap.

Contains pattern detection and local module extraction functionality.
"""

from replimap.patterns.local_module import (
    ExtractionPlan,
    LocalModuleExtractor,
    ModuleGenerator,
    ModuleSuggestion,
)

__all__ = [
    "ExtractionPlan",
    "LocalModuleExtractor",
    "ModuleGenerator",
    "ModuleSuggestion",
]
