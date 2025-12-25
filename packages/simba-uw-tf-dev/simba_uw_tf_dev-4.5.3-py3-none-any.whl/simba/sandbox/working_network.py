"""
Working Network Visualization - Simple and Reliable

This version uses simple colors and basic rendering to avoid hanging issues.
"""

import pyvista as pv
import numpy as np
import random
from pathlib import Path

def create_working_network(n_nodes=43):
    """Create a simple, working network."""
    print(f"Creating working network with {n_nodes} nodes...")
    
    # Generate random node positions
    np.random.seed(42)
    node_positions = np.random.uniform(-5, 5, (n_nodes, 3))
    
    # Create basic PolyData
    points = pv.PolyData(node_positions)
    
    # Add some simple connections (every other node)
    edges = []
    for i in range(0, n_nodes, 2):
        if i + 1 < n_nodes:
            edges.extend([i, i + 1])
    
    if edges:
        lines = np.array(edges).reshape(-1, 2)
        points.lines = lines
        print(f"Created {len(lines)} simple connections")
    
    print(f"Created network with {len(points.points)} points")
    return points

def create_working_video(output_path="working_network_video.mp4", duration=10, fps=30):
    """Create a working network video."""
    print("Starting working network video creation...")
    
    # Create the network
    network = create_working_network(n_nodes=43)
    
    # Create plotter
    print("Creating plotter...")
    plotter = pv.Plotter(off_screen=True, window_size=[800, 600])
    
    # Add network with simple approach
    print("Adding network to plotter...")
    
    # Method 1: Just add points with a single color
    try:
        plotter.add_mesh(network, 
                         color='lightblue', 
                         point_size=10,
                         render_points_as_spheres=True)
        print("✓ Added points successfully")
    except Exception as e:
        print(f"✗ Error adding points: {e}")
        return
    
    # Method 2: Add lines separately if they exist
    if hasattr(network, 'lines') and len(network.lines) > 0:
        print("Adding connection lines...")
        try:
            # Create line mesh
            line_mesh = pv.PolyData()
            line_mesh.points = network.points
            line_mesh.lines = network.lines
            
            plotter.add_mesh(line_mesh, 
                             color='white', 
                             line_width=2,
                             style='wireframe')
            print("✓ Added lines successfully")
        except Exception as e:
            print(f"✗ Error adding lines: {e}")
    
    # Simple scene setup
    print("Setting up scene...")
    plotter.set_background('black')
    
    # Calculate total frames
    total_frames = duration * fps
    print(f"Total frames: {total_frames}")
    
    # Set up camera
    print("Setting up camera...")
    plotter.camera.position = (15, 15, 15)
    plotter.camera.focal_point = (0, 0, 0)
    
    # Test with a single frame first
    print("Testing single frame...")
    try:
        test_path = Path(output_path).parent / "test_frame.png"
        plotter.screenshot(str(test_path))
        print(f"✓ Test frame saved: {test_path}")
    except Exception as e:
        print(f"✗ Error saving test frame: {e}")
        return
    
    # Try to create video
    print(f"Attempting to create video: {output_path}")
    try:
        plotter.open_movie(output_path, framerate=fps)
        print("✓ Movie writer opened successfully!")
        
        print("Rendering frames...")
        for frame in range(total_frames):
            # Calculate rotation angle
            angle = 2 * np.pi * frame / total_frames
            
            # Update camera position
            radius = 20
            x = radius * np.cos(angle)
            y = radius * np.sin(angle)
            z = 10
            
            plotter.camera.position = (x, y, z)
            plotter.camera.focal_point = (0, 0, 0)
            
            # Render frame
            plotter.write_frame()
            
            # Print progress
            if frame % 30 == 0 or frame == total_frames - 1:
                progress = (frame + 1) / total_frames * 100
                print(f"Frame {frame + 1:4d}/{total_frames} | Progress: {progress:5.1f}%")
        
        plotter.close()
        print(f"✓ Video created successfully: {output_path}")
        
    except Exception as e:
        print(f"Video creation failed: {e}")
        print("Creating individual frames instead...")
        create_frames_fallback(plotter, output_path, total_frames)

def create_frames_fallback(plotter, output_path, total_frames):
    """Create individual frame images as fallback."""
    frames_dir = Path(output_path).parent / "frames"
    frames_dir.mkdir(exist_ok=True)
    
    print(f"Creating frames in: {frames_dir}")
    
    try:
        for frame in range(total_frames):
            # Calculate rotation angle
            angle = 2 * np.pi * frame / total_frames
            
            # Update camera position
            radius = 20
            x = radius * np.cos(angle)
            y = radius * np.sin(angle)
            z = 10
            
            plotter.camera.position = (x, y, z)
            plotter.camera.focal_point = (0, 0, 0)
            
            # Save frame
            frame_path = frames_dir / f"frame_{frame:04d}.png"
            plotter.screenshot(str(frame_path))
            
            if frame % 30 == 0:
                progress = (frame + 1) / total_frames * 100
                print(f"Frame {frame + 1:4d}/{total_frames} | Progress: {progress:5.1f}%")
        
        # Check if frames were created
        frame_files = list(frames_dir.glob("frame_*.png"))
        print(f"Total frames created: {len(frame_files)}")
        
        print(f"Frames saved to: {frames_dir}")
        print("To create video from frames, run:")
        print(f"ffmpeg -framerate 30 -i {frames_dir}/frame_%04d.png -c:v libx264 -pix_fmt yuv420p {output_path}")
        
    except Exception as e:
        print(f"Error in frame creation: {e}")

def create_interactive_view():
    """Create an interactive view."""
    print("Creating interactive network view...")
    
    network = create_working_network(n_nodes=43)
    
    plotter = pv.Plotter()
    
    # Simple approach - just points
    plotter.add_mesh(network, 
                     color='lightblue', 
                     point_size=10,
                     render_points_as_spheres=True)
    
    # Add lines if they exist
    if hasattr(network, 'lines') and len(network.lines) > 0:
        line_mesh = pv.PolyData()
        line_mesh.points = network.points
        line_mesh.lines = network.lines
        
        plotter.add_mesh(line_mesh, 
                         color='white', 
                         line_width=2,
                         style='wireframe')
    
    plotter.set_background('black')
    plotter.add_text("Working Network (43 nodes)", position='upper_left')
    
    print("Interactive window opened. Close to continue.")
    plotter.show()

if __name__ == "__main__":
    # Create output directory
    script_dir = Path(__file__).parent
    output_dir = script_dir / "output"
    output_dir.mkdir(exist_ok=True)
    
    print(f"Output directory: {output_dir}")
    
    # Create working video
    video_path = output_dir / "working_network_video.mp4"
    create_working_video(str(video_path), duration=10, fps=30)
    
    # Create interactive view
    print("\nCreating interactive view...")
    create_interactive_view()
