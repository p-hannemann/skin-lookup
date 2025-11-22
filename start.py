import os
import shutil
from PIL import Image
import numpy as np
import imagehash
from scipy.ndimage import uniform_filter
from scipy.ndimage import variance
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
WEIGHT_DOMINANT_COLORS = 0.55  # Dominant color matching - most important
WEIGHT_COLOR_HISTOGRAM = 0.30  # Color distribution
WEIGHT_PERCEPTUAL_HASH = 0.15  # Structure similarity via hash (less important for render vs flat)

def extract_dominant_colors(img, n_colors=12):
    """Extract the most dominant colors from an image with weighted importance."""
    # Convert to RGB and get pixel data
    img_rgb = img.convert('RGB')
    pixels = np.array(img_rgb).reshape(-1, 3)
    
    # Remove near-transparent pixels if the image has alpha
    if img.mode == 'RGBA':
        alpha = np.array(img)[:, :, 3].flatten()
        pixels = pixels[alpha > 128]  # Only consider non-transparent pixels
    
    if len(pixels) == 0:
        return np.array([[0, 0, 0]]), np.array([1.0])
    
    # Simple color quantization using histogram
    from collections import Counter
    # Finer quantization for better color matching
    pixels_rounded = (pixels // 16) * 16
    color_counts = Counter(map(tuple, pixels_rounded))
    
    # Get top N colors with their weights
    top_colors = color_counts.most_common(n_colors)
    if not top_colors:
        return np.array([[0, 0, 0]]), np.array([1.0])
    
    total_pixels = sum(count for _, count in top_colors)
    colors = np.array([color for color, _ in top_colors])
    weights = np.array([count / total_pixels for _, count in top_colors])
    
    return colors, weights

def color_palette_distance(colors1, weights1, colors2, weights2):
    """Calculate weighted distance between two color palettes."""
    if len(colors1) == 0 or len(colors2) == 0:
        return 1.0
    
    # For each color in palette 1, find best match in palette 2
    # Weight by importance (frequency) of colors
    total_distance = 0.0
    
    for i, c1 in enumerate(colors1):
        # Find closest color in palette 2
        min_dist = float('inf')
        for j, c2 in enumerate(colors2):
            # Calculate color distance in RGB space
            dist = np.sqrt(np.sum((c1.astype(float) - c2.astype(float)) ** 2))
            min_dist = min(min_dist, dist)
        
        # Weight by the importance of this color in palette 1
        total_distance += min_dist * weights1[i]
    
    # Normalize by max possible distance (255*sqrt(3) for RGB)
    normalized_distance = total_distance / 441.67
    
    # Also penalize if palette sizes are very different (indicates different color diversity)
    diversity_penalty = abs(len(colors1) - len(colors2)) / max(len(colors1), len(colors2)) * 0.2
    
    return min(normalized_distance + diversity_penalty, 1.0)

def get_image_features(image_path):
    """Extract multiple features from an image for robust matching."""
    try:
        # Load image
        img = Image.open(image_path).convert('RGBA')
        
        # 1. Average hash - better for different perspectives than pHash
        # Using multiple hash types for robustness
        ahash = imagehash.average_hash(img, hash_size=12)
        phash = imagehash.phash(img, hash_size=12)
        dhash = imagehash.dhash(img, hash_size=12)
        
        # 2. Enhanced color histogram with separate channels
        img_rgb = img.convert('RGB')
        pixels = np.array(img_rgb)
        
        # Calculate per-channel histograms
        hist_r, _ = np.histogram(pixels[:, :, 0].flatten(), bins=32, range=[0, 256])
        hist_g, _ = np.histogram(pixels[:, :, 1].flatten(), bins=32, range=[0, 256])
        hist_b, _ = np.histogram(pixels[:, :, 2].flatten(), bins=32, range=[0, 256])
        
        # Normalize each channel separately
        hist_r = hist_r.astype(np.float64) / (np.sum(hist_r) + 1e-10)
        hist_g = hist_g.astype(np.float64) / (np.sum(hist_g) + 1e-10)
        hist_b = hist_b.astype(np.float64) / (np.sum(hist_b) + 1e-10)
        
        combined_histogram = np.concatenate([hist_r, hist_g, hist_b])
        
        # 3. Dominant colors with weights
        dominant_colors, color_weights = extract_dominant_colors(img, n_colors=12)
        
        return {
            'ahash': ahash,
            'phash': phash,
            'dhash': dhash,
            'histogram': combined_histogram,
            'dominant_colors': dominant_colors,
            'color_weights': color_weights,
            'image': img,
            'path': image_path
        }, None

    except FileNotFoundError:
        return None, "File not found (Path error)"
    except Exception as e:
        return None, f"Error: {type(e).__name__} - {e}"

def calculate_similarity(target_features, candidate_features):
    """Calculate a weighted similarity score between two images.
    Returns a score where LOWER is better (distance metric)."""
    
    # 1. Multiple hash comparison for different aspects
    ahash_distance = float(target_features['ahash'] - candidate_features['ahash']) / 144.0  # 12x12
    phash_distance = float(target_features['phash'] - candidate_features['phash']) / 144.0  # 12x12
    dhash_distance = float(target_features['dhash'] - candidate_features['dhash']) / 144.0  # 12x12
    
    # Average hash distances
    avg_hash_distance = (ahash_distance + phash_distance + dhash_distance) / 3.0
    
    # 2. Enhanced histogram distance (already normalized)
    hist_distance = np.linalg.norm(
        target_features['histogram'] - candidate_features['histogram']
    )
    
    # 3. Weighted dominant color palette distance
    color_distance = color_palette_distance(
        target_features['dominant_colors'],
        target_features['color_weights'],
        candidate_features['dominant_colors'],
        candidate_features['color_weights']
    )
    
    # Calculate weighted combined distance
    combined_distance = (
        WEIGHT_PERCEPTUAL_HASH * avg_hash_distance +
        WEIGHT_COLOR_HISTOGRAM * hist_distance +
        WEIGHT_DOMINANT_COLORS * color_distance
    )
    
    return combined_distance, {
        'hash_dist': avg_hash_distance * 144,  # Convert back for display
        'hist_dist': hist_distance,
        'color_dist': color_distance,
        'combined': combined_distance
    }

def find_closest_match(root_dir, target_file_abs_path, show_top_n=5):
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

    best_match = None
    min_distance = float('inf')
    best_metrics = None
    processed_files = 0
    skipped_files = 0
    top_matches = []  # Store top N matches

    print(f"\nStarting multi-metric comparison...")
    print(f"Weights: Hash={WEIGHT_PERCEPTUAL_HASH}, Histogram={WEIGHT_COLOR_HISTOGRAM}, Colors={WEIGHT_DOMINANT_COLORS}\n")

    # Second pass: Process all files
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


def estimate_runtime_and_confirm(file_count):
    """Estimate runtime and ask for confirmation if it exceeds 5 minutes."""
    # Rough estimate: ~0.02 seconds per file (can vary based on system)
    estimated_seconds = file_count * 0.02
    estimated_minutes = estimated_seconds / 60
    
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
        
        # Count files first for runtime estimation
        print(f"\nCounting files for runtime estimation...")
        file_count = sum(1 for _, _, files in os.walk(SKIN_ROOT_DIR) for _ in files)
        print(f"Found {file_count:,} files to process.")
        
        # Estimate runtime and get confirmation if needed
        estimate_runtime_and_confirm(file_count)

        # Run the search and get the top matches
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