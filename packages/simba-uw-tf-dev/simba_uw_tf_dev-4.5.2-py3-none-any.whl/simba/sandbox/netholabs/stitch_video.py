import os
import time
import gc
from typing import Union, Dict, List
import redis
import pickle
from multiprocessing import shared_memory
import multiprocessing
import cv2
import numpy as np
from collections import defaultdict
import psutil
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from simba.utils.read_write import read_img_batch_from_video_gpu, get_video_meta_data, read_frm_of_video
from simba.mixins.image_mixin import ImageMixin
from simba.video_processors.async_frame_reader import AsyncVideoFrameReader, get_async_frame_batch
from simba.video_processors.extract_frames import video_to_frames

class Timer:
    def __init__(self, name):
        self.name = name
        self.start_time = None
        self.total_time = 0
        
    def start(self):
        self.start_time = time.time()
        
    def stop(self):
        if self.start_time is not None:
            self.total_time += time.time() - self.start_time
            self.start_time = None
            
    def get_time(self):
        return self.total_time
        
    def reset(self):
        self.total_time = 0
        self.start_time = None

# Global video cache to avoid repeated metadata loading
VIDEO_CACHE = {}
VIDEO_CACHE_LOCK = threading.Lock()
FRAME_CACHE = {}  # Cache for extracted frames
FRAME_CACHE_LOCK = threading.Lock()

def get_video_metadata_cached(video_path: str):
    """Get video metadata with caching to avoid repeated I/O"""
    with VIDEO_CACHE_LOCK:
        if video_path not in VIDEO_CACHE:
            try:
                VIDEO_CACHE[video_path] = get_video_meta_data(video_path=video_path)
            except:
                VIDEO_CACHE[video_path] = None
        return VIDEO_CACHE[video_path]

def extract_video_frames_to_disk(video_path: str, frames_dir: str, force_extract: bool = False, frame_indices: List[int] = None) -> bool:
    """
    Extract specific frames from a video to disk for fast random access
    """
    if not os.path.isfile(video_path):
        return False
    
    # If no specific frames requested, extract all (for backward compatibility)
    if frame_indices is None:
        # Check if frames already exist
        if not force_extract and os.path.exists(frames_dir):
            # Check if we have at least some frames
            existing_frames = [f for f in os.listdir(frames_dir) if f.endswith('.png')]
            if len(existing_frames) > 0:
                print(f"Frames already exist in {frames_dir}, skipping extraction")
                return True
        
        try:
            print(f"Extracting ALL frames from {video_path} to {frames_dir}")
            os.makedirs(frames_dir, exist_ok=True)
            video_to_frames(video_path, frames_dir, overwrite=True, every=1, chunk_size=1000)
            print(f"Successfully extracted frames to {frames_dir}")
            return True
        except Exception as e:
            print(f"Error extracting frames from {video_path}: {e}")
            return False
    else:
        # Extract only the specific frames we need
        try:
            print(f"Extracting {len(frame_indices)} specific frames from {video_path} to {frames_dir}")
            os.makedirs(frames_dir, exist_ok=True)
            
            # Use cv2 to read specific frames
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                print(f"Error opening video {video_path}")
                return False
            
            # Sort frame indices for efficient seeking
            sorted_indices = sorted(frame_indices)
            extracted_count = 0
            
            for frame_idx in sorted_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if ret:
                    frame_path = os.path.join(frames_dir, f"{frame_idx}.png")
                    cv2.imwrite(frame_path, frame)
                    extracted_count += 1
            
            cap.release()
            print(f"Successfully extracted {extracted_count}/{len(frame_indices)} frames to {frames_dir}")
            return True
        except Exception as e:
            print(f"Error extracting specific frames from {video_path}: {e}")
            return False

def read_frame_from_disk(frames_dir: str, frame_idx: int) -> np.ndarray:
    """
    Read a single frame from disk (much faster than video seeking)
    """
    frame_path = os.path.join(frames_dir, f"{frame_idx}.png")
    try:
        if os.path.exists(frame_path):
            img = cv2.imread(frame_path, cv2.IMREAD_COLOR)
            if img is not None:
                return img
    except Exception as e:
        print(f"Error reading frame {frame_idx} from {frame_path}: {e}")
    
    # Return blank image if frame not found
    return ImageMixin().create_uniform_img(size=(1280, 720), color=(255, 255, 255))

def read_frames_from_disk_batch(frames_dir: str, frame_indices: List[int]) -> Dict[int, np.ndarray]:
    """
    Read multiple frames from disk efficiently
    """
    timer = Timer("read_frames_from_disk_batch")
    timer.start()
    
    results = {}
    
    # Use ThreadPoolExecutor for parallel disk reading
    def read_single_frame(frame_idx):
        return frame_idx, read_frame_from_disk(frames_dir, frame_idx)
    
    with ThreadPoolExecutor(max_workers=8) as executor:
        future_to_frame = {executor.submit(read_single_frame, frame_idx): frame_idx for frame_idx in frame_indices}
        for future in as_completed(future_to_frame):
            frame_idx, img = future.result()
            results[frame_idx] = img
    
    timer.stop()
    print(f"Read {len(results)} frames from disk in {timer.get_time():.2f}s")
    return results

def save_fast_grid_video_streaming(images_dict, out_path, fps=30):
    """
    Streaming version that writes frames as they're processed
    Properly handles multiple videos per camera position
    """
    timer = Timer("save_fast_grid_video_streaming")
    timer.start()
    
    # Layout: bottom-to-top per column, left-to-right
    grid_layout = [
        [3, 6, 9],  # top row
        [2, 5, 8],  # middle row
        [1, 4, 7]   # bottom row
    ]

    timestamps = sorted(images_dict.keys())
    
    # Get first available image to determine shape
    first_ts = timestamps[0]
    first_img = None
    for cam_data in images_dict[first_ts].values():
        if cam_data:
            first_img = next(iter(cam_data.values()))
            break

    if first_img is None:
        raise ValueError("No images found in the first timestamp.")

    H, W = first_img.shape[:2]
    out_shape = (H * 3, W * 3, 3)
    to_bgr = (first_img.ndim == 2)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(out_path, fourcc, fps, (W * 3, H * 3))

    # Pre-allocate frame array
    frame = np.zeros(out_shape, dtype=np.uint8)
    
    for ts in timestamps:
        frame.fill(0)  # Reset frame
        
        # Track which grid positions are occupied
        occupied_positions = set()
        
        for row_idx, row in enumerate(grid_layout):
            for col_idx, cam_id in enumerate(row):
                cam_data = images_dict[ts].get(str(cam_id))
                if not cam_data:
                    continue
                
                # Get all videos for this camera at this timestamp
                videos_for_camera = list(cam_data.values())
                if not videos_for_camera:
                    continue
                
                # If multiple videos exist for this camera, we need to handle them
                if len(videos_for_camera) > 1:
                    # For now, use the first video (you might want to modify this logic)
                    # In the future, this could be extended to create sub-grids or mosaics
                    img = videos_for_camera[0]
                else:
                    img = videos_for_camera[0]
                
                if img is None:
                    continue

                if to_bgr:
                    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                elif img.ndim == 3 and img.shape[2] == 1:
                    img = np.repeat(img, 3, axis=2)

                y0 = row_idx * H
                x0 = col_idx * W
                frame[y0:y0+H, x0:x0+W] = img
                occupied_positions.add((row_idx, col_idx))

        writer.write(frame)

    writer.release()
    timer.stop()
    print(f"Video saved: {out_path} (took {timer.get_time():.2f}s)")

def save_fast_grid_video(images_dict, out_path, fps=30):
    """
    Saves a grid video from a nested image dictionary:
    images_dict[timestamp][camera_id][video_name] = img
    """
    timer = Timer("save_fast_grid_video")
    timer.start()
    
    # Layout: bottom-to-top per column, left-to-right
    grid_layout = [
        [3, 6, 9],  # top row
        [2, 5, 8],  # middle row
        [1, 4, 7]   # bottom row
    ]

    timestamps = sorted(images_dict.keys())
    cam_ids = [str(cam) for row in grid_layout for cam in row]

    # Get first available image to determine shape
    first_ts = timestamps[0]
    first_img = None
    for cam_data in images_dict[first_ts].values():
        if cam_data:
            first_img = next(iter(cam_data.values()))
            break

    if first_img is None:
        raise ValueError("No images found in the first timestamp.")

    H, W = first_img.shape[:2]
    out_shape = (H * 3, W * 3, 3)
    CH = 3 if first_img.ndim == 3 else 1

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(out_path, fourcc, fps, (W * 3, H * 3))
    to_bgr = (first_img.ndim == 2)

    for ts in timestamps:
        frame = np.zeros(out_shape, dtype=np.uint8)
        for row_idx, row in enumerate(grid_layout):
            for col_idx, cam_id in enumerate(row):
                cam_data = images_dict[ts].get(str(cam_id))
                if not cam_data:
                    continue
                # Pick the first video (arbitrary but consistent)
                img = next(iter(cam_data.values()))
                if img is None:
                    continue

                if to_bgr:
                    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                elif img.ndim == 3 and img.shape[2] == 1:
                    img = np.repeat(img, 3, axis=2)

                y0 = row_idx * H
                x0 = col_idx * W
                frame[y0:y0+H, x0:x0+W] = img

        writer.write(frame)

    writer.release()
    timer.stop()
    print(f"Video saved: {out_path} (took {timer.get_time():.2f}s)")

def save_fast_grid_video_streaming_hw_accel(images_dict, out_path, fps=30):
    """
    Streaming version that writes frames as they're processed with hardware acceleration
    Properly handles multiple videos per camera position
    """
    timer = Timer("save_fast_grid_video_streaming_hw_accel")
    timer.start()
    
    # Layout: bottom-to-top per column, left-to-right
    grid_layout = [
        [3, 6, 9],  # top row
        [2, 5, 8],  # middle row
        [1, 4, 7]   # bottom row
    ]

    timestamps = sorted(images_dict.keys())
    
    # Get first available image to determine shape
    first_ts = timestamps[0]
    first_img = None
    for cam_data in images_dict[first_ts].values():
        if cam_data:
            first_img = next(iter(cam_data.values()))
            break

    if first_img is None:
        raise ValueError("No images found in the first timestamp.")

    H, W = first_img.shape[:2]
    out_shape = (H * 3, W * 3, 3)
    to_bgr = (first_img.ndim == 2)

    # Use cv2.VideoWriter_fourcc('h264') for hardware acceleration
    fourcc = cv2.VideoWriter_fourcc('h', '2', '6', '4')
    writer = cv2.VideoWriter(out_path, fourcc, fps, (W * 3, H * 3))

    # Pre-allocate frame array
    frame = np.zeros(out_shape, dtype=np.uint8)
    
    for ts in timestamps:
        frame.fill(0)  # Reset frame
        
        # Track which grid positions are occupied
        occupied_positions = set()
        
        for row_idx, row in enumerate(grid_layout):
            for col_idx, cam_id in enumerate(row):
                cam_data = images_dict[ts].get(str(cam_id))
                if not cam_data:
                    continue
                
                # Get all videos for this camera at this timestamp
                videos_for_camera = list(cam_data.values())
                if not videos_for_camera:
                    continue
                
                # If multiple videos exist for this camera, we need to handle them
                if len(videos_for_camera) > 1:
                    # For now, use the first video (you might want to modify this logic)
                    # In the future, this could be extended to create sub-grids or mosaics
                    img = videos_for_camera[0]
                else:
                    img = videos_for_camera[0]
                
                if img is None:
                    continue

                if to_bgr:
                    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                elif img.ndim == 3 and img.shape[2] == 1:
                    img = np.repeat(img, 3, axis=2)

                y0 = row_idx * H
                x0 = col_idx * W
                frame[y0:y0+H, x0:x0+W] = img
                occupied_positions.add((row_idx, col_idx))

        writer.write(frame)

    writer.release()
    timer.stop()
    print(f"Video saved: {out_path} (took {timer.get_time():.2f}s)")

def _read_video_frames_parallel_optimized(video_path: str, frame_indices: List[int]) -> Dict[int, np.ndarray]:
    """
    Optimized parallel frame reading for random frame access
    """
    if not os.path.isfile(video_path):
        return {}
    
    try:
        # Get video metadata once with caching
        vid_meta = get_video_metadata_cached(video_path)
        
        # Group frames into consecutive chunks for batch reading
        sorted_indices = sorted(frame_indices)
        chunks = []
        current_chunk = [sorted_indices[0]]
        
        for i in range(1, len(sorted_indices)):
            if sorted_indices[i] - sorted_indices[i-1] <= 5:  # Allow small gaps
                current_chunk.append(sorted_indices[i])
            else:
                chunks.append(current_chunk)
                current_chunk = [sorted_indices[i]]
        chunks.append(current_chunk)
        
        # Read each chunk in parallel
        results = {}
        
        def read_chunk(chunk):
            chunk_results = {}
            if len(chunk) == 1:
                # Single frame
                try:
                    img = read_frm_of_video(video_path=video_path, frame_index=chunk[0])
                    chunk_results[chunk[0]] = img
                except:
                    chunk_results[chunk[0]] = ImageMixin().create_uniform_img(size=(1280, 720), color=(255, 255, 255))
            else:
                # Batch read consecutive frames
                try:
                    batch_frames = read_img_batch_from_video_gpu(
                        video_path=video_path,
                        start_frm=chunk[0],
                        end_frm=chunk[-1],
                        verbose=False,
                        out_format='array'
                    )
                    
                    for i, frame_idx in enumerate(chunk):
                        if i < len(batch_frames):
                            chunk_results[frame_idx] = batch_frames[i]
                        else:
                            chunk_results[frame_idx] = ImageMixin().create_uniform_img(size=(1280, 720), color=(255, 255, 255))
                except:
                    # Fallback to individual reading
                    for frame_idx in chunk:
                        try:
                            img = read_frm_of_video(video_path=video_path, frame_index=frame_idx)
                            chunk_results[frame_idx] = img
                        except:
                            chunk_results[frame_idx] = ImageMixin().create_uniform_img(size=(1280, 720), color=(255, 255, 255))
            return chunk_results
        
        # Use ThreadPoolExecutor for parallel chunk reading
        with ThreadPoolExecutor(max_workers=8) as executor:
            future_to_chunk = {executor.submit(read_chunk, chunk): chunk for chunk in chunks}
            for future in as_completed(future_to_chunk):
                chunk_results = future.result()
                results.update(chunk_results)
        
        return results
        
    except Exception as e:
        print(f"Error reading frames from {video_path}: {e}")
        return {frame_idx: ImageMixin().create_uniform_img(size=(1280, 720), color=(255, 255, 255)) 
                for frame_idx in frame_indices}

def _read_video_frames_async(video_path: str, frame_indices: List[int]) -> Dict[int, np.ndarray]:
    """
    Optimized frame reading for random access - uses direct frame reading for specific frames
    """
    if not os.path.isfile(video_path):
        return {}
    
    try:
        # For random access, direct frame reading is more efficient than async batch reading
        # Use ThreadPoolExecutor for parallel individual frame reading
        results = {}
        
        def read_single_frame(frame_idx):
            try:
                img = read_frm_of_video(video_path=video_path, frame_index=frame_idx)
                return frame_idx, img
            except Exception as e:
                print(f"Error reading frame {frame_idx} from {video_path}: {e}")
                return frame_idx, ImageMixin().create_uniform_img(size=(1280, 720), color=(255, 255, 255))
        
        # Use ThreadPoolExecutor for parallel reading
        with ThreadPoolExecutor(max_workers=min(8, len(frame_indices))) as executor:
            future_to_frame = {executor.submit(read_single_frame, frame_idx): frame_idx 
                             for frame_idx in frame_indices}
            
            for future in as_completed(future_to_frame):
                frame_idx, img = future.result()
                results[frame_idx] = img
        
        return results
        
    except Exception as e:
        print(f"Error reading frames from {video_path}: {e}")
        return {frame_idx: ImageMixin().create_uniform_img(size=(1280, 720), color=(255, 255, 255)) 
                for frame_idx in frame_indices}

def _read_video_frames_parallel(video_path: str, frame_indices: List[int]) -> Dict[int, np.ndarray]:
    """
    Parallel frame reading using ThreadPoolExecutor
    """
    if not os.path.isfile(video_path):
        return {}
    
    try:
        # Get video metadata once with caching
        vid_meta = get_video_metadata_cached(video_path)
        
        # Try batch reading first
        if len(frame_indices) > 1:
            min_frame = min(frame_indices)
            max_frame = max(frame_indices)
            frame_range = max_frame - min_frame + 1
            
            # If frames are close, read in batch
            if frame_range <= len(frame_indices) * 5:  # More lenient threshold
                try:
                    batch_frames = read_img_batch_from_video_gpu(
                        video_path=video_path, 
                        start_frm=min_frame, 
                        end_frm=max_frame, 
                        verbose=False, 
                        out_format='array'
                    )
                    
                    # Map batch indices back to requested indices
                    results = {}
                    for frame_idx in frame_indices:
                        batch_idx = frame_idx - min_frame
                        if 0 <= batch_idx < len(batch_frames):
                            results[frame_idx] = batch_frames[batch_idx]
                        else:
                            results[frame_idx] = ImageMixin().create_uniform_img(size=(1280, 720), color=(255, 255, 255))
                    return results
                except:
                    pass
        
        # Fallback to parallel individual frame reading
        results = {}
        
        def read_single_frame(frame_idx):
            try:
                img = read_frm_of_video(video_path=video_path, frame_index=frame_idx)
                return frame_idx, img
            except:
                return frame_idx, ImageMixin().create_uniform_img(size=(1280, 720), color=(255, 255, 255))
        
        # Use ThreadPoolExecutor for parallel reading
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_frame = {executor.submit(read_single_frame, frame_idx): frame_idx for frame_idx in frame_indices}
            for future in as_completed(future_to_frame):
                frame_idx, img = future.result()
                results[frame_idx] = img
        
        return results
        
    except Exception as e:
        print(f"Error reading frames from {video_path}: {e}")
        return {frame_idx: ImageMixin().create_uniform_img(size=(1280, 720), color=(255, 255, 255)) 
                for frame_idx in frame_indices}

def _batch_read_frames_memory_efficient(video_path: str, frame_indices: List[int], max_batch_size: int = 50) -> Dict[int, np.ndarray]:
    """
    Memory-efficient batch frame reading with size limits
    """
    timer = Timer("_batch_read_frames_memory_efficient")
    timer.start()
    
    if not os.path.isfile(video_path):
        timer.stop()
        return {}
    
    try:
        # Get video metadata once with caching
        vid_meta = get_video_metadata_cached(video_path)
        
        # Process in smaller chunks to avoid memory issues
        results = {}
        for i in range(0, len(frame_indices), max_batch_size):
            chunk_indices = frame_indices[i:i + max_batch_size]
            
            if len(chunk_indices) > 1:
                min_frame = min(chunk_indices)
                max_frame = max(chunk_indices)
                frame_range = max_frame - min_frame + 1
                
                # Only batch read if frames are close together
                if frame_range <= len(chunk_indices) * 3:
                    try:
                        batch_frames = read_img_batch_from_video_gpu(
                            video_path=video_path, 
                            start_frm=min_frame, 
                            end_frm=max_frame, 
                            verbose=False, 
                            out_format='array'
                        )
                        
                        # Map batch indices back to requested indices
                        for frame_idx in chunk_indices:
                            batch_idx = frame_idx - min_frame
                            if 0 <= batch_idx < len(batch_frames):
                                results[frame_idx] = batch_frames[batch_idx].copy()  # Copy to avoid reference issues
                            else:
                                results[frame_idx] = ImageMixin().create_uniform_img(size=(1280, 720), color=(255, 255, 255))
                        
                        # Clear batch_frames to free memory
                        del batch_frames
                        gc.collect()
                        
                    except Exception as e:
                        print(f"Batch reading failed for {video_path}: {e}")
                        # Fallback to individual reading for this chunk
                        for frame_idx in chunk_indices:
                            try:
                                img = read_frm_of_video(video_path=video_path, frame_index=frame_idx)
                                results[frame_idx] = img
                            except:
                                results[frame_idx] = ImageMixin().create_uniform_img(size=(1280, 720), color=(255, 255, 255))
                else:
                    # Individual reading for scattered frames
                    for frame_idx in chunk_indices:
                        try:
                            img = read_frm_of_video(video_path=video_path, frame_index=frame_idx)
                            results[frame_idx] = img
                        except:
                            results[frame_idx] = ImageMixin().create_uniform_img(size=(1280, 720), color=(255, 255, 255))
            else:
                # Single frame
                frame_idx = chunk_indices[0]
                try:
                    img = read_frm_of_video(video_path=video_path, frame_index=frame_idx)
                    results[frame_idx] = img
                except:
                    results[frame_idx] = ImageMixin().create_uniform_img(size=(1280, 720), color=(255, 255, 255))
        
        timer.stop()
        print(f"Read {len(results)} frames from {video_path} in {timer.get_time():.2f}s")
        return results
        
    except Exception as e:
        print(f"Error reading frames from {video_path}: {e}")
        timer.stop()
        return {frame_idx: ImageMixin().create_uniform_img(size=(1280, 720), color=(255, 255, 255)) 
                for frame_idx in frame_indices}

def _batch_read_frames(video_path: str, frame_indices: List[int]) -> Dict[int, np.ndarray]:
    """
    Read multiple frames from a video efficiently in one operation
    """
    timer = Timer("_batch_read_frames")
    timer.start()
    
    if not os.path.isfile(video_path):
        timer.stop()
        return {}
    
    try:
        # Get video metadata once with caching
        vid_meta = get_video_metadata_cached(video_path)
        
        # Read frames in batch if possible
        if len(frame_indices) > 1:
            min_frame = min(frame_indices)
            max_frame = max(frame_indices)
            frame_range = max_frame - min_frame + 1
            
            # If frames are consecutive or close, read in batch
            if frame_range <= len(frame_indices) * 2:  # Allow some gaps
                try:
                    batch_frames = read_img_batch_from_video_gpu(
                        video_path=video_path, 
                        start_frm=min_frame, 
                        end_frm=max_frame, 
                        verbose=False, 
                        out_format='array'
                    )
                    
                    # Map batch indices back to requested indices
                    results = {}
                    for i, frame_idx in enumerate(frame_indices):
                        batch_idx = frame_idx - min_frame
                        if 0 <= batch_idx < len(batch_frames):
                            results[frame_idx] = batch_frames[batch_idx]
                        else:
                            results[frame_idx] = ImageMixin().create_uniform_img(size=(1280, 720), color=(255, 255, 255))
                    
                    timer.stop()
                    print(f"Batch read {len(results)} frames from {video_path} in {timer.get_time():.2f}s")
                    return results
                except:
                    pass
        
        # Fallback to individual frame reading
        results = {}
        for frame_idx in frame_indices:
            try:
                img = read_frm_of_video(video_path=video_path, frame_index=frame_idx)
                results[frame_idx] = img
            except:
                results[frame_idx] = ImageMixin().create_uniform_img(size=(1280, 720), color=(255, 255, 255))
        
        timer.stop()
        print(f"Individual read {len(results)} frames from {video_path} in {timer.get_time():.2f}s")
        return results
        
    except:
        # Return blank images if video reading fails
        timer.stop()
        return {frame_idx: ImageMixin().create_uniform_img(size=(1280, 720), color=(255, 255, 255)) 
                for frame_idx in frame_indices}

def _stitch_helper_disk_fast(data: tuple):
    """
    Ultra-fast disk-based version that reads frames directly from extracted images
    """
    batch_id, time_stamps, lookup_data = data
    timer = Timer(f"_stitch_helper_disk_fast_batch_{batch_id}")
    timer.start()
    
    results = {}
    
    try:
        # Group frame requests by video to enable batch reading
        grouping_timer = Timer("grouping_frames")
        grouping_timer.start()
        video_frame_requests = defaultdict(lambda: defaultdict(list))
        
        for time_stamp in time_stamps:
            for camera_id, video_data in lookup_data[time_stamp].items():
                for video_name, frame_id in video_data.items():
                    if frame_id != -1:
                        video_frame_requests[video_name][time_stamp].append((camera_id, frame_id))
        grouping_timer.stop()
        print(f"Grouped frames in {grouping_timer.get_time():.2f}s")
        
        # Process each video with disk reading
        for video_name, frame_requests in video_frame_requests.items():
            video_timer = Timer(f"video_{video_name}")
            video_timer.start()
            
            video_path = f'{video_name}.mp4'
            frames_dir = f'{video_name}_frames'  # Directory for extracted frames
            
            # Read frames from disk
            all_frame_ids = []
            for ts_requests in frame_requests.values():
                all_frame_ids.extend([frame_id for _, frame_id in ts_requests])
            frames_dict = read_frames_from_disk_batch(frames_dir, all_frame_ids)
            
            # Build results for this video
            for time_stamp in time_stamps:
                if time_stamp not in results:
                    results[time_stamp] = {}
                
                for camera_id, video_data in lookup_data[time_stamp].items():
                    if camera_id not in results[time_stamp]:
                        results[time_stamp][camera_id] = {}
                    
                    # Only set the current video being processed
                    if video_name in video_data:
                        frame_id = video_data[video_name]
                        if frame_id != -1:
                            img = frames_dict.get(frame_id)
                            if img is None:
                                img = ImageMixin().create_uniform_img(size=(1280, 720), color=(255, 255, 255))
                        else:
                            img = ImageMixin().create_uniform_img(size=(1280, 720), color=(255, 255, 255))
                        
                        results[time_stamp][camera_id][video_name] = img
            
            # Clear frames_dict to free memory
            del frames_dict
            gc.collect()
            
            video_timer.stop()
            print(f"Processed video {video_name} in {video_timer.get_time():.2f}s")
        
        timer.stop()
        print(f"Batch {batch_id} completed in {timer.get_time():.2f}s")
        return results, batch_id
        
    except Exception as e:
        print(f"Error in _stitch_helper_disk_fast: {e}")
        timer.stop()
        # Return blank results on error
        for time_stamp in time_stamps:
            results[time_stamp] = {}
            for camera_id, video_data in lookup_data[time_stamp].items():
                results[time_stamp][camera_id] = {}
                for video_name, frame_id in video_data.items():
                    results[time_stamp][camera_id][video_name] = ImageMixin().create_uniform_img(size=(1280, 720), color=(255, 255, 255))
        
        return results, batch_id

def _stitch_helper_async_fast(data: tuple):
    """
    Optimized async-fast version with reduced overhead and better memory management
    """
    batch_id, time_stamps, lookup_data = data
    timer = Timer(f"_stitch_helper_async_fast_batch_{batch_id}")
    timer.start()
    
    results = {}
    
    try:
        # Group frame requests by video to enable batch reading
        video_frame_requests = defaultdict(lambda: defaultdict(list))
        
        for time_stamp in time_stamps:
            for camera_id, video_data in lookup_data[time_stamp].items():
                for video_name, frame_id in video_data.items():
                    if frame_id != -1:
                        video_frame_requests[video_name][time_stamp].append((camera_id, frame_id))
        
        # Process each video with optimized reading
        for video_name, frame_requests in video_frame_requests.items():
            video_path = f'{video_name}.mp4'
            all_frame_ids = []
            for ts_requests in frame_requests.values():
                all_frame_ids.extend([frame_id for _, frame_id in ts_requests])
            
            # Read frames with optimized processing
            frames_dict = _read_video_frames_async(video_path, all_frame_ids)
            
            # Build results for this video
            for time_stamp in time_stamps:
                if time_stamp not in results:
                    results[time_stamp] = {}
                
                for camera_id, video_data in lookup_data[time_stamp].items():
                    if camera_id not in results[time_stamp]:
                        results[time_stamp][camera_id] = {}
                    
                    # Only set the current video being processed
                    if video_name in video_data:
                        frame_id = video_data[video_name]
                        if frame_id != -1:
                            img = frames_dict.get(frame_id)
                            if img is None:
                                img = ImageMixin().create_uniform_img(size=(1280, 720), color=(255, 255, 255))
                        else:
                            img = ImageMixin().create_uniform_img(size=(1280, 720), color=(255, 255, 255))
                        
                        results[time_stamp][camera_id][video_name] = img
            
            # Clear frames_dict to free memory
            del frames_dict
            gc.collect()
        
        timer.stop()
        print(f"Batch {batch_id} completed in {timer.get_time():.2f}s")
        return results, batch_id
        
    except Exception as e:
        print(f"Error in _stitch_helper_async_fast: {e}")
        timer.stop()
        # Return blank results on error
        for time_stamp in time_stamps:
            results[time_stamp] = {}
            for camera_id, video_data in lookup_data[time_stamp].items():
                results[time_stamp][camera_id] = {}
                for video_name, frame_id in video_data.items():
                    results[time_stamp][camera_id][video_name] = ImageMixin().create_uniform_img(size=(1280, 720), color=(255, 255, 255))
        
        return results, batch_id

def _stitch_helper_ultra_fast(data: tuple):
    """
    Ultra-fast version with parallel video reading and minimal overhead
    """
    batch_id, time_stamps, lookup_data = data
    timer = Timer(f"_stitch_helper_ultra_fast_batch_{batch_id}")
    timer.start()
    
    results = {}
    
    try:
        # Group frame requests by video to enable batch reading
        grouping_timer = Timer("grouping_frames")
        grouping_timer.start()
        video_frame_requests = defaultdict(lambda: defaultdict(list))
        
        for time_stamp in time_stamps:
            for camera_id, video_data in lookup_data[time_stamp].items():
                for video_name, frame_id in video_data.items():
                    if frame_id != -1:
                        video_frame_requests[video_name][time_stamp].append((camera_id, frame_id))
        grouping_timer.stop()
        print(f"Grouped frames in {grouping_timer.get_time():.2f}s")
        
        # Process each video with parallel reading
        for video_name, frame_requests in video_frame_requests.items():
            video_timer = Timer(f"video_{video_name}")
            video_timer.start()
            
            video_path = f'{video_name}.mp4'
            all_frame_ids = []
            for ts_requests in frame_requests.values():
                all_frame_ids.extend([frame_id for _, frame_id in ts_requests])
            
            # Read frames with parallel processing
            frames_dict = _read_video_frames_parallel(video_path, all_frame_ids)
            
            # Build results for this video
            for time_stamp in time_stamps:
                if time_stamp not in results:
                    results[time_stamp] = {}
                
                for camera_id, video_data in lookup_data[time_stamp].items():
                    if camera_id not in results[time_stamp]:
                        results[time_stamp][camera_id] = {}
                    
                    # Only set the current video being processed
                    if video_name in video_data:
                        frame_id = video_data[video_name]
                        if frame_id != -1:
                            img = frames_dict.get(frame_id)
                            if img is None:
                                img = ImageMixin().create_uniform_img(size=(1280, 720), color=(255, 255, 255))
                        else:
                            img = ImageMixin().create_uniform_img(size=(1280, 720), color=(255, 255, 255))
                        
                        results[time_stamp][camera_id][video_name] = img
            
            # Clear frames_dict to free memory
            del frames_dict
            gc.collect()
            
            video_timer.stop()
            print(f"Processed video {video_name} in {video_timer.get_time():.2f}s")
        
        timer.stop()
        print(f"Batch {batch_id} completed in {timer.get_time():.2f}s")
        return results, batch_id
        
    except Exception as e:
        print(f"Error in _stitch_helper_ultra_fast: {e}")
        timer.stop()
        # Return blank results on error
        for time_stamp in time_stamps:
            results[time_stamp] = {}
            for camera_id, video_data in lookup_data[time_stamp].items():
                results[time_stamp][camera_id] = {}
                for video_name, frame_id in video_data.items():
                    results[time_stamp][camera_id][video_name] = ImageMixin().create_uniform_img(size=(1280, 720), color=(255, 255, 255))
        
        return results, batch_id

def _stitch_helper_optimized_memory_efficient(data: tuple):
    """
    Memory-efficient optimized version that processes in smaller chunks
    """
    batch_id, time_stamps, lookup_data = data
    timer = Timer(f"_stitch_helper_optimized_memory_efficient_batch_{batch_id}")
    timer.start()
    
    results = {}
    
    try:
        # Group frame requests by video to enable batch reading
        grouping_timer = Timer("grouping_frames")
        grouping_timer.start()
        video_frame_requests = defaultdict(lambda: defaultdict(list))
        
        for time_stamp in time_stamps:
            for camera_id, video_data in lookup_data[time_stamp].items():
                for video_name, frame_id in video_data.items():
                    if frame_id != -1:
                        video_frame_requests[video_name][time_stamp].append((camera_id, frame_id))
        grouping_timer.stop()
        print(f"Grouped frames in {grouping_timer.get_time():.2f}s")
        
        # Process each video with memory limits
        for video_name, frame_requests in video_frame_requests.items():
            video_timer = Timer(f"video_{video_name}")
            video_timer.start()
            
            video_path = f'{video_name}.mp4'
            all_frame_ids = []
            for ts_requests in frame_requests.values():
                all_frame_ids.extend([frame_id for _, frame_id in ts_requests])
            
            # Read frames with memory limits
            frames_dict = _batch_read_frames_memory_efficient(video_path, all_frame_ids, max_batch_size=30)
            
            # Build results for this video
            for time_stamp in time_stamps:
                if time_stamp not in results:
                    results[time_stamp] = {}
                
                for camera_id, video_data in lookup_data[time_stamp].items():
                    if camera_id not in results[time_stamp]:
                        results[time_stamp][camera_id] = {}
                    
                    # Only set the current video being processed
                    if video_name in video_data:
                        frame_id = video_data[video_name]
                        if frame_id != -1:
                            img = frames_dict.get(frame_id)
                            if img is None:
                                img = ImageMixin().create_uniform_img(size=(1280, 720), color=(255, 255, 255))
                        else:
                            img = ImageMixin().create_uniform_img(size=(1280, 720), color=(255, 255, 255))
                        
                        results[time_stamp][camera_id][video_name] = img
            
            # Clear frames_dict to free memory
            del frames_dict
            gc.collect()
            
            video_timer.stop()
            print(f"Processed video {video_name} in {video_timer.get_time():.2f}s")
        
        timer.stop()
        print(f"Batch {batch_id} completed in {timer.get_time():.2f}s")
        return results, batch_id
        
    except Exception as e:
        print(f"Error in _stitch_helper_optimized_memory_efficient: {e}")
        timer.stop()
        # Return blank results on error
        for time_stamp in time_stamps:
            results[time_stamp] = {}
            for camera_id, video_data in lookup_data[time_stamp].items():
                results[time_stamp][camera_id] = {}
                for video_name, frame_id in video_data.items():
                    results[time_stamp][camera_id][video_name] = ImageMixin().create_uniform_img(size=(1280, 720), color=(255, 255, 255))
        
        return results, batch_id

def _stitch_helper_optimized(data: tuple):
    """
    Optimized version that reads frames in batches
    """
    batch_id, time_stamps, lookup_data = data
    timer = Timer(f"_stitch_helper_optimized_batch_{batch_id}")
    timer.start()
    
    # Group frame requests by video to enable batch reading
    video_frame_requests = defaultdict(lambda: defaultdict(list))
    
    for time_stamp in time_stamps:
        for camera_id, video_data in lookup_data[time_stamp].items():
            for video_name, frame_id in video_data.items():
                if frame_id != -1:
                    video_frame_requests[video_name][time_stamp].append((camera_id, frame_id))
    
    # Read frames in batches for each video
    video_frames_cache = {}
    for video_name, frame_requests in video_frame_requests.items():
        video_path = f'{video_name}.mp4'
        all_frame_ids = []
        for ts_requests in frame_requests.values():
            all_frame_ids.extend([frame_id for _, frame_id in ts_requests])
        
        # Read all frames for this video in one batch
        frames_dict = _batch_read_frames(video_path, all_frame_ids)
        video_frames_cache[video_name] = frames_dict
    
    # Build results using cached frames
    for time_stamp in time_stamps:
        results[time_stamp] = {}
        for camera_id, video_data in lookup_data[time_stamp].items():
            results[time_stamp][camera_id] = {}
            for video_name, frame_id in video_data.items():
                if frame_id != -1 and video_name in video_frames_cache:
                    img = video_frames_cache[video_name].get(frame_id)
                    if img is None:
                        img = ImageMixin().create_uniform_img(size=(1280, 720), color=(255, 255, 255))
                else:
                    img = ImageMixin().create_uniform_img(size=(1280, 720), color=(255, 255, 255))
                
                results[time_stamp][camera_id][video_name] = img
    
    timer.stop()
    print(f"Batch {batch_id} completed in {timer.get_time():.2f}s")
    return results, batch_id

def _stitch_helper(data: tuple):
    batch_id, time_stamps = data
    timer = Timer(f"_stitch_helper_batch_{batch_id}")
    timer.start()
    
    shm2 = shared_memory.SharedMemory(name='video_lk')
    data = pickle.loads(shm2.buf.tobytes())
    results = {}
    for cnt, time_stamp in enumerate(time_stamps):
        results[time_stamp] = {}

        for camera_id, video_data in data[time_stamp].items():
            results[time_stamp][camera_id] = {}
            for video_name, frame_id in video_data.items():
                video_path = os.path.join(f'{video_name}.mp4')
                if frame_id != -1 and os.path.isfile(video_path):
                    vid_meta = get_video_meta_data(video_path=video_path)
                    try:
                        img = read_frm_of_video(video_path=video_path, frame_index=frame_id)
                    #img = read_img_batch_from_video_gpu(video_path=video_path, start_frm=frame_id, end_frm=frame_id, verbose=False, out_format='array')
                    except:
                        img = ImageMixin().create_uniform_img(size=(1280, 720), color=(255, 255, 255))
                else:
                    img = ImageMixin().create_uniform_img(size=(1280, 720), color=(255, 255, 255))

                results[time_stamp][camera_id][video_name] = img
    
    timer.stop()
    print(f"Original batch {batch_id} completed in {timer.get_time():.2f}s")
    return results, batch_id

        #             break
        #         break
        #     break
        # break

class StitchVideoFromLk:

    def __init__(self,
                 lookup_path: Union[str, os.PathLike],
                 save_dir: str,
                 core_cnt: int = 12,
                 batch_size: int = 250,
                 use_optimized: bool = True,
                 use_memory_efficient: bool = True,
                 use_ultra_fast: bool = True,
                 use_async_fast: bool = True,
                 use_disk_fast: bool = True):

        total_timer = Timer("total_processing")
        total_timer.start()
        
        with open(lookup_path, 'rb') as f:
            raw_lk = pickle.load(f)

        time_stamps = list(raw_lk.keys())
        print(f"Processing {len(time_stamps)} timestamps")
        
        if use_optimized:
            if use_disk_fast:
                self._process_disk_fast(raw_lk, time_stamps, save_dir, core_cnt, batch_size)
            elif use_async_fast:
                self._process_async_fast(raw_lk, time_stamps, save_dir, core_cnt, batch_size)
            elif use_ultra_fast:
                self._process_ultra_fast(raw_lk, time_stamps, save_dir, core_cnt, batch_size)
            elif use_memory_efficient:
                self._process_memory_efficient(raw_lk, time_stamps, save_dir, core_cnt, batch_size)
            else:
                self._process_optimized(raw_lk, time_stamps, save_dir, core_cnt, batch_size)
        else:
            self._process_original(raw_lk, time_stamps, save_dir, core_cnt, batch_size)
        
        total_timer.stop()
        print(f"Total processing time: {total_timer.get_time():.2f}s")

    def _process_disk_fast(self, raw_lk, time_stamps, save_dir, core_cnt, batch_size):
        """
        Disk-fast processing using extracted frames for maximum speed
        """
        print("Starting disk-based fast processing...")
        
        # Extract frames to disk first (in main process to avoid nested multiprocessing)
        print("Extracting video frames to disk...")
        extract_timer = Timer("extract_all_frames")
        extract_timer.start()
        
        # Get all unique video paths and their required frame indices
        video_frame_requirements = defaultdict(set)
        for time_stamp in time_stamps:
            for camera_id, video_data in raw_lk[time_stamp].items():
                for video_name, frame_id in video_data.items():
                    if frame_id != -1:
                        video_path = f'{video_name}.mp4'
                        video_frame_requirements[video_path].add(frame_id)
        
        # DEBUG: Print detailed information about frame requirements
        print(f"\n=== FRAME EXTRACTION DEBUG ===")
        print(f"Total timestamps: {len(time_stamps)}")
        print(f"Number of videos: {len(video_frame_requirements)}")
        
        for video_path, frame_indices in video_frame_requirements.items():
            frame_list = list(frame_indices)
            print(f"\nVideo: {video_path}")
            print(f"  - Total frames needed: {len(frame_list)}")
            print(f"  - Frame range: {min(frame_list)} to {max(frame_list)}")
            print(f"  - Sample frames: {frame_list[:10]}...")
            
            # Check if this looks like a sequential range
            if len(frame_list) > 1:
                sorted_frames = sorted(frame_list)
                gaps = [sorted_frames[i+1] - sorted_frames[i] for i in range(len(sorted_frames)-1)]
                avg_gap = sum(gaps) / len(gaps) if gaps else 0
                print(f"  - Average gap between frames: {avg_gap:.2f}")
        
        print(f"\n=== END DEBUG ===\n")
        
        # Extract only the frames we need for each video
        total_frames_to_extract = 0
        for video_path, frame_indices in video_frame_requirements.items():
            frames_dir = f'{video_path[:-4]}_frames'  # Remove .mp4 extension
            frame_list = list(frame_indices)
            total_frames_to_extract += len(frame_list)
            print(f"Extracting {len(frame_list)} specific frames for {video_path} to {frames_dir}")
            if not extract_video_frames_to_disk(video_path, frames_dir, frame_indices=frame_list):
                print(f"Warning: Failed to extract frames for {video_path}")
        
        extract_timer.stop()
        print(f"Frame extraction completed in {extract_timer.get_time():.2f}s")
        print(f"Total frames extracted: {total_frames_to_extract} (vs extracting all frames)")
        
        # Use very small batches for maximum parallelism
        optimal_batch_size = min(batch_size, core_cnt)  # One batch per core
        time_stamps_splits = [time_stamps[i:i + optimal_batch_size] 
                             for i in range(0, len(time_stamps), optimal_batch_size)]
        
        print(f"Processing {len(time_stamps_splits)} batches of size {optimal_batch_size}")
        
        for cnt, time_stamps_split in enumerate(time_stamps_splits):
            batch_timer = Timer(f"batch_{cnt}")
            batch_timer.start()
            
            print(f"Processing batch {cnt+1}/{len(time_stamps_splits)} ({len(time_stamps_split)} timestamps)")
            
            # Create work items with lookup data - one chunk per core
            chunk_size = max(1, len(time_stamps_split) // core_cnt)
            work_items = [(i, time_stamps_split, raw_lk) 
                         for i, time_stamps_split in enumerate([time_stamps_split[i:i + chunk_size] 
                                                              for i in range(0, len(time_stamps_split), chunk_size)])]
            
            batch_results = {}
            with multiprocessing.Pool(core_cnt, maxtasksperchild=3) as pool:  # Very frequent recycling
                for batch_cnt, (results, batch_id) in enumerate(pool.imap(_stitch_helper_disk_fast, work_items, chunksize=1)):
                    batch_results.update(results)
                    save_fast_grid_video_streaming(images_dict=results, 
                                                 out_path=os.path.join(save_dir, f'{cnt}_{batch_id}.mp4'))
            
            # Force garbage collection after each batch
            gc.collect()
            
            batch_timer.stop()
            print(f"Batch {cnt} completed in {batch_timer.get_time():.2f}s")

    def _process_async_fast(self, raw_lk, time_stamps, save_dir, core_cnt, batch_size):
        """
        Optimized processing for 120 FPS with better batch sizing and parallel processing
        """
        # Use larger batches for better efficiency while maintaining parallelism
        optimal_batch_size = min(50, core_cnt * 5)  # Larger batches for better efficiency
        time_stamps_splits = [time_stamps[i:i + optimal_batch_size] 
                             for i in range(0, len(time_stamps), optimal_batch_size)]
        
        print(f"Processing {len(time_stamps_splits)} batches of size {optimal_batch_size} for 120 FPS optimization")
        
        for cnt, time_stamps_split in enumerate(time_stamps_splits):
            batch_timer = Timer(f"batch_{cnt}")
            batch_timer.start()
            
            print(f"Processing batch {cnt+1}/{len(time_stamps_splits)} ({len(time_stamps_split)} timestamps)")
            
            # Check memory before processing
            memory = psutil.virtual_memory()
            if memory.percent > 80:
                print(f"High memory usage ({memory.percent}%), forcing garbage collection...")
                gc.collect()
                time.sleep(0.5)
            
            # Process the entire batch in one worker for better efficiency
            work_items = [(cnt, time_stamps_split, raw_lk)]
            
            batch_results = {}
            with multiprocessing.Pool(core_cnt, maxtasksperchild=3) as pool:  # Less frequent recycling
                for batch_cnt, (results, batch_id) in enumerate(pool.imap(_stitch_helper_async_fast, work_items, chunksize=1)):
                    batch_results.update(results)
                    # Use hardware acceleration for video encoding
                    save_fast_grid_video_streaming_hw_accel(images_dict=results, 
                                                          out_path=os.path.join(save_dir, f'{cnt}_{batch_id}.mp4'))
            
            # Force garbage collection after each batch
            gc.collect()
            
            batch_timer.stop()
            fps_achieved = len(time_stamps_split) / batch_timer.get_time() if batch_timer.get_time() > 0 else 0
            print(f"Batch {cnt} completed in {batch_timer.get_time():.2f}s ({fps_achieved:.1f} FPS)")

    def _process_ultra_fast(self, raw_lk, time_stamps, save_dir, core_cnt, batch_size):
        """
        Ultra-fast processing with parallel video reading and minimal overhead
        Optimized for 120 FPS processing with hardware acceleration
        """
        # Use very small batches for maximum parallelism and memory efficiency
        optimal_batch_size = min(10, core_cnt)  # Very small batches for 120 FPS
        time_stamps_splits = [time_stamps[i:i + optimal_batch_size] 
                             for i in range(0, len(time_stamps), optimal_batch_size)]
        
        print(f"Processing {len(time_stamps_splits)} batches of size {optimal_batch_size} for 120 FPS optimization")
        
        for cnt, time_stamps_split in enumerate(time_stamps_splits):
            batch_timer = Timer(f"batch_{cnt}")
            batch_timer.start()
            
            print(f"Processing batch {cnt+1}/{len(time_stamps_splits)} ({len(time_stamps_split)} timestamps)")
            
            # Check memory before processing
            memory = psutil.virtual_memory()
            if memory.percent > 80:
                print(f"High memory usage ({memory.percent}%), forcing garbage collection...")
                gc.collect()
                time.sleep(0.5)
            
            # Create work items with lookup data - one chunk per core for maximum parallelism
            chunk_size = max(1, len(time_stamps_split) // core_cnt)
            work_items = [(i, time_stamps_split, raw_lk) 
                         for i, time_stamps_split in enumerate([time_stamps_split[i:i + chunk_size] 
                                                              for i in range(0, len(time_stamps_split), chunk_size)])]
            
            batch_results = {}
            with multiprocessing.Pool(core_cnt, maxtasksperchild=2) as pool:  # Very frequent recycling for memory
                for batch_cnt, (results, batch_id) in enumerate(pool.imap(_stitch_helper_ultra_fast, work_items, chunksize=1)):
                    batch_results.update(results)
                    # Use hardware acceleration for video encoding
                    save_fast_grid_video_streaming_hw_accel(images_dict=results, 
                                                          out_path=os.path.join(save_dir, f'{cnt}_{batch_id}.mp4'))
            
            # Force garbage collection after each batch
            gc.collect()
            
            batch_timer.stop()
            fps_achieved = len(time_stamps_split) / batch_timer.get_time() if batch_timer.get_time() > 0 else 0
            print(f"Batch {cnt} completed in {batch_timer.get_time():.2f}s ({fps_achieved:.1f} FPS)")

    def _process_memory_efficient(self, raw_lk, time_stamps, save_dir, core_cnt, batch_size):
        """
        Memory-efficient processing with smaller batches and resource management
        """
        # Use much smaller batches for faster processing
        optimal_batch_size = min(batch_size, core_cnt * 2)  # Even smaller batches for speed
        time_stamps_splits = [time_stamps[i:i + optimal_batch_size] 
                             for i in range(0, len(time_stamps), optimal_batch_size)]
        
        print(f"Processing {len(time_stamps_splits)} batches of size {optimal_batch_size}")
        
        for cnt, time_stamps_split in enumerate(time_stamps_splits):
            batch_timer = Timer(f"batch_{cnt}")
            batch_timer.start()
            
            print(f"Processing batch {cnt+1}/{len(time_stamps_splits)} ({len(time_stamps_split)} timestamps)")
            
            # Check available memory
            memory = psutil.virtual_memory()
            if memory.percent > 85:
                print(f"High memory usage ({memory.percent}%), forcing garbage collection...")
                gc.collect()
                time.sleep(1)
            
            # Create work items with lookup data - use smaller chunks for faster processing
            chunk_size = max(1, core_cnt // 2)  # Smaller chunks for better load balancing
            work_items = [(i, time_stamps_split, raw_lk) 
                         for i, time_stamps_split in enumerate([time_stamps_split[i:i + chunk_size] 
                                                              for i in range(0, len(time_stamps_split), chunk_size)])]
            
            batch_results = {}
            with multiprocessing.Pool(core_cnt, maxtasksperchild=5) as pool:  # Even more frequent recycling
                for batch_cnt, (results, batch_id) in enumerate(pool.imap(_stitch_helper_optimized_memory_efficient, work_items, chunksize=1)):
                    batch_results.update(results)
                    save_fast_grid_video(images_dict=results, 
                                       out_path=os.path.join(save_dir, f'{cnt}_{batch_id}.mp4'))
            
            # Force garbage collection after each batch
            gc.collect()
            
            batch_timer.stop()
            print(f"Batch {cnt} completed in {batch_timer.get_time():.2f}s")

    def _process_optimized(self, raw_lk, time_stamps, save_dir, core_cnt, batch_size):
        """
        Optimized processing with batch frame reading and better multiprocessing
        """
        # Create larger batches for better efficiency
        optimal_batch_size = max(batch_size, core_cnt * 10)  # Ensure batches are large enough
        time_stamps_splits = [time_stamps[i:i + optimal_batch_size] 
                             for i in range(0, len(time_stamps), optimal_batch_size)]
        
        for cnt, time_stamps_split in enumerate(time_stamps_splits):
            print(f"Processing batch {cnt+1}/{len(time_stamps_splits)} ({len(time_stamps_split)} timestamps)")
            
            # Create work items with lookup data
            work_items = [(i, time_stamps_split, raw_lk) 
                         for i, time_stamps_split in enumerate([time_stamps_split[i:i + core_cnt] 
                                                              for i in range(0, len(time_stamps_split), core_cnt)])]
            
            batch_results = {}
            with multiprocessing.Pool(core_cnt, maxtasksperchild=20) as pool:
                for batch_cnt, (results, batch_id) in enumerate(pool.imap(_stitch_helper_optimized, work_items, chunksize=1)):
                    batch_results.update(results)
                    save_fast_grid_video(images_dict=results, 
                                       out_path=os.path.join(save_dir, f'{cnt}_{batch_id}.mp4'))

    def _process_original(self, raw_lk, time_stamps, save_dir, core_cnt, batch_size):
        """
        Original processing method (kept for comparison)
        """
        #data = pickle.dumps(raw_lk)
        # try:
        #     existing_shm = shared_memory.SharedMemory(name='video_lk')
        #     existing_shm.close()
        #     existing_shm.unlink()
        #     print('s')
        #     time.sleep(4)
        # except FileNotFoundError as e:
        #     print(e.args)
        #     pass
        # shm = shared_memory.SharedMemory(create=True, size=len(data), name='video_lk')
        # shm.buf[:len(data)] = data

        time_stamps_splits = [time_stamps[i:i + batch_size] for i in range(0, len(time_stamps), batch_size)]
        for cnt, time_stamps_split in enumerate(time_stamps_splits):
            batch_time_stamps_splits = [time_stamps_split[i:i + core_cnt] for i in range(0, len(time_stamps_split), core_cnt)]
            batch_time_stamps_splits = [(i, j) for i, j in enumerate(batch_time_stamps_splits)]
            batch_results = {}
            with multiprocessing.Pool(core_cnt, maxtasksperchild=50) as pool:
                for batch_cnt, (results, batch_id) in enumerate(pool.imap(_stitch_helper, batch_time_stamps_splits, chunksize=1)):
                    # for frm_id, camera_data in results.items():
                    #     for img in camera_data.values():
                    #         print(np.unique(img))
                    # print(results.keys())

                    save_fast_grid_video(images_dict=results, out_path=os.path.join(save_dir, f'{cnt}_{batch_id}.mp4'))

                #break

        #time_stamps_split = split_func(time_stamps, batch_size)
        #print(time_stamps_split)
        #time_stamps_split = split_func(time_stamps_split, core_cnt)
        # time_stamps_split = [(i, j) for i, j in enumerate(time_stamps_split)]

    #     self.put_dict_in_redis(data=data)
    #
    #
    # def put_dict_in_redis(self, data: dict, redis_key: str = "video_lookup"):
    #     r = redis.Redis(host='localhost', port=6379, db=0)
    #     r.set(redis_key, pickle.dumps(data))

if __name__ == "__main__":
    # Add freeze_support for Windows multiprocessing
    multiprocessing.freeze_support()
    
    StitchVideoFromLk(lookup_path=r"D:\netholabs\temporal_stitching\lk.pk", 
                      save_dir=r'D:\netholabs\temporal_stitching\concat',
                      use_optimized=True,
                      use_disk_fast=False,        # Skip disk extraction for speed
                      use_async_fast=True,        # Use optimized async reading for 120 FPS
                      use_ultra_fast=False,       # Disable ultra-fast to use async-fast
                      batch_size=50,              # Larger batches for better efficiency
                      core_cnt=16)                # Use more cores for 120 FPS




