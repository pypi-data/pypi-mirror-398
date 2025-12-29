"""
Base Renderer for RepliMap.

Defines the abstract interface for all output renderers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from replimap.core import GraphEngine


class BaseRenderer(ABC):
    """
    Abstract base class for output renderers.

    Renderers convert the resource graph to Infrastructure-as-Code
    formats like Terraform, CloudFormation, or Pulumi.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of this renderer."""
        ...

    @property
    @abstractmethod
    def format_name(self) -> str:
        """Technical name of the output format."""
        ...

    @abstractmethod
    def render(self, graph: GraphEngine, output_dir: Path) -> dict[str, Path]:
        """
        Render the graph to output files.

        Args:
            graph: The GraphEngine containing resources
            output_dir: Directory to write output files

        Returns:
            Dictionary mapping filenames to their full paths
        """
        ...

    @abstractmethod
    def preview(self, graph: GraphEngine) -> dict[str, list[str]]:
        """
        Preview what would be generated without writing files.

        Args:
            graph: The GraphEngine containing resources

        Returns:
            Dictionary mapping filenames to lists of resource IDs
        """
        ...

    def validate(self, graph: GraphEngine) -> list[str]:
        """
        Validate the graph can be rendered.

        Args:
            graph: The GraphEngine to validate

        Returns:
            List of validation warnings (empty if valid)
        """
        return []
