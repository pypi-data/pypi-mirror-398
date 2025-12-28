"""
Core Kaizen framework components.

This module contains the foundational classes and interfaces for the Kaizen framework:
- Framework initialization and management
- Base classes and interfaces
- Agent creation and management
"""

from .agents import Agent, AgentManager
from .config import KaizenConfig, MemoryProvider, OptimizationEngine

# PERFORMANCE OPTIMIZED: Use lightweight imports for <100ms startup
from .framework import Kaizen

# Signature classes available in kaizen.signatures (Option 3: DSPy-inspired)

__all__ = [
    "Kaizen",
    "MemoryProvider",
    "OptimizationEngine",
    "KaizenConfig",
    "Agent",
    "AgentManager",
]
