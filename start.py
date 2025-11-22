import os
import shutil # <--- NEW: Imported for file copying
from PIL import Image
import numpy as np

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

def get_color_signature(image_path):
    """Calculates a normalized color histogram (the signature) for an image."""
    try:
        # Load image and convert to RGB
        img = Image.open(image_path).convert('RGB')

        # Calculate the histogram
        histogram, _ = np.histogram(
            np.array(img).flatten(),
            bins=HISTOGRAM_BINS * 3,
            range=[0, 256]
        )

        # Normalize the histogram
        normalized_histogram = histogram.astype(np.float64) / np.sum(histogram)

        return normalized_histogram, None

    except FileNotFoundError:
        return None, "File not found (Path error)"

    except Exception as e:
        return None, f"PIL Error: {type(e).__name__} - {e}"

def find_closest_match(root_dir, target_file_abs_path):
    """Recursively searches for the best histogram match and returns the path."""

    target_signature, error = get_color_signature(target_file_abs_path)
    if target_signature is None:
        print(f"Fatal Error: Could not get signature for {TARGET_RENDER_FILE}. Reason: {error}")
        # Return None on error so the main block knows not to copy a file
        return None

    best_match = None
    min_distance = float('inf')
    total_files = 0
    processed_files = 0

    # Recursively search the root directory
    for root, _, files in os.walk(root_dir):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            total_files += 1

            skin_signature, error = get_color_signature(file_path)

            if skin_signature is not None:
                processed_files += 1

                # --- VERBOSE SUCCESS OUTPUT ---
                print(f"[SUCCESS] Processed: {file_path}")
                # ------------------------------

                distance = np.linalg.norm(target_signature - skin_signature)

                if distance < min_distance:
                    min_distance = distance
                    best_match = file_path
            else:
                # --- VERBOSE SKIP OUTPUT ---
                print(f"[SKIPPED] File: {file_path} | Reason: {error}")
                # ---------------------------

    print("\n--- Search Results ---")
    print(f"Search complete. Examined {total_files} files.")
    print(f"Successfully processed {processed_files} files (Interpreted as .png).")

    if best_match:
        print(f"The closest **Color Histogram Match** found for '{TARGET_RENDER_FILE}' is:")
        print(f"MATCH: **{best_match}**")
        print(f"DISTANCE: {min_distance:.4f} (Lower is better)")
        print("----------------------")
        return best_match # <--- NEW: Return the path
    else:
        print(f"No suitable files were successfully processed in the directory: {root_dir}")
        return None # <--- NEW: Return None if no match found


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