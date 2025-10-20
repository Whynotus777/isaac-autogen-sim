#!/usr/bin/env python3
"""
Isaac Sim Headless Execution Script (Definitive Version)
Loads a USD, runs physics, and renders to MP4 using the native Movie Capture tool.
"""

import argparse
import sys
import asyncio
from pathlib import Path

# Initialize SimulationApp first, as it's a prerequisite for all other Isaac/Omni imports.
try:
    from omni.isaac.kit import SimulationApp
except ImportError:
    print("FATAL ERROR: Could not import Isaac Sim. Ensure this is run with Isaac Sim's python executable.", file=sys.stderr)
    sys.exit(1)


def parse_args():
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(description="Execute USD simulation and render to video.")
    parser.add_argument("--usd_path", type=str, required=True, help="Path to the input USD file.")
    parser.add_argument("--output_path", type=str, required=True, help="Path for the output MP4 video file.")
    parser.add_argument("--duration", type=float, default=10.0, help="Simulation duration in seconds.")
    parser.add_argument("--fps", type=int, default=60, help="Frames per second for rendering.")
    parser.add_argument("--width", type=int, default=1280, help="Video width.")
    parser.add_argument("--height", type=int, default=720, help="Video height.")
    return parser.parse_args()


async def run_and_render(args, simulation_app):
    """Core asynchronous task to run the simulation and capture video."""

    # Late import of Isaac modules, which must happen after the SimulationApp is initialized.
    from omni.isaac.core import World
    from omni.isaac.core.utils.stage import open_stage
    import omni.timeline

    # Try to import movie capture
    try:
        import omni.kit.movie_capture as movie_capture
        has_movie_capture = True
    except ImportError:
        print("⚠️  WARNING: Movie capture not available. Simulation will run without recording.", file=sys.stderr)
        has_movie_capture = False

    # 1. Load the USD Stage
    print(f"\n📂 Loading USD stage: {args.usd_path}")
    try:
        if not open_stage(usd_path=str(args.usd_path)):
            print(f"FATAL ERROR: Could not open stage at {args.usd_path}", file=sys.stderr)
            return False
    except Exception as e:
        print(f"FATAL ERROR: Exception while opening stage: {e}", file=sys.stderr)
        return False

    # Wait one frame for the stage to load properly
    await simulation_app.update_async()
    print("✅ Stage loaded successfully.")

    # 2. Initialize the Physics World
    print("\n⚛️  Initializing physics simulation...")
    world = World(physics_dt=1.0 / args.fps, stage_units_in_meters=1.0)

    try:
        await world.initialize_simulation_context_async()
    except AttributeError:
        # Fallback for different API versions
        world.initialize_simulation_context()

    await world.reset_async()
    print("✅ Physics simulation initialized.")

    # 3. Configure and Start Movie Capture
    if has_movie_capture:
        try:
            mc_interface = movie_capture.get_movie_capture_interface()

            capture_settings = {
                "output_path": str(args.output_path.parent),
                "name": args.output_path.stem,
                "resolution": (args.width, args.height),
                "fps": args.fps,
                "file_format": "mp4",
                "end_time_secs": args.duration,
            }

            mc_interface.set_capture_settings(capture_settings)
            print(f"\n🎥 Movie capture configured:")
            print(f"   Output: {args.output_path}")
            print(f"   Duration: {args.duration}s @ {args.fps} FPS")
            print(f"   Resolution: {args.width}x{args.height}")

            print("\n🎬 Starting capture...")
            mc_interface.start_capture()
            await simulation_app.update_async()  # Crucial: ensures the start command is processed
            print("✅ Capture started successfully.")

        except Exception as e:
            print(f"⚠️  WARNING: Could not start movie capture: {e}", file=sys.stderr)
            print("   Simulation will run without recording.")
            has_movie_capture = False

    # 4. Start the Simulation Timeline
    print("\n▶️  Starting simulation timeline...")
    timeline = omni.timeline.get_timeline_interface()
    timeline.play()
    await simulation_app.update_async()  # Crucial: ensures play command is processed
    print("✅ Simulation timeline is playing.")

    # 5. Run the Simulation Loop
    print(f"\n⏳ Running simulation for {args.duration} seconds...")
    print(f"   Total frames: {int(args.duration * args.fps)}")

    # Use proper frame stepping instead of asyncio.sleep
    start_time = world.current_time
    frame_count = 0
    total_frames = int(args.duration * args.fps)

    while world.current_time - start_time < args.duration:
        world.step(render=True)
        # The 'render=True' step implicitly triggers the movie capture for the frame.
        frame_count += 1

        # Progress indicator every second
        if frame_count % args.fps == 0:
            elapsed = world.current_time - start_time
            progress = (elapsed / args.duration) * 100
            print(f"   Progress: {progress:.1f}% ({frame_count}/{total_frames} frames, {elapsed:.1f}s)")

    print(f"\n✅ Simulation complete! Rendered {frame_count} frames.")

    # 6. Stop Everything and Wait for Completion
    print("\n🛑 Stopping timeline...")
    timeline.stop()

    if has_movie_capture:
        # The wait_for_capture_end_async() is the most critical part.
        # It pauses the script until the movie capture tool confirms the video file is fully written.
        print("⏳ Waiting for video encoding to finish...")
        print("   (This may take a few moments as Isaac Sim finalizes the MP4...)")

        try:
            await mc_interface.wait_for_capture_end_async()
            print("✅ Video encoding complete!")
        except AttributeError:
            # Fallback if async method not available
            print("⚠️  wait_for_capture_end_async() not available, using fallback...")
            # Give some time for encoding to complete
            await asyncio.sleep(5)
        except Exception as e:
            print(f"⚠️  Warning during capture finalization: {e}", file=sys.stderr)

    return True


def main():
    """Main execution function."""

    args = parse_args()
    args.usd_path = Path(args.usd_path)
    args.output_path = Path(args.output_path)

    # Validate input
    if not args.usd_path.exists():
        print(f"FATAL ERROR: USD file not found: {args.usd_path}", file=sys.stderr)
        sys.exit(1)

    # Create output directory
    args.output_path.parent.mkdir(parents=True, exist_ok=True)

    print("="*70)
    print("🎬 ISAAC SIM HEADLESS RENDERER (Definitive Version)")
    print("="*70)
    print(f"📂 Input USD: {args.usd_path}")
    print(f"🎥 Output Video: {args.output_path}")
    print(f"⏱️  Duration: {args.duration}s @ {args.fps} FPS")
    print(f"📐 Resolution: {args.width}x{args.height}")
    print("="*70)

    # Initialize the SimulationApp with the correct settings
    print("\n🚀 Initializing Isaac Sim (headless mode)...")
    simulation_app = SimulationApp({
        "headless": True,
        "width": args.width,
        "height": args.height,
        "active_gpu": 0
    })
    print("✅ Isaac Sim application initialized.")

    success = False

    try:
        # Run the main asynchronous task
        success = asyncio.run(run_and_render(args, simulation_app))

        print("\n" + "="*70)

        # Final check for the output file
        if success and args.output_path.exists() and args.output_path.stat().st_size > 0:
            file_size = args.output_path.stat().st_size / (1024 * 1024)
            print("🎉 EXECUTION COMPLETE - SUCCESS!")
            print("="*70)
            print(f"✅ Video file created: {args.output_path}")
            print(f"   File size: {file_size:.2f} MB")
        else:
            print("⚠️  EXECUTION COMPLETE - WITH WARNINGS")
            print("="*70)
            if not args.output_path.exists():
                print(f"❌ Video file was NOT created at: {args.output_path}")
                print("\n💡 Possible reasons:")
                print("   - Movie capture extension not available in Isaac Sim")
                print("   - Isaac Sim version incompatibility")
                print("   - Insufficient permissions")
                print("\n🔧 Troubleshooting:")
                print("   1. Check Isaac Sim logs for errors")
                print("   2. Verify movie capture extension is installed")
                print("   3. Try running with GUI mode first")
            else:
                print(f"⚠️  Video file exists but may be empty: {args.output_path}")

    except Exception as e:
        print(f"\n❌ FATAL ERROR during execution: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        print("\n🔄 Shutting down Isaac Sim...")
        simulation_app.close()
        print("✅ Shutdown complete.")

        # Exit with a success or failure code
        if success and args.output_path.exists():
            sys.exit(0)
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
