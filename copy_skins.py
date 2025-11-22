import os
import shutil
from pathlib import Path


def copy_and_rename_to_png(input_dir):
    """
    Copy a directory recursively and add .png extension to all files in the output.
    
    Args:
        input_dir: Source directory path
    """
    input_path = Path(input_dir)
    output_dir = f"{input_dir}_png"
    output_path = Path(output_dir)
    
    # Check if input directory exists
    if not input_path.exists():
        print(f"Error: Input directory '{input_dir}' does not exist.")
        return
    
    if not input_path.is_dir():
        print(f"Error: '{input_dir}' is not a directory.")
        return
    
    # Create output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Walk through the input directory
    for root, dirs, files in os.walk(input_path):
        # Calculate relative path from input directory
        rel_path = Path(root).relative_to(input_path)
        current_output_dir = output_path / rel_path
        
        # Create subdirectories in output
        current_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy and rename files
        for file in files:
            src_file = Path(root) / file
            dst_file = current_output_dir / (file + '.png')
            
            try:
                shutil.copy2(src_file, dst_file)
                print(f"Copied: {src_file} -> {dst_file}")
            except Exception as e:
                print(f"Error copying {src_file}: {e}")
    
    print(f"\nCompleted! Files copied from '{input_dir}' to '{output_dir}' with .png extension added.")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python copy_skins.py <input_directory>")
        print("Example: python copy_skins.py skins")
        sys.exit(1)
    
    input_directory = sys.argv[1]
    
    copy_and_rename_to_png(input_directory)
