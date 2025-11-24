"""
File operations for skin matching and copying.
"""

import os
from pathlib import Path
import shutil
import time
from .image_matcher import get_image_features, calculate_similarity


def collect_all_files(root_dir):
    """Recursively collect all files in a directory."""
    all_files = []
    for root, _, files in os.walk(root_dir):
        for file_name in files:
            all_files.append(os.path.join(root, file_name))
    return all_files


def find_matching_skins(target_image_path, search_directory, top_n=5, algorithm="balanced", progress_callback=None, cancel_check=None):
    """
    Find the top N matching skins for a target image.
    
    Args:
        target_image_path: Path to the input image to match
        search_directory: Directory containing skin files to search
        top_n: Number of top matches to return
        algorithm: Matching algorithm to use ("balanced", "skin_optimized", "deep_features", "color_distribution", "fast")
        progress_callback: Optional callback function(current, total, message)
        cancel_check: Optional callback function that returns True if cancellation is requested
        
    Returns:
        List of tuples: (distance, file_path, metrics)
    """
    
    # Extract features from target image
    print(f"[DEBUG] Extracting features from target image: {target_image_path}")
    if progress_callback:
        progress_callback(0, 0, "Extracting features from target image...")
    
    feature_start = time.time()
    target_features, error = get_image_features(target_image_path, algorithm=algorithm)
    feature_time = time.time() - feature_start
    
    print(f"[DEBUG] Target features extraction complete in {feature_time:.2f}s. Success: {target_features is not None}")
    if target_features is None:
        return None, f"Could not extract features: {error}"
    
    # Collect all files
    if progress_callback:
        progress_callback(0, 0, "Counting files...")
    
    all_files = collect_all_files(search_directory)
    total_files = len(all_files)
    
    if total_files == 0:
        return None, "No files found in search directory"
    
    if progress_callback:
        progress_callback(0, total_files, f"Found {total_files:,} files")
    
    # Process files and find matches
    top_matches = []
    processed_files = 0
    skipped_files = 0
    start_time = time.time()
    
    for idx, file_path in enumerate(all_files, 1):
        # Check for cancellation
        if cancel_check and cancel_check():
            return top_matches if top_matches else None, "Cancelled by user"
        
        candidate_features, error = get_image_features(file_path, algorithm=algorithm)
        
        if candidate_features is not None:
            processed_files += 1
            distance, metrics = calculate_similarity(target_features, candidate_features, algorithm=algorithm)
            
            # Keep track of top N matches
            top_matches.append((distance, file_path, metrics))
            top_matches.sort(key=lambda x: x[0])
            top_matches = top_matches[:top_n]
        else:
            skipped_files += 1
        
        # Progress update - show every 10 files for AI algorithms, every 100 for others
        update_interval = 10 if algorithm in ["ai_perceptual", "ai_mobile"] else 100
        if progress_callback and (idx % update_interval == 0 or idx == total_files):
            elapsed = time.time() - start_time
            if idx > 0:
                avg_time = elapsed / idx
                files_per_sec = idx / elapsed
                eta_seconds = avg_time * (total_files - idx)
                eta_minutes = int(eta_seconds / 60)
                eta_str = f"{eta_minutes}m {int(eta_seconds % 60)}s" if eta_minutes > 0 else f"{int(eta_seconds)}s"
                progress_callback(idx, total_files, f"Processing ({files_per_sec:.1f} files/sec)... ETA: {eta_str}")
    
    return top_matches, None


def copy_skin_files(matches, output_directory, clear_existing=True):
    """
    Copy matched skin files to output directory.
    
    Args:
        matches: List of (distance, file_path, metrics) tuples
        output_directory: Directory to copy files to
        clear_existing: Whether to clear existing files first
        
    Returns:
        List of successfully copied files
    """
    
    # Create output directory
    os.makedirs(output_directory, exist_ok=True)
    
    # Clear existing files if requested
    if clear_existing:
        for filename in os.listdir(output_directory):
            file_path = os.path.join(output_directory, filename)
            if os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
    
    # Copy matched files
    copied_files = []
    for i, (distance, match_path, metrics) in enumerate(matches, 1):
        source_filename = os.path.basename(match_path)
        dest_filename = f"match_{i}_{source_filename}.png"
        dest_path = os.path.join(output_directory, dest_filename)
        
        try:
            shutil.copy2(match_path, dest_path)
            copied_files.append((dest_path, distance, metrics))
        except Exception as e:
            print(f"Error copying {source_filename}: {e}")
    
    return copied_files
