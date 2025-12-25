import pickle
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import argparse
import matplotlib.cm as cm
from matplotlib.colors import to_rgb
from shapely.geometry import Point

def load_tracks(pickle_path: str) -> dict:
    """Load processed tracks from pickle file."""
    with open(pickle_path, 'rb') as f:
        data = pickle.load(f)
    
    # Convert the loaded data to a format compatible with the visualisation
    processed_data = {}
    for track_id, frames in data.items():
        processed_data[track_id] = []
        for frame_idx, parts in sorted(frames.items()):
            frame_data = {}
            for part, point in parts.items():
                if hasattr(point, 'x') and hasattr(point, 'y'):
                    frame_data[part] = [point.x, point.y]
            if frame_data:  # Only add frame if it has valid points
                processed_data[track_id].append(frame_data)
    
    return processed_data

def create_video(tracks: dict, output_path: str, width: int = 800, height: int = 600, fps: int = 30):
    """
    Create a video visualisation of the tracking data.
    
    Args:
        tracks: Dictionary containing track data
        output_path: Path to save the output video
        width: Width of the output video
        height: Height of the output video
        fps: Frames per second of the output video
    """
    # Specify colour map
    viridis = cm.get_cmap('viridis', 4)
    
    # Define body parts and assign colours
    body_parts = ['Head', 'Thorax', 'Abdomen', 'Tail']
    colors = {}
    
    # Convert colours from RGBA to BGR for OpenCV
    for i, part in enumerate(body_parts):
        # Convert colours to 0-255 range
        rgba = viridis(i / (len(body_parts) - 1))
        # Convert colours to BGR and scale to 0-255
        bgr = (np.array(rgba[:3]) * 255)[::-1].astype(np.uint8)
        colors[part] = tuple(map(int, bgr))
    
    # Find the maximum number of frames across all tracks
    max_frames = max(len(track_data) for track_data in tracks.values()) if tracks else 0
    
    if max_frames == 0:
        print("No frames found in the tracks data.")
        return
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    # Create a blank frame
    frame = np.ones((height, width, 3), dtype=np.uint8) * 255  # White background
    
    # Process frames
    for frame_idx in range(max_frames):
        frame.fill(255)
        
        # Draw each track
        for track_id, track_data in tracks.items():
            # Skip if this track doesn't have this frame
            if frame_idx >= len(track_data):
                continue
                
            frame_data = track_data[frame_idx]
            
            # Draw each body part
            for part, point_data in frame_data.items():
                if point_data is None:
                    continue
                    
                # Extract coordinates (now a direct [x, y] list)
                x, y = point_data
                x, y = int(x), int(y)
                
                # Draw keypoints
                color = colors.get(part, (200, 200, 200))  # Light gray for unlabelled body parts
                cv2.circle(frame, (x, y), 5, color.tolist() if hasattr(color, 'tolist') else color, -1)
                
                # Add body part labels
                text_color = (0, 0, 0)
                cv2.putText(frame, f"{track_id}:{part}", (x + 10, y - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1)
        
        # Add frame number
        cv2.putText(frame, f"Frame: {frame_idx}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        
        # Write the frame
        out.write(frame)
        
        # Indicate progress
        if frame_idx % 50 == 0:
            print(f"Processed frame {frame_idx}/{max_frames}")
    
    out.release()
    print(f"Video saved to {output_path}")

def main():
    # Set video parameters
    parser = argparse.ArgumentParser(description='Visualise tracking data')
    parser.add_argument('--input', type=str, default='ProcessedTracks.pkl',
                      help='Path to input pickle file with tracking data')
    parser.add_argument('--output', type=str, default='VisualisedTracks.avi',
                      help='Path to output video file')
    parser.add_argument('--width', type=int, default=800,
                      help='Width of the output video')
    parser.add_argument('--height', type=int, default=600,
                      help='Height of the output video')
    parser.add_argument('--fps', type=int, default=30,
                      help='Frames per second of the output video')
    
    args = parser.parse_args()
    
    # Load tracks
    print(f"Loading tracks from {args.input}...")
    tracks = load_tracks(args.input)
    print(f"Loaded {len(tracks)} tracks")
    
    # Create video
    print("Creating video visualisation...")
    create_video(tracks, args.output, args.width, args.height, args.fps)

if __name__ == "__main__":
    main()
