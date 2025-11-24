"""
Image matching utilities for skin comparison.
Uses color histograms, dominant colors, and perceptual hashing.
"""

import numpy as np
from PIL import Image
import imagehash


# Matching algorithm weights
WEIGHT_DOMINANT_COLORS = 0.60
WEIGHT_COLOR_HISTOGRAM = 0.35
WEIGHT_PERCEPTUAL_HASH = 0.05


def extract_dominant_colors_fast(img_array, n_colors=12):
    """Fast extraction of dominant colors using numpy."""
    # Finer quantization for better color accuracy
    pixels_quantized = (img_array // 16) * 16
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
    """Extract multiple features from an image."""
    try:
        # Load image once
        img = Image.open(image_path)
        
        # Hash for basic structure
        ahash = imagehash.average_hash(img, hash_size=8)
        
        # Work directly with array
        img_array = np.array(img.convert('RGB'))
        
        # Better histogram - more bins for accuracy
        hist, _ = np.histogramdd(
            img_array.reshape(-1, 3),
            bins=(24, 24, 24),
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
    """Calculate a weighted similarity score."""
    
    # 1. Hash comparison
    hash_distance = float(target_features['ahash'] - candidate_features['ahash']) / 64.0
    
    # 2. Chi-squared distance for histograms
    hist1 = target_features['histogram']
    hist2 = candidate_features['histogram']
    hist_distance = np.sum((hist1 - hist2) ** 2 / (hist1 + hist2 + 1e-10)) / 2
    
    # 3. Weighted color palette distance
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
