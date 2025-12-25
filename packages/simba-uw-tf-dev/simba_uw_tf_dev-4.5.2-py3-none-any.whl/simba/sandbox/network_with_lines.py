"""
Network with Lines - Alternative Approach

This version creates network lines using cylinders between points instead of PyVista's line rendering.
"""

import pyvista as pv
import numpy as np
import random
from pathlib import Path

def create_network_with_cylinders(n_nodes=43):
    """Create a more organic network with nodes and smooth connections."""
    print(f"Creating organic network with {n_nodes} nodes and smooth connections...")
    
    # Generate more structured node positions (clustered around center with some outliers)
    np.random.seed(42)
    
    # Create a core cluster
    core_nodes = int(n_nodes * 0.7)  # 70% of nodes in core
    core_positions = np.random.normal(0, 2, (core_nodes, 3))
    
    # Create some peripheral nodes
    peripheral_nodes = n_nodes - core_nodes
    peripheral_positions = np.random.uniform(-8, 8, (peripheral_nodes, 3))
    
    # Combine positions
    node_positions = np.vstack([core_positions, peripheral_positions])
    
    # Create more intelligent connections based on distance and clustering
    connections = []
    connection_probability = 0.12  # Higher probability for more connections
    
    for i in range(n_nodes):
        for j in range(i + 1, n_nodes):
            # Calculate distance between nodes
            distance = np.linalg.norm(node_positions[i] - node_positions[j])
            
            # Higher probability for closer nodes, but also some long-range connections
            if distance < 3:  # Close nodes
                prob = connection_probability * 2
            elif distance < 6:  # Medium distance
                prob = connection_probability
            else:  # Far nodes
                prob = connection_probability * 0.3
            
            if random.random() < prob:
                connections.append((i, j))
    
    print(f"Created {len(connections)} connections")
    
    # Create more natural node colors (warmer palette)
    colors = []
    sizes = []
    for i in range(n_nodes):
        # Generate warmer, more natural colors
        hue = (i / n_nodes) * 0.8 + 0.1  # Avoid pure red/blue
        saturation = 0.7 + 0.3 * np.random.random()  # Variable saturation
        value = 0.6 + 0.4 * np.random.random()  # Variable brightness
        
        # Convert HSV to RGB
        import colorsys
        r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
        colors.append([r, g, b])
        
        # More natural size distribution (smaller variation)
        size = 0.25 + 0.2 * np.random.random()  # 0.25 to 0.45 radius
        sizes.append(size)
    
    return node_positions, connections, colors, sizes

def create_network_video(output_path="network_with_cylinders_video.mp4", duration=60, fps=30):
    """Create a network video using cylinders for connections."""
    print("Starting network video creation with cylinders...")
    
    # Create the network data
    node_positions, connections, colors, sizes = create_network_with_cylinders(n_nodes=43)
    
    # Create plotter with higher resolution
    print("Creating plotter...")
    plotter = pv.Plotter(off_screen=True, window_size=[1920, 1080])  # Full HD resolution
    
    # Add nodes as colorful spheres with variable sizes
    print("Adding nodes...")
    try:
        for i, pos in enumerate(node_positions):
            # Create a sphere for each node with variable size
            sphere = pv.Sphere(radius=sizes[i], center=pos)
            color = colors[i]
            plotter.add_mesh(sphere, color=color)
        
        print("✓ Added all nodes successfully")
    except Exception as e:
        print(f"✗ Error adding nodes: {e}")
        return
    
    # Add connections as smooth cylinders
    print("Adding smooth connections as cylinders...")
    try:
        for i, (start_idx, end_idx) in enumerate(connections):
            start_pos = node_positions[start_idx]
            end_pos = node_positions[end_idx]
            
            # Calculate cylinder properties
            center = (start_pos + end_pos) / 2
            direction = end_pos - start_pos
            length = np.linalg.norm(direction)
            
            if length > 0:
                # Create smoother, more organic cylinder
                # Vary thickness based on connection length (shorter = thicker)
                thickness = max(0.015, 0.03 - length * 0.002)
                
                # Add slight color variation based on distance
                distance_factor = min(1.0, length / 8.0)
                color_intensity = 0.6 + 0.4 * (1 - distance_factor)
                connection_color = [color_intensity, color_intensity, color_intensity]
                
                cylinder = pv.Cylinder(center=center, direction=direction, 
                                     radius=thickness, height=length)
                plotter.add_mesh(cylinder, color=connection_color, opacity=0.7)
        
        print("✓ Added all connections successfully")
    except Exception as e:
        print(f"✗ Error adding connections: {e}")
        return
    
    # Simple scene setup
    print("Setting up scene...")
    plotter.set_background('black')
    
    # Calculate total frames
    total_frames = duration * fps
    print(f"Total frames: {total_frames}")
    
    # Set up camera with wider field of view
    print("Setting up camera...")
    plotter.camera.position = (15, 15, 15)
    plotter.camera.focal_point = (0, 0, 0)
    plotter.camera.fov = 60  # Wider field of view to keep all nodes visible
    
    # Test with a single frame first
    print("Testing single frame...")
    try:
        test_path = Path(output_path).parent / "test_network_frame.png"
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
            # Calculate rotation angle (smooth rotation)
            angle = 2 * np.pi * frame / total_frames  # 360 degrees (1 full rotation)
            
            # Create smooth camera movement - keep all nodes in view
            radius = 30 + 5 * np.sin(2 * np.pi * frame / total_frames)  # Smooth radius variation: 25-35
            x = radius * np.cos(angle)
            y = radius * np.sin(angle)
            z = 10 + 5 * np.sin(4 * np.pi * frame / total_frames)  # Smooth Z variation: 5-15
            
            # Add smooth tilt changes
            tilt = 0.5 * np.sin(3 * np.pi * frame / total_frames)  # Gentle tilt variation
            
            # Debug: Print camera position for first few frames
            if frame < 5 or frame % 50 == 0:
                print(f"Frame {frame}: pos=({x:.1f}, {y:.1f}, {z:.1f}), tilt={tilt:.1f}")
            
            # Set camera position
            plotter.camera.position = (x, y, z)
            plotter.camera.focal_point = (0, 0, 0)
            plotter.camera.up = (0, 0, 1 + tilt)  # Add tilt to up vector
            
            # Force render update
            plotter.render()
            
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
            # Calculate rotation angle (smooth rotation)
            angle = 2 * np.pi * frame / total_frames  # 360 degrees (1 full rotation)
            
            # Create smooth camera movement - keep all nodes in view
            radius = 30 + 5 * np.sin(2 * np.pi * frame / total_frames)  # Smooth radius variation: 25-35
            x = radius * np.cos(angle)
            y = radius * np.sin(angle)
            z = 10 + 5 * np.sin(4 * np.pi * frame / total_frames)  # Smooth Z variation: 5-15
            
            # Add smooth tilt changes
            tilt = 0.5 * np.sin(3 * np.pi * frame / total_frames)  # Gentle tilt variation
            
            plotter.camera.position = (x, y, z)
            plotter.camera.focal_point = (0, 0, 0)
            plotter.camera.up = (0, 0, 1 + tilt)  # Add tilt to up vector
            plotter.render()
            
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
    """Create an interactive network view."""
    print("Creating interactive network view...")
    
    node_positions, connections, colors, sizes = create_network_with_cylinders(n_nodes=43)
    
    plotter = pv.Plotter()
    
    # Add nodes with variable sizes
    for i, pos in enumerate(node_positions):
        sphere = pv.Sphere(radius=sizes[i], center=pos)
        color = colors[i]
        plotter.add_mesh(sphere, color=color)
    
    # Add smooth connections
    for start_idx, end_idx in connections:
        start_pos = node_positions[start_idx]
        end_pos = node_positions[end_idx]
        
        center = (start_pos + end_pos) / 2
        direction = end_pos - start_pos
        length = np.linalg.norm(direction)
        
        if length > 0:
            # Create smoother, more organic cylinder
            thickness = max(0.015, 0.03 - length * 0.002)
            
            # Add slight color variation based on distance
            distance_factor = min(1.0, length / 8.0)
            color_intensity = 0.6 + 0.4 * (1 - distance_factor)
            connection_color = [color_intensity, color_intensity, color_intensity]
            
            cylinder = pv.Cylinder(center=center, direction=direction, 
                                 radius=thickness, height=length)
            plotter.add_mesh(cylinder, color=connection_color, opacity=0.7)
    
    plotter.set_background('black')
    plotter.add_text("Network with Cylinder Connections (43 nodes)", position='upper_left')
    
    print("Interactive window opened. Close to continue.")
    plotter.show()

if __name__ == "__main__":
    # Create output directory
    script_dir = Path(__file__).parent
    output_dir = script_dir / "output"
    output_dir.mkdir(exist_ok=True)
    
    print(f"Output directory: {output_dir}")
    
    # Create network video
    video_path = output_dir / "network_with_cylinders_video.mp4"
    create_network_video(str(video_path), duration=60, fps=30)
    
    # Create interactive view
    print("\nCreating interactive view...")
    create_interactive_view()
