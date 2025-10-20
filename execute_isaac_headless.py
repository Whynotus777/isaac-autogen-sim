#!/usr/bin/env python3
"""
Isaac Sim Headless Execution Script
Loads a USD file, runs physics simulation, and renders to MP4 using the native Movie Capture tool.
"""

import argparse
import sys
import asyncio
from pathlib import Path

# Isaac Sim imports
try:
    from omni.isaac.kit import SimulationApp
except ImportError:
    print("ERROR: Could not import Isaac Sim. Make sure you're running this with Isaac Sim's Python.")
    print("Usage: /path/to/isaac_sim/python.sh execute_isaac_headless.py --usd_path scene.usd --output_path video.mp4")
    sys.exit(1)


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Execute USD simulation in Isaac Sim and render to video"
    )
    parser.add_argument(
        "--usd_path",
        type=str,
        required=True,
        help="Path to input USD scene file"
    )
    parser.add_argument(
        "--output_path",
        type=str,
        required=True,
        help="Path to output MP4 video file"
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=10.0,
        help="Simulation duration in seconds (default: 10.0)"
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=60,
        help="Frames per second for simulation and video (default: 60)"
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1280,
        help="Video width in pixels (default: 1280)"
    )
    parser.add_argument(
        "--height",
        type=int,
        default=720,
        help="Video height in pixels (default: 720)"
    )

    return parser.parse_args()


async def run_simulation_and_render(args):
    """The core asynchronous task to run simulation and capture video."""

    # Import necessary modules after app start
    import omni.timeline
    import omni.usd
    from omni.isaac.core import World
    from omni.isaac.core.utils.stage import open_stage

    try:
        import omni.kit.capture.viewport as movie_capture
        use_movie_capture = True
    except ImportError:
        print("⚠️  Warning: Movie capture module not available, trying alternative...")
        try:
            import omni.kit.movie_capture as movie_capture
            use_movie_capture = True
        except ImportError:
            use_movie_capture = False
            print("⚠️  Movie capture not available, simulation will run without recording")

    # Load the USD stage
    print(f"\n📂 Loading USD scene: {args.usd_path}")
    open_stage(str(args.usd_path))

    # Verify stage loaded
    stage = omni.usd.get_context().get_stage()
    if stage is None:
        raise RuntimeError("Failed to load USD stage")

    print("✅ USD stage loaded successfully")

    # Initialize physics world
    print("\n⚛️  Initializing physics simulation...")
    world = World(physics_dt=1.0 / args.fps)

    # Use async initialization if available
    try:
        await world.initialize_simulation_context_async()
    except AttributeError:
        # Fallback to sync if async not available
        world.initialize_simulation_context()

    await world.reset_async()
    print("✅ Physics simulation initialized")

    if use_movie_capture:
        # Configure movie capture
        print(f"\n🎥 Setting up movie capture...")

        try:
            mc_interface = movie_capture.get_movie_capture_interface()

            # Configure capture settings
            output_dir = str(args.output_path.parent)
            output_name = args.output_path.stem

            capture_settings = {
                "output_path": output_dir,
                "name": output_name,
                "resolution": (args.width, args.height),
                "fps": args.fps,
                "file_format": "mp4",
                "duration": args.duration,
            }

            # Try different API versions
            try:
                mc_interface.set_capture_settings(capture_settings)
            except:
                # Alternative API
                mc_interface.set_output_directory(output_dir)
                mc_interface.set_file_name(output_name)
                mc_interface.set_resolution(args.width, args.height)
                mc_interface.set_fps(args.fps)

            print(f"   Output: {args.output_path}")
            print(f"   Duration: {args.duration}s @ {args.fps} FPS")
            print("✅ Movie capture configured")

            # Start capturing
            print("\n🎬 Starting video capture...")
            mc_interface.start_capture()

        except Exception as e:
            print(f"⚠️  Warning: Could not start movie capture: {e}")
            print("   Simulation will run without recording")
            use_movie_capture = False

    # Get timeline
    timeline = omni.timeline.get_timeline_interface()
    timeline.set_time_codes_per_seconds(args.fps)

    # Start the simulation
    print("\n▶️  Starting simulation...")
    timeline.play()

    # Run simulation for specified duration
    total_frames = int(args.duration * args.fps)
    print(f"   Running {total_frames} frames...")

    for frame in range(total_frames):
        # Step the world
        await world.step_async(render=True)

        # Progress indicator
        if frame % args.fps == 0:
            progress = (frame / total_frames) * 100
            print(f"   Progress: {progress:.1f}% ({frame}/{total_frames} frames)")

    # Stop timeline
    timeline.stop()
    print("\n✅ Simulation complete!")

    if use_movie_capture:
        try:
            # Wait for capture to finish
            print("\n🎥 Finalizing video encoding...")

            try:
                await mc_interface.wait_for_capture_end_async()
            except AttributeError:
                # Fallback: just stop capture
                mc_interface.stop_capture()
                # Give it some time to finish
                await asyncio.sleep(2)

            print("✅ Video capture complete!")

        except Exception as e:
            print(f"⚠️  Warning during video finalization: {e}")


def main():
    """Main execution function"""

    args = parse_args()

    # Validate inputs
    usd_path = Path(args.usd_path)
    if not usd_path.exists():
        print(f"ERROR: USD file not found: {usd_path}")
        sys.exit(1)

    output_path = Path(args.output_path)
    output_dir = output_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Update args with Path objects
    args.usd_path = usd_path
    args.output_path = output_path

    print("="*70)
    print("🎬 ISAAC SIM HEADLESS RENDERER")
    print("="*70)
    print(f"📂 Input USD: {usd_path}")
    print(f"🎥 Output Video: {output_path}")
    print(f"⏱️  Duration: {args.duration}s @ {args.fps} FPS")
    print(f"📐 Resolution: {args.width}x{args.height}")
    print("="*70)

    # Initialize Isaac Sim in headless mode
    print("\n🚀 Initializing Isaac Sim (headless mode)...")

    simulation_app = SimulationApp({
        "headless": True,
        "width": args.width,
        "height": args.height,
    })

    print("✅ Isaac Sim initialized successfully")

    try:
        # Run the main async simulation
        asyncio.run(run_simulation_and_render(args))

        print("\n" + "="*70)
        print("🎉 EXECUTION COMPLETE")
        print("="*70)

        if output_path.exists():
            print(f"✅ Video saved: {output_path}")
        else:
            print(f"⚠️  Video file not found at: {output_path}")
            print("   Check if movie capture module is available in your Isaac Sim installation")

    except Exception as e:
        print(f"\n❌ ERROR during execution: {e}")
        import traceback
        traceback.print_exc()
        simulation_app.close()
        sys.exit(1)

    finally:
        # Clean shutdown
        print("\n🔄 Shutting down Isaac Sim...")
        simulation_app.close()
        print("✅ Shutdown complete")


if __name__ == "__main__":
    main()
