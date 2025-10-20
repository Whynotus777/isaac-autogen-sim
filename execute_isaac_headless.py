#!/usr/bin/env python3
"""
Isaac Sim Headless Execution Script
Loads a USD file, runs physics simulation, and renders to MP4 video
"""

import argparse
import sys
import subprocess
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

    # Temporary directory for frames
    frames_dir = output_dir / "frames_temp"
    frames_dir.mkdir(exist_ok=True)

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

    try:
        import omni.replicator.core as rep
        use_replicator = True
    except ImportError:
        print("⚠️  Warning: Replicator not available, using fallback frame capture")
        use_replicator = False

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
        world = World(physics_dt=1.0 / args.fps)
        world.reset()

        print("✅ Physics simulation initialized")

        # Setup video capture
        print(f"\n🎥 Setting up video capture...")

        if use_replicator:
            # Try to find a camera in the scene
            camera_path = None
            for prim in stage.Traverse():
                if prim.GetTypeName() == "Camera":
                    camera_path = str(prim.GetPath())
                    break

            if not camera_path:
                # Create a default camera if none exists
                print("   Creating default camera...")
                camera_path = "/World/Camera"
                from pxr import UsdGeom, Gf
                camera = UsdGeom.Camera.Define(stage, camera_path)
                camera.CreateFocalLengthAttr(35)
                xformable = UsdGeom.Xformable(camera)
                xform_op = xformable.AddTranslateOp()
                xform_op.Set(Gf.Vec3d(0, -5, 2))

            print(f"   Using camera: {camera_path}")

            # Create render product
            render_product = rep.create.render_product(camera_path, (args.width, args.height))

            # Create writer for frames
            writer = rep.WriterRegistry.get("BasicWriter")
            writer.initialize(
                output_dir=str(frames_dir),
                rgb=True,
            )
            writer.attach([render_product])

            print("✅ Replicator video writer attached")

        # Get timeline
        timeline = omni.timeline.get_timeline_interface()

        # Calculate total frames
        total_frames = int(args.duration * args.fps)
        dt = 1.0 / args.fps

        print(f"\n   Total frames: {total_frames}")
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

            if use_replicator:
                # Trigger Replicator to save frame
                rep.orchestrator.step()

            # Progress indicator
            if frame % args.fps == 0:
                progress = (frame / total_frames) * 100
                print(f"   Progress: {progress:.1f}% ({frame}/{total_frames} frames)")

            frames_rendered += 1

        # Stop timeline
        timeline.stop()

        print(f"\n✅ Simulation complete! Rendered {frames_rendered} frames")

        # Encode frames to video using ffmpeg
        if use_replicator and frames_dir.exists():
            print("\n📹 Encoding frames to video...")

            # Find the frame files
            frame_files = sorted(frames_dir.glob("rgb_*.png"))

            if frame_files:
                print(f"   Found {len(frame_files)} frame files")

                # Check if ffmpeg is available
                try:
                    ffmpeg_check = subprocess.run(
                        ["ffmpeg", "-version"],
                        capture_output=True,
                        timeout=5
                    )

                    if ffmpeg_check.returncode == 0:
                        # Create video with ffmpeg
                        ffmpeg_cmd = [
                            "ffmpeg",
                            "-y",  # Overwrite output
                            "-framerate", str(args.fps),
                            "-pattern_type", "glob",
                            "-i", str(frames_dir / "rgb_*.png"),
                            "-c:v", "libx264",
                            "-pix_fmt", "yuv420p",
                            "-preset", "fast",
                            str(output_path)
                        ]

                        result = subprocess.run(
                            ffmpeg_cmd,
                            capture_output=True,
                            text=True,
                            timeout=120
                        )

                        if result.returncode == 0 and output_path.exists():
                            print(f"✅ Video encoded successfully: {output_path}")

                            # Clean up frame files
                            print("   Cleaning up temporary frames...")
                            for frame_file in frame_files:
                                frame_file.unlink()
                            frames_dir.rmdir()
                        else:
                            print(f"⚠️  ffmpeg encoding failed:")
                            print(result.stderr)
                    else:
                        print("⚠️  ffmpeg not working properly")

                except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                    print(f"⚠️  ffmpeg not available: {e}")
                    print(f"   Frame files saved to: {frames_dir}")
            else:
                print("⚠️  No frame files found")

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
