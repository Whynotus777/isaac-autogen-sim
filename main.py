#!/usr/bin/env python3
"""
Main entry point for the Autonomous Simulation Design Platform.

This demonstrates the complete Phase 1 and Phase 2 workflow:
- Natural language input
- Multi-agent coordination
- Scene generation
- Physics application
- Validation
- USD output
"""

import argparse
from pathlib import Path
from typing import Optional
import json

from agents.architect_agent import ArchitectAgent
from agents.validator_agent import ValidatorAgent
from pipelines.phase1_pipeline import Phase1Pipeline


class AutonomousSimulationPlatform:
    """Main orchestrator for the autonomous simulation platform."""

    def __init__(self, llm_config: Optional[dict] = None):
        """
        Initialize the platform.

        Args:
            llm_config: LLM configuration for AutoGen agents
        """
        self.architect = ArchitectAgent(llm_config=llm_config)
        self.validator = ValidatorAgent(llm_config=llm_config)
        self.pipeline = Phase1Pipeline(llm_config=llm_config)

        print("🚀 Autonomous Simulation Design Platform initialized")
        print("   - Architect Agent: Ready")
        print("   - Validator Agent: Ready")
        print("   - SceneGraph Agent: Ready")
        print("   - Physics Agent: Ready")

    def create_from_prompt(
        self,
        prompt: str,
        output_dir: Optional[Path] = None,
        validate: bool = True,
        explain: bool = True,
    ) -> Path:
        """
        Create a complete simulation from a natural language prompt.

        Args:
            prompt: Natural language description of the simulation
            output_dir: Directory for output files
            validate: Whether to validate the output
            explain: Whether to print explanation of the plan

        Returns:
            Path to the final USD file
        """
        print("\n" + "="*60)
        print("📝 Processing Request")
        print("="*60)
        print(f"Prompt: {prompt}\n")

        # Step 1: Parse prompt and generate config
        print("[1/5] Architect: Analyzing request...")
        config = self.architect.generate_simulation_config(prompt)

        # Explain the plan
        if explain:
            print("\n[2/5] Architect: Generated plan")
            print(f"   Simulation: {config['name']}")
            print(f"   Scene commands: {len(config['scene']['commands'])}")
            print(f"   Physics commands: {len(config['physics']['commands'])}")

        # Save configuration
        if output_dir is None:
            output_dir = Path("output")
        output_dir.mkdir(parents=True, exist_ok=True)

        config_path = output_dir / f"{config['name']}_config.json"
        self.architect.save_config(config, config_path)

        # Step 2: Execute pipeline
        print("\n[3/5] Pipeline: Executing...")
        try:
            final_usd = self.pipeline.run_from_dict(config, output_dir)
        except Exception as e:
            print(f"❌ Pipeline execution failed: {e}")
            raise

        # Step 3: Validate
        if validate:
            print("\n[4/5] Validator: Checking simulation...")
            report = self.validator.validate(final_usd)

            print("\n" + report.summary())

            if not self.validator.request_user_confirmation(report, auto_approve=True):
                print("❌ Simulation rejected by validator")
                return None

        # Step 4: Complete
        print("\n[5/5] ✅ Simulation created successfully!")
        print(f"   Output: {final_usd}")
        print(f"   Config: {config_path}")

        return final_usd

    def create_from_config(
        self,
        config_path: Path,
        output_dir: Optional[Path] = None,
        validate: bool = True,
    ) -> Path:
        """
        Create simulation from a JSON configuration file.

        Args:
            config_path: Path to configuration JSON
            output_dir: Output directory
            validate: Whether to validate

        Returns:
            Path to final USD file
        """
        print("\n" + "="*60)
        print("📝 Processing Configuration File")
        print("="*60)
        print(f"Config: {config_path}\n")

        # Execute pipeline
        final_usd = self.pipeline.run(config_path, output_dir)

        # Validate if requested
        if validate:
            print("\nValidator: Checking simulation...")
            report = self.validator.validate(final_usd)
            print("\n" + report.summary())

            if not self.validator.request_user_confirmation(report, auto_approve=True):
                print("❌ Simulation rejected by validator")
                return None

        print("\n✅ Simulation created successfully!")
        print(f"   Output: {final_usd}")

        return final_usd


def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser(
        description="Autonomous Simulation Design Platform"
    )

    parser.add_argument(
        "--prompt",
        type=str,
        help="Natural language description of the simulation"
    )

    parser.add_argument(
        "--config",
        type=Path,
        help="Path to JSON configuration file"
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output"),
        help="Output directory (default: ./output)"
    )

    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip validation step"
    )

    parser.add_argument(
        "--no-explain",
        action="store_true",
        help="Skip plan explanation"
    )

    parser.add_argument(
        "--example",
        action="store_true",
        help="Run example simulation"
    )

    args = parser.parse_args()

    # Initialize platform
    platform = AutonomousSimulationPlatform()

    # Run example if requested
    if args.example:
        print("\n🎯 Running example: Block falling onto table")
        prompt = "Create a scene with a table and a block suspended above it. The block should fall and land on the table due to gravity."
        platform.create_from_prompt(
            prompt,
            output_dir=args.output,
            validate=not args.no_validate,
            explain=not args.no_explain,
        )
        return

    # Process prompt
    if args.prompt:
        platform.create_from_prompt(
            args.prompt,
            output_dir=args.output,
            validate=not args.no_validate,
            explain=not args.no_explain,
        )
        return

    # Process config file
    if args.config:
        platform.create_from_config(
            args.config,
            output_dir=args.output,
            validate=not args.no_validate,
        )
        return

    # No input provided
    parser.print_help()


if __name__ == "__main__":
    main()
