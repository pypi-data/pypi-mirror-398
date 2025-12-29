"""
Transformers for RepliMap.

Transformers modify the resource graph before Terraform generation:
- Sanitization: Remove sensitive data
- Downsizing: Reduce instance sizes for cost savings
- Renaming: Apply environment-specific naming patterns
- Network remapping: Update network references for new VPC
"""

from .base import BaseTransformer, TransformationPipeline
from .downsizer import DownsizeTransformer
from .network_remapper import NetworkRemapTransformer
from .renamer import RenamingTransformer
from .sanitizer import SanitizationTransformer

__all__ = [
    "BaseTransformer",
    "TransformationPipeline",
    "SanitizationTransformer",
    "DownsizeTransformer",
    "RenamingTransformer",
    "NetworkRemapTransformer",
]


def create_default_pipeline(
    downsize: bool = True,
    rename_pattern: str | None = None,
    sanitize: bool = True,
) -> TransformationPipeline:
    """
    Create a default transformation pipeline.

    Args:
        downsize: Whether to include instance downsizing
        rename_pattern: Optional renaming pattern (e.g., "prod:stage")
        sanitize: Whether to include sensitive data sanitization

    Returns:
        Configured TransformationPipeline
    """
    pipeline = TransformationPipeline()

    # Sanitization first (remove secrets before other transforms)
    if sanitize:
        pipeline.add(SanitizationTransformer())

    # Renaming (before network remap so names are consistent)
    if rename_pattern:
        pipeline.add(RenamingTransformer.from_pattern(rename_pattern))
    else:
        pipeline.add(RenamingTransformer())

    # Downsizing
    if downsize:
        pipeline.add(DownsizeTransformer())

    # Network remapping last (uses terraform_name which may have been renamed)
    pipeline.add(NetworkRemapTransformer())

    return pipeline
