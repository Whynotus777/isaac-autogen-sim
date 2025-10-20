"""
Integration tests for Optimization Agent.
"""

import pytest
import torch
from pathlib import Path

from agents.optimization_agent import OptimizationAgent
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


class TestOptimizationAgent:
    """Tests for OptimizationAgent."""

    @pytest.fixture
    def agent(self):
        """Create optimization agent for testing."""
        return OptimizationAgent(llm_config=None)

    @pytest.fixture
    def simple_problem(self):
        """Create a simple optimization problem."""
        return OptimizationProblem(
            problem_name="test_problem",
            objective=OptimizationObjective.MINIMIZE,
            metrics=[
                MetricDefinition(
                    name="distance",
                    prim_path="/World/Object",
                    metric_type="position",
                    target_position=[1.0, 1.0, 1.0]
                )
            ],
            parameters=[
                OptimizableParameter(
                    name="param_x",
                    prim_path="/World/Object",
                    parameter_type=ParameterType.POSITION,
                    initial_value=0.0,
                    min_value=-10.0,
                    max_value=10.0,
                    learning_rate=0.1
                ),
                OptimizableParameter(
                    name="param_y",
                    prim_path="/World/Object",
                    parameter_type=ParameterType.POSITION,
                    initial_value=0.0,
                    min_value=-10.0,
                    max_value=10.0,
                    learning_rate=0.1
                )
            ],
            optimizer_config=OptimizerConfig(
                optimizer_type=OptimizerType.ADAM,
                learning_rate=0.1
            ),
            termination=TerminationCondition(
                max_iterations=50,
                tolerance=0.01,
                patience=10
            ),
            simulation=SimulationSettings(
                num_steps=100
            )
        )

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent is not None
        assert isinstance(agent.device, torch.device)

    def test_parameter_initialization(self, agent, simple_problem):
        """Test parameter initialization."""
        parameters = agent._initialize_parameters(simple_problem.parameters)

        assert len(parameters) == 2
        assert "param_x" in parameters
        assert "param_y" in parameters
        assert parameters["param_x"].item() == 0.0
        assert parameters["param_y"].item() == 0.0

    def test_optimizer_creation_adam(self, agent, simple_problem):
        """Test ADAM optimizer creation."""
        parameters = agent._initialize_parameters(simple_problem.parameters)
        optimizer = agent._create_optimizer(parameters, simple_problem.optimizer_config)

        assert optimizer is not None
        assert isinstance(optimizer, torch.optim.Adam)

    def test_optimizer_creation_sgd(self, agent, simple_problem):
        """Test SGD optimizer creation."""
        simple_problem.optimizer_config.optimizer_type = OptimizerType.SGD

        parameters = agent._initialize_parameters(simple_problem.parameters)
        optimizer = agent._create_optimizer(parameters, simple_problem.optimizer_config)

        assert isinstance(optimizer, torch.optim.SGD)

    def test_mock_loss_computation(self, agent, simple_problem):
        """Test mock loss and gradient computation."""
        parameters = agent._initialize_parameters(simple_problem.parameters)
        loss, gradients = agent._mock_loss_and_gradients(parameters, simple_problem)

        assert isinstance(loss, float)
        assert loss >= 0.0
        assert len(gradients) == 2
        assert "param_x" in gradients
        assert "param_y" in gradients

    def test_parameter_bounds_projection(self, agent, simple_problem):
        """Test parameter projection to bounds."""
        parameters = agent._initialize_parameters(simple_problem.parameters)

        # Set parameters outside bounds
        parameters["param_x"].data = torch.tensor(15.0)  # Above max (10.0)
        parameters["param_y"].data = torch.tensor(-15.0)  # Below min (-10.0)

        # Project to bounds
        agent._project_to_bounds(parameters, simple_problem.parameters)

        # Check projection worked
        assert parameters["param_x"].item() == 10.0
        assert parameters["param_y"].item() == -10.0

    def test_optimization_converges(self, agent, simple_problem):
        """Test that optimization converges for simple problem."""
        result = agent.optimize(simple_problem, simulation_runner=None)

        assert result is not None
        assert result.num_iterations > 0
        assert result.final_loss < result.loss_history[0]  # Loss decreased
        assert len(result.loss_history) == result.num_iterations

    def test_optimization_result_structure(self, agent, simple_problem):
        """Test optimization result has correct structure."""
        result = agent.optimize(simple_problem)

        assert result.problem_name == "test_problem"
        assert isinstance(result.converged, bool)
        assert result.num_iterations > 0
        assert result.final_loss >= 0.0
        assert len(result.final_parameters) == 2
        assert "param_x" in result.final_parameters
        assert "param_y" in result.final_parameters
        assert len(result.loss_history) == result.num_iterations
        assert result.computation_time > 0.0

    def test_early_stopping(self, agent):
        """Test early stopping with patience."""
        problem = OptimizationProblem(
            problem_name="early_stop_test",
            objective=OptimizationObjective.MINIMIZE,
            metrics=[
                MetricDefinition(
                    name="test",
                    prim_path="/World/Object",
                    metric_type="position"
                )
            ],
            parameters=[
                OptimizableParameter(
                    name="param",
                    prim_path="/World/Object",
                    parameter_type=ParameterType.POSITION,
                    initial_value=1.0,  # Already at target
                )
            ],
            optimizer_config=OptimizerConfig(
                optimizer_type=OptimizerType.ADAM,
                learning_rate=0.01
            ),
            termination=TerminationCondition(
                max_iterations=1000,
                tolerance=0.001,
                patience=5  # Small patience for early stop
            ),
            simulation=SimulationSettings(num_steps=10)
        )

        result = agent.optimize(problem)

        # Should stop before max iterations due to patience
        assert result.num_iterations < 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
