"""
Pydantic models for scene graph commands.
These models define the structured input schema for the SceneGraph agent.
"""

from typing import Literal, Optional, Union, List
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class PrimType(str, Enum):
    """OpenUSD primitive types."""
    SPHERE = "Sphere"
    CUBE = "Cube"
    CYLINDER = "Cylinder"
    CONE = "Cone"
    PLANE = "Plane"
    MESH = "Mesh"
    XFORM = "Xform"
    CAMERA = "Camera"
    LIGHT = "Light"


class Vec3(BaseModel):
    """3D vector representation."""
    model_config = ConfigDict(frozen=True)

    x: float = Field(default=0.0, description="X coordinate")
    y: float = Field(default=0.0, description="Y coordinate")
    z: float = Field(default=0.0, description="Z coordinate")


class Quaternion(BaseModel):
    """Quaternion representation for rotations."""
    model_config = ConfigDict(frozen=True)

    w: float = Field(default=1.0, description="W component (scalar)")
    x: float = Field(default=0.0, description="X component")
    y: float = Field(default=0.0, description="Y component")
    z: float = Field(default=0.0, description="Z component")


class RGBAColor(BaseModel):
    """RGBA color representation."""
    model_config = ConfigDict(frozen=True)

    r: float = Field(ge=0.0, le=1.0, description="Red channel (0-1)")
    g: float = Field(ge=0.0, le=1.0, description="Green channel (0-1)")
    b: float = Field(ge=0.0, le=1.0, description="Blue channel (0-1)")
    a: float = Field(default=1.0, ge=0.0, le=1.0, description="Alpha channel (0-1)")


class MaterialProperties(BaseModel):
    """Material properties for rendering."""
    diffuse_color: Optional[RGBAColor] = Field(default=None, description="Base diffuse color")
    metallic: float = Field(default=0.0, ge=0.0, le=1.0, description="Metallic property (0-1)")
    roughness: float = Field(default=0.5, ge=0.0, le=1.0, description="Roughness property (0-1)")
    opacity: float = Field(default=1.0, ge=0.0, le=1.0, description="Opacity (0-1)")
    emissive_color: Optional[RGBAColor] = Field(default=None, description="Emissive color")
    emissive_intensity: float = Field(default=0.0, ge=0.0, description="Emissive intensity")


class CreatePrim(BaseModel):
    """Command to create a new primitive in the scene."""
    command_type: Literal["CreatePrim"] = "CreatePrim"

    prim_path: str = Field(
        ...,
        description="USD path for the primitive (e.g., '/World/Sphere_01')",
        pattern=r"^/[a-zA-Z0-9_/]+$"
    )
    prim_type: PrimType = Field(..., description="Type of primitive to create")

    # Optional: Generate from text prompt using 3D generative API
    generate_from_prompt: Optional[str] = Field(
        default=None,
        description="Text prompt to generate 3D asset (e.g., 'a wooden table')"
    )

    # Scale for the primitive
    scale: Vec3 = Field(default=Vec3(x=1.0, y=1.0, z=1.0), description="Scale of the primitive")

    # Optional attributes
    visible: bool = Field(default=True, description="Whether the prim is visible")


class SetTransform(BaseModel):
    """Command to set the transform of a primitive."""
    command_type: Literal["SetTransform"] = "SetTransform"

    prim_path: str = Field(
        ...,
        description="USD path to the primitive",
        pattern=r"^/[a-zA-Z0-9_/]+$"
    )

    position: Optional[Vec3] = Field(default=None, description="Position in world space")
    rotation: Optional[Quaternion] = Field(default=None, description="Rotation as quaternion")
    scale: Optional[Vec3] = Field(default=None, description="Scale factors")


class SetMaterial(BaseModel):
    """Command to set material properties on a primitive."""
    command_type: Literal["SetMaterial"] = "SetMaterial"

    prim_path: str = Field(
        ...,
        description="USD path to the primitive",
        pattern=r"^/[a-zA-Z0-9_/]+$"
    )

    material_name: str = Field(..., description="Name for the material")
    properties: MaterialProperties = Field(..., description="Material properties")


class SetRelationship(BaseModel):
    """Command to create a parent-child relationship between prims."""
    command_type: Literal["SetRelationship"] = "SetRelationship"

    parent_path: str = Field(..., description="USD path to the parent prim")
    child_path: str = Field(..., description="USD path to the child prim")


class CreateLight(BaseModel):
    """Command to create a light source."""
    command_type: Literal["CreateLight"] = "CreateLight"

    light_path: str = Field(
        ...,
        description="USD path for the light",
        pattern=r"^/[a-zA-Z0-9_/]+$"
    )
    light_type: Literal["DistantLight", "SphereLight", "RectLight", "DomeLight"] = Field(
        ...,
        description="Type of light to create"
    )

    color: RGBAColor = Field(default=RGBAColor(r=1.0, g=1.0, b=1.0), description="Light color")
    intensity: float = Field(default=1000.0, ge=0.0, description="Light intensity")
    position: Optional[Vec3] = Field(default=None, description="Light position")


class CreateCamera(BaseModel):
    """Command to create a camera."""
    command_type: Literal["CreateCamera"] = "CreateCamera"

    camera_path: str = Field(
        ...,
        description="USD path for the camera",
        pattern=r"^/[a-zA-Z0-9_/]+$"
    )

    position: Vec3 = Field(..., description="Camera position")
    look_at: Vec3 = Field(..., description="Point the camera looks at")
    focal_length: float = Field(default=50.0, gt=0.0, description="Focal length in mm")
    fstop: float = Field(default=2.8, gt=0.0, description="F-stop value")


# Union type for all scene commands
SceneCommand = Union[
    CreatePrim,
    SetTransform,
    SetMaterial,
    SetRelationship,
    CreateLight,
    CreateCamera,
]


class SceneConfiguration(BaseModel):
    """Complete scene configuration with multiple commands."""
    scene_name: str = Field(..., description="Name of the scene")
    description: Optional[str] = Field(default=None, description="Description of the scene")
    commands: List[SceneCommand] = Field(..., description="List of scene commands to execute")
