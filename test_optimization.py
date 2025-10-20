#!/usr/bin/env python3
"""
Standalone test of the Optimization Agent.
This demonstrates gradient-based optimization without requiring full platform setup.
"""

#!/usr/bin/env python3
import os
import sys
import time
import torch
import torch.optim as optim
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any, List, Tuple, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import models directly
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
    OptimizationResult,
)


def main():
    print("\n" + "="*70)
    print("AUTONOMOUS SIMULATION PLATFORM - OPTIMIZATION DEMO")
    print("="*70)

    print("\n🚀 Initializing Optimization Agent...")
    agent = OptimizationAgent(llm_config=None)

    print("✅ Agent initialized")
    print(f"   Device: {agent.device}")
    print(f"   PyTorch version: {torch.__version__}")
    print(f"   CUDA available: {torch.cuda.is_available()}")

    # Create optimization problem
    print("\n📋 Creating optimization problem...")
    problem = OptimizationProblem(
        problem_name="simple_quadratic_optimization",
        description="Optimize two parameters to minimize quadratic loss (target=1.0)",
        objective=OptimizationObjective.MINIMIZE,
        metrics=[
            MetricDefinition(
                name="quadratic_error",
                prim_path="/World/Object",
                metric_type="position",
                target_position=[1.0, 1.0, 1.0]
            )
        ],
        parameters=[
            OptimizableParameter(
                name="parameter_x",
                prim_path="/World/Object",
                parameter_type=ParameterType.POSITION,
                initial_value=0.0,
                min_value=-10.0,
                max_value=10.0,
                learning_rate=0.1
            ),
            OptimizableParameter(
                name="parameter_y",
                prim_path="/World/Object",
                parameter_type=ParameterType.POSITION,
                initial_value=-2.0,
                min_value=-10.0,
                max_value=10.0,
                learning_rate=0.1
            )
        ],
        optimizer_config=OptimizerConfig(
            optimizer_type=OptimizerType.ADAM,
            learning_rate=0.1,
            beta1=0.9,
            beta2=0.999
        ),
        termination=TerminationCondition(
            max_iterations=50,
            tolerance=0.001,
            min_improvement=0.0001,
            patience=10
        ),
        simulation=SimulationSettings(
            num_steps=100,
            enable_gradients=True
        )
    )

    print("✅ Problem created")
    print(f"   Objective: {problem.objective}")
    print(f"   Parameters: {len(problem.parameters)}")
    print(f"   Max iterations: {problem.termination.max_iterations}")
    print(f"   Optimizer: {problem.optimizer_config.optimizer_type.value}")

    # Run optimization
    print("\n🔄 Running optimization...")
    print("   (Using mock physics - gradients computed analytically)")
    print()

    result = agent.optimize(problem, simulation_runner=None)

    # Display results
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    print(f"\n✅ Optimization Complete!")
    print(f"\n   Converged: {result.converged}")
    print(f"   Iterations: {result.num_iterations}")
    print(f"   Best iteration: {result.best_iteration}")
    print(f"   Computation time: {result.computation_time:.2f}s")
    print(f"\n   Initial loss: {result.loss_history[0]:.6f}")
    print(f"   Final loss: {result.final_loss:.6f}")
    print(f"   Improvement: {(1 - result.final_loss/result.loss_history[0])*100:.1f}%")

    print(f"\n   Final Parameters:")
    for name, value in result.final_parameters.items():
        initial = [p for p in problem.parameters if p.name == name][0].initial_value
        print(f"     {name:15s}: {initial:8.4f} → {value:8.4f}")

    print(f"\n   Loss History (first 10 iterations):")
    for i, loss in enumerate(result.loss_history[:10]):
        print(f"     Iter {i:2d}: {loss:.6f}")
    if len(result.loss_history) > 10:
        print(f"     ... ({len(result.loss_history) - 10} more iterations)")

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print("""
This demo showed:
  ✓ PyTorch-based gradient computation
  ✓ Adam optimizer with automatic differentiation
  ✓ Convergence detection with patience
  ✓ Parameter bounds enforcement
  ✓ Loss history tracking

In a full implementation with Isaac Lab:
  • Real physics simulation would replace mock gradients
  • Differentiable physics engine (Newton/PhysX)
  • Actual USD scene manipulation
  • Real-time parameter updates
  • Closed-loop learning from simulation results
    """)

    print("="*70)
    print("Demo complete! All systems operational. 🎉")
    print("="*70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
