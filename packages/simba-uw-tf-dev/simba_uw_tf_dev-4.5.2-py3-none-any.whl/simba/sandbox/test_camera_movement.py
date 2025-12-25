"""
Test Camera Movement - Simple test to verify camera changes work
"""

import pyvista as pv
import numpy as np
from pathlib import Path

def test_camera_movement():
    """Test if camera movement works in off-screen mode."""
    print("Testing camera movement...")
    
    # Create a simple scene
    sphere = pv.Sphere(radius=1, center=(0, 0, 0))
    
    # Create plotter
    plotter = pv.Plotter(off_screen=True, window_size=[400, 300])
    plotter.add_mesh(sphere, color='red')
    plotter.set_background('white')
    
    # Test different camera positions
    positions = [
        (5, 0, 0),    # Right side
        (0, 5, 0),    # Front
        (-5, 0, 0),   # Left side
        (0, -5, 0),   # Back
        (0, 0, 5),    # Top
    ]
    
    for i, pos in enumerate(positions):
        print(f"Setting camera to position {pos}")
        plotter.camera.position = pos
        plotter.camera.focal_point = (0, 0, 0)
        plotter.camera.up = (0, 0, 1)
        
        # Force render update
        plotter.render()
        
        # Take screenshot
        filename = f"test_camera_{i}.png"
        plotter.screenshot(filename)
        print(f"Saved: {filename}")
    
    plotter.close()
    print("Camera movement test complete!")

def test_network_camera():
    """Test camera movement with network."""
    print("Testing network camera movement...")
    
    # Create simple network
    points = np.random.uniform(-2, 2, (10, 3))
    network = pv.PolyData(points)
    
    plotter = pv.Plotter(off_screen=True, window_size=[400, 300])
    plotter.add_mesh(network, color='blue', point_size=8, render_points_as_spheres=True)
    plotter.set_background('black')
    
    # Test 5 different camera positions
    for frame in range(5):
        angle = 2 * np.pi * frame / 5
        radius = 10
        x = radius * np.cos(angle)
        y = radius * np.sin(angle)
        z = 5
        
        print(f"Frame {frame}: pos=({x:.1f}, {y:.1f}, {z:.1f})")
        
        plotter.camera.position = (x, y, z)
        plotter.camera.focal_point = (0, 0, 0)
        plotter.camera.up = (0, 0, 1)
        plotter.render()
        
        filename = f"test_network_{frame}.png"
        plotter.screenshot(filename)
        print(f"Saved: {filename}")
    
    plotter.close()
    print("Network camera test complete!")

if __name__ == "__main__":
    print("Camera Movement Tests")
    print("=" * 30)
    
    test_camera_movement()
    print()
    test_network_camera()
    
    print("\nCheck the generated PNG files to see if camera movement is working!")
