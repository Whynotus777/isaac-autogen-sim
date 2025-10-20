"""
SceneGraph Agent: Generates OpenUSD scenes from structured commands.
"""

import os
from typing import List, Optional, Dict, Any
from pathlib import Path
try:
    from autogen_agentchat import AssistantAgent
except ImportError:
    # Fallback for older autogen versions
    import autogen
    AssistantAgent = autogen.AssistantAgent
from pxr import Usd, UsdGeom, UsdShade, Gf, Sdf

from models.scene_commands import (
    SceneCommand,
    CreatePrim,
    SetTransform,
    SetMaterial,
    CreateLight,
    CreateCamera,
    SetRelationship,
    PrimType,
    SceneConfiguration,
)
from utils.generative_3d import CSMClient, SplineClient


class SceneGraphAgent:
    """
    Agent responsible for generating OpenUSD scene graphs from structured commands.
    Uses AutoGen for LLM-powered code generation when needed.
    """

    def __init__(
        self,
        llm_config: Optional[Dict[str, Any]] = None,
        csm_api_key: Optional[str] = None,
        spline_api_key: Optional[str] = None,
    ):
        """
        Initialize the SceneGraph agent.

        Args:
            llm_config: Configuration for the AutoGen LLM (API keys, model selection, etc.)
            csm_api_key: API key for CSM.ai (optional)
            spline_api_key: API key for Spline AI (optional)
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

        self.assistant = AssistantAgent(
            name="SceneGraph",
            system_message=self._get_system_message(),
            model_client=None,  # Will be configured with llm_config if needed
        )

        # Initialize 3D generation clients
        self.csm_client = None
        self.spline_client = None

        if csm_api_key or os.getenv("CSM_API_KEY"):
            try:
                self.csm_client = CSMClient(csm_api_key)
            except ValueError:
                pass  # API key not available

        if spline_api_key or os.getenv("SPLINE_API_KEY"):
            try:
                self.spline_client = SplineClient(spline_api_key)
            except ValueError:
                pass  # API key not available

    def _get_system_message(self) -> str:
        """Get the system message for the AutoGen assistant."""
        return """You are the SceneGraph agent, an expert in OpenUSD scene creation.
Your role is to:
1. Parse structured scene commands (CreatePrim, SetTransform, SetMaterial, etc.)
2. Generate Python code using the OpenUSD API to build the scene
3. Call generative 3D APIs when needed to create assets from text prompts
4. Ensure the scene is properly structured with correct hierarchies and references

You have access to:
- The complete OpenUSD Python API (pxr module)
- CSM.ai and Spline AI for generating 3D assets from text
- All scene command models defined in the system

Always generate clean, well-documented Python code that creates valid USD files.
"""

    def create_scene(
        self,
        commands: List[SceneCommand],
        output_path: Path,
        stage_up_axis: str = "Z",
    ) -> Usd.Stage:
        """
        Create a USD scene from a list of structured commands.

        Args:
            commands: List of scene commands to execute
            output_path: Path where the USD file will be saved
            stage_up_axis: Up axis for the stage (Y or Z)

        Returns:
            The created USD stage

        Raises:
            ValueError: If commands are invalid
            RuntimeError: If scene creation fails
        """
        # Create new USD stage
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        stage = Usd.Stage.CreateNew(str(output_path))
        UsdGeom.SetStageUpAxis(stage, stage_up_axis)

        # Set stage metadata
        stage.SetDefaultPrim(stage.GetPrimAtPath("/World"))

        # Create root prim
        UsdGeom.Xform.Define(stage, "/World")

        # Execute each command
        for i, command in enumerate(commands):
            try:
                self._execute_command(stage, command)
            except Exception as e:
                raise RuntimeError(f"Failed to execute command {i} ({type(command).__name__}): {e}") from e

        # Save the stage
        stage.Save()

        return stage

    def _execute_command(self, stage: Usd.Stage, command: SceneCommand) -> None:
        """Execute a single scene command on the stage."""
        if isinstance(command, CreatePrim):
            self._create_prim(stage, command)
        elif isinstance(command, SetTransform):
            self._set_transform(stage, command)
        elif isinstance(command, SetMaterial):
            self._set_material(stage, command)
        elif isinstance(command, CreateLight):
            self._create_light(stage, command)
        elif isinstance(command, CreateCamera):
            self._create_camera(stage, command)
        elif isinstance(command, SetRelationship):
            self._set_relationship(stage, command)
        else:
            raise ValueError(f"Unknown command type: {type(command)}")

    def _create_prim(self, stage: Usd.Stage, command: CreatePrim) -> None:
        """Create a primitive in the scene."""
        # Check if we need to generate from prompt
        if command.generate_from_prompt:
            asset_path = self._generate_3d_asset(command.generate_from_prompt)
            # Create a reference to the generated asset
            prim = stage.DefinePrim(command.prim_path)
            prim.GetReferences().AddReference(str(asset_path))
        else:
            # Create standard USD geometry
            if command.prim_type == PrimType.SPHERE:
                prim = UsdGeom.Sphere.Define(stage, command.prim_path)
            elif command.prim_type == PrimType.CUBE:
                prim = UsdGeom.Cube.Define(stage, command.prim_path)
            elif command.prim_type == PrimType.CYLINDER:
                prim = UsdGeom.Cylinder.Define(stage, command.prim_path)
            elif command.prim_type == PrimType.CONE:
                prim = UsdGeom.Cone.Define(stage, command.prim_path)
            elif command.prim_type == PrimType.PLANE:
                prim = UsdGeom.Mesh.Define(stage, command.prim_path)
                # Create a simple plane mesh
                prim.GetPointsAttr().Set([(-1, 0, -1), (1, 0, -1), (1, 0, 1), (-1, 0, 1)])
                prim.GetFaceVertexCountsAttr().Set([4])
                prim.GetFaceVertexIndicesAttr().Set([0, 1, 2, 3])
            elif command.prim_type == PrimType.XFORM:
                prim = UsdGeom.Xform.Define(stage, command.prim_path)
            else:
                prim = stage.DefinePrim(command.prim_path)

        # Set visibility
        imageable = UsdGeom.Imageable(stage.GetPrimAtPath(command.prim_path))
        if not command.visible:
            imageable.MakeInvisible()

        # Apply scale
        xformable = UsdGeom.Xformable(stage.GetPrimAtPath(command.prim_path))
        xformable.AddScaleOp().Set(
            Gf.Vec3f(command.scale.x, command.scale.y, command.scale.z)
        )

    def _set_transform(self, stage: Usd.Stage, command: SetTransform) -> None:
        """Set the transform of a primitive."""
        prim = stage.GetPrimAtPath(command.prim_path)
        if not prim:
            raise ValueError(f"Prim not found: {command.prim_path}")

        xformable = UsdGeom.Xformable(prim)

        if command.position:
            xformable.AddTranslateOp().Set(
                Gf.Vec3d(command.position.x, command.position.y, command.position.z)
            )

        if command.rotation:
            quat = Gf.Quatf(
                command.rotation.w,
                command.rotation.x,
                command.rotation.y,
                command.rotation.z
            )
            xformable.AddOrientOp().Set(quat)

        if command.scale:
            xformable.AddScaleOp().Set(
                Gf.Vec3f(command.scale.x, command.scale.y, command.scale.z)
            )

    def _set_material(self, stage: Usd.Stage, command: SetMaterial) -> None:
        """Set material properties on a primitive."""
        prim = stage.GetPrimAtPath(command.prim_path)
        if not prim:
            raise ValueError(f"Prim not found: {command.prim_path}")

        # Create material
        material_path = f"/World/Materials/{command.material_name}"
        material = UsdShade.Material.Define(stage, material_path)

        # Create PBR shader
        shader = UsdShade.Shader.Define(stage, f"{material_path}/Shader")
        shader.CreateIdAttr("UsdPreviewSurface")

        # Set material properties
        props = command.properties

        if props.diffuse_color:
            shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(
                Gf.Vec3f(props.diffuse_color.r, props.diffuse_color.g, props.diffuse_color.b)
            )

        shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(props.metallic)
        shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(props.roughness)
        shader.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(props.opacity)

        if props.emissive_color:
            shader.CreateInput("emissiveColor", Sdf.ValueTypeNames.Color3f).Set(
                Gf.Vec3f(props.emissive_color.r, props.emissive_color.g, props.emissive_color.b)
            )

        # Connect shader to material
        material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")

        # Bind material to prim
        UsdShade.MaterialBindingAPI(prim).Bind(material)

    def _create_light(self, stage: Usd.Stage, command: CreateLight) -> None:
        """Create a light in the scene."""
        if command.light_type == "DistantLight":
            light = UsdLux.DistantLight.Define(stage, command.light_path)
        elif command.light_type == "SphereLight":
            light = UsdLux.SphereLight.Define(stage, command.light_path)
        elif command.light_type == "RectLight":
            light = UsdLux.RectLight.Define(stage, command.light_path)
        elif command.light_type == "DomeLight":
            light = UsdLux.DomeLight.Define(stage, command.light_path)
        else:
            raise ValueError(f"Unknown light type: {command.light_type}")

        # Set light properties
        light.CreateColorAttr().Set(
            Gf.Vec3f(command.color.r, command.color.g, command.color.b)
        )
        light.CreateIntensityAttr().Set(command.intensity)

        # Set position if provided
        if command.position:
            xformable = UsdGeom.Xformable(light.GetPrim())
            xformable.AddTranslateOp().Set(
                Gf.Vec3d(command.position.x, command.position.y, command.position.z)
            )

    def _create_camera(self, stage: Usd.Stage, command: CreateCamera) -> None:
        """Create a camera in the scene."""
        camera = UsdGeom.Camera.Define(stage, command.camera_path)

        # Set camera properties
        camera.CreateFocalLengthAttr().Set(command.focal_length)
        camera.CreateFStopAttr().Set(command.fstop)

        # Set camera transform to look at target
        xformable = UsdGeom.Xformable(camera.GetPrim())
        xformable.AddTranslateOp().Set(
            Gf.Vec3d(command.position.x, command.position.y, command.position.z)
        )

        # Calculate look-at rotation
        eye = Gf.Vec3d(command.position.x, command.position.y, command.position.z)
        target = Gf.Vec3d(command.look_at.x, command.look_at.y, command.look_at.z)
        up = Gf.Vec3d(0, 0, 1)  # Assuming Z-up

        look_dir = (target - eye).GetNormalized()
        right = Gf.Cross(look_dir, up).GetNormalized()
        up_corrected = Gf.Cross(right, look_dir).GetNormalized()

        # Create rotation matrix and convert to quaternion
        rotation_matrix = Gf.Matrix4d(1.0)
        rotation_matrix.SetRow(0, Gf.Vec4d(right[0], right[1], right[2], 0))
        rotation_matrix.SetRow(1, Gf.Vec4d(up_corrected[0], up_corrected[1], up_corrected[2], 0))
        rotation_matrix.SetRow(2, Gf.Vec4d(-look_dir[0], -look_dir[1], -look_dir[2], 0))

        quat = rotation_matrix.ExtractRotationQuat()
        xformable.AddOrientOp().Set(quat)

    def _set_relationship(self, stage: Usd.Stage, command: SetRelationship) -> None:
        """Create a parent-child relationship between prims."""
        parent = stage.GetPrimAtPath(command.parent_path)
        child = stage.GetPrimAtPath(command.child_path)

        if not parent:
            raise ValueError(f"Parent prim not found: {command.parent_path}")
        if not child:
            raise ValueError(f"Child prim not found: {command.child_path}")

        # Reparent child under parent
        new_child_path = f"{command.parent_path}/{child.GetName()}"
        UsdGeom.Xform.Define(stage, new_child_path)

        # Copy child to new location (simplified - full implementation would handle all attributes)
        stage.GetPrimAtPath(new_child_path).GetReferences().AddReference(
            "", command.child_path
        )

    def _generate_3d_asset(self, prompt: str) -> Path:
        """Generate a 3D asset from a text prompt using available APIs."""
        # Try CSM first
        if self.csm_client:
            try:
                return self.csm_client.generate_sync(prompt, output_format="usd")
            except Exception as e:
                print(f"CSM generation failed: {e}")

        # Fall back to Spline
        if self.spline_client:
            try:
                return self.spline_client.generate_sync(prompt, output_format="usd")
            except Exception as e:
                print(f"Spline generation failed: {e}")

        raise RuntimeError(
            "No generative 3D API available. Please configure CSM_API_KEY or SPLINE_API_KEY."
        )

    def create_from_config(self, config: SceneConfiguration, output_path: Path) -> Usd.Stage:
        """
        Create a scene from a SceneConfiguration object.

        Args:
            config: Scene configuration with commands
            output_path: Path to save the USD file

        Returns:
            The created USD stage
        """
        return self.create_scene(config.commands, output_path)
