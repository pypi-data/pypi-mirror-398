"""
Simple PyVista Network Visualization Video Example

A simplified version that creates a 3D network visualization with 43 nodes
and a spinning camera for 10 seconds duration.
"""

import pyvista as pv
import numpy as np
import random
from pathlib import Path

def create_simple_network(n_nodes=43):
    """Create a network with points and lines, plus different colors."""
    print(f"Creating network with {n_nodes} nodes...")
    
    # Generate random node positions in 3D space
    np.random.seed(42)
    node_positions = np.random.uniform(-5, 5, (n_nodes, 3))
    
    # Create edges based on connection probability
    edges = []
    for i in range(n_nodes):
        for j in range(i + 1, n_nodes):
            if random.random() < 0.6:  # 60% connection probability
                edges.extend([i, j])
    
    # Create PolyData with points
    points = pv.PolyData(node_positions)
    
    # Add edges as lines
    if edges:
        lines = np.array(edges).reshape(-1, 2)
        points.lines = lines
        print(f"Created {len(lines)} connections")
    
    # Create different colors for each node
    colors = []
    for i in range(n_nodes):
        # Create a color based on node index
        hue = i / n_nodes
        r = int(255 * (0.5 + 0.5 * np.sin(hue * 2 * np.pi)))
        g = int(255 * (0.5 + 0.5 * np.sin(hue * 2 * np.pi + 2 * np.pi / 3)))
        b = int(255 * (0.5 + 0.5 * np.sin(hue * 2 * np.pi + 4 * np.pi / 3)))
        colors.append([r, g, b])
    
    points['colors'] = colors
    
    print(f"Created network with {len(points.points)} points and {len(points.lines)} lines")
    return points

def create_simple_video(output_path="simple_network_video.mp4", duration=10, fps=30):
    """Create a simple network video."""
    print("Starting simple network video creation...")
    
    # Create the network
    network = create_simple_network(n_nodes=43)
    
    # Create plotter with minimal settings
    print("Creating plotter...")
    plotter = pv.Plotter(off_screen=True, window_size=[800, 600])
    
    # Add the network with colors and lines
    print("Adding network to plotter...")
    
    # Add points with individual colors
    plotter.add_mesh(network, 
                     scalars='colors',
                     rgb=True,
                     point_size=12,
                     render_points_as_spheres=True)
    
    # Add lines separately for better visibility
    if hasattr(network, 'lines') and len(network.lines) > 0:
        print("Adding connection lines...")
        # Create a separate mesh for lines
        line_mesh = pv.PolyData()
        line_mesh.points = network.points
        line_mesh.lines = network.lines
        
        plotter.add_mesh(line_mesh, 
                         color='white', 
                         line_width=3,
                         style='wireframe',
                         opacity=0.8)
    
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
    
    # Try to create video
    print(f"Attempting to create video: {output_path}")
    try:
        plotter.open_movie(output_path, framerate=fps)
        print("Movie writer opened successfully!")
        
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
        print(f"Video created successfully: {output_path}")
        
    except Exception as e:
        print(f"Video creation failed: {e}")
        print("Creating individual frames instead...")
        create_frames_fallback(plotter, output_path, total_frames)

def create_frames_fallback(plotter, output_path, total_frames):
    """Create individual frame images as fallback."""
    frames_dir = Path(output_path).parent / "frames"
    frames_dir.mkdir(exist_ok=True)
    
    print(f"Creating frames in: {frames_dir}")
    print(f"Frames directory exists: {frames_dir.exists()}")
    print(f"Frames directory path: {frames_dir.absolute()}")
    
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
            try:
                plotter.screenshot(str(frame_path))
                if frame < 5:  # Print first few frames for debugging
                    print(f"Saved frame {frame}: {frame_path}")
            except Exception as e:
                print(f"Error saving frame {frame}: {e}")
                break
            
            if frame % 30 == 0:
                progress = (frame + 1) / total_frames * 100
                print(f"Frame {frame + 1:4d}/{total_frames} | Progress: {progress:5.1f}%")
        
        # Check if frames were actually created
        frame_files = list(frames_dir.glob("frame_*.png"))
        print(f"Total frames created: {len(frame_files)}")
        if frame_files:
            print(f"First frame: {frame_files[0]}")
            print(f"Last frame: {frame_files[-1]}")
        
        print(f"Frames saved to: {frames_dir}")
        print("To create video from frames, run:")
        print(f"ffmpeg -framerate 30 -i {frames_dir}/frame_%04d.png -c:v libx264 -pix_fmt yuv420p {output_path}")
        
    except Exception as e:
        print(f"Error in frame creation: {e}")
        import traceback
        traceback.print_exc()

def create_interactive_view():
    """Create an interactive view of the network."""
    print("Creating interactive network view...")
    
    network = create_simple_network(n_nodes=43)
    
    plotter = pv.Plotter()
    
    # Add points with individual colors
    plotter.add_mesh(network, 
                     scalars='colors',
                     rgb=True,
                     point_size=12,
                     render_points_as_spheres=True)
    
    # Add lines for connections
    if hasattr(network, 'lines') and len(network.lines) > 0:
        line_mesh = pv.PolyData()
        line_mesh.points = network.points
        line_mesh.lines = network.lines
        
        plotter.add_mesh(line_mesh, 
                         color='white', 
                         line_width=3,
                         style='wireframe',
                         opacity=0.8)
    
    plotter.set_background('black')
    plotter.add_text("Interactive Network (43 nodes with connections)", position='upper_left')
    
    print("Interactive window opened. Close to continue.")
    plotter.show()

if __name__ == "__main__":
    # Create output directory in the same directory as the script
    script_dir = Path(__file__).parent
    output_dir = script_dir / "output"
    output_dir.mkdir(exist_ok=True)
    
    print(f"Output directory: {output_dir}")
    print(f"Output directory exists: {output_dir.exists()}")
    
    # Create simple video
    video_path = output_dir / "simple_network_video.mp4"
    create_simple_video(str(video_path), duration=10, fps=30)
    
    # Create interactive view
    print("\nCreating interactive view...")
    create_interactive_view()
