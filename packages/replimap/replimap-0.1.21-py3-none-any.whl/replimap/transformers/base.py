"""
Base Transformer for RepliMap.

Transformers process the resource graph to modify configurations
before Terraform generation. This includes sanitization, downsizing,
renaming, and network remapping.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from replimap.core import GraphEngine


logger = logging.getLogger(__name__)


class BaseTransformer(ABC):
    """
    Abstract base class for graph transformers.

    Transformers modify the resource graph in place. They are executed
    in sequence by the TransformationPipeline.

    Subclasses must implement:
    - name: Human-readable name for logging
    - transform(): The transformation logic
    """

    name: str = "BaseTransformer"

    @abstractmethod
    def transform(self, graph: GraphEngine) -> GraphEngine:
        """
        Transform the resource graph.

        Args:
            graph: The GraphEngine to transform

        Returns:
            The transformed GraphEngine (may be same instance)
        """
        pass


class TransformationPipeline:
    """
    Manages execution of multiple transformers in sequence.

    Transformers are executed in the order they are added.
    Each transformer receives the output of the previous one.
    """

    def __init__(self) -> None:
        """Initialize an empty pipeline."""
        self._transformers: list[BaseTransformer] = []

    def add(self, transformer: BaseTransformer) -> TransformationPipeline:
        """
        Add a transformer to the pipeline.

        Args:
            transformer: The transformer to add

        Returns:
            Self for method chaining
        """
        self._transformers.append(transformer)
        logger.debug(f"Added transformer: {transformer.name}")
        return self

    def execute(self, graph: GraphEngine) -> GraphEngine:
        """
        Execute all transformers in sequence.

        Args:
            graph: The input GraphEngine

        Returns:
            The transformed GraphEngine
        """
        logger.info(
            f"Executing transformation pipeline ({len(self._transformers)} transformers)"
        )

        current = graph
        for transformer in self._transformers:
            logger.info(f"Running transformer: {transformer.name}")
            current = transformer.transform(current)

        logger.info("Transformation pipeline complete")
        return current

    def __len__(self) -> int:
        return len(self._transformers)

    def __repr__(self) -> str:
        names = [t.name for t in self._transformers]
        return f"TransformationPipeline({names})"
