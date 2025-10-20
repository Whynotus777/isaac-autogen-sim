"""
Phase 1 Pipeline: Sequential workflow from JSON to executable USD simulation.

This pipeline:
1. Parses JSON configuration
2. Sends scene commands to SceneGraph agent -> generates base USD
3. Sends physics commands to Physics agent -> annotates USD with physics
4. Outputs a single executable USD file
"""

import json
from typing import Dict, Any, Optional, List
from pathlib import Path
from pydantic import BaseModel, Field, ValidationError

from agents import SceneGraphAgent, PhysicsAgent
from models.scene_commands import SceneCommand, SceneConfiguration
from models.physics_commands import PhysicsCommand, PhysicsConfiguration


class SimulationConfig(BaseModel):
    """Complete simulation configuration combining scene and physics."""
    name: str = Field(..., description="Name of the simulation")
    description: Optional[str] = Field(default=None, description="Description")

    # Scene configuration
    scene: Dict[str, Any] = Field(..., description="Scene commands configuration")

    # Physics configuration
    physics: Dict[str, Any] = Field(..., description="Physics commands configuration")

    # Output settings
    output_path: Optional[str] = Field(
        default=None,
        description="Custom output path for the final USD file"
    )


class Phase1Pipeline:
    """
    Phase 1 sequential pipeline for simulation generation.

    Workflow:
    JSON Config -> SceneGraph Agent -> Base USD -> Physics Agent -> Final USD
    """

    def __init__(
        self,
        llm_config: Optional[Dict[str, Any]] = None,
        csm_api_key: Optional[str] = None,
        spline_api_key: Optional[str] = None,
    ):
        """
        Initialize the Phase 1 pipeline.

        Args:
            llm_config: LLM configuration for AutoGen agents
            csm_api_key: API key for CSM.ai
            spline_api_key: API key for Spline AI
        """
        self.scene_agent = SceneGraphAgent(
            llm_config=llm_config,
            csm_api_key=csm_api_key,
            spline_api_key=spline_api_key,
        )
        self.physics_agent = PhysicsAgent(llm_config=llm_config)

    def run(
        self,
        config_path: Path,
        output_dir: Optional[Path] = None,
    ) -> Path:
        """
        Execute the complete Phase 1 pipeline.

        Args:
            config_path: Path to JSON configuration file
            output_dir: Directory for output files (default: ./output)

        Returns:
            Path to the final USD file

        Raises:
            ValidationError: If configuration is invalid
            RuntimeError: If pipeline execution fails
        """
        # Set default output directory
        if output_dir is None:
            output_dir = Path("output")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: Load and parse configuration
        print(f"[Phase1Pipeline] Loading configuration from {config_path}")
        config = self._load_config(config_path)

        # Step 2: Parse scene commands
        print("[Phase1Pipeline] Parsing scene configuration...")
        scene_config = self._parse_scene_config(config.scene)

        # Step 3: Generate base USD with SceneGraph agent
        print("[Phase1Pipeline] Generating scene geometry...")
        base_usd_path = output_dir / f"{config.name}_scene.usd"
        self.scene_agent.create_from_config(scene_config, base_usd_path)
        print(f"[Phase1Pipeline] Scene created: {base_usd_path}")

        # Step 4: Parse physics commands
        print("[Phase1Pipeline] Parsing physics configuration...")
        physics_config = self._parse_physics_config(config.physics)

        # Step 5: Apply physics with Physics agent
        print("[Phase1Pipeline] Applying physics properties...")
        if config.output_path:
            final_usd_path = Path(config.output_path)
        else:
            final_usd_path = output_dir / f"{config.name}_final.usd"

        self.physics_agent.apply_from_config(
            base_usd_path,
            physics_config,
            final_usd_path
        )
        print(f"[Phase1Pipeline] Physics applied: {final_usd_path}")

        # Step 6: Validate output
        print("[Phase1Pipeline] Validating output...")
        if not final_usd_path.exists():
            raise RuntimeError(f"Final USD file was not created: {final_usd_path}")

        print(f"[Phase1Pipeline] Pipeline complete! Output: {final_usd_path}")
        return final_usd_path

    def _load_config(self, config_path: Path) -> SimulationConfig:
        """Load and validate JSON configuration."""
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, 'r') as f:
            data = json.load(f)

        try:
            config = SimulationConfig(**data)
        except ValidationError as e:
            raise ValidationError(f"Invalid configuration: {e}") from e

        return config

    def _parse_scene_config(self, scene_data: Dict[str, Any]) -> SceneConfiguration:
        """Parse scene configuration into SceneConfiguration object."""
        try:
            # The scene_data should have 'scene_name', 'description', and 'commands'
            scene_config = SceneConfiguration(**scene_data)
        except ValidationError as e:
            raise ValidationError(f"Invalid scene configuration: {e}") from e

        return scene_config

    def _parse_physics_config(
        self,
        physics_data: Dict[str, Any]
    ) -> PhysicsConfiguration:
        """Parse physics configuration into PhysicsConfiguration object."""
        try:
            # The physics_data should have 'configuration_name', 'description', and 'commands'
            physics_config = PhysicsConfiguration(**physics_data)
        except ValidationError as e:
            raise ValidationError(f"Invalid physics configuration: {e}") from e

        return physics_config

    def run_from_dict(
        self,
        config_dict: Dict[str, Any],
        output_dir: Optional[Path] = None,
    ) -> Path:
        """
        Execute the pipeline from a dictionary configuration.

        Args:
            config_dict: Configuration as a dictionary
            output_dir: Directory for output files

        Returns:
            Path to the final USD file
        """
        # Validate config
        try:
            config = SimulationConfig(**config_dict)
        except ValidationError as e:
            raise ValidationError(f"Invalid configuration: {e}") from e

        # Create temporary config file
        if output_dir is None:
            output_dir = Path("output")
        output_dir.mkdir(parents=True, exist_ok=True)

        temp_config_path = output_dir / "_temp_config.json"
        with open(temp_config_path, 'w') as f:
            json.dump(config_dict, f, indent=2)

        try:
            result = self.run(temp_config_path, output_dir)
        finally:
            # Clean up temp file
            if temp_config_path.exists():
                temp_config_path.unlink()

        return result


# Convenience function for quick pipeline execution
def execute_phase1(
    config_path: Path,
    output_dir: Optional[Path] = None,
    llm_config: Optional[Dict[str, Any]] = None,
) -> Path:
    """
    Convenience function to execute Phase 1 pipeline.

    Args:
        config_path: Path to JSON configuration
        output_dir: Output directory
        llm_config: LLM configuration

    Returns:
        Path to final USD file
    """
    pipeline = Phase1Pipeline(llm_config=llm_config)
    return pipeline.run(config_path, output_dir)
