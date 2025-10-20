#!/usr/bin/env python3
"""
Generative UI for Autonomous Simulation Platform
Complete end-to-end workflow: Natural Language → USD Generation → Isaac Sim Rendering → Video Output
"""

import gradio as gr
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple
import time

from main import AutonomousSimulationPlatform


class GenerativeSimulationUI:
    """
    End-to-end generative simulation interface.
    Takes natural language input, generates USD scenes, and renders them in Isaac Sim.
    """

    def __init__(self):
        """Initialize the UI with the simulation platform"""
        self.platform = None
        self.output_dir = Path("output/live_sims")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Find Isaac Sim python executable
        self.isaac_python = self._find_isaac_python()

        print("🚀 Generative Simulation UI initialized")
        print(f"📂 Output directory: {self.output_dir}")
        if self.isaac_python:
            print(f"🐍 Isaac Sim Python: {self.isaac_python}")
        else:
            print("⚠️  Warning: Isaac Sim Python not found automatically")

    def _find_isaac_python(self) -> Optional[Path]:
        """Attempt to find Isaac Sim python executable"""

        # Common Isaac Sim installation locations
        possible_paths = [
            Path.home() / ".local/share/ov/pkg/isaac-sim-5.0.0/python.sh",
            Path.home() / ".local/share/ov/pkg/isaac-sim-4.2.0/python.sh",
            Path("/opt/nvidia/isaac-sim/python.sh"),
            Path.cwd() / "venv311/bin/python",  # Fallback to our venv
        ]

        for path in possible_paths:
            if path.exists():
                return path

        return None

    def run_isaac_simulation(
        self,
        usd_path: Path,
        duration: float = 10.0,
        fps: int = 60
    ) -> Tuple[bool, Path, str]:
        """
        Execute USD simulation in Isaac Sim and render to video.

        Args:
            usd_path: Path to input USD scene file
            duration: Simulation duration in seconds
            fps: Frames per second for rendering

        Returns:
            Tuple of (success, video_path, log_output)
        """

        if not usd_path.exists():
            return False, None, f"❌ USD file not found: {usd_path}"

        if not self.isaac_python:
            return False, None, "❌ Isaac Sim Python executable not found. Please set path manually."

        # Output video path (same directory as USD file)
        video_path = usd_path.parent / f"{usd_path.stem}_simulation.mp4"

        # Path to execution script
        exec_script = Path(__file__).parent / "execute_isaac_headless.py"

        if not exec_script.exists():
            return False, None, f"❌ Execution script not found: {exec_script}"

        # Build command
        command = [
            str(self.isaac_python),
            str(exec_script),
            "--usd_path", str(usd_path),
            "--output_path", str(video_path),
            "--duration", str(duration),
            "--fps", str(fps)
        ]

        log_output = f"🎬 **Launching Isaac Sim Renderer**\n\n"
        log_output += f"**Command:**\n```\n{' '.join(command)}\n```\n\n"

        try:
            # Execute the command
            log_output += "⏳ Running simulation (this may take several minutes)...\n\n"

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            # Capture output
            log_output += "**STDOUT:**\n```\n"
            log_output += result.stdout if result.stdout else "(no output)"
            log_output += "\n```\n\n"

            if result.stderr:
                log_output += "**STDERR:**\n```\n"
                log_output += result.stderr
                log_output += "\n```\n\n"

            # Check success
            if result.returncode == 0:
                if video_path.exists():
                    log_output += f"✅ **Simulation Complete!**\n"
                    log_output += f"   📹 Video: {video_path.name}\n"
                    return True, video_path, log_output
                else:
                    log_output += "⚠️ **Warning:** Process succeeded but video file not found\n"
                    return False, None, log_output
            else:
                log_output += f"❌ **Execution Failed** (exit code: {result.returncode})\n"
                return False, None, log_output

        except subprocess.TimeoutExpired:
            log_output += "❌ **Timeout:** Simulation took longer than 5 minutes\n"
            return False, None, log_output

        except Exception as e:
            log_output += f"❌ **Exception:** {str(e)}\n"
            import traceback
            log_output += f"```\n{traceback.format_exc()}\n```\n"
            return False, None, log_output

    def generate_simulation(
        self,
        prompt: str,
        progress=gr.Progress()
    ) -> Tuple[str, Optional[str], bool]:
        """
        Main workflow: Generate USD from prompt

        Args:
            prompt: Natural language description of simulation
            progress: Gradio progress tracker

        Returns:
            Tuple of (status_log, video_path, video_visible)
        """

        if not prompt or len(prompt.strip()) < 3:
            return "⚠️ Please enter a simulation description", None, False

        status_log = "🚀 **Starting Generative Workflow**\n\n"
        status_log += f"**Your Prompt:** \"{prompt}\"\n\n"

        try:
            # Step 1: Initialize agents
            progress(0.1, desc="Initializing AI agents...")
            status_log += "🤖 **Step 1: Initializing AI Agents**\n"
            status_log += "- Loading Architect Agent...\n"
            status_log += "- Loading SceneGraph Agent...\n"
            status_log += "- Loading Physics Agent...\n"
            status_log += "- Loading Validator Agent...\n"

            # Initialize platform (lazy loading)
            if self.platform is None:
                self.platform = AutonomousSimulationPlatform()

            status_log += "✅ All agents ready\n\n"

            # Step 2: Generate USD scene
            progress(0.3, desc="Generating USD scene...")
            status_log += "🏗️ **Step 2: Generating USD Scene**\n"
            status_log += "- Architect parsing your request...\n"

            # Create timestamped output directory for this simulation
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            sim_output_dir = self.output_dir / f"sim_{timestamp}"
            sim_output_dir.mkdir(parents=True, exist_ok=True)

            status_log += "- SceneGraph building geometry...\n"
            status_log += "- Physics applying properties...\n"
            status_log += "- Validator checking consistency...\n"

            # Call the generative workflow
            try:
                usd_path = self.platform.create_from_prompt(
                    prompt=prompt,
                    output_dir=sim_output_dir,
                    validate=True,
                    explain=True
                )

                status_log += f"\n✅ **USD Scene Generated Successfully!**\n"
                status_log += f"   📁 Output: `{usd_path}`\n\n"

                progress(0.6, desc="USD generation complete!")

                # Step 3: Execute in Isaac Sim
                status_log += "🎬 **Step 3: Launching Isaac Sim for Physics Execution**\n"
                status_log += "   This may take a few minutes...\n\n"

                progress(0.7, desc="Launching Isaac Sim...")

                # Run Isaac Sim simulation
                success, video_path, isaac_log = self.run_isaac_simulation(
                    usd_path=usd_path,
                    duration=10.0,
                    fps=60
                )

                # Append Isaac Sim logs
                status_log += isaac_log

                if success and video_path and video_path.exists():
                    # Success! Display video
                    progress(1.0, desc="Complete! Video ready.")

                    status_log += "\n" + "="*50 + "\n"
                    status_log += "🎉 **SIMULATION COMPLETE!**\n"
                    status_log += "="*50 + "\n\n"
                    status_log += f"✅ **USD Scene:** `{usd_path.name}`\n"
                    status_log += f"✅ **Video:** `{video_path.name}`\n"
                    status_log += f"✅ **Duration:** 10 seconds @ 60 FPS\n\n"
                    status_log += "🎥 **Watch your simulation below!**\n"

                    return status_log, str(video_path), True

                else:
                    # Isaac Sim execution failed
                    status_log += "\n⚠️ **Isaac Sim execution encountered issues**\n"
                    status_log += "   The USD file was generated successfully, but video rendering failed.\n"
                    status_log += f"   You can still view the USD file at: `{usd_path}`\n\n"

                    return status_log, None, False

            except Exception as gen_error:
                status_log += f"\n❌ **Generation Error:** {str(gen_error)}\n"
                status_log += "\n**Details:**\n"
                import traceback
                status_log += f"```\n{traceback.format_exc()}\n```\n"
                return status_log, None, False

        except Exception as e:
            error_log = status_log + f"\n\n❌ **Error:** {str(e)}\n"
            error_log += "\n**Stack trace:**\n```\n"
            import traceback
            error_log += traceback.format_exc()
            error_log += "\n```"
            return error_log, None, False


def create_ui() -> gr.Blocks:
    """Create the Gradio interface"""

    # Initialize the UI backend
    ui_backend = GenerativeSimulationUI()

    # Create the Gradio UI
    with gr.Blocks(
        title="🎬 Generative Simulation Platform",
        theme=gr.themes.Soft()
    ) as demo:

        gr.Markdown("""
        # 🎬 Generative Autonomous Simulation Platform
        ### From Natural Language to Physics-Accurate Video

        **Complete Pipeline:** Natural Language → AI Agents → USD Scene → Isaac Sim → MP4 Video

        **Status:** 🟢 All Systems Ready | End-to-End Generation Active
        """)

        with gr.Row():
            with gr.Column(scale=6):
                # User input
                prompt_input = gr.Textbox(
                    label="🎯 Describe Your Simulation",
                    placeholder="Example: 'Two robots playing tennis on a court' or 'Car crash test at 50 km/h' or 'Drone flying through obstacles'",
                    lines=3,
                    max_lines=5
                )

                # Generate button
                generate_btn = gr.Button(
                    "🚀 Generate & Run Simulation",
                    variant="primary",
                    size="lg"
                )

                # Status log
                status_output = gr.Textbox(
                    label="📊 Generation Status & Logs",
                    lines=20,
                    max_lines=30,
                    interactive=False
                )

                # Video output (initially hidden)
                video_output = gr.Video(
                    label="🎥 Simulation Result",
                    visible=False
                )

            with gr.Column(scale=4):
                gr.Markdown("""
                ### 🎯 Example Prompts

                **🤖 Robotics:**
                - Two robots playing tennis
                - Humanoid robot walking
                - Robot arm picking objects
                - Dancing robots synchronized

                **🚗 Vehicles:**
                - Car crash test 50 km/h
                - Drone flying through forest
                - Rocket launching
                - Autonomous car parking

                **⚽ Sports & Games:**
                - Soccer match physics
                - Basketball free throw
                - Bowling ball hitting pins
                - Pool table break shot

                **🏗️ Engineering:**
                - Bridge collapse simulation
                - Building demolition
                - Crane lifting heavy load
                - Earthquake stress test

                **🌍 Physics:**
                - Ball bouncing on trampoline
                - Pendulum swinging
                - Dominos chain reaction
                - Water pouring simulation

                ---

                ### ⚙️ System Components

                **AI Agents:**
                - 🏗️ Architect Agent
                - 📐 SceneGraph Agent
                - ⚛️ Physics Agent
                - ✅ Validator Agent
                - 🎯 Optimization Agent

                **Tech Stack:**
                - Python 3.11
                - PyTorch 2.7.0
                - Isaac Sim 5.0.0
                - Isaac Lab 0.47.1
                - OpenUSD
                - Microsoft AutoGen
                - Gradio
                """)

        gr.Markdown("""
        ---
        ### 🎬 How It Works:

        1. **Natural Language Input** → You describe any simulation
        2. **AI Agents Parse** → Architect, SceneGraph, Physics agents analyze
        3. **USD Generation** → Complete 3D scene created in OpenUSD format
        4. **Isaac Sim Execution** → Physics simulation runs in NVIDIA Isaac Sim
        5. **Video Rendering** → Simulation recorded as high-quality MP4
        6. **Results Display** → Video shows in browser automatically

        **🎯 This is a complete end-to-end generative pipeline!**

        ---
        *Built with: Microsoft AutoGen • OpenUSD • NVIDIA Isaac Lab • PyTorch • Gradio*
        """)

        # Event handlers
        generate_btn.click(
            fn=ui_backend.generate_simulation,
            inputs=[prompt_input],
            outputs=[status_output, video_output, video_output]  # Last one controls visibility
        )

        # Allow Enter key to submit
        prompt_input.submit(
            fn=ui_backend.generate_simulation,
            inputs=[prompt_input],
            outputs=[status_output, video_output, video_output]
        )

    return demo


def main():
    """Main entry point"""

    print("\n" + "="*70)
    print("🎬 GENERATIVE AUTONOMOUS SIMULATION PLATFORM")
    print("="*70)
    print("\n✨ Features:")
    print("   - Natural language to USD scene generation")
    print("   - Automatic Isaac Sim physics execution")
    print("   - Real-time video rendering")
    print("   - Complete end-to-end pipeline")
    print("\n🤖 AI Agents:")
    print("   - Architect Agent (scene parsing)")
    print("   - SceneGraph Agent (USD generation)")
    print("   - Physics Agent (dynamics)")
    print("   - Validator Agent (quality checks)")
    print("\n🎯 Status: All systems ready!")
    print("="*70)
    print()

    # Create and launch UI
    demo = create_ui()

    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )


if __name__ == "__main__":
    main()
