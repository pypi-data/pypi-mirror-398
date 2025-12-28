"""
Advanced AI node base class for Kaizen framework.

This module provides the AINodeBase class for creating signature-aware AI nodes
that integrate with the Kaizen framework's declarative programming features.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, Optional

from kailash.nodes.base import Node, NodeParameter

if TYPE_CHECKING:
    from ..signatures import Signature


class AINodeBase(Node, ABC):
    """
    Base class for AI nodes with signature support in Kaizen framework.

    Extends Kailash Node with signature-based programming capabilities,
    enabling declarative AI workflow construction.

    Examples:
        >>> class CustomAINode(AINodeBase):
        ...     def get_parameters(self):
        ...         return {
        ...             "input_text": NodeParameter(name="input_text", type=str, required=True)
        ...         }
        ...
        ...     def run(self, **kwargs):
        ...         return {"result": f"Processed: {kwargs['input_text']}"}
    """

    def __init__(self, id: str, signature: Optional["Signature"] = None, **kwargs):
        """
        Initialize AI node with optional signature.

        Args:
            id: Unique node identifier
            signature: Optional signature for declarative programming
            **kwargs: Additional node configuration
        """
        super().__init__(id=id, **kwargs)
        self.signature = signature
        self._execution_pattern = "direct"  # direct, cot, react

    @abstractmethod
    def get_parameters(self) -> Dict[str, NodeParameter]:
        """
        Define node parameters.

        Returns:
            Dictionary mapping parameter names to NodeParameter objects
        """
        pass

    @abstractmethod
    def run(self, **kwargs) -> Dict[str, Any]:
        """
        Execute node logic.

        Args:
            **kwargs: Node input parameters

        Returns:
            Dictionary with execution results
        """
        pass

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Async execution interface (default implementation calls run).

        Args:
            **kwargs: Node input parameters

        Returns:
            Dictionary with execution results
        """
        return self.run(**kwargs)

    def set_signature(self, signature: "SignatureBase"):
        """
        Set or update the node's signature.

        Args:
            signature: Signature object defining inputs/outputs
        """
        self.signature = signature

    def set_execution_pattern(self, pattern: str):
        """
        Set the execution pattern for the node.

        Args:
            pattern: Execution pattern ("direct", "cot", "react")
        """
        if pattern not in ["direct", "cot", "react"]:
            raise ValueError(f"Invalid execution pattern: {pattern}")
        self._execution_pattern = pattern

    def get_signature_info(self) -> Dict[str, Any]:
        """
        Get signature information for the node.

        Returns:
            Dictionary with signature details
        """
        if self.signature is None:
            return {"has_signature": False}

        return {
            "has_signature": True,
            "signature_name": getattr(self.signature, "name", "unnamed"),
            "signature_description": getattr(self.signature, "description", ""),
            "execution_pattern": self._execution_pattern,
        }

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert node to dictionary representation.

        Returns:
            Dictionary representation of the node
        """
        base_dict = super().to_dict() if hasattr(super(), "to_dict") else {}
        base_dict.update(
            {
                "id": self.id,
                "signature_info": self.get_signature_info(),
                "execution_pattern": self._execution_pattern,
            }
        )
        return base_dict


# Export for interfaces.py import
__all__ = ["AINodeBase"]
