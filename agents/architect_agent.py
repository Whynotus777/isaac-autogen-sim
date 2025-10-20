"""
Architect Agent: Natural language interface and orchestrator for the multi-agent system.
"""

import os
import re
import json
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
import autogen
from pydantic import BaseModel

from models.scene_commands import (
    CreatePrim,
    SetTransform,
    SetMaterial,
    CreateLight,
    CreateCamera,
    PrimType,
    Vec3,
    Quaternion,
    RGBAColor,
    MaterialProperties,
)
from models.physics_commands import (
    ApplyRigidBody,
    SetFriction,
    ApplyCollider,
    ConfigureSolver,
    RigidBodyProperties,
    FrictionProperties,
    SolverSettings,
    ColliderType,
)


class SimulationIntent(BaseModel):
    """Parsed intent from natural language."""
    intent_type: str  # "create_scene", "add_physics", "modify_object", etc.
    entities: List[str]  # Objects mentioned
    properties: Dict[str, Any]  # Properties and parameters
    constraints: List[str]  # Constraints or requirements


class ArchitectAgent:
    """
    Architect Agent: Orchestrates the multi-agent system.

    Responsibilities:
    1. Parse natural language prompts
    2. Identify key entities and objectives
    3. Decompose requests into structured tasks
    4. Coordinate specialist agents (SceneGraph, Physics, Validator)
    5. Manage the GroupChat workflow
    """

    def __init__(self, llm_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Architect agent.

        Args:
            llm_config: Configuration for the AutoGen LLM
        """
        # Set up AutoGen conversable agent
        if llm_config is None:
            llm_config = {
                "config_list": [{
                    "model": "gpt-4",
                    "api_key": os.getenv("OPENAI_API_KEY"),
                }],
                "timeout": 120,
                "temperature": 0.2,
            }

        self.agent = autogen.ConversableAgent(
            name="Architect",
            system_message=self._get_system_message(),
            llm_config=llm_config,
            human_input_mode="NEVER",
        )

        # Conversation history
        self.conversation_history: List[Dict[str, str]] = []

    def _get_system_message(self) -> str:
        """Get the system message for the Architect agent."""
        return """You are the Architect agent, the orchestrator of an autonomous simulation design platform.

Your role is to:
1. **Parse Natural Language**: Understand user requests for creating physics simulations
2. **Entity Identification**: Extract key objects, materials, forces, and constraints
3. **Task Decomposition**: Break down complex requests into structured commands for:
   - SceneGraph agent (geometry, materials, lighting, cameras)
   - Physics agent (rigid bodies, colliders, joints, solver settings)
   - Validator agent (checking for errors and inconsistencies)
4. **Orchestration**: Coordinate the multi-agent workflow to produce complete simulations

**Understanding User Intent:**
- Identify what objects need to be created
- Determine physical properties (mass, friction, etc.)
- Recognize spatial relationships and constraints
- Infer reasonable defaults when details aren't specified

**Output Format:**
Generate JSON configurations that can be consumed by the SceneGraph and Physics agents.

**Examples:**
User: "Create a scene where a robot arm pushes a block off a table"
You should identify:
- Entities: robot arm, block, table
- Scene commands: Create table (cube), create block (cube), create robot arm (articulated)
- Physics: Apply rigid bodies, set masses, create joints for robot arm, configure gravity
- Constraints: Block starts on table, arm can reach block

Always think step-by-step and ensure all physical properties are reasonable.
"""

    def parse_prompt(self, prompt: str) -> SimulationIntent:
        """
        Parse a natural language prompt into structured intent.

        Args:
            prompt: Natural language description of desired simulation

        Returns:
            Structured SimulationIntent object
        """
        # Use LLM to parse the prompt
        parsing_prompt = f"""Parse the following simulation request and extract:
1. Intent type (create_scene, add_physics, modify_object, query_simulation)
2. Entities mentioned (objects, materials, forces)
3. Properties and parameters
4. Constraints or requirements

Request: {prompt}

Return a JSON object with keys: intent_type, entities, properties, constraints
"""

        # Get response from LLM
        response = self.agent.generate_reply(
            messages=[{"role": "user", "content": parsing_prompt}]
        )

        # Parse the response
        try:
            # Extract JSON from response if it's wrapped in text
            json_match = re.search(r'\{.*\}', str(response), re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
            else:
                parsed = json.loads(str(response))

            intent = SimulationIntent(**parsed)
        except Exception as e:
            # Fallback: basic parsing
            intent = SimulationIntent(
                intent_type="create_scene",
                entities=self._extract_entities_simple(prompt),
                properties={},
                constraints=[]
            )

        return intent

    def decompose_to_commands(
        self,
        prompt: str
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Decompose a natural language prompt into scene and physics commands.

        Args:
            prompt: Natural language description

        Returns:
            Tuple of (scene_commands, physics_commands)
        """
        decomposition_prompt = f"""Given this simulation request, decompose it into:
1. Scene commands (geometry, materials, lights, cameras)
2. Physics commands (rigid bodies, colliders, joints, solver settings)

Request: {prompt}

For each command, specify:
- command_type (e.g., "CreatePrim", "ApplyRigidBody")
- All required parameters
- Reasonable default values for unspecified properties

Return two JSON arrays: "scene_commands" and "physics_commands"

Example format:
{{
  "scene_commands": [
    {{
      "command_type": "CreatePrim",
      "prim_path": "/World/Table",
      "prim_type": "Cube",
      "scale": {{"x": 2.0, "y": 1.0, "z": 0.1}}
    }}
  ],
  "physics_commands": [
    {{
      "command_type": "ApplyRigidBody",
      "prim_path": "/World/Table",
      "properties": {{
        "mass": 50.0,
        "linear_damping": 0.0,
        "angular_damping": 0.05
      }},
      "is_kinematic": true
    }}
  ]
}}
"""

        # Get response from LLM
        response = self.agent.generate_reply(
            messages=[{"role": "user", "content": decomposition_prompt}]
        )

        # Parse the response
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', str(response), re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
            else:
                parsed = json.loads(str(response))

            scene_commands = parsed.get("scene_commands", [])
            physics_commands = parsed.get("physics_commands", [])

        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            # Return empty commands as fallback
            scene_commands = []
            physics_commands = []

        return scene_commands, physics_commands

    def generate_simulation_config(
        self,
        prompt: str,
        simulation_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate a complete simulation configuration from natural language.

        Args:
            prompt: Natural language description of the simulation
            simulation_name: Name for the simulation (auto-generated if None)

        Returns:
            Complete simulation configuration dictionary
        """
        # Generate name if not provided
        if simulation_name is None:
            simulation_name = self._generate_simulation_name(prompt)

        # Parse the prompt
        intent = self.parse_prompt(prompt)

        # Decompose into commands
        scene_commands, physics_commands = self.decompose_to_commands(prompt)

        # Build complete configuration
        config = {
            "name": simulation_name,
            "description": prompt,
            "scene": {
                "scene_name": simulation_name,
                "description": f"Scene for: {prompt}",
                "commands": scene_commands
            },
            "physics": {
                "configuration_name": f"{simulation_name}_physics",
                "description": f"Physics configuration for: {prompt}",
                "commands": physics_commands
            }
        }

        # Add default solver configuration if not present
        has_solver = any(
            cmd.get("command_type") == "ConfigureSolver"
            for cmd in physics_commands
        )

        if not has_solver and physics_commands:
            # Add default solver configuration
            solver_command = {
                "command_type": "ConfigureSolver",
                "scene_path": "/World/PhysicsScene",
                "settings": {
                    "time_step": 1.0/60.0,
                    "position_iterations": 4,
                    "velocity_iterations": 1,
                    "gravity": {"x": 0.0, "y": 0.0, "z": -9.81},
                    "enable_ccd": False,
                    "enable_stabilization": True,
                    "broadphase_type": "GPU"
                }
            }
            config["physics"]["commands"].insert(0, solver_command)

        return config

    def _extract_entities_simple(self, text: str) -> List[str]:
        """Simple keyword-based entity extraction (fallback)."""
        common_objects = [
            "cube", "sphere", "cylinder", "cone", "plane", "table", "block",
            "robot", "arm", "ball", "box", "floor", "wall", "ramp", "pendulum"
        ]

        entities = []
        text_lower = text.lower()

        for obj in common_objects:
            if obj in text_lower:
                entities.append(obj)

        return entities

    def _generate_simulation_name(self, prompt: str) -> str:
        """Generate a simulation name from the prompt."""
        # Take first few words, clean them up
        words = prompt.lower().split()[:3]
        name = "_".join(re.sub(r'[^a-z0-9]', '', word) for word in words)
        return name or "simulation"

    def explain_plan(self, config: Dict[str, Any]) -> str:
        """
        Generate a human-readable explanation of the simulation plan.

        Args:
            config: Simulation configuration dictionary

        Returns:
            Human-readable plan description
        """
        explanation_prompt = f"""Given this simulation configuration, provide a clear,
step-by-step explanation of what will be created and simulated:

Configuration:
{json.dumps(config, indent=2)}

Format the explanation as:
1. Scene Overview: What objects will be created
2. Object Details: Positions, materials, properties
3. Physics Setup: Masses, forces, constraints
4. Expected Behavior: What will happen when the simulation runs
"""

        response = self.agent.generate_reply(
            messages=[{"role": "user", "content": explanation_prompt}]
        )

        return str(response)

    def save_config(self, config: Dict[str, Any], output_path: Path) -> None:
        """Save configuration to JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(config, f, indent=2)

        print(f"Configuration saved to: {output_path}")
