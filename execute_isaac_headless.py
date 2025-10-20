#!/usr/bin/env python3
"""
Isaac Sim Headless Execution Script (Robust Version)
Loads a USD, runs physics, and renders to MP4 using the native Movie Capture tool.
"""

import argparse
import sys
import asyncio
from pathlib import Path

# Initialize SimulationApp first
try:
    from omni.isaac.kit import SimulationApp
except ImportError:
    print("FATAL ERROR: Could not import Isaac Sim. Ensure this is run with Isaac Sim's python executable.", file=sys.stderr)
    sys.exit(1)


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Execute USD simulation and render to video.")
    parser.add_argument("--usd_path", type=str, required=True, help="Path to input USD file.")
    parser.add_argument("--output_path", type=str, required=True, help="Path to output MP4 video file.")
    parser.add_argument("--duration", type=float, default=10.0, help="Simulation duration in seconds.")
    parser.add_argument("--fps", type=int, default=60, help="Frames per second.")
    parser.add_argument("--width", type=int, default=1280, help="Video width.")
    parser.add_argument("--height", type=int, default=720, help="Video height.")
    return parser.parse_args()


async def run_simulation_and_render(args, simulation_app):
    """Core async task to run simulation and capture video."""

    # Late import of Isaac modules (after SimulationApp initialization)
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

    # 1. Load the stage
    print(f"\n📂 Loading USD stage: {args.usd_path}")
    try:
        open_stage(usd_path=str(args.usd_path))
        print("✅ Stage loaded successfully.")
    except Exception as e:
        print(f"FATAL ERROR: Could not open stage at {args.usd_path}: {e}", file=sys.stderr)
        return False

    # Give the app time to process the stage
    await simulation_app.update_async()

    # 2. Initialize the physics world
    print("\n⚛️  Initializing physics simulation...")
    world = World(physics_dt=1.0 / args.fps)

    try:
        await world.initialize_simulation_context_async()
    except AttributeError:
        # Fallback for different API versions
        world.initialize_simulation_context()

    await world.reset_async()
    print("✅ Physics simulation initialized.")

    # 3. Configure and start movie capture
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
                "capture_every_nth_frame": 1,
            }

            mc_interface.set_capture_settings(capture_settings)
            print(f"\n🎥 Movie capture configured:")
            print(f"   Output: {args.output_path}")
            print(f"   Duration: {args.duration}s @ {args.fps} FPS")
            print(f"   Resolution: {args.width}x{args.height}")

            print("\n🎬 Starting capture...")
            mc_interface.start_capture()

            # Ensure capture starts
            await simulation_app.update_async()
            print("✅ Capture started successfully.")

        except Exception as e:
            print(f"⚠️  WARNING: Could not start movie capture: {e}", file=sys.stderr)
            print("   Simulation will run without recording.")
            has_movie_capture = False

    # 4. Start the simulation timeline
    print("\n▶️  Starting simulation timeline...")
    timeline = omni.timeline.get_timeline_interface()
    timeline.set_time_codes_per_seconds(args.fps)
    timeline.play()

    # Ensure timeline starts
    await simulation_app.update_async()
    print("✅ Timeline started.")

    # 5. Wait for the specified duration
    print(f"\n⏳ Simulating for {args.duration} seconds...")
    print(f"   (This will take approximately {args.duration} seconds...)")

    # Sleep for the duration, updating periodically
    total_steps = int(args.duration)
    for step in range(total_steps):
        await asyncio.sleep(1.0)
        progress = ((step + 1) / total_steps) * 100
        print(f"   Progress: {progress:.1f}% ({step + 1}/{total_steps} seconds)")

    print("\n✅ Simulation time complete.")

    # 6. Stop the capture and simulation
    print("\n🛑 Stopping timeline...")
    timeline.stop()
    await simulation_app.update_async()

    if has_movie_capture:
        print("🛑 Stopping capture...")
        try:
            mc_interface.stop_capture()
            await simulation_app.update_async()
        except Exception as e:
            print(f"⚠️  Warning during capture stop: {e}", file=sys.stderr)

        # Give the encoder time to finish writing the file
        print("\n✍️  Finalizing video file...")
        print("   (Waiting up to 15 seconds for encoder to finish...)")

        for i in range(15):
            if args.output_path.exists():
                print(f"   ✅ Video file detected after {i+1} second(s)!")
                break
            await asyncio.sleep(1)
            if (i + 1) % 5 == 0:
                print(f"   Still waiting... ({i+1}/15 seconds)")

    print("\n✅ Simulation and rendering complete.")
    return True


def main():
    """Main execution function"""

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
    print("🎬 ISAAC SIM HEADLESS RENDERER (Robust Version)")
    print("="*70)
    print(f"📂 Input USD: {args.usd_path}")
    print(f"🎥 Output Video: {args.output_path}")
    print(f"⏱️  Duration: {args.duration}s @ {args.fps} FPS")
    print(f"📐 Resolution: {args.width}x{args.height}")
    print("="*70)

    # Initialize Isaac Sim
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
        # Run the main async task
        success = asyncio.run(run_simulation_and_render(args, simulation_app))

        print("\n" + "="*70)

        if success and args.output_path.exists():
            file_size = args.output_path.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            print("🎉 EXECUTION COMPLETE - SUCCESS!")
            print("="*70)
            print(f"✅ Video file created: {args.output_path}")
            print(f"   File size: {file_size_mb:.2f} MB")
        else:
            print("⚠️  EXECUTION COMPLETE - WITH WARNINGS")
            print("="*70)
            if not args.output_path.exists():
                print(f"❌ Video file was NOT created at: {args.output_path}")
                print("   This may be due to:")
                print("   - Movie capture extension not available in your Isaac Sim build")
                print("   - Insufficient permissions to write to output directory")
                print("   - Isaac Sim version incompatibility")
                print("\n💡 Troubleshooting:")
                print("   1. Check Isaac Sim logs for errors")
                print("   2. Verify movie capture extension is installed")
                print("   3. Try running with GUI mode first to test")

    except Exception as e:
        print(f"\n❌ FATAL ERROR during execution: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        print("\n🔄 Shutting down Isaac Sim...")
        simulation_app.close()
        print("✅ Shutdown complete.")

    # Exit with appropriate code
    if success and args.output_path.exists():
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
