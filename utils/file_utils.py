"""
File copying utilities for skin files.
"""

import os
import shutil
from pathlib import Path


def copy_and_rename_to_png(input_dir, output_dir=None, merge_files=False, log_callback=None, cancel_check=None):
    """
    Copy a directory recursively and add .png extension to all files in the output.
    
    Args:
        input_dir: Source directory path
        output_dir: Destination directory path (default: input_dir_png)
        merge_files: Whether to merge all files into single folder
        log_callback: Optional function to call with log messages
        cancel_check: Optional function that returns True if should cancel
        
    Returns:
        bool: True if successful, False otherwise
    """
    def log(message):
        if log_callback:
            log_callback(message)
        else:
            print(message)
    
    input_path = Path(input_dir)
    if output_dir is None:
        output_dir = f"{input_dir}_png"
    output_path = Path(output_dir)
    
    # Check if input directory exists
    if not input_path.exists():
        log(f"Error: Input directory '{input_dir}' does not exist.")
        return False
    
    if not input_path.is_dir():
        log(f"Error: '{input_dir}' is not a directory.")
        return False
    
    # Create output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)
    
    if merge_files:
        log("Merge mode: All files will be copied to a single folder.\n")
    
    file_count = 0
    file_name_counter = {}  # Track duplicate filenames when merging
    
    # Walk through the input directory
    for root, dirs, files in os.walk(input_path):
        # Check for cancellation
        if cancel_check and cancel_check():
            return False
        
        if merge_files:
            # Merge mode: all files go to root output directory
            current_output_dir = output_path
        else:
            # Normal mode: preserve directory structure
            rel_path = Path(root).relative_to(input_path)
            current_output_dir = output_path / rel_path
            # Create subdirectories in output
            current_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy and rename files
        for file in files:
            # Check for cancellation before each file
            if cancel_check and cancel_check():
                return False
            
            src_file = Path(root) / file
            
            if merge_files:
                # Handle potential duplicate filenames
                base_name = file
                if base_name in file_name_counter:
                    file_name_counter[base_name] += 1
                    # Add counter before .png extension
                    dst_file = current_output_dir / f"{base_name}_{file_name_counter[base_name]}.png"
                else:
                    file_name_counter[base_name] = 0
                    dst_file = current_output_dir / (base_name + '.png')
            else:
                dst_file = current_output_dir / (file + '.png')
            
            try:
                shutil.copy2(src_file, dst_file)
                file_count += 1
                if file_count % 10 == 0:  # Log every 10 files to avoid spam
                    log(f"Copied {file_count} files...")
            except Exception as e:
                log(f"Error copying {src_file}: {e}")
    
    if not (cancel_check and cancel_check()):
        mode_text = " (merged)" if merge_files else ""
        log(f"\nCompleted! {file_count} files copied{mode_text} from '{input_dir}' to '{output_dir}' with .png extension added.")
    return True
