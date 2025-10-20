"""
Pydantic models for optimization commands.
These models define optimization problems and parameters.
"""

from typing import Literal, Optional, List, Dict, Any, Callable
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class OptimizationObjective(str, Enum):
    """Types of optimization objectives."""
    MINIMIZE = "minimize"
    MAXIMIZE = "maximize"
    TARGET = "target"  # Reach a specific target value


class ParameterType(str, Enum):
    """Types of parameters that can be optimized."""
    FORCE = "force"
    TORQUE = "torque"
    POSITION = "position"
    VELOCITY = "velocity"
    MASS = "mass"
    FRICTION = "friction"
    STIFFNESS = "stiffness"
    DAMPING = "damping"
    CONTROL_SIGNAL = "control_signal"


class OptimizerType(str, Enum):
    """Gradient-based optimizer types."""
    SGD = "sgd"  # Stochastic Gradient Descent
    ADAM = "adam"  # Adaptive Moment Estimation
    LBFGS = "lbfgs"  # Limited-memory BFGS
    RMSPROP = "rmsprop"
    ADAGRAD = "adagrad"


class OptimizableParameter(BaseModel):
    """Definition of a parameter to optimize."""
    name: str = Field(..., description="Name/identifier for this parameter")
    prim_path: str = Field(..., description="USD path to the object")
    parameter_type: ParameterType = Field(..., description="Type of parameter")

    # Bounds
    initial_value: float = Field(..., description="Initial value")
    min_value: Optional[float] = Field(default=None, description="Minimum allowed value")
    max_value: Optional[float] = Field(default=None, description="Maximum allowed value")

    # Learning settings
    learning_rate: float = Field(default=0.01, gt=0.0, description="Learning rate for this parameter")
    requires_grad: bool = Field(default=True, description="Whether to compute gradients")


class MetricDefinition(BaseModel):
    """Definition of a metric to optimize."""
    name: str = Field(..., description="Name of the metric")
    prim_path: str = Field(..., description="USD path to measure from")
    metric_type: Literal["position", "velocity", "energy", "distance", "custom"] = Field(
        ...,
        description="Type of metric to measure"
    )

    # For position/distance metrics
    target_position: Optional[List[float]] = Field(
        default=None,
        description="Target position [x, y, z] for position/distance metrics"
    )

    # For custom metrics
    custom_function: Optional[str] = Field(
        default=None,
        description="Python code for custom metric computation"
    )

    # Weights
    weight: float = Field(default=1.0, description="Weight for this metric in multi-objective optimization")


class TerminationCondition(BaseModel):
    """Conditions for terminating optimization."""
    max_iterations: int = Field(default=100, gt=0, description="Maximum number of iterations")
    tolerance: float = Field(default=1e-4, gt=0.0, description="Convergence tolerance")
    min_improvement: float = Field(
        default=1e-6,
        gt=0.0,
        description="Minimum improvement required to continue"
    )
    patience: int = Field(
        default=10,
        gt=0,
        description="Iterations without improvement before stopping"
    )


class OptimizerConfig(BaseModel):
    """Configuration for the gradient-based optimizer."""
    optimizer_type: OptimizerType = Field(..., description="Type of optimizer to use")

    # Learning rate settings
    learning_rate: float = Field(default=0.01, gt=0.0, description="Global learning rate")
    learning_rate_decay: float = Field(default=1.0, ge=0.0, le=1.0, description="LR decay per epoch")

    # Momentum/adaptive settings
    momentum: float = Field(default=0.9, ge=0.0, le=1.0, description="Momentum coefficient")
    beta1: float = Field(default=0.9, ge=0.0, le=1.0, description="Adam beta1")
    beta2: float = Field(default=0.999, ge=0.0, le=1.0, description="Adam beta2")
    epsilon: float = Field(default=1e-8, gt=0.0, description="Numerical stability epsilon")

    # Gradient clipping
    clip_grad_norm: Optional[float] = Field(default=None, description="Maximum gradient norm")


class SimulationSettings(BaseModel):
    """Settings for simulation during optimization."""
    num_steps: int = Field(default=300, gt=0, description="Number of simulation steps per iteration")
    time_step: float = Field(default=1.0/60.0, gt=0.0, description="Simulation timestep")

    # Differentiable physics settings
    enable_gradients: bool = Field(default=True, description="Enable gradient computation")
    gradient_mode: Literal["analytical", "finite_diff", "auto"] = Field(
        default="auto",
        description="Method for computing gradients"
    )


class OptimizationProblem(BaseModel):
    """Complete definition of an optimization problem."""
    problem_name: str = Field(..., description="Name of the optimization problem")
    description: Optional[str] = Field(default=None, description="Description of what to optimize")

    # Objective
    objective: OptimizationObjective = Field(..., description="Optimization objective")
    metrics: List[MetricDefinition] = Field(..., description="Metrics to optimize")

    # Parameters to optimize
    parameters: List[OptimizableParameter] = Field(..., description="Parameters to optimize")

    # Optimizer configuration
    optimizer_config: OptimizerConfig = Field(..., description="Optimizer settings")

    # Termination conditions
    termination: TerminationCondition = Field(..., description="When to stop optimization")

    # Simulation settings
    simulation: SimulationSettings = Field(..., description="Simulation configuration")

    # Constraints (optional)
    constraints: List[str] = Field(default_factory=list, description="Optimization constraints")


class OptimizationResult(BaseModel):
    """Results from an optimization run."""
    problem_name: str
    converged: bool
    num_iterations: int
    final_loss: float
    final_parameters: Dict[str, float]
    loss_history: List[float]
    parameter_history: Dict[str, List[float]]
    best_iteration: int
    computation_time: float  # seconds


class OptimizationCommand(BaseModel):
    """Command to run an optimization."""
    command_type: Literal["RunOptimization"] = "RunOptimization"

    usd_path: str = Field(..., description="Path to USD file to optimize")
    problem: OptimizationProblem = Field(..., description="Optimization problem definition")
    output_path: Optional[str] = Field(
        default=None,
        description="Path to save optimized USD file"
    )

    # Visualization and logging
    visualize: bool = Field(default=False, description="Generate visualization plots")
    log_interval: int = Field(default=10, gt=0, description="Logging frequency (iterations)")
    save_checkpoints: bool = Field(default=True, description="Save intermediate checkpoints")
