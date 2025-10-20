"""
Optimization Agent: Gradient-based optimization using differentiable physics.
"""

import os
import time
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
import autogen
import torch
import torch.optim as optim
import numpy as np
from dataclasses import dataclass

from models.optimization_commands import (
    OptimizationProblem,
    OptimizationResult,
    OptimizableParameter,
    OptimizerType,
    OptimizationObjective,
)


@dataclass
class OptimizationState:
    """Current state of optimization."""
    iteration: int
    loss: float
    parameters: Dict[str, torch.Tensor]
    gradients: Dict[str, torch.Tensor]
    best_loss: float
    best_parameters: Dict[str, torch.Tensor]
    iterations_without_improvement: int


class OptimizationAgent:
    """
    Optimization Agent: Uses gradient-based optimization to tune simulation parameters.

    Capabilities:
    1. Extract gradients from differentiable physics simulations
    2. Apply various optimization algorithms (SGD, Adam, L-BFGS)
    3. Implement closed-loop learning
    4. Automatic parameter tuning
    """

    def __init__(
        self,
        llm_config: Optional[Dict[str, Any]] = None,
        device: Optional[str] = None,
    ):
        """
        Initialize the Optimization agent.

        Args:
            llm_config: Configuration for AutoGen LLM
            device: Device for PyTorch computations (cuda/cpu)
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
            name="Optimization",
            system_message=self._get_system_message(),
            llm_config=llm_config,
        )

        # Set device
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        print(f"[OptimizationAgent] Using device: {self.device}")

    def _get_system_message(self) -> str:
        """Get system message for the agent."""
        return """You are the Optimization agent, an expert in gradient-based optimization and differentiable physics.

Your role is to:
1. Configure optimization problems for physical simulations
2. Extract and process gradients from differentiable physics
3. Apply optimization algorithms (SGD, Adam, L-BFGS, etc.)
4. Implement closed-loop learning systems
5. Tune parameters to achieve desired simulation outcomes

You have access to:
- PyTorch for gradient computation and optimization
- Differentiable physics engines (Newton, PhysX)
- Various optimization algorithms
- Automatic differentiation

Your goal is to automatically find optimal parameters that achieve user-specified objectives.
"""

    def optimize(
        self,
        problem: OptimizationProblem,
        simulation_runner: Optional[Any] = None,
    ) -> OptimizationResult:
        """
        Run optimization for the given problem.

        Args:
            problem: Optimization problem definition
            simulation_runner: Optional simulation runner (if None, uses mock gradients)

        Returns:
            OptimizationResult with final parameters and history
        """
        print(f"\n{'='*60}")
        print(f"Starting Optimization: {problem.problem_name}")
        print(f"{'='*60}")

        start_time = time.time()

        # Initialize parameters
        parameters = self._initialize_parameters(problem.parameters)

        # Create optimizer
        optimizer = self._create_optimizer(parameters, problem.optimizer_config)

        # Initialize state
        state = OptimizationState(
            iteration=0,
            loss=float('inf'),
            parameters=parameters,
            gradients={},
            best_loss=float('inf'),
            best_parameters={k: v.clone() for k, v in parameters.items()},
            iterations_without_improvement=0,
        )

        # Optimization history
        loss_history = []
        param_history = {name: [] for name in parameters.keys()}

        # Main optimization loop
        for iteration in range(problem.termination.max_iterations):
            state.iteration = iteration

            # Run simulation and compute loss
            loss, gradients = self._compute_loss_and_gradients(
                parameters,
                problem,
                simulation_runner
            )

            state.loss = loss
            state.gradients = gradients

            # Record history
            loss_history.append(loss)
            for name, value in parameters.items():
                param_history[name].append(value.item())

            # Check for improvement
            if loss < state.best_loss - problem.termination.min_improvement:
                state.best_loss = loss
                state.best_parameters = {k: v.clone() for k, v in parameters.items()}
                state.iterations_without_improvement = 0
            else:
                state.iterations_without_improvement += 1

            # Logging
            log_interval = getattr(problem, 'log_interval', 10)
            if iteration % log_interval == 0:
                self._log_progress(state, problem)

            # Check termination conditions
            if self._check_termination(state, problem.termination):
                print(f"\n✓ Optimization converged at iteration {iteration}")
                break

            # Optimization step
            optimizer.zero_grad()

            # Set gradients
            for name, param in parameters.items():
                if name in gradients:
                    param.grad = gradients[name]

            # Apply gradient clipping if specified
            if problem.optimizer_config.clip_grad_norm:
                torch.nn.utils.clip_grad_norm_(
                    parameters.values(),
                    problem.optimizer_config.clip_grad_norm
                )

            # Update parameters
            optimizer.step()

            # Project parameters to bounds
            self._project_to_bounds(parameters, problem.parameters)

        # Prepare result
        computation_time = time.time() - start_time

        result = OptimizationResult(
            problem_name=problem.problem_name,
            converged=(state.iterations_without_improvement < problem.termination.patience),
            num_iterations=state.iteration + 1,
            final_loss=state.best_loss,
            final_parameters={
                name: param.item() for name, param in state.best_parameters.items()
            },
            loss_history=loss_history,
            parameter_history=param_history,
            best_iteration=loss_history.index(state.best_loss),
            computation_time=computation_time,
        )

        print(f"\n{'='*60}")
        print(f"Optimization Complete")
        print(f"{'='*60}")
        print(f"Final Loss: {result.final_loss:.6f}")
        print(f"Iterations: {result.num_iterations}")
        print(f"Time: {computation_time:.2f}s")
        print(f"Converged: {result.converged}")

        return result

    def _initialize_parameters(
        self,
        param_defs: List[OptimizableParameter]
    ) -> Dict[str, torch.Tensor]:
        """Initialize optimization parameters as PyTorch tensors."""
        parameters = {}

        for param_def in param_defs:
            tensor = torch.tensor(
                param_def.initial_value,
                dtype=torch.float32,
                device=self.device,
                requires_grad=param_def.requires_grad
            )
            parameters[param_def.name] = tensor

        return parameters

    def _create_optimizer(
        self,
        parameters: Dict[str, torch.Tensor],
        config: Any,
    ) -> optim.Optimizer:
        """Create PyTorch optimizer from configuration."""
        param_list = [p for p in parameters.values() if p.requires_grad]

        if config.optimizer_type == OptimizerType.SGD:
            return optim.SGD(
                param_list,
                lr=config.learning_rate,
                momentum=config.momentum
            )
        elif config.optimizer_type == OptimizerType.ADAM:
            return optim.Adam(
                param_list,
                lr=config.learning_rate,
                betas=(config.beta1, config.beta2),
                eps=config.epsilon
            )
        elif config.optimizer_type == OptimizerType.LBFGS:
            return optim.LBFGS(
                param_list,
                lr=config.learning_rate,
                max_iter=20
            )
        elif config.optimizer_type == OptimizerType.RMSPROP:
            return optim.RMSprop(
                param_list,
                lr=config.learning_rate,
                alpha=config.beta2,
                eps=config.epsilon
            )
        elif config.optimizer_type == OptimizerType.ADAGRAD:
            return optim.Adagrad(
                param_list,
                lr=config.learning_rate,
                eps=config.epsilon
            )
        else:
            raise ValueError(f"Unknown optimizer type: {config.optimizer_type}")

    def _compute_loss_and_gradients(
        self,
        parameters: Dict[str, torch.Tensor],
        problem: OptimizationProblem,
        simulation_runner: Optional[Any],
    ) -> Tuple[float, Dict[str, torch.Tensor]]:
        """
        Compute loss and gradients by running simulation.

        In a full implementation, this would:
        1. Update USD with current parameters
        2. Run differentiable simulation
        3. Compute metrics from final state
        4. Backpropagate to get gradients

        For now, uses mock gradients for demonstration.
        """
        if simulation_runner is not None:
            # Use actual simulation runner
            return simulation_runner.run_and_compute_gradients(parameters, problem)
        else:
            # Mock implementation for demonstration
            return self._mock_loss_and_gradients(parameters, problem)

    def _mock_loss_and_gradients(
        self,
        parameters: Dict[str, torch.Tensor],
        problem: OptimizationProblem,
    ) -> Tuple[float, Dict[str, torch.Tensor]]:
        """
        Mock loss and gradient computation.

        Uses a simple quadratic loss for demonstration:
        loss = sum((param - target)^2 for param in parameters)
        """
        loss = 0.0
        gradients = {}

        for name, param in parameters.items():
            # Mock target: optimize towards 1.0
            target = 1.0
            param_loss = (param - target) ** 2
            loss += param_loss.item()

            # Compute gradient
            gradients[name] = 2.0 * (param - target)

        return loss, gradients

    def _project_to_bounds(
        self,
        parameters: Dict[str, torch.Tensor],
        param_defs: List[OptimizableParameter],
    ) -> None:
        """Project parameters to their valid bounds."""
        param_def_dict = {p.name: p for p in param_defs}

        for name, param in parameters.items():
            param_def = param_def_dict[name]

            if param_def.min_value is not None:
                param.data = torch.clamp(param.data, min=param_def.min_value)

            if param_def.max_value is not None:
                param.data = torch.clamp(param.data, max=param_def.max_value)

    def _check_termination(self, state: OptimizationState, termination: Any) -> bool:
        """Check if optimization should terminate."""
        # Check convergence
        if state.loss < termination.tolerance:
            return True

        # Check patience
        if state.iterations_without_improvement >= termination.patience:
            return True

        return False

    def _log_progress(self, state: OptimizationState, problem: OptimizationProblem) -> None:
        """Log optimization progress."""
        print(f"Iter {state.iteration:4d} | Loss: {state.loss:.6f} | Best: {state.best_loss:.6f}")

        # Log parameters
        for name, value in state.parameters.items():
            grad_norm = state.gradients.get(name, torch.tensor(0.0)).norm().item()
            print(f"  {name:15s}: {value.item():8.4f} | grad: {grad_norm:8.4f}")


class SimulationRunner:
    """
    Wrapper for running differentiable simulations.

    This would integrate with Isaac Lab's differentiable physics.
    """

    def __init__(self, usd_path: Path):
        """Initialize simulation runner with USD file."""
        self.usd_path = usd_path
        # In full implementation: load USD, setup Isaac Lab simulation

    def run_and_compute_gradients(
        self,
        parameters: Dict[str, torch.Tensor],
        problem: OptimizationProblem,
    ) -> Tuple[float, Dict[str, torch.Tensor]]:
        """
        Run simulation with current parameters and compute gradients.

        Steps:
        1. Apply parameters to USD scene
        2. Run simulation for N steps
        3. Measure final state against metrics
        4. Compute loss
        5. Backpropagate through simulation
        6. Return loss and gradients
        """
        # Placeholder for actual implementation
        raise NotImplementedError(
            "Full simulation runner requires Isaac Lab integration"
        )
