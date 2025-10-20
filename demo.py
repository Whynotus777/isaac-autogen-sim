#!/usr/bin/env python3
"""
Comprehensive demo of the Autonomous Simulation Design Platform.

Demonstrates all three phases:
- Phase 1: Scene generation and physics application
- Phase 2: Natural language interface and validation
- Phase 3: Gradient-based optimization
"""

import argparse
from pathlib import Path
import json

from main import AutonomousSimulationPlatform
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
from pipelines.phase3_pipeline import Phase3Pipeline


def demo_phase1():
    """Demonstrate Phase 1: Basic scene and physics generation."""
    print("\n" + "="*70)
    print("PHASE 1 DEMO: Scene Generation & Physics Application")
    print("="*70)

    platform = AutonomousSimulationPlatform()

    # Use config file
    config_path = Path("examples/falling_block.json")

    if not config_path.exists():
        print(f"\n⚠️  Config file not found: {config_path}")
        print("    Run this demo from the project root directory")
        return None

    print(f"\nUsing configuration: {config_path}")
    print("This demonstrates:")
    print("  • SceneGraph Agent: Creates geometry, materials, lights")
    print("  • Physics Agent: Applies rigid bodies, colliders, friction")
    print("  • Sequential Pipeline: JSON → USD workflow\n")

    usd_path = platform.create_from_config(
        config_path,
        output_dir=Path("output/demo/phase1"),
        validate=True
    )

    if usd_path:
        print(f"\n✅ Phase 1 Complete!")
        print(f"   USD file: {usd_path}")

    return usd_path


def demo_phase2():
    """Demonstrate Phase 2: Natural language interface."""
    print("\n" + "="*70)
    print("PHASE 2 DEMO: Natural Language Interface")
    print("="*70)

    platform = AutonomousSimulationPlatform()

    # Example prompts
    prompts = [
        "Create a simple pendulum with a 1 meter rod and a 1kg mass",
        "A ball rolling down a ramp into a box",
        "Two cubes stacked on top of each other on a table",
    ]

    print("\nThis demonstrates:")
    print("  • Architect Agent: Parses natural language")
    print("  • Task Decomposition: Breaks down complex requests")
    print("  • Validator Agent: Checks for errors")
    print("  • Multi-Agent Coordination: All agents working together\n")

    # Demo with first prompt
    prompt = prompts[0]
    print(f"Demo Prompt: '{prompt}'\n")

    usd_path = platform.create_from_prompt(
        prompt,
        output_dir=Path("output/demo/phase2"),
        validate=True,
        explain=True
    )

    if usd_path:
        print(f"\n✅ Phase 2 Complete!")
        print(f"   USD file: {usd_path}")
        print(f"\nTry these other prompts:")
        for i, p in enumerate(prompts[1:], 1):
            print(f"   {i}. {p}")

    return usd_path


def demo_phase3():
    """Demonstrate Phase 3: Gradient-based optimization."""
    print("\n" + "="*70)
    print("PHASE 3 DEMO: Gradient-Based Optimization")
    print("="*70)

    print("\nThis demonstrates:")
    print("  • Optimization Agent: Gradient-based parameter tuning")
    print("  • Closed-Loop Learning: Automatic parameter refinement")
    print("  • Differentiable Physics: Gradient computation (mock)")
    print("  • Visualization: Optimization progress plots\n")

    # Create a simple optimization problem
    problem = OptimizationProblem(
        problem_name="demo_optimization",
        description="Simple demo: optimize two parameters to reach target of 1.0",
        objective=OptimizationObjective.MINIMIZE,
        metrics=[
            MetricDefinition(
                name="error",
                prim_path="/World/Object",
                metric_type="position",
                target_position=[1.0, 1.0, 1.0]
            )
        ],
        parameters=[
            OptimizableParameter(
                name="param_1",
                prim_path="/World/Object",
                parameter_type=ParameterType.POSITION,
                initial_value=0.0,
                min_value=-5.0,
                max_value=5.0,
                learning_rate=0.1
            ),
            OptimizableParameter(
                name="param_2",
                prim_path="/World/Object",
                parameter_type=ParameterType.POSITION,
                initial_value=0.5,
                min_value=-5.0,
                max_value=5.0,
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
            patience=10
        ),
        simulation=SimulationSettings(
            num_steps=100,
            enable_gradients=True
        )
    )

    # Run optimization
    pipeline = Phase3Pipeline()

    # For demo, we'll use a mock USD path
    mock_usd = Path("output/demo/phase3/demo.usd")
    mock_usd.parent.mkdir(parents=True, exist_ok=True)

    print("Running optimization...")
    print(f"  Parameters: {len(problem.parameters)}")
    print(f"  Max iterations: {problem.termination.max_iterations}")
    print(f"  Optimizer: {problem.optimizer_config.optimizer_type.value}\n")

    result = pipeline.run(
        mock_usd,
        problem,
        output_dir=Path("output/demo/phase3"),
        visualize=True
    )

    print(f"\n✅ Phase 3 Complete!")
    print(f"   Final loss: {result.final_loss:.6f}")
    print(f"   Iterations: {result.num_iterations}")
    print(f"   Converged: {result.converged}")
    print(f"   Final parameters:")
    for name, value in result.final_parameters.items():
        print(f"     {name}: {value:.4f}")

    return result


def demo_all():
    """Run complete demonstration of all phases."""
    print("\n" + "="*70)
    print("COMPLETE PLATFORM DEMONSTRATION")
    print("="*70)
    print("\nThis will demonstrate:")
    print("  Phase 1: Scene generation from JSON")
    print("  Phase 2: Natural language interface")
    print("  Phase 3: Gradient-based optimization\n")

    input("Press Enter to start Phase 1...")
    phase1_result = demo_phase1()

    input("\nPress Enter to start Phase 2...")
    phase2_result = demo_phase2()

    input("\nPress Enter to start Phase 3...")
    phase3_result = demo_phase3()

    print("\n" + "="*70)
    print("DEMO COMPLETE!")
    print("="*70)
    print("\nAll outputs saved to: output/demo/")
    print("\nWhat you've seen:")
    print("  ✓ Multi-agent system for simulation design")
    print("  ✓ Natural language → USD conversion")
    print("  ✓ Automatic validation and error checking")
    print("  ✓ Gradient-based optimization (with mock physics)")
    print("  ✓ Visualization and logging")
    print("\nNext steps:")
    print("  1. Install Python 3.11 + Isaac Sim for real physics")
    print("  2. Try your own prompts with: python main.py --prompt 'your idea'")
    print("  3. Create custom optimization problems")
    print("  4. Integrate with your own simulation workflows")


def main():
    """Main demo entry point."""
    parser = argparse.ArgumentParser(
        description="Demo of Autonomous Simulation Design Platform"
    )

    parser.add_argument(
        "--phase",
        type=int,
        choices=[1, 2, 3],
        help="Run specific phase demo (1, 2, or 3)"
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Run complete demo of all phases"
    )

    args = parser.parse_args()

    try:
        if args.phase == 1:
            demo_phase1()
        elif args.phase == 2:
            demo_phase2()
        elif args.phase == 3:
            demo_phase3()
        elif args.all:
            demo_all()
        else:
            # Interactive menu
            print("\n" + "="*70)
            print("AUTONOMOUS SIMULATION DESIGN PLATFORM - DEMO")
            print("="*70)
            print("\nChoose a demo:")
            print("  1. Phase 1: Scene Generation & Physics")
            print("  2. Phase 2: Natural Language Interface")
            print("  3. Phase 3: Gradient-Based Optimization")
            print("  4. All Phases (Complete Demo)")
            print("  0. Exit")

            choice = input("\nEnter choice (0-4): ").strip()

            if choice == "1":
                demo_phase1()
            elif choice == "2":
                demo_phase2()
            elif choice == "3":
                demo_phase3()
            elif choice == "4":
                demo_all()
            elif choice == "0":
                print("Exiting...")
            else:
                print("Invalid choice")

    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
