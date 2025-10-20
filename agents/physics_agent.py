"""
Physics Agent: Applies physics properties to OpenUSD scenes.
"""

import os
from typing import List, Optional, Dict, Any
from pathlib import Path
import autogen
from pxr import Usd, UsdGeom, UsdPhysics, PhysxSchema, Gf, Sdf

from models.physics_commands import (
    PhysicsCommand,
    ApplyRigidBody,
    SetFriction,
    ApplyCollider,
    CreateJoint,
    ConfigureSolver,
    ApplyForce,
    PhysicsConfiguration,
    ColliderType,
    JointType,
)


class PhysicsAgent:
    """
    Agent responsible for adding physics properties to OpenUSD scenes.
    Uses AutoGen for LLM-powered assistance when needed.
    """

    def __init__(self, llm_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Physics agent.

        Args:
            llm_config: Configuration for the AutoGen LLM
        """
        # Set up AutoGen assistant
        if llm_config is None:
            llm_config = {
                "config_list": [{
                    "model": "gpt-4",
                    "api_key": os.getenv("OPENAI_API_KEY"),
                }],
                "timeout": 120,
                "temperature": 0.1,
            }

        self.assistant = autogen.AssistantAgent(
            name="Physics",
            system_message=self._get_system_message(),
            llm_config=llm_config,
        )

    def _get_system_message(self) -> str:
        """Get the system message for the AutoGen assistant."""
        return """You are the Physics agent, an expert in rigid body dynamics and physics simulation.
Your role is to:
1. Parse structured physics commands (ApplyRigidBody, SetFriction, ConfigureSolver, etc.)
2. Apply physics schemas and properties to existing USD prims
3. Configure physics scenes with appropriate solver settings
4. Create joints and constraints between rigid bodies
5. Ensure physics properties are correctly set for stable simulation

You have access to:
- The complete OpenUSD Physics API (UsdPhysics module)
- PhysX-specific schemas (PhysxSchema module)
- NVIDIA Newton physics integration (when configured)

Always ensure physics properties are physically plausible and will result in stable simulations.
"""

    def apply_physics(
        self,
        input_usd_path: Path,
        commands: List[PhysicsCommand],
        output_path: Optional[Path] = None,
    ) -> Usd.Stage:
        """
        Apply physics properties to an existing USD scene.

        Args:
            input_usd_path: Path to the input USD file
            commands: List of physics commands to execute
            output_path: Path to save the modified USD (if None, modifies in place)

        Returns:
            The modified USD stage

        Raises:
            ValueError: If commands are invalid
            RuntimeError: If physics application fails
        """
        # Open existing USD stage
        stage = Usd.Stage.Open(str(input_usd_path))
        if not stage:
            raise RuntimeError(f"Failed to open USD file: {input_usd_path}")

        # Execute each command
        for i, command in enumerate(commands):
            try:
                self._execute_command(stage, command)
            except Exception as e:
                raise RuntimeError(
                    f"Failed to execute command {i} ({type(command).__name__}): {e}"
                ) from e

        # Save the stage
        if output_path:
            stage.Export(str(output_path))
        else:
            stage.Save()

        return stage

    def _execute_command(self, stage: Usd.Stage, command: PhysicsCommand) -> None:
        """Execute a single physics command on the stage."""
        if isinstance(command, ConfigureSolver):
            self._configure_solver(stage, command)
        elif isinstance(command, ApplyRigidBody):
            self._apply_rigid_body(stage, command)
        elif isinstance(command, SetFriction):
            self._set_friction(stage, command)
        elif isinstance(command, ApplyCollider):
            self._apply_collider(stage, command)
        elif isinstance(command, CreateJoint):
            self._create_joint(stage, command)
        elif isinstance(command, ApplyForce):
            self._apply_force(stage, command)
        else:
            raise ValueError(f"Unknown command type: {type(command)}")

    def _configure_solver(self, stage: Usd.Stage, command: ConfigureSolver) -> None:
        """Configure the physics scene and solver settings."""
        # Create or get physics scene
        scene_prim = stage.GetPrimAtPath(command.scene_path)
        if not scene_prim:
            scene_prim = stage.DefinePrim(command.scene_path)

        physics_scene = UsdPhysics.Scene.Define(stage, command.scene_path)

        # Set gravity
        settings = command.settings
        physics_scene.CreateGravityDirectionAttr().Set(
            Gf.Vec3f(
                settings.gravity.x,
                settings.gravity.y,
                settings.gravity.z
            )
        )
        gravity_magnitude = (
            settings.gravity.x**2 + settings.gravity.y**2 + settings.gravity.z**2
        ) ** 0.5
        physics_scene.CreateGravityMagnitudeAttr().Set(gravity_magnitude)

        # Apply PhysX-specific settings
        physx_scene = PhysxSchema.PhysxSceneAPI.Apply(scene_prim)

        # Set timestep
        physx_scene.CreateTimeStepsPerSecondAttr().Set(1.0 / settings.time_step)

        # Set solver iterations
        physx_scene.CreateSolverTypeAttr().Set("TGS")  # Temporal Gauss-Seidel

        # Enable/disable features
        if settings.enable_ccd:
            physx_scene.CreateEnableCCDAttr().Set(True)

        if settings.enable_stabilization:
            physx_scene.CreateEnableStabilizationAttr().Set(True)

        # Set broadphase type
        if settings.broadphase_type == "GPU":
            physx_scene.CreateBroadphaseTypeAttr().Set("GPU")
        elif settings.broadphase_type == "MBP":
            physx_scene.CreateBroadphaseTypeAttr().Set("MBP")
        else:
            physx_scene.CreateBroadphaseTypeAttr().Set("SAP")

    def _apply_rigid_body(self, stage: Usd.Stage, command: ApplyRigidBody) -> None:
        """Apply rigid body physics to a prim."""
        prim = stage.GetPrimAtPath(command.prim_path)
        if not prim:
            raise ValueError(f"Prim not found: {command.prim_path}")

        # Apply RigidBodyAPI
        rigid_body = UsdPhysics.RigidBodyAPI.Apply(prim)

        # Set rigid body properties
        props = command.properties

        # Mass
        mass_api = UsdPhysics.MassAPI.Apply(prim)
        mass_api.CreateMassAttr().Set(props.mass)

        # Damping
        rigid_body.CreateLinearDampingAttr().Set(props.linear_damping)
        rigid_body.CreateAngularDampingAttr().Set(props.angular_damping)

        # Inertia tensor (if provided)
        if props.inertia_diagonal:
            mass_api.CreateDiagonalInertiaAttr().Set(
                Gf.Vec3f(
                    props.inertia_diagonal.x,
                    props.inertia_diagonal.y,
                    props.inertia_diagonal.z
                )
            )

        # Initial velocities
        rigid_body.CreateVelocityAttr().Set(
            Gf.Vec3f(
                props.initial_linear_velocity.x,
                props.initial_linear_velocity.y,
                props.initial_linear_velocity.z
            )
        )
        rigid_body.CreateAngularVelocityAttr().Set(
            Gf.Vec3f(
                props.initial_angular_velocity.x,
                props.initial_angular_velocity.y,
                props.initial_angular_velocity.z
            )
        )

        # Kinematic flag
        if command.is_kinematic:
            rigid_body.CreateKinematicEnabledAttr().Set(True)

    def _set_friction(self, stage: Usd.Stage, command: SetFriction) -> None:
        """Set friction properties on a collider."""
        prim = stage.GetPrimAtPath(command.prim_path)
        if not prim:
            raise ValueError(f"Prim not found: {command.prim_path}")

        # Get or create collision API
        collision_api = UsdPhysics.CollisionAPI.Get(stage, command.prim_path)
        if not collision_api:
            collision_api = UsdPhysics.CollisionAPI.Apply(prim)

        # Create material if it doesn't exist
        material_path = f"{command.prim_path}/PhysicsMaterial"
        material_prim = stage.GetPrimAtPath(material_path)

        if not material_prim:
            material_prim = stage.DefinePrim(material_path)

        material = UsdPhysics.MaterialAPI.Apply(material_prim)

        # Set friction properties
        props = command.properties
        material.CreateStaticFrictionAttr().Set(props.static_friction)
        material.CreateDynamicFrictionAttr().Set(props.dynamic_friction)
        material.CreateRestitutionAttr().Set(props.restitution)

        # Bind material to collision
        physics_material_api = UsdPhysics.MaterialAPI.Get(stage, material_path)
        collision_api.GetPrim().GetRelationship("physics:material").AddTarget(
            material_path
        )

    def _apply_collider(self, stage: Usd.Stage, command: ApplyCollider) -> None:
        """Apply a collision shape to a prim."""
        prim = stage.GetPrimAtPath(command.prim_path)
        if not prim:
            raise ValueError(f"Prim not found: {command.prim_path}")

        # Apply CollisionAPI
        collision_api = UsdPhysics.CollisionAPI.Apply(prim)

        # Apply mesh collision if needed
        if command.collider_type == ColliderType.MESH:
            mesh_collision = UsdPhysics.MeshCollisionAPI.Apply(prim)
            mesh_collision.CreateApproximationAttr().Set("meshSimplification")
        elif command.collider_type == ColliderType.CONVEX_HULL:
            mesh_collision = UsdPhysics.MeshCollisionAPI.Apply(prim)
            mesh_collision.CreateApproximationAttr().Set("convexHull")

        # Set collision group
        if command.collision_group != 0:
            collision_api.CreateCollisionEnabledAttr().Set(True)

        # Handle offset
        if command.offset.x != 0 or command.offset.y != 0 or command.offset.z != 0:
            xformable = UsdGeom.Xformable(prim)
            xformable.AddTranslateOp().Set(
                Gf.Vec3d(command.offset.x, command.offset.y, command.offset.z)
            )

    def _create_joint(self, stage: Usd.Stage, command: CreateJoint) -> None:
        """Create a joint between two rigid bodies."""
        body0 = stage.GetPrimAtPath(command.body0_path)
        body1 = stage.GetPrimAtPath(command.body1_path)

        if not body0:
            raise ValueError(f"Body0 not found: {command.body0_path}")
        if not body1:
            raise ValueError(f"Body1 not found: {command.body1_path}")

        # Create joint prim
        joint_prim = stage.DefinePrim(command.joint_path)
        props = command.properties

        # Apply appropriate joint type
        if props.joint_type == JointType.REVOLUTE:
            joint = UsdPhysics.RevoluteJoint.Define(stage, command.joint_path)
            joint.CreateAxisAttr().Set("X")  # Default axis
        elif props.joint_type == JointType.PRISMATIC:
            joint = UsdPhysics.PrismaticJoint.Define(stage, command.joint_path)
            joint.CreateAxisAttr().Set("X")
        elif props.joint_type == JointType.FIXED:
            joint = UsdPhysics.FixedJoint.Define(stage, command.joint_path)
        elif props.joint_type == JointType.SPHERICAL:
            joint = UsdPhysics.SphericalJoint.Define(stage, command.joint_path)
        elif props.joint_type == JointType.D6:
            joint = UsdPhysics.Joint.Define(stage, command.joint_path)
        else:
            raise ValueError(f"Unknown joint type: {props.joint_type}")

        # Set body relationships
        joint.CreateBody0Rel().SetTargets([command.body0_path])
        joint.CreateBody1Rel().SetTargets([command.body1_path])

        # Set local positions
        joint.CreateLocalPos0Attr().Set(
            Gf.Vec3f(command.local_pos0.x, command.local_pos0.y, command.local_pos0.z)
        )
        joint.CreateLocalPos1Attr().Set(
            Gf.Vec3f(command.local_pos1.x, command.local_pos1.y, command.local_pos1.z)
        )

        # Set joint limits
        if props.lower_limit is not None or props.upper_limit is not None:
            if props.lower_limit is not None:
                joint.CreateLowerLimitAttr().Set(props.lower_limit)
            if props.upper_limit is not None:
                joint.CreateUpperLimitAttr().Set(props.upper_limit)

        # Set joint drive
        if props.drive_enabled:
            drive_api = UsdPhysics.DriveAPI.Apply(joint_prim, "angular")
            drive_api.CreateTypeAttr().Set("force")
            drive_api.CreateStiffnessAttr().Set(props.stiffness)
            drive_api.CreateDampingAttr().Set(props.damping)
            drive_api.CreateMaxForceAttr().Set(props.max_force)

    def _apply_force(self, stage: Usd.Stage, command: ApplyForce) -> None:
        """Apply a force to a rigid body (for initial conditions or triggers)."""
        prim = stage.GetPrimAtPath(command.prim_path)
        if not prim:
            raise ValueError(f"Prim not found: {command.prim_path}")

        # Check if rigid body API is applied
        rigid_body = UsdPhysics.RigidBodyAPI.Get(stage, command.prim_path)
        if not rigid_body:
            raise ValueError(
                f"Prim does not have rigid body physics: {command.prim_path}"
            )

        # For initial forces, we set the velocity instead
        # (actual force application would happen during simulation)
        if command.is_impulse:
            # Apply as initial velocity
            force_vec = Gf.Vec3f(command.force.x, command.force.y, command.force.z)

            # Get mass to convert force to velocity
            mass_api = UsdPhysics.MassAPI.Get(stage, command.prim_path)
            if mass_api:
                mass = mass_api.GetMassAttr().Get()
                velocity = force_vec / mass
                rigid_body.CreateVelocityAttr().Set(velocity)

    def apply_from_config(
        self,
        input_usd_path: Path,
        config: PhysicsConfiguration,
        output_path: Optional[Path] = None,
    ) -> Usd.Stage:
        """
        Apply physics from a PhysicsConfiguration object.

        Args:
            input_usd_path: Path to input USD file
            config: Physics configuration with commands
            output_path: Path to save output (optional)

        Returns:
            The modified USD stage
        """
        return self.apply_physics(input_usd_path, config.commands, output_path)
