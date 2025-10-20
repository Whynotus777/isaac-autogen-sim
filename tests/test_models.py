"""
Unit tests for Pydantic models.
"""

import pytest
from pydantic import ValidationError

from models.scene_commands import (
    CreatePrim,
    SetTransform,
    SetMaterial,
    Vec3,
    Quaternion,
    RGBAColor,
    MaterialProperties,
    PrimType,
)

from models.physics_commands import (
    ApplyRigidBody,
    SetFriction,
    ConfigureSolver,
    RigidBodyProperties,
    FrictionProperties,
    SolverSettings,
)

from models.optimization_commands import (
    OptimizationProblem,
    OptimizableParameter,
    MetricDefinition,
    OptimizerConfig,
    TerminationCondition,
    SimulationSettings,
    ParameterType,
    OptimizerType,
    OptimizationObjective,
)


class TestSceneCommands:
    """Tests for scene command models."""

    def test_vec3_creation(self):
        """Test Vec3 creation."""
        vec = Vec3(x=1.0, y=2.0, z=3.0)
        assert vec.x == 1.0
        assert vec.y == 2.0
        assert vec.z == 3.0

    def test_vec3_defaults(self):
        """Test Vec3 defaults to zeros."""
        vec = Vec3()
        assert vec.x == 0.0
        assert vec.y == 0.0
        assert vec.z == 0.0

    def test_quaternion_creation(self):
        """Test Quaternion creation."""
        quat = Quaternion(w=1.0, x=0.0, y=0.0, z=0.0)
        assert quat.w == 1.0

    def test_rgba_color_validation(self):
        """Test RGBA color value validation."""
        # Valid color
        color = RGBAColor(r=0.5, g=0.5, b=0.5, a=1.0)
        assert color.r == 0.5

        # Invalid color (out of range)
        with pytest.raises(ValidationError):
            RGBAColor(r=1.5, g=0.5, b=0.5)

    def test_create_prim_valid(self):
        """Test CreatePrim with valid data."""
        cmd = CreatePrim(
            prim_path="/World/Cube",
            prim_type=PrimType.CUBE,
            scale=Vec3(x=1.0, y=1.0, z=1.0)
        )
        assert cmd.prim_path == "/World/Cube"
        assert cmd.prim_type == PrimType.CUBE

    def test_create_prim_invalid_path(self):
        """Test CreatePrim with invalid path."""
        with pytest.raises(ValidationError):
            CreatePrim(
                prim_path="invalid_path",  # Missing leading slash
                prim_type=PrimType.CUBE
            )

    def test_set_material(self):
        """Test SetMaterial command."""
        cmd = SetMaterial(
            prim_path="/World/Cube",
            material_name="TestMaterial",
            properties=MaterialProperties(
                diffuse_color=RGBAColor(r=1.0, g=0.0, b=0.0),
                metallic=0.5,
                roughness=0.5
            )
        )
        assert cmd.material_name == "TestMaterial"
        assert cmd.properties.metallic == 0.5


class TestPhysicsCommands:
    """Tests for physics command models."""

    def test_rigid_body_properties(self):
        """Test RigidBodyProperties."""
        props = RigidBodyProperties(mass=10.0)
        assert props.mass == 10.0
        assert props.linear_damping == 0.0

    def test_rigid_body_properties_invalid_mass(self):
        """Test invalid mass raises error."""
        with pytest.raises(ValidationError):
            RigidBodyProperties(mass=-1.0)

    def test_friction_properties(self):
        """Test FrictionProperties."""
        props = FrictionProperties(
            static_friction=0.6,
            dynamic_friction=0.5,
            restitution=0.3
        )
        assert props.static_friction == 0.6
        assert props.dynamic_friction == 0.5

    def test_solver_settings(self):
        """Test SolverSettings."""
        settings = SolverSettings(
            time_step=1.0/60.0,
            gravity=Vec3(x=0.0, y=0.0, z=-9.81)
        )
        assert settings.time_step == pytest.approx(1.0/60.0)
        assert settings.gravity.z == -9.81

    def test_apply_rigid_body(self):
        """Test ApplyRigidBody command."""
        cmd = ApplyRigidBody(
            prim_path="/World/Cube",
            properties=RigidBodyProperties(mass=1.0),
            is_kinematic=False
        )
        assert cmd.prim_path == "/World/Cube"
        assert not cmd.is_kinematic


class TestOptimizationCommands:
    """Tests for optimization command models."""

    def test_optimizable_parameter(self):
        """Test OptimizableParameter creation."""
        param = OptimizableParameter(
            name="test_param",
            prim_path="/World/Object",
            parameter_type=ParameterType.FORCE,
            initial_value=10.0,
            min_value=0.0,
            max_value=100.0
        )
        assert param.name == "test_param"
        assert param.initial_value == 10.0

    def test_metric_definition(self):
        """Test MetricDefinition."""
        metric = MetricDefinition(
            name="distance",
            prim_path="/World/Object",
            metric_type="distance",
            target_position=[1.0, 2.0, 3.0]
        )
        assert metric.name == "distance"
        assert metric.target_position == [1.0, 2.0, 3.0]

    def test_optimizer_config(self):
        """Test OptimizerConfig."""
        config = OptimizerConfig(
            optimizer_type=OptimizerType.ADAM,
            learning_rate=0.01
        )
        assert config.optimizer_type == OptimizerType.ADAM
        assert config.learning_rate == 0.01

    def test_termination_condition(self):
        """Test TerminationCondition."""
        term = TerminationCondition(
            max_iterations=100,
            tolerance=1e-4
        )
        assert term.max_iterations == 100
        assert term.tolerance == 1e-4

    def test_optimization_problem_complete(self):
        """Test complete OptimizationProblem."""
        problem = OptimizationProblem(
            problem_name="test_problem",
            objective=OptimizationObjective.MINIMIZE,
            metrics=[
                MetricDefinition(
                    name="loss",
                    prim_path="/World/Object",
                    metric_type="position"
                )
            ],
            parameters=[
                OptimizableParameter(
                    name="param1",
                    prim_path="/World/Object",
                    parameter_type=ParameterType.FORCE,
                    initial_value=1.0
                )
            ],
            optimizer_config=OptimizerConfig(
                optimizer_type=OptimizerType.ADAM,
                learning_rate=0.01
            ),
            termination=TerminationCondition(
                max_iterations=100,
                tolerance=1e-4
            ),
            simulation=SimulationSettings(
                num_steps=100
            )
        )

        assert problem.problem_name == "test_problem"
        assert len(problem.parameters) == 1
        assert len(problem.metrics) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
