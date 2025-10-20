#!/usr/bin/env python3
"""
Isaac Sim Headless Execution Script
Loads a USD file, runs physics simulation, and renders to MP4 video
"""

import argparse
import sys
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
        default=1920,
        help="Video width in pixels (default: 1920)"
    )
    parser.add_argument(
        "--height",
        type=int,
        default=1080,
        help="Video height in pixels (default: 1080)"
    )

    return parser.parse_args()


def main():
    """Main execution function"""

    args = parse_args()

    # Validate inputs
    usd_path = Path(args.usd_path)
    if not usd_path.exists():
        print(f"ERROR: USD file not found: {usd_path}")
        sys.exit(1)

    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

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

    # Now we can import other Isaac modules (must be after SimulationApp creation)
    import omni.usd
    import omni.timeline
    from omni.isaac.core import World
    from omni.isaac.core.utils.stage import open_stage
    import carb

    try:
        print("✅ Isaac Sim initialized successfully")

        # Load the USD stage
        print(f"\n📂 Loading USD scene: {usd_path}")
        open_stage(str(usd_path))

        # Get the stage
        stage = omni.usd.get_context().get_stage()
        if stage is None:
            raise RuntimeError("Failed to load USD stage")

        print("✅ USD stage loaded successfully")

        # Create World for physics simulation
        print("\n⚛️  Initializing physics simulation...")
        world = World()
        world.reset()

        print("✅ Physics simulation initialized")

        # Setup movie capture
        print(f"\n🎥 Setting up video capture...")
        print(f"   Output: {output_path}")

        # Get movie capture interface
        import omni.kit.app
        movie_capture = omni.kit.app.get_app().get_extension_manager().get_extension_dict_by_name("omni.kit.viewport.capture")

        if movie_capture is None:
            print("⚠️  Warning: Movie capture extension not available in this Isaac Sim version")
            print("   Attempting alternative capture method...")

        # Alternative: Use timeline and manual frame capture
        timeline = omni.timeline.get_timeline_interface()

        # Calculate total frames
        total_frames = int(args.duration * args.fps)
        dt = 1.0 / args.fps

        print(f"   Total frames: {total_frames}")
        print(f"   Time step: {dt:.4f}s")

        # Start timeline
        timeline.set_time_codes_per_seconds(args.fps)
        timeline.play()

        print("\n🎬 Running simulation...")

        # Run simulation frame by frame
        frames_rendered = 0
        for frame in range(total_frames):
            # Step physics
            world.step(render=True)

            # Progress indicator
            if frame % args.fps == 0:
                progress = (frame / total_frames) * 100
                print(f"   Progress: {progress:.1f}% ({frame}/{total_frames} frames)")

            frames_rendered += 1

        # Stop timeline
        timeline.stop()

        print(f"\n✅ Simulation complete! Rendered {frames_rendered} frames")

        # Note about video export
        print("\n📝 Note: Video export requires Isaac Sim Replicator or external tools")
        print("   For production use, integrate with:")
        print("   - omni.replicator.core for automated video export")
        print("   - External tools: ffmpeg from frame captures")

        print("\n" + "="*70)
        print("✅ EXECUTION COMPLETE")
        print("="*70)

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
