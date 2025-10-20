"""
Multi-agent system for autonomous simulation design.

This package contains all agents for the autonomous simulation platform:
- SceneGraphAgent: Generates 3D scenes from structured commands
- PhysicsAgent: Applies physics properties to scenes
- ArchitectAgent: Natural language orchestration and coordination
- ValidatorAgent: Static analysis and quality assurance
- OptimizationAgent: Gradient-based parameter optimization
"""

from .scene_graph_agent import SceneGraphAgent
from .physics_agent import PhysicsAgent
from .architect_agent import ArchitectAgent
from .validator_agent import ValidatorAgent
from .optimization_agent import OptimizationAgent

__all__ = [
    "SceneGraphAgent",
    "PhysicsAgent",
    "ArchitectAgent",
    "ValidatorAgent",
    "OptimizationAgent",
]
