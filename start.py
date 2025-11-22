import os
import shutil
from PIL import Image
import numpy as np
import imagehash
from scipy.ndimage import uniform_filter
from scipy.ndimage import variance

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
WEIGHT_PERCEPTUAL_HASH = 0.40  # Structure similarity via hash
WEIGHT_COLOR_HISTOGRAM = 0.30  # Color distribution
WEIGHT_SSIM = 0.30             # Structural similarity

def ssim(img1, img2):
    """Calculate Structural Similarity Index between two images."""
    # Convert images to grayscale numpy arrays
    arr1 = np.array(img1.convert('L'), dtype=np.float64)
    arr2 = np.array(img2.convert('L'), dtype=np.float64)
    
    # Resize to same dimensions if needed
    if arr1.shape != arr2.shape:
        img2_resized = img2.resize(img1.size, Image.LANCZOS)
        arr2 = np.array(img2_resized.convert('L'), dtype=np.float64)
    
    # Constants for stability
    C1 = (0.01 * 255) ** 2
    C2 = (0.03 * 255) ** 2
    
    # Calculate means
    mu1 = uniform_filter(arr1, size=11)
    mu2 = uniform_filter(arr2, size=11)
    
    # Calculate variances and covariance
    mu1_sq = mu1 ** 2
    mu2_sq = mu2 ** 2
    mu1_mu2 = mu1 * mu2
    
    sigma1_sq = uniform_filter(arr1 ** 2, size=11) - mu1_sq
    sigma2_sq = uniform_filter(arr2 ** 2, size=11) - mu2_sq
    sigma12 = uniform_filter(arr1 * arr2, size=11) - mu1_mu2
    
    # Calculate SSIM
    ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / \
               ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))
    
    return np.mean(ssim_map)

def get_image_features(image_path):
    """Extract multiple features from an image for robust matching."""
    try:
        # Load image
        img = Image.open(image_path).convert('RGBA')
        
        # 1. Perceptual hash (captures structure)
        phash = imagehash.phash(img, hash_size=16)
        
        # 2. Color histogram (captures color distribution)
        img_rgb = img.convert('RGB')
        histogram, _ = np.histogram(
            np.array(img_rgb).flatten(),
            bins=HISTOGRAM_BINS * 3,
            range=[0, 256]
        )
        normalized_histogram = histogram.astype(np.float64) / np.sum(histogram)
        
        return {
            'phash': phash,
            'histogram': normalized_histogram,
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
    
    # 1. Perceptual hash distance (0 = identical, higher = more different)
    phash_distance = float(target_features['phash'] - candidate_features['phash'])
    # Normalize to 0-1 range (max hamming distance for 16x16 hash is 256)
    phash_distance_norm = phash_distance / 256.0
    
    # 2. Histogram distance (0 = identical, higher = more different)
    hist_distance = np.linalg.norm(
        target_features['histogram'] - candidate_features['histogram']
    )
    
    # 3. SSIM (returns 0-1 where 1 is identical, so we invert it)
    ssim_value = ssim(target_features['image'], candidate_features['image'])
    ssim_distance = 1.0 - ssim_value  # Convert to distance metric
    
    # Calculate weighted combined distance
    combined_distance = (
        WEIGHT_PERCEPTUAL_HASH * phash_distance_norm +
        WEIGHT_COLOR_HISTOGRAM * hist_distance +
        WEIGHT_SSIM * ssim_distance
    )
    
    return combined_distance, {
        'phash_dist': phash_distance,
        'hist_dist': hist_distance,
        'ssim_value': ssim_value,
        'combined': combined_distance
    }

def find_closest_match(root_dir, target_file_abs_path, show_top_n=5):
    """Recursively searches for the best match using multiple similarity metrics."""

    target_features, error = get_image_features(target_file_abs_path)
    if target_features is None:
        print(f"Fatal Error: Could not extract features for {TARGET_RENDER_FILE}. Reason: {error}")
        return None

    best_match = None
    min_distance = float('inf')
    best_metrics = None
    total_files = 0
    processed_files = 0
    top_matches = []  # Store top N matches

    print(f"\nStarting multi-metric comparison...")
    print(f"Weights: pHash={WEIGHT_PERCEPTUAL_HASH}, Histogram={WEIGHT_COLOR_HISTOGRAM}, SSIM={WEIGHT_SSIM}\n")

    # Recursively search the root directory
    for root, _, files in os.walk(root_dir):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            total_files += 1

            candidate_features, error = get_image_features(file_path)

            if candidate_features is not None:
                processed_files += 1

                if processed_files % 1000 == 0:
                    print(f"Progress: Processed {processed_files}/{total_files} files...")

                distance, metrics = calculate_similarity(target_features, candidate_features)

                # Keep track of top N matches
                top_matches.append((distance, file_path, metrics))
                top_matches.sort(key=lambda x: x[0])
                top_matches = top_matches[:show_top_n]

                if distance < min_distance:
                    min_distance = distance
                    best_match = file_path
                    best_metrics = metrics

    print("\n" + "="*70)
    print("--- SEARCH RESULTS ---")
    print("="*70)
    print(f"Examined {total_files} files.")
    print(f"Successfully processed {processed_files} files.\n")

    if best_match:
        print(f"🏆 BEST MATCH: {os.path.basename(best_match)}")
        print(f"   Path: {best_match}")
        print(f"   Combined Distance: {best_metrics['combined']:.6f} (Lower is better)")
        print(f"   - Perceptual Hash Distance: {best_metrics['phash_dist']:.1f} bits different")
        print(f"   - Histogram Distance: {best_metrics['hist_dist']:.6f}")
        print(f"   - SSIM Score: {best_metrics['ssim_value']:.4f} (1.0 = identical)")
        
        if show_top_n > 1 and len(top_matches) > 1:
            print(f"\n📊 Top {len(top_matches)} Matches:")
            for i, (dist, path, metrics) in enumerate(top_matches, 1):
                print(f"\n{i}. {os.path.basename(path)}")
                print(f"   Combined: {metrics['combined']:.6f} | "
                      f"pHash: {metrics['phash_dist']:.1f} | "
                      f"SSIM: {metrics['ssim_value']:.4f}")
        
        print("="*70)
        return best_match
    else:
        print(f"No suitable files were successfully processed in the directory: {root_dir}")
        return None


if __name__ == "__main__":

    # 1. Create Output Directory (NEW)
    if not os.path.exists(OUTPUT_DIR_ABS_PATH):
        try:
            os.makedirs(OUTPUT_DIR_ABS_PATH)
            print(f"Created output directory: **{OUTPUT_DIR_RELATIVE}**")
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

        # Run the search and get the path of the best match
        best_match_path = find_closest_match(SKIN_ROOT_DIR, TARGET_FILE_ABS_PATH)

        # 3. Copy the file if a match was found (NEW)
        if best_match_path:
            # The file name is the hash (e.g., '00022cceee157dfc...')
            source_filename = os.path.basename(best_match_path)

            # Destination filename will be the hash + ".png"
            dest_filename = f"{source_filename}.png"
            dest_file_abs_path = os.path.join(OUTPUT_DIR_ABS_PATH, dest_filename)

            try:
                # copy2 preserves metadata like modification times
                shutil.copy2(best_match_path, dest_file_abs_path)
                print(f"\n[OUTPUT] Copied match to: **{dest_file_abs_path}**")
            except Exception as e:
                print(f"\n*** ERROR: Failed to copy the matched file. {e} ***")