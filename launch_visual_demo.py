#!/usr/bin/env python3
"""
Visual Demo - Opens a matplotlib window showing physics simulation
"""

import matplotlib
matplotlib.use('TkAgg')  # Use Tk backend for interactive display

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import torch

print("\n" + "="*70)
print("🎬 LAUNCHING VISUAL PHYSICS DEMO 🎬")
print("="*70)
print("\nInitializing visualization...")

# Simulation parameters
dt = 0.01
num_steps = 200
mass = 1.0
radius = 0.1
gravity = -9.81
damping = 0.5

# Initial conditions
position = torch.tensor([0.0, 0.0, 2.0], dtype=torch.float32)
velocity = torch.tensor([0.0, 0.0, 0.0], dtype=torch.float32)
acceleration = torch.tensor([0.0, 0.0, gravity], dtype=torch.float32)

# Storage
positions = []
times = []

# Run simulation
print("Running physics simulation...")
for step in range(num_steps):
    velocity = velocity + acceleration * dt
    position = position + velocity * dt

    # Ground collision
    if position[2] < radius:
        position[2] = radius
        velocity[2] = -velocity[2] * damping

    positions.append(position.clone().numpy())
    times.append(step * dt)

positions = np.array(positions)
times = np.array(times)

print("Creating visualization window...")
print("✓ A window should open showing the bouncing ball animation!")
print("✓ Close the window to exit\n")

# Create figure
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
fig.suptitle('🚀 Autonomous Simulation Platform - Physics Demo 🚀', fontsize=16, fontweight='bold')

# Setup plot 1: Ball trajectory
ax1.set_xlim(-0.5, 2.5)
ax1.set_ylim(0, 2.5)
ax1.set_xlabel('Time (s)', fontsize=12)
ax1.set_ylabel('Height (m)', fontsize=12)
ax1.set_title('Bouncing Ball - Height vs Time', fontsize=14)
ax1.grid(True, alpha=0.3)
ax1.axhline(y=0, color='brown', linewidth=3, label='Ground')

line, = ax1.plot([], [], 'b-', linewidth=2, label='Ball trajectory')
point, = ax1.plot([], [], 'ro', markersize=15, label='Current position')
ax1.legend(loc='upper right')

# Setup plot 2: Side view animation
ax2.set_xlim(-0.5, 0.5)
ax2.set_ylim(0, 2.5)
ax2.set_xlabel('X Position', fontsize=12)
ax2.set_ylabel('Height (m)', fontsize=12)
ax2.set_title('Side View - Real-time Animation', fontsize=14)
ax2.grid(True, alpha=0.3)
ax2.axhline(y=0, color='brown', linewidth=3)

ball, = ax2.plot([], [], 'o', markersize=40, color='red', markeredgecolor='darkred', markeredgewidth=2)
trail, = ax2.plot([], [], 'r-', alpha=0.3, linewidth=1)

# Text annotations
info_text = ax2.text(0.02, 0.98, '', transform=ax2.transAxes,
                     verticalalignment='top', fontsize=10,
                     bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

trail_x = []
trail_y = []

def init():
    line.set_data([], [])
    point.set_data([], [])
    ball.set_data([], [])
    trail.set_data([], [])
    info_text.set_text('')
    return line, point, ball, trail, info_text

def animate(frame):
    # Update trajectory plot
    line.set_data(times[:frame+1], positions[:frame+1, 2])
    point.set_data([times[frame]], [positions[frame, 2]])

    # Update ball position
    ball.set_data([0], [positions[frame, 2]])

    # Update trail
    trail_x.append(0)
    trail_y.append(positions[frame, 2])
    if len(trail_x) > 20:
        trail_x.pop(0)
        trail_y.pop(0)
    trail.set_data(trail_x, trail_y)

    # Update info text
    height = positions[frame, 2]
    time = times[frame]
    vel = np.linalg.norm(velocity.numpy()) if frame < len(positions)-1 else 0

    info_text.set_text(
        f'Time: {time:.2f} s\n'
        f'Height: {height:.2f} m\n'
        f'Frame: {frame}/{num_steps-1}'
    )

    return line, point, ball, trail, info_text

# Create animation
anim = FuncAnimation(fig, animate, init_func=init, frames=num_steps,
                    interval=20, blit=True, repeat=True)

plt.tight_layout()
print("🎬 WINDOW OPENED! Watch the bouncing ball animation!")
print("   The ball falls from 2m height and bounces with damping")
print("   Top plot: Height vs Time")
print("   Bottom plot: Real-time side view with trail")
print("\n   Close the window when done.\n")

plt.show()

print("\n" + "="*70)
print("✅ Demo Complete!")
print("="*70)
