"""
Data models for the autonomous simulation platform.

All command schemas are defined using Pydantic for type safety and validation:
- scene_commands: Geometry, materials, lights, cameras
- physics_commands: Rigid bodies, colliders, joints, solver
- optimization_commands: Optimization problems, parameters, metrics
"""

from .scene_commands import (
    CreatePrim,
    SetMaterial,
    SetTransform,
    CreateLight,
    CreateCamera,
    SceneCommand,
    SceneConfiguration,
    Vec3,
    Quaternion,
    RGBAColor,
    PrimType,
)

from .physics_commands import (
    ApplyRigidBody,
    SetFriction,
    ApplyCollider,
    CreateJoint,
    ConfigureSolver,
    PhysicsCommand,
    PhysicsConfiguration,
    RigidBodyProperties,
    FrictionProperties,
    SolverSettings,
)

from .optimization_commands import (
    OptimizationProblem,
    OptimizationResult,
    OptimizableParameter,
    MetricDefinition,
    OptimizerConfig,
    TerminationCondition,
    SimulationSettings,
    OptimizationCommand,
    OptimizerType,
    ParameterType,
    OptimizationObjective,
)

__all__ = [
    # Scene Commands
    "CreatePrim",
    "SetMaterial",
    "SetTransform",
    "CreateLight",
    "CreateCamera",
    "SceneCommand",
    "SceneConfiguration",
    "Vec3",
    "Quaternion",
    "RGBAColor",
    "PrimType",
    # Physics Commands
    "ApplyRigidBody",
    "SetFriction",
    "ApplyCollider",
    "CreateJoint",
    "ConfigureSolver",
    "PhysicsCommand",
    "PhysicsConfiguration",
    "RigidBodyProperties",
    "FrictionProperties",
    "SolverSettings",
    # Optimization Commands
    "OptimizationProblem",
    "OptimizationResult",
    "OptimizableParameter",
    "MetricDefinition",
    "OptimizerConfig",
    "TerminationCondition",
    "SimulationSettings",
    "OptimizationCommand",
    "OptimizerType",
    "ParameterType",
    "OptimizationObjective",
]
