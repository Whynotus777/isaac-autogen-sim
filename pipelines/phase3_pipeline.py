"""
Phase 3 Pipeline: Closed-loop optimization with differentiable physics.

This pipeline:
1. Takes a simulation USD and optimization problem
2. Runs simulation to get gradients
3. Updates parameters based on gradients
4. Repeats until convergence
5. Outputs optimized USD file
"""

import json
from typing import Dict, Any, Optional
from pathlib import Path
import matplotlib.pyplot as plt

from agents.optimization_agent import OptimizationAgent, SimulationRunner
from models.optimization_commands import OptimizationProblem, OptimizationResult


class Phase3Pipeline:
    """
    Phase 3: Closed-loop optimization pipeline.

    Workflow:
    USD + Problem → Run Sim → Compute Gradients → Update Parameters → Repeat
    """

    def __init__(self, llm_config: Optional[Dict[str, Any]] = None):
        """
        Initialize Phase 3 pipeline.

        Args:
            llm_config: LLM configuration for agents
        """
        self.optimizer_agent = OptimizationAgent(llm_config=llm_config)

    def run(
        self,
        usd_path: Path,
        problem: OptimizationProblem,
        output_dir: Optional[Path] = None,
        visualize: bool = True,
    ) -> OptimizationResult:
        """
        Run the complete optimization pipeline.

        Args:
            usd_path: Path to input USD file
            problem: Optimization problem definition
            output_dir: Directory for outputs
            visualize: Whether to generate visualization plots

        Returns:
            OptimizationResult with final parameters
        """
        if output_dir is None:
            output_dir = Path("output/optimization")
        output_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n{'='*60}")
        print(f"Phase 3: Optimization Pipeline")
        print(f"{'='*60}")
        print(f"Input USD: {usd_path}")
        print(f"Problem: {problem.problem_name}")
        print(f"Objective: {problem.objective}")
        print(f"Parameters: {len(problem.parameters)}")
        print(f"Metrics: {len(problem.metrics)}")

        # Create simulation runner
        # In full implementation, this would load Isaac Lab
        simulation_runner = None  # Use mock for now

        # Run optimization
        print(f"\n[1/4] Running optimization...")
        result = self.optimizer_agent.optimize(problem, simulation_runner)

        # Save results
        print(f"\n[2/4] Saving results...")
        self._save_results(result, output_dir)

        # Generate visualizations
        if visualize:
            print(f"\n[3/4] Generating visualizations...")
            self._visualize_results(result, output_dir)

        # Save optimized USD (would apply final parameters)
        print(f"\n[4/4] Saving optimized USD...")
        optimized_usd_path = output_dir / f"{problem.problem_name}_optimized.usd"
        # In full implementation: apply result.final_parameters to USD
        print(f"  (Optimized USD would be saved to: {optimized_usd_path})")

        print(f"\n✅ Optimization pipeline complete!")
        print(f"  Results: {output_dir}")

        return result

    def run_from_config(
        self,
        usd_path: Path,
        config_path: Path,
        output_dir: Optional[Path] = None,
    ) -> OptimizationResult:
        """
        Run optimization from a JSON configuration file.

        Args:
            usd_path: Path to USD file
            config_path: Path to optimization config JSON
            output_dir: Output directory

        Returns:
            OptimizationResult
        """
        # Load configuration
        with open(config_path, 'r') as f:
            config_dict = json.load(f)

        # Parse into OptimizationProblem
        problem = OptimizationProblem(**config_dict)

        return self.run(usd_path, problem, output_dir)

    def _save_results(self, result: OptimizationResult, output_dir: Path) -> None:
        """Save optimization results to JSON."""
        results_path = output_dir / f"{result.problem_name}_results.json"

        results_dict = {
            "problem_name": result.problem_name,
            "converged": result.converged,
            "num_iterations": result.num_iterations,
            "final_loss": result.final_loss,
            "final_parameters": result.final_parameters,
            "best_iteration": result.best_iteration,
            "computation_time": result.computation_time,
            "loss_history": result.loss_history,
            "parameter_history": result.parameter_history,
        }

        with open(results_path, 'w') as f:
            json.dump(results_dict, f, indent=2)

        print(f"  Results saved: {results_path}")

    def _visualize_results(self, result: OptimizationResult, output_dir: Path) -> None:
        """Generate visualization plots of optimization progress."""
        # Create figure with subplots
        fig, axes = plt.subplots(2, 1, figsize=(10, 8))

        # Plot 1: Loss over iterations
        ax1 = axes[0]
        ax1.plot(result.loss_history, linewidth=2)
        ax1.axvline(
            result.best_iteration,
            color='r',
            linestyle='--',
            label=f'Best (iter {result.best_iteration})'
        )
        ax1.set_xlabel('Iteration')
        ax1.set_ylabel('Loss')
        ax1.set_title(f'Optimization Progress: {result.problem_name}')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.set_yscale('log')

        # Plot 2: Parameter evolution
        ax2 = axes[1]
        for param_name, param_history in result.parameter_history.items():
            ax2.plot(param_history, label=param_name, linewidth=2)

        ax2.set_xlabel('Iteration')
        ax2.set_ylabel('Parameter Value')
        ax2.set_title('Parameter Evolution')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()

        # Save plot
        plot_path = output_dir / f"{result.problem_name}_optimization.png"
        plt.savefig(plot_path, dpi=150, bbox_inches='tight')
        plt.close()

        print(f"  Plot saved: {plot_path}")


def run_optimization(
    usd_path: Path,
    problem: OptimizationProblem,
    output_dir: Optional[Path] = None,
    llm_config: Optional[Dict[str, Any]] = None,
) -> OptimizationResult:
    """
    Convenience function to run optimization pipeline.

    Args:
        usd_path: Path to USD file
        problem: Optimization problem
        output_dir: Output directory
        llm_config: LLM configuration

    Returns:
        OptimizationResult
    """
    pipeline = Phase3Pipeline(llm_config=llm_config)
    return pipeline.run(usd_path, problem, output_dir)
