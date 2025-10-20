"""
Pydantic models for physics commands.
These models define the structured input schema for the Physics agent.
"""

from typing import Literal, Optional, Union, List
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

from .scene_commands import Vec3


class ColliderType(str, Enum):
    """Collision shape types."""
    BOX = "Box"
    SPHERE = "Sphere"
    CAPSULE = "Capsule"
    CYLINDER = "Cylinder"
    MESH = "Mesh"
    CONVEX_HULL = "ConvexHull"


class RigidBodyProperties(BaseModel):
    """Properties for a rigid body."""
    mass: float = Field(gt=0.0, description="Mass in kilograms")
    linear_damping: float = Field(default=0.0, ge=0.0, description="Linear damping coefficient")
    angular_damping: float = Field(default=0.05, ge=0.0, description="Angular damping coefficient")

    # Inertia tensor (optional, computed from mass and shape if not provided)
    inertia_diagonal: Optional[Vec3] = Field(
        default=None,
        description="Diagonal of the inertia tensor"
    )

    # Initial velocities
    initial_linear_velocity: Vec3 = Field(
        default=Vec3(x=0.0, y=0.0, z=0.0),
        description="Initial linear velocity"
    )
    initial_angular_velocity: Vec3 = Field(
        default=Vec3(x=0.0, y=0.0, z=0.0),
        description="Initial angular velocity"
    )


class ApplyRigidBody(BaseModel):
    """Command to apply rigid body physics to a primitive."""
    command_type: Literal["ApplyRigidBody"] = "ApplyRigidBody"

    prim_path: str = Field(
        ...,
        description="USD path to the primitive",
        pattern=r"^/[a-zA-Z0-9_/]+$"
    )

    properties: RigidBodyProperties = Field(..., description="Rigid body properties")

    is_kinematic: bool = Field(
        default=False,
        description="If true, body is kinematic (controlled, not simulated)"
    )


class FrictionProperties(BaseModel):
    """Friction properties for a collider."""
    static_friction: float = Field(ge=0.0, le=1.0, description="Static friction coefficient")
    dynamic_friction: float = Field(ge=0.0, le=1.0, description="Dynamic friction coefficient")
    restitution: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Coefficient of restitution (bounciness)"
    )


class SetFriction(BaseModel):
    """Command to set friction properties on a collider."""
    command_type: Literal["SetFriction"] = "SetFriction"

    prim_path: str = Field(
        ...,
        description="USD path to the primitive with collider",
        pattern=r"^/[a-zA-Z0-9_/]+$"
    )

    properties: FrictionProperties = Field(..., description="Friction properties")


class ApplyCollider(BaseModel):
    """Command to apply a collision shape to a primitive."""
    command_type: Literal["ApplyCollider"] = "ApplyCollider"

    prim_path: str = Field(
        ...,
        description="USD path to the primitive",
        pattern=r"^/[a-zA-Z0-9_/]+$"
    )

    collider_type: ColliderType = Field(..., description="Type of collision shape")

    # Collider offset from the prim's origin
    offset: Vec3 = Field(
        default=Vec3(x=0.0, y=0.0, z=0.0),
        description="Offset of collider from prim origin"
    )

    # Collision filtering
    collision_group: int = Field(
        default=0,
        ge=0,
        description="Collision group for filtering"
    )


class JointType(str, Enum):
    """Joint types for articulated bodies."""
    REVOLUTE = "Revolute"
    PRISMATIC = "Prismatic"
    FIXED = "Fixed"
    SPHERICAL = "Spherical"
    D6 = "D6"  # 6-DOF configurable joint


class JointProperties(BaseModel):
    """Properties for a joint."""
    joint_type: JointType = Field(..., description="Type of joint")

    # Joint limits
    lower_limit: Optional[float] = Field(default=None, description="Lower joint limit")
    upper_limit: Optional[float] = Field(default=None, description="Upper joint limit")

    # Joint drive (motor)
    drive_enabled: bool = Field(default=False, description="Enable joint drive")
    stiffness: float = Field(default=0.0, ge=0.0, description="Drive stiffness")
    damping: float = Field(default=0.0, ge=0.0, description="Drive damping")
    max_force: float = Field(default=float('inf'), gt=0.0, description="Maximum drive force")

    # Joint axis (for revolute/prismatic)
    axis: Vec3 = Field(
        default=Vec3(x=1.0, y=0.0, z=0.0),
        description="Joint axis of rotation/translation"
    )


class CreateJoint(BaseModel):
    """Command to create a joint between two bodies."""
    command_type: Literal["CreateJoint"] = "CreateJoint"

    joint_path: str = Field(
        ...,
        description="USD path for the joint",
        pattern=r"^/[a-zA-Z0-9_/]+$"
    )

    body0_path: str = Field(..., description="USD path to the first body (parent)")
    body1_path: str = Field(..., description="USD path to the second body (child)")

    properties: JointProperties = Field(..., description="Joint properties")

    # Joint frame positions
    local_pos0: Vec3 = Field(
        default=Vec3(x=0.0, y=0.0, z=0.0),
        description="Joint position in body0 frame"
    )
    local_pos1: Vec3 = Field(
        default=Vec3(x=0.0, y=0.0, z=0.0),
        description="Joint position in body1 frame"
    )


class SolverSettings(BaseModel):
    """Physics solver configuration."""
    # Timestep
    time_step: float = Field(
        default=1.0/60.0,
        gt=0.0,
        le=1.0/30.0,
        description="Physics timestep in seconds"
    )

    # Solver iterations
    position_iterations: int = Field(
        default=4,
        ge=1,
        le=255,
        description="Number of position solver iterations"
    )
    velocity_iterations: int = Field(
        default=1,
        ge=1,
        le=255,
        description="Number of velocity solver iterations"
    )

    # Gravity
    gravity: Vec3 = Field(
        default=Vec3(x=0.0, y=0.0, z=-9.81),
        description="Gravity vector"
    )

    # Performance settings
    enable_ccd: bool = Field(
        default=False,
        description="Enable continuous collision detection"
    )
    enable_stabilization: bool = Field(
        default=True,
        description="Enable solver stabilization"
    )

    # Broadphase settings
    broadphase_type: Literal["SAP", "MBP", "GPU"] = Field(
        default="GPU",
        description="Broadphase algorithm (SAP=Sweep and Prune, MBP=Multi Box Pruning)"
    )


class ConfigureSolver(BaseModel):
    """Command to configure the physics solver."""
    command_type: Literal["ConfigureSolver"] = "ConfigureSolver"

    scene_path: str = Field(
        default="/World/PhysicsScene",
        description="USD path to the physics scene",
        pattern=r"^/[a-zA-Z0-9_/]+$"
    )

    settings: SolverSettings = Field(..., description="Solver settings")


class ApplyForce(BaseModel):
    """Command to apply a force to a rigid body."""
    command_type: Literal["ApplyForce"] = "ApplyForce"

    prim_path: str = Field(
        ...,
        description="USD path to the rigid body",
        pattern=r"^/[a-zA-Z0-9_/]+$"
    )

    force: Vec3 = Field(..., description="Force vector to apply")
    position: Optional[Vec3] = Field(
        default=None,
        description="Position to apply force (None = center of mass)"
    )
    is_impulse: bool = Field(
        default=False,
        description="If true, apply as impulse instead of continuous force"
    )


# Union type for all physics commands
PhysicsCommand = Union[
    ApplyRigidBody,
    SetFriction,
    ApplyCollider,
    CreateJoint,
    ConfigureSolver,
    ApplyForce,
]


class PhysicsConfiguration(BaseModel):
    """Complete physics configuration with multiple commands."""
    configuration_name: str = Field(..., description="Name of the physics configuration")
    description: Optional[str] = Field(default=None, description="Description")
    commands: List[PhysicsCommand] = Field(..., description="List of physics commands to execute")
