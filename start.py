import os
import shutil
from PIL import Image
import numpy as np
import imagehash
import time
import argparse
import sys

# --- USER CONFIGURATION (Simple Relative Paths) ---

# The folder containing all the searchable skin templates, RELATIVE to the script.
SKIN_ROOT_DIR_RELATIVE = "skins"

# The target render image, RELATIVE to the script.
TARGET_RENDER_FILE = "input.png"

# NEW: The folder where the best match will be copied.
OUTPUT_DIR_RELATIVE = "output"
# ---------------------------------------------------

# --- AUTOMATED PATH FINDING ---
# Get the absolute path of the directory containing the script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Define absolute paths based on the script's location
SKIN_ROOT_DIR = os.path.join(SCRIPT_DIR, SKIN_ROOT_DIR_RELATIVE)
TARGET_FILE_ABS_PATH = os.path.join(SCRIPT_DIR, TARGET_RENDER_FILE)
OUTPUT_DIR_ABS_PATH = os.path.join(SCRIPT_DIR, OUTPUT_DIR_RELATIVE) # <--- NEW
# ------------------------------

# Define the number of bins for the histogram
BINS_PER_CHANNEL = 4
HISTOGRAM_BINS = 256 // BINS_PER_CHANNEL

# Matching algorithm weights (adjust these to tune matching behavior)
WEIGHT_DOMINANT_COLORS = 0.60  # Dominant color matching - most important
WEIGHT_COLOR_HISTOGRAM = 0.35  # Color distribution
WEIGHT_PERCEPTUAL_HASH = 0.05  # Structure similarity via hash (less important for render vs flat)

def extract_dominant_colors_fast(img_array, n_colors=12):
    """Fast extraction of dominant colors using numpy - balanced accuracy."""
    # Finer quantization for better color accuracy
    pixels_quantized = (img_array // 16) * 16  # Better color precision
    pixels_flat = pixels_quantized.reshape(-1, 3)
    
    # Convert to single values for faster unique counting
    pixel_codes = (pixels_flat[:, 0] << 16) | (pixels_flat[:, 1] << 8) | pixels_flat[:, 2]
    
    # Count unique colors
    unique_codes, counts = np.unique(pixel_codes, return_counts=True)
    
    # Get top N
    top_indices = np.argsort(counts)[-n_colors:][::-1]
    top_codes = unique_codes[top_indices]
    top_counts = counts[top_indices]
    
    # Decode back to RGB
    colors = np.zeros((len(top_codes), 3), dtype=np.uint8)
    colors[:, 0] = (top_codes >> 16) & 0xFF
    colors[:, 1] = (top_codes >> 8) & 0xFF
    colors[:, 2] = top_codes & 0xFF
    
    weights = top_counts / top_counts.sum()
    
    return colors, weights

def color_palette_distance_fast(colors1, weights1, colors2, weights2):
    """Fast weighted distance between color palettes using vectorized operations."""
    if len(colors1) == 0 or len(colors2) == 0:
        return 1.0
    
    # Vectorized distance calculation
    # Compute all pairwise distances at once
    c1 = colors1.astype(float)
    c2 = colors2.astype(float)
    
    # Broadcasting: (n1, 1, 3) - (1, n2, 3) = (n1, n2, 3)
    diffs = c1[:, np.newaxis, :] - c2[np.newaxis, :, :]
    distances = np.sqrt(np.sum(diffs ** 2, axis=2))
    
    # For each color in palette 1, find minimum distance to palette 2
    min_distances = np.min(distances, axis=1)
    
    # Weight by color importance
    weighted_distance = np.sum(min_distances * weights1)
    
    # Normalize
    return min(weighted_distance / 441.67, 1.0)

def get_image_features(image_path):
    """Extract multiple features from an image - balanced speed and accuracy."""
    try:
        # Load image once
        img = Image.open(image_path)
        
        # Hash for basic structure (keep it simple)
        ahash = imagehash.average_hash(img, hash_size=8)
        
        # Work directly with array
        img_array = np.array(img.convert('RGB'))
        
        # Better histogram - more bins for accuracy but still optimized
        hist, _ = np.histogramdd(
            img_array.reshape(-1, 3),
            bins=(24, 24, 24),  # Increased from 16 for better color distinction
            range=[(0, 256), (0, 256), (0, 256)]
        )
        
        # Flatten and normalize
        hist = hist.flatten()
        hist = hist / (hist.sum() + 1e-10)
        
        # More dominant colors for better matching
        dominant_colors, color_weights = extract_dominant_colors_fast(img_array, n_colors=12)
        
        return {
            'ahash': ahash,
            'histogram': hist,
            'dominant_colors': dominant_colors,
            'color_weights': color_weights,
            'path': image_path
        }, None

    except FileNotFoundError:
        return None, "File not found"
    except Exception as e:
        return None, f"Error: {type(e).__name__}"

def calculate_similarity(target_features, candidate_features):
    """Calculate a weighted similarity score - balanced speed and accuracy."""
    
    # 1. Single hash comparison
    hash_distance = float(target_features['ahash'] - candidate_features['ahash']) / 64.0  # 8x8
    
    # 2. Chi-squared distance for histograms (better for color matching than euclidean)
    hist1 = target_features['histogram']
    hist2 = candidate_features['histogram']
    hist_distance = np.sum((hist1 - hist2) ** 2 / (hist1 + hist2 + 1e-10)) / 2
    
    # 3. Weighted color palette distance with better normalization
    color_distance = color_palette_distance_fast(
        target_features['dominant_colors'],
        target_features['color_weights'],
        candidate_features['dominant_colors'],
        candidate_features['color_weights']
    )
    
    # Calculate weighted combined distance
    combined_distance = (
        WEIGHT_PERCEPTUAL_HASH * hash_distance +
        WEIGHT_COLOR_HISTOGRAM * hist_distance +
        WEIGHT_DOMINANT_COLORS * color_distance
    )
    
    return combined_distance, {
        'hash_dist': hash_distance * 64,
        'hist_dist': hist_distance,
        'color_dist': color_distance,
        'combined': combined_distance
    }

def find_closest_match(root_dir, target_file_abs_path, show_top_n=5, skip_confirmation=False):
    """Recursively searches for the best match using multiple similarity metrics."""

    target_features, error = get_image_features(target_file_abs_path)
    if target_features is None:
        print(f"Fatal Error: Could not extract features for {TARGET_RENDER_FILE}. Reason: {error}")
        return None

    # First pass: Count all files
    print(f"\nCounting files in directory...")
    all_files = []
    for root, _, files in os.walk(root_dir):
        for file_name in files:
            all_files.append(os.path.join(root, file_name))
    
    total_files = len(all_files)
    print(f"Found {total_files:,} files to process.")
    
    # Estimate runtime using first file as benchmark (unless skipped)
    if not skip_confirmation and total_files > 0:
        estimate_runtime_and_confirm(target_features, all_files[0], total_files)

    best_match = None
    min_distance = float('inf')
    best_metrics = None
    processed_files = 0
    skipped_files = 0
    top_matches = []  # Store top N matches

    print(f"\nStarting optimized comparison...")
    print(f"Weights: Hash={WEIGHT_PERCEPTUAL_HASH}, Histogram={WEIGHT_COLOR_HISTOGRAM}, Colors={WEIGHT_DOMINANT_COLORS}\n")

    # Process sequentially with optimized algorithms
    comparison_start_time = time.time()
    for idx, file_path in enumerate(all_files, 1):
        candidate_features, error = get_image_features(file_path)

        if candidate_features is not None:
            processed_files += 1
            distance, metrics = calculate_similarity(target_features, candidate_features)

            # Keep track of top N matches
            top_matches.append((distance, file_path, metrics))
            top_matches.sort(key=lambda x: x[0])
            top_matches = top_matches[:show_top_n]

            if distance < min_distance:
                min_distance = distance
                best_match = file_path
                best_metrics = metrics
        else:
            skipped_files += 1
        
        # Update progress bar
        if idx % 100 == 0 or idx == total_files:
            percent = (idx / total_files) * 100
            bar_length = 50
            filled = int(bar_length * idx / total_files)
            bar = '█' * filled + '░' * (bar_length - filled)
            
            # Calculate ETA
            elapsed = time.time() - comparison_start_time
            if idx > 0:
                avg_time_per_file = elapsed / idx
                remaining_files = total_files - idx
                eta_seconds = avg_time_per_file * remaining_files
                
                if eta_seconds < 60:
                    eta_str = f"{int(eta_seconds)}s"
                else:
                    eta_minutes = int(eta_seconds // 60)
                    eta_secs = int(eta_seconds % 60)
                    eta_str = f"{eta_minutes}m {eta_secs}s"
            else:
                eta_str = "calculating..."
            
            print(f"\r[{bar}] {percent:.1f}% ({idx}/{total_files}) | Processed: {processed_files} | Skipped: {skipped_files} | ETA: {eta_str}", end='', flush=True)

    print("\n\n" + "="*70)
    print("--- SEARCH RESULTS ---")
    print("="*70)
    print(f"Total files: {total_files}")
    print(f"Successfully processed: {processed_files}")
    print(f"Skipped (errors): {skipped_files}\n")

    if best_match:
        print(f"🏆 BEST MATCH: {os.path.basename(best_match)}")
        print(f"   Path: {best_match}")
        print(f"   Combined Distance: {best_metrics['combined']:.6f} (Lower is better)")
        print(f"   - Hash Distance: {best_metrics['hash_dist']:.1f} bits different")
        print(f"   - Histogram Distance: {best_metrics['hist_dist']:.6f}")
        print(f"   - Color Palette Distance: {best_metrics['color_dist']:.4f}")
        
        if show_top_n > 1 and len(top_matches) > 1:
            print(f"\n📊 Top {len(top_matches)} Matches:")
            for i, (dist, path, metrics) in enumerate(top_matches, 1):
                print(f"\n{i}. {os.path.basename(path)}")
                print(f"   Combined: {metrics['combined']:.6f} | "
                      f"Hash: {metrics['hash_dist']:.1f} | "
                      f"Colors: {metrics['color_dist']:.4f}")
        
        print("="*70)
        return top_matches  # Return all top matches instead of just best
    else:
        print(f"No suitable files were successfully processed in the directory: {root_dir}")
        return None


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Minecraft Skin Matcher - Find matching skin files for a 3D rendered skin image.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python start.py
      Run with default settings (searches ./skins directory)
  
  python start.py -p "C:\\Users\\Username\\AppData\\Roaming\\.minecraft\\assets\\skins"
      Search a custom directory for skin matches
  
  python start.py -p "D:\\MinecraftSkins" -i "my_render.png"
      Search custom directory with a different input image

Note: The script compares input.png (or specified image) against all skin files
      in the search directory and copies the top 5 matches to ./output/
        '''
    )
    
    parser.add_argument(
        '-p', '--path',
        type=str,
        default=None,
        metavar='PATH',
        help='Absolute path to the directory containing skin files to search. If not specified, uses ./skins relative to script location.'
    )
    
    parser.add_argument(
        '-i', '--input',
        type=str,
        default='input.png',
        metavar='FILE',
        help='Input render image filename (default: input.png)'
    )
    
    return parser.parse_args()


def estimate_runtime_and_confirm(target_features, test_file_path, file_count):
    """Estimate runtime by benchmarking against a test file and ask for confirmation if it exceeds 5 minutes."""
    print("   Running benchmark comparison...")
    
    # Time a single comparison
    benchmark_start = time.time()
    test_features, error = get_image_features(test_file_path)
    
    if test_features is not None:
        calculate_similarity(target_features, test_features)
        time_per_file = time.time() - benchmark_start
    else:
        # Fallback to rough estimate if benchmark fails
        time_per_file = 0.02
        print("   (Benchmark failed, using estimated time)")
    
    estimated_seconds = file_count * time_per_file
    estimated_minutes = estimated_seconds / 60
    
    print(f"   Benchmark: {time_per_file*1000:.1f}ms per file")
    
    if estimated_minutes > 5:
        hours = int(estimated_minutes // 60)
        minutes = int(estimated_minutes % 60)
        
        if hours > 0:
            time_str = f"{hours}h {minutes}m"
        else:
            time_str = f"{int(estimated_minutes)}m"
        
        print(f"\n⚠️  WARNING: Expected runtime is approximately {time_str}")
        print(f"   Processing {file_count:,} files may take a while.")
        
        response = input("   Do you want to continue? [y/N]: ").strip().lower()
        
        if response not in ['y', 'yes']:
            print("\n❌ Operation cancelled by user.")
            sys.exit(0)
        print()
    else:
        print(f"   Estimated runtime: {int(estimated_seconds)}s\n")


if __name__ == "__main__":
    # Parse command line arguments
    args = parse_arguments()
    
    # Start timing
    start_time = time.time()
    
    # Update paths based on arguments
    if args.path:
        SKIN_ROOT_DIR = os.path.abspath(args.path)
        if not os.path.exists(SKIN_ROOT_DIR):
            print(f"❌ ERROR: Specified path does not exist: {SKIN_ROOT_DIR}")
            sys.exit(1)
        if not os.path.isdir(SKIN_ROOT_DIR):
            print(f"❌ ERROR: Specified path is not a directory: {SKIN_ROOT_DIR}")
            sys.exit(1)
    
    # Update input file if specified
    if args.input != 'input.png':
        TARGET_FILE_ABS_PATH = os.path.join(SCRIPT_DIR, args.input)

    # 1. Prepare Output Directory - Clear existing files and create if needed
    if os.path.exists(OUTPUT_DIR_ABS_PATH):
        # Clear all existing files in the output directory
        try:
            for filename in os.listdir(OUTPUT_DIR_ABS_PATH):
                file_path = os.path.join(OUTPUT_DIR_ABS_PATH, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            print(f"Cleared existing files from output directory: {OUTPUT_DIR_RELATIVE}")
        except Exception as e:
            print(f"*** ERROR: Could not clear output directory. {e} ***")
            exit()
    else:
        # Create the output directory if it doesn't exist
        try:
            os.makedirs(OUTPUT_DIR_ABS_PATH)
            print(f"Created output directory: {OUTPUT_DIR_RELATIVE}")
        except Exception as e:
            print(f"*** ERROR: Could not create output directory. {e} ***")
            exit()

    # 2. Check Input Files
    if not os.path.exists(TARGET_FILE_ABS_PATH):
        print(f"*** ERROR: The target render file '{TARGET_RENDER_FILE}' was not found. ***")
        print(f"Please ensure your 3D render is renamed to '{TARGET_RENDER_FILE}' and is located at: {SCRIPT_DIR}")

    elif not os.path.exists(SKIN_ROOT_DIR):
        print(f"*** ERROR: The calculated skin search folder does not exist. ***")
        print(f"Expected Path: {SKIN_ROOT_DIR}")
        print(f"ACTION: Please create a folder named '{SKIN_ROOT_DIR_RELATIVE}' in the same directory as this script.")

    else:
        print(f"Starting search recursively from: {SKIN_ROOT_DIR}")

        # Run the search and get the top matches (runtime estimation happens inside)
        top_matches = find_closest_match(SKIN_ROOT_DIR, TARGET_FILE_ABS_PATH, show_top_n=5)

        # 3. Copy all top matches if found
        if top_matches:
            print(f"\n{'='*70}")
            print("Copying top {0} matches to output directory...".format(len(top_matches)))
            print(f"{'='*70}\n")
            
            for i, (distance, match_path, metrics) in enumerate(top_matches, 1):
                # The file name is the hash (e.g., '00022cceee157dfc...')
                source_filename = os.path.basename(match_path)

                # Destination filename: rank_originalname.png
                dest_filename = f"match_{i}_{source_filename}.png"
                dest_file_abs_path = os.path.join(OUTPUT_DIR_ABS_PATH, dest_filename)

                try:
                    # copy2 preserves metadata like modification times
                    shutil.copy2(match_path, dest_file_abs_path)
                    print(f"✅ Match #{i}: {dest_filename}")
                    print(f"   Distance: {distance:.6f} | Hash: {metrics['hash_dist']:.1f} | Colors: {metrics['color_dist']:.4f}")
                except Exception as e:
                    print(f"❌ ERROR copying match #{i}: {e}")
            
            print(f"\n{'='*70}")
            print(f"✅ Copied {len(top_matches)} matches to: {OUTPUT_DIR_ABS_PATH}")
            print(f"{'='*70}")
    
    # Calculate and display total time
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    if elapsed_time < 60:
        time_str = f"{elapsed_time:.2f} seconds"
    elif elapsed_time < 3600:
        minutes = int(elapsed_time // 60)
        seconds = elapsed_time % 60
        time_str = f"{minutes}m {seconds:.1f}s"
    else:
        hours = int(elapsed_time // 3600)
        minutes = int((elapsed_time % 3600) // 60)
        time_str = f"{hours}h {minutes}m"
    
    print(f"\n⏱️  Total execution time: {time_str}")