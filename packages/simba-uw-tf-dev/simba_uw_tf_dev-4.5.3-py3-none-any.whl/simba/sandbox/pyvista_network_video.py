"""
PyVista Network Visualization Video Example

Creates a 3D network visualization with 43 nodes, mostly connected, 
and a spinning camera for 10 seconds duration.
"""

import pyvista as pv
import numpy as np
import random
from pathlib import Path

def create_network_graph(n_nodes=43, connection_probability=0.7):
    """
    Create a network graph with specified number of nodes and connection probability.
    
    :param int n_nodes: Number of nodes in the network
    :param float connection_probability: Probability of connection between any two nodes
    :return: PyVista PolyData object representing the network
    """
    print(f"Creating network with {n_nodes} nodes...")
    
    # Generate random node positions in 3D space
    np.random.seed(42)  # For reproducible results
    node_positions = np.random.uniform(-5, 5, (n_nodes, 3))
    print(f"Generated {len(node_positions)} node positions")
    
    # Create edges based on connection probability
    edges = []
    for i in range(n_nodes):
        for j in range(i + 1, n_nodes):
            if random.random() < connection_probability:
                edges.extend([i, j])
    
    print(f"Created {len(edges)//2} edges")
    
    # Create PyVista PolyData for the network
    points = pv.PolyData(node_positions)
    print(f"Created PolyData with {len(points.points)} points")
    
    # Add edges as lines
    if edges:
        lines = np.array(edges).reshape(-1, 2)
        print(f"Reshaped edges to {lines.shape}")
        points.lines = lines
        print(f"Added {len(lines)} lines to PolyData")
    else:
        print("No edges to add")
    
    print(f"Final PolyData: {len(points.points)} points, {len(points.lines)} lines")
    return points

def create_frame_images(plotter, output_path, total_frames, fps):
    """
    Create individual frame images as fallback when video creation fails.
    """
    print("Creating individual frame images...")
    
    # Create frames directory
    frames_dir = Path(output_path).parent / "frames"
    frames_dir.mkdir(exist_ok=True)
    
    try:
        for frame in range(total_frames):
            # Calculate rotation angle (full 360 degrees over duration)
            angle = 2 * np.pi * frame / total_frames
            
            # Update camera position for spinning motion
            radius = 15
            x = radius * np.cos(angle)
            y = radius * np.sin(angle)
            z = 5 + 3 * np.sin(angle * 2)  # Add some vertical movement
            
            plotter.camera.position = (x, y, z)
            plotter.camera.focal_point = (0, 0, 0)
            
            # Save frame as image
            frame_path = frames_dir / f"frame_{frame:04d}.png"
            plotter.screenshot(str(frame_path))
            
            if frame % 30 == 0:  # Print progress every second
                progress = (frame + 1) / total_frames * 100
                print(f"Frame {frame + 1:4d}/{total_frames} | Progress: {progress:5.1f}%")
        
        print(f"Frames saved to: {frames_dir}")
        print("You can create a video from these frames using ffmpeg:")
        print(f"ffmpeg -framerate {fps} -i {frames_dir}/frame_%04d.png -c:v libx264 -pix_fmt yuv420p {output_path}")
        
    except Exception as e:
        print(f"Error creating frame images: {e}")

def create_network_video(output_path="network_video.mp4", duration=10, fps=30):
    """
    Create a network visualization video with spinning camera.
    
    :param str output_path: Path to save the output video
    :param int duration: Video duration in seconds
    :param int fps: Frames per second
    """
    print("Starting network video creation...")
    
    # Create the network
    print("Creating network graph...")
    network = create_network_graph(n_nodes=43, connection_probability=0.7)
    print(f"Network created with {len(network.points)} nodes and {len(network.lines)} edges")
    
    # Create plotter
    print("Initializing PyVista plotter...")
    plotter = pv.Plotter(off_screen=True)
    
    # Add the network to the plotter
    print("Adding network to plotter...")
    print(f"Network type: {type(network)}")
    print(f"Network points shape: {network.points.shape if hasattr(network, 'points') else 'No points'}")
    print(f"Network lines shape: {network.lines.shape if hasattr(network, 'lines') else 'No lines'}")
    
    try:
        # Try adding just points first
        print("Adding points to plotter...")
        plotter.add_mesh(network, 
                         color='lightblue', 
                         point_size=8,
                         render_points_as_spheres=True)
        print("Points added successfully!")
        
        # Then try adding lines separately if they exist
        if hasattr(network, 'lines') and len(network.lines) > 0:
            print("Adding lines to plotter...")
            # Create a separate mesh for lines
            line_mesh = pv.PolyData()
            line_mesh.points = network.points
            line_mesh.lines = network.lines
            plotter.add_mesh(line_mesh, 
                             color='white', 
                             line_width=2,
                             style='wireframe')
            print("Lines added successfully!")
        else:
            print("No lines to add")
            
    except Exception as e:
        print(f"Error adding network to plotter: {e}")
        print("Trying simplified approach...")
        # Fallback: just add points
        plotter.add_mesh(network, color='lightblue', point_size=8)
    
    # Set up the scene
    print("Setting up scene...")
    plotter.set_background('black')
    plotter.add_axes()
    plotter.add_floor(color='gray', opacity=0.1)
    
    # Add lighting
    print("Adding lighting...")
    plotter.add_light(pv.Light(position=(5, 5, 5), focal_point=(0, 0, 0)))
    plotter.add_light(pv.Light(position=(-5, -5, 5), focal_point=(0, 0, 0)))
    
    # Calculate total frames
    total_frames = duration * fps
    print(f"Total frames to render: {total_frames}")
    
    # Set up camera for spinning motion
    print("Setting up camera...")
    plotter.camera.position = (10, 10, 10)
    plotter.camera.focal_point = (0, 0, 0)
    plotter.camera.up = (0, 0, 1)
    
    # Create video writer
    print(f"Opening movie writer for: {output_path}")
    try:
        plotter.open_movie(output_path, framerate=fps)
        print("Movie writer opened successfully!")
    except Exception as e:
        print(f"Error opening movie writer: {e}")
        print("This is likely because imageio-ffmpeg is not installed.")
        print("To fix this, run: pip install imageio-ffmpeg")
        print("For now, creating individual frame images instead...")
        create_frame_images(plotter, output_path, total_frames, fps)
        return
    
    print(f"Creating network video with {total_frames} frames...")
    print(f"Duration: {duration}s, FPS: {fps}")
    print("=" * 50)
    
    # Generate frames with spinning camera
    print("Starting frame rendering...")
    try:
        for frame in range(total_frames):
            if frame == 0:
                print("Rendering first frame...")
            
            # Calculate rotation angle (full 360 degrees over duration)
            angle = 2 * np.pi * frame / total_frames
            
            # Update camera position for spinning motion
            radius = 15
            x = radius * np.cos(angle)
            y = radius * np.sin(angle)
            z = 5 + 3 * np.sin(angle * 2)  # Add some vertical movement
            
            plotter.camera.position = (x, y, z)
            plotter.camera.focal_point = (0, 0, 0)
            
            # Render frame
            try:
                plotter.write_frame()
                if frame == 0:
                    print("First frame rendered successfully!")
            except Exception as e:
                print(f"Error rendering frame {frame}: {e}")
                break
            
            # Print progress with percentage and time remaining
            progress = (frame + 1) / total_frames * 100
            elapsed_time = (frame + 1) / fps
            remaining_time = (total_frames - frame - 1) / fps
            
            if frame % 10 == 0 or frame == total_frames - 1:  # Print every 10 frames or last frame
                print(f"Frame {frame + 1:4d}/{total_frames} | "
                      f"Progress: {progress:5.1f}% | "
                      f"Elapsed: {elapsed_time:5.1f}s | "
                      f"Remaining: {remaining_time:5.1f}s")
        
        print("All frames rendered successfully!")
        
    except Exception as e:
        print(f"Error during frame rendering: {e}")
    
    # Close the movie
    print("Closing movie writer...")
    try:
        plotter.close()
        print(f"Video saved to: {output_path}")
    except Exception as e:
        print(f"Error closing movie writer: {e}")

def create_interactive_network():
    """
    Create an interactive network visualization for exploration.
    """
    # Create the network
    network = create_network_graph(n_nodes=43, connection_probability=0.7)
    
    # Create interactive plotter
    plotter = pv.Plotter()
    
    # Add the network
    plotter.add_mesh(network, 
                     color='lightblue', 
                     line_width=2,
                     point_size=8,
                     render_points_as_spheres=True)
    
    # Set up the scene
    plotter.set_background('black')
    plotter.add_axes()
    plotter.add_floor(color='gray', opacity=0.1)
    
    # Add title
    plotter.add_text("Interactive Network Visualization (43 nodes)", 
                     position='upper_left', 
                     font_size=12)
    
    print("Interactive network visualization opened.")
    print("Controls:")
    print("- Left mouse: Rotate")
    print("- Right mouse: Pan")
    print("- Mouse wheel: Zoom")
    print("- Close window to exit")
    
    # Show the interactive plot
    plotter.show()


def test_pyvista():
    """Test if PyVista is working properly."""
    print("Testing PyVista installation...")
    try:
        import pyvista as pv
        print(f"PyVista version: {pv.__version__}")
        
        # Test basic functionality
        sphere = pv.Sphere()
        print(f"Created sphere with {len(sphere.points)} points")
        
        # Test plotter creation
        plotter = pv.Plotter(off_screen=True)
        plotter.add_mesh(sphere)
        print("Off-screen plotter created successfully")
        plotter.close()
        
        # Test simple network creation
        print("Testing simple network creation...")
        points = np.random.uniform(-5, 5, (10, 3))
        simple_network = pv.PolyData(points)
        print(f"Created simple network with {len(simple_network.points)} points")
        
        plotter2 = pv.Plotter(off_screen=True)
        plotter2.add_mesh(simple_network, point_size=8)
        print("Simple network added to plotter successfully")
        plotter2.close()
        
        print("PyVista test passed!")
        return True
    except Exception as e:
        print(f"PyVista test failed: {e}")
        return False

# Test PyVista first
if test_pyvista():
    output_dir = Path("C:\projects\simba\simba\output")
    output_dir.mkdir(exist_ok=True)
    print(output_dir)
    # Create the network video
    video_path = output_dir / "network_video.mp4"
    print(f"\nCreating video at: {video_path}")
    create_network_video(str(video_path), duration=10, fps=30)
    
    # Optionally create interactive version
    print("\nCreating interactive network visualization...")
    create_interactive_network()
else:
    print("PyVista test failed. Please check your installation.")
