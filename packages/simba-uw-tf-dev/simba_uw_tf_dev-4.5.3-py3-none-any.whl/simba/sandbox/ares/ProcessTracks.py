import pandas as pd
from shapely.geometry import Point, mapping
from typing import Dict, List, Tuple
import os
import json
import pickle
from pathlib import Path

def load_sleap_data(file_path: str) -> pd.DataFrame:
    """Load SLEAP tracking data from CSV file."""
    print(f"Loading data from {file_path}...")
    df = pd.read_csv(file_path)
    print(f"Loaded {len(df)} rows with columns: {', '.join(df.columns)}")
    return df

def extract_body_parts(columns: list) -> list:
    """Extract body part names from column headers."""
    parts = set()
    for col in columns:
        if '.x' in col:
            part = col.split('.x')[0]
            if part not in ['track', 'frame_idx', 'instance']:
                parts.add(part)
    return sorted(list(parts))

def create_point_objects(df: pd.DataFrame) -> Dict[str, Dict[int, Dict[str, Point]]]:
    """
    Convert SLEAP tracking data into Shapely Point objects.
    
    Args:
        df: DataFrame containing SLEAP tracking data
        
    Returns:
        Dictionary with structure: {track_id: {frame_idx: {body_part: Point}}}
    """
    # Extract body parts from column names
    body_parts = extract_body_parts(df.columns.tolist())
    print(f"Detected body parts: {', '.join(body_parts)}")
    tracks = {}
    
    for _, row in df.iterrows():
        track_id = row['track']
        frame_idx = row['frame_idx']
        
        if track_id not in tracks:
            tracks[track_id] = {}
        if frame_idx not in tracks[track_id]:
            tracks[track_id][frame_idx] = {}
            
        for part in body_parts:
            x = row[f'{part}.x']
            y = row[f'{part}.y']
            # Only create a Point if both x and y are valid numbers
            if pd.notna(x) and pd.notna(y) and not pd.isnull(x) and not pd.isnull(y):
                try:
                    tracks[track_id][frame_idx][part] = Point(float(x), float(y))
                except (ValueError, TypeError):
                    # Skip if conversion fails
                    continue
            
    return tracks

def save_to_pickle(data: Dict, output_path: str) -> None:
    """Save the processed data to a pickle file.
    
    Args:
        data: Dictionary containing track data to be saved
        output_path: Path where the pickle file will be saved
    """
    # Create a copy of the data to avoid modifying the original
    data_to_save = {}
    for track_id, frames in data.items():
        # Sort frames by frame index
        sorted_frames = sorted(frames.items(), key=lambda x: x[0])
        data_to_save[track_id] = dict(sorted_frames)
    
    # Write to pickle file
    with open(output_path, 'wb') as f:
        pickle.dump(data_to_save, f, protocol=pickle.HIGHEST_PROTOCOL)
    print(f"\nSaved processed data to {output_path}")

def main():
    # Specify tracking data directory
    script_dir = Path(__file__).parent
    input_file = script_dir / 'Test Data//Termite Test.csv'
    output_file = script_dir / 'ProcessedTracks.json'
    
    try:
        # Load and process the data
        print(f"Loading SLEAP data from {input_file}...")
        df = load_sleap_data(str(input_file))
        tracks = create_point_objects(df)
        
        print(f"\nProcessing complete!")
        print(f"Found {len(tracks)} tracks")
        for track_id, frames in tracks.items():
            print(f"\nTrack {track_id}:")
            print(f"  - Frames: {len(frames)}")
            print(f"  - Duration: {len(frames)} frames")
            
            sorted_frames = sorted(frames.keys())
            if sorted_frames:
                first_frame = sorted_frames[0]
                last_frame = sorted_frames[-1]
                print(f"  - First frame: {first_frame}")
                print(f"  - Last frame: {last_frame}")
                print("\n  First frame points:")
                for part, point in frames[first_frame].items():
                    print(f"    {part}: ({point.x:.2f}, {point.y:.2f})")
        
        # Save the processed tracking data
        save_to_pickle(tracks, str(output_file).replace('.json', '.pkl'))
        return tracks
        
    except Exception as e:
        print(f"\nError processing file: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()
