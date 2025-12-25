"""
Points-Only Network Visualization

This version avoids lines entirely and just uses colorful points to represent the network.
"""

import pyvista as pv
import numpy as np
import random
from pathlib import Path

def create_points_network(n_nodes=43):
    """Create a network with just colorful points (no lines)."""
    print(f"Creating points network with {n_nodes} nodes...")
    
    # Generate random node positions
    np.random.seed(42)
    node_positions = np.random.uniform(-5, 5, (n_nodes, 3))
    
    # Create PolyData
    points = pv.PolyData(node_positions)
    
    # Create different colors for each node using simple color names
    color_names = ['red', 'blue', 'green', 'yellow', 'orange', 'purple', 'cyan', 'magenta', 
                   'lime', 'pink', 'brown', 'gray', 'olive', 'navy', 'teal', 'maroon',
                   'gold', 'silver', 'coral', 'salmon', 'turquoise', 'violet', 'indigo',
                   'crimson', 'darkgreen', 'darkblue', 'darkred', 'darkorange', 'darkviolet',
                   'lightblue', 'lightgreen', 'lightcoral', 'lightpink', 'lightgray',
                   'mediumblue', 'mediumgreen', 'mediumpurple', 'mediumseagreen', 'mediumvioletred',
                   'orangered', 'royalblue', 'seagreen']
    
    # Assign colors to points
    point_colors = []
    for i in range(n_nodes):
        color_name = color_names[i % len(color_names)]
        point_colors.append(color_name)
    
    points['colors'] = point_colors
    
    print(f"Created network with {len(points.points)} colorful points")
    return points

def create_points_video(output_path="points_network_video.mp4", duration=10, fps=30):
    """Create a video with just colorful points."""
    print("Starting points network video creation...")
    
    # Create the network
    network = create_points_network(n_nodes=43)
    
    # Create plotter
    print("Creating plotter...")
    plotter = pv.Plotter(off_screen=True, window_size=[800, 600])
    
    # Add network with different colors for each point
    print("Adding colorful points to plotter...")
    
    # Method: Add each point individually with its own color
    try:
        for i in range(len(network.points)):
            # Create a single point
            single_point = pv.PolyData([network.points[i]])
            color = network['colors'][i]
            
            plotter.add_mesh(single_point, 
                           color=color, 
                           point_size=15,
                           render_points_as_spheres=True)
        
        print("✓ Added all colorful points successfully")
    except Exception as e:
        print(f"✗ Error adding points: {e}")
        return
    
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
        test_path = Path(output_path).parent / "test_points_frame.png"
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
    """Create an interactive view with colorful points."""
    print("Creating interactive points view...")
    
    network = create_points_network(n_nodes=43)
    
    plotter = pv.Plotter()
    
    # Add each point with its own color
    for i in range(len(network.points)):
        single_point = pv.PolyData([network.points[i]])
        color = network['colors'][i]
        
        plotter.add_mesh(single_point, 
                       color=color, 
                       point_size=15,
                       render_points_as_spheres=True)
    
    plotter.set_background('black')
    plotter.add_text("Colorful Points Network (43 nodes)", position='upper_left')
    
    print("Interactive window opened. Close to continue.")
    plotter.show()

if __name__ == "__main__":
    # Create output directory
    script_dir = Path(__file__).parent
    output_dir = script_dir / "output"
    output_dir.mkdir(exist_ok=True)
    
    print(f"Output directory: {output_dir}")
    
    # Create points video
    video_path = output_dir / "points_network_video.mp4"
    create_points_video(str(video_path), duration=10, fps=30)
    
    # Create interactive view
    print("\nCreating interactive view...")
    create_interactive_view()



















