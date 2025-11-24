"""
Image matching utilities for skin comparison.
Uses multiple algorithms for different matching scenarios.
"""

import numpy as np
from PIL import Image, ImageFilter
import imagehash

# Optional imports for advanced algorithms
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    from skimage.metrics import structural_similarity as ssim
    SSIM_AVAILABLE = True
except ImportError:
    SSIM_AVAILABLE = False


# Algorithm weight configurations
ALGORITHM_WEIGHTS = {
    "balanced": {
        "dominant_colors": 0.60,
        "color_histogram": 0.35,
        "perceptual_hash": 0.05
    },
    "skin_optimized": {
        "texture_pattern": 0.40,
        "dominant_colors": 0.35,
        "dimension_match": 0.15,
        "color_histogram": 0.10
    },
    "deep_features": {
        "edge_similarity": 0.50,
        "ssim": 0.30,
        "dominant_colors": 0.20
    },
    "color_distribution": {
        "color_histogram": 0.70,
        "dominant_colors": 0.30
    },
    "fast": {
        "color_histogram": 0.80,
        "perceptual_hash": 0.20
    }
}


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


def is_minecraft_skin_texture(img):
    """Check if image dimensions match Minecraft skin format (64x64 or 64x32)."""
    width, height = img.size
    return (width == 64 and height == 64) or (width == 64 and height == 32)


def extract_texture_pattern(img_array):
    """Extract texture pattern features for skin detection."""
    # Calculate variance in small blocks (8x8)
    h, w = img_array.shape[:2]
    if h < 8 or w < 8:
        return np.array([0])
    
    block_size = min(8, h // 8, w // 8)
    variances = []
    
    for i in range(0, h - block_size, block_size):
        for j in range(0, w - block_size, block_size):
            block = img_array[i:i+block_size, j:j+block_size]
            variances.append(np.var(block))
    
    return np.array(variances) if variances else np.array([0])


def extract_edge_features(img):
    """Extract edge detection features."""
    if not CV2_AVAILABLE:
        # Fallback: use PIL edge detection
        gray = img.convert('L')
        edges_pil = gray.filter(ImageFilter.FIND_EDGES)
        edges = np.array(edges_pil)
        edge_density = np.sum(edges > 50) / edges.size
        return edges, edge_density
    
    # Convert to grayscale
    gray = img.convert('L')
    gray_array = np.array(gray)
    
    # Apply edge detection
    edges = cv2.Canny(gray_array, 50, 150)
    
    # Calculate edge density
    edge_density = np.sum(edges > 0) / edges.size
    
    return edges, edge_density


def calculate_ssim_similarity(img1, img2):
    """Calculate structural similarity between two images."""
    if not SSIM_AVAILABLE:
        # Fallback: use simple pixel-wise comparison
        try:
            target_size = (128, 128)
            img1_resized = img1.resize(target_size, Image.Resampling.LANCZOS)
            img2_resized = img2.resize(target_size, Image.Resampling.LANCZOS)
            
            arr1 = np.array(img1_resized.convert('L')).astype(float)
            arr2 = np.array(img2_resized.convert('L')).astype(float)
            
            # Mean squared error as distance
            mse = np.mean((arr1 - arr2) ** 2)
            return min(mse / 10000.0, 1.0)
        except:
            return 1.0
    
    try:
        # Resize to same dimensions for comparison
        target_size = (128, 128)
        img1_resized = img1.resize(target_size, Image.Resampling.LANCZOS)
        img2_resized = img2.resize(target_size, Image.Resampling.LANCZOS)
        
        # Convert to grayscale arrays
        img1_gray = np.array(img1_resized.convert('L'))
        img2_gray = np.array(img2_resized.convert('L'))
        
        # Calculate SSIM
        similarity = ssim(img1_gray, img2_gray)
        return 1.0 - similarity  # Convert to distance
    except:
        return 1.0


def get_image_features(image_path, algorithm="balanced"):
    """Extract multiple features from an image based on algorithm."""
    try:
        # Load image once
        img = Image.open(image_path)
        img_array = np.array(img.convert('RGB'))
        
        features = {
            'algorithm': algorithm,
            'path': image_path
        }
        
        # Common features for most algorithms
        if algorithm in ["balanced", "skin_optimized", "fast"]:
            features['ahash'] = imagehash.average_hash(img, hash_size=8)
        
        if algorithm in ["balanced", "skin_optimized", "color_distribution", "deep_features", "fast"]:
            dominant_colors, color_weights = extract_dominant_colors_fast(img_array, n_colors=12)
            features['dominant_colors'] = dominant_colors
            features['color_weights'] = color_weights
        
        if algorithm in ["balanced", "color_distribution", "fast"]:
            # Histogram bins based on algorithm
            bins = 16 if algorithm == "fast" else 24
            hist, _ = np.histogramdd(
                img_array.reshape(-1, 3),
                bins=(bins, bins, bins),
                range=[(0, 256), (0, 256), (0, 256)]
            )
            hist = hist.flatten()
            hist = hist / (hist.sum() + 1e-10)
            features['histogram'] = hist
        
        # Skin-optimized specific features
        if algorithm == "skin_optimized":
            features['is_skin_texture'] = is_minecraft_skin_texture(img)
            features['texture_pattern'] = extract_texture_pattern(img_array)
            features['dimensions'] = img.size
        
        # Deep features specific
        if algorithm == "deep_features":
            edges, edge_density = extract_edge_features(img)
            features['edges'] = edges
            features['edge_density'] = edge_density
            features['img_for_ssim'] = img  # Store for SSIM calculation
        
        return features, None

    except FileNotFoundError:
        return None, "File not found"
    except Exception as e:
        return None, f"Error: {type(e).__name__}"


def calculate_similarity(target_features, candidate_features, algorithm="balanced"):
    """Calculate a weighted similarity score based on algorithm."""
    
    algorithm = target_features.get('algorithm', algorithm)
    weights = ALGORITHM_WEIGHTS.get(algorithm, ALGORITHM_WEIGHTS['balanced'])
    
    metrics = {}
    combined_distance = 0.0
    
    # Balanced algorithm (default)
    if algorithm == "balanced":
        hash_distance = float(target_features['ahash'] - candidate_features['ahash']) / 64.0
        
        hist1 = target_features['histogram']
        hist2 = candidate_features['histogram']
        hist_distance = np.sum((hist1 - hist2) ** 2 / (hist1 + hist2 + 1e-10)) / 2
        
        color_distance = color_palette_distance_fast(
            target_features['dominant_colors'],
            target_features['color_weights'],
            candidate_features['dominant_colors'],
            candidate_features['color_weights']
        )
        
        combined_distance = (
            weights['perceptual_hash'] * hash_distance +
            weights['color_histogram'] * hist_distance +
            weights['dominant_colors'] * color_distance
        )
        
        metrics = {
            'hash_dist': hash_distance * 64,
            'hist_dist': hist_distance,
            'color_dist': color_distance,
            'combined': combined_distance
        }
    
    # Skin-Optimized algorithm
    elif algorithm == "skin_optimized":
        # Dimension match bonus
        dim_distance = 0.0
        if candidate_features.get('is_skin_texture'):
            dim_distance = 0.0  # Perfect match for skin texture
        else:
            dim_distance = 0.5  # Penalty for non-skin textures
        
        # Texture pattern similarity
        pattern1 = target_features.get('texture_pattern', np.array([0]))
        pattern2 = candidate_features.get('texture_pattern', np.array([0]))
        if len(pattern1) > 0 and len(pattern2) > 0:
            min_len = min(len(pattern1), len(pattern2))
            texture_distance = np.mean(np.abs(pattern1[:min_len] - pattern2[:min_len])) / 100.0
        else:
            texture_distance = 1.0
        
        # Color features
        color_distance = color_palette_distance_fast(
            target_features['dominant_colors'],
            target_features['color_weights'],
            candidate_features['dominant_colors'],
            candidate_features['color_weights']
        )
        
        hist1 = target_features.get('histogram', None)
        hist2 = candidate_features.get('histogram', None)
        if hist1 is not None and hist2 is not None:
            hist_distance = np.sum((hist1 - hist2) ** 2 / (hist1 + hist2 + 1e-10)) / 2
        else:
            hist_distance = 0.5
        
        combined_distance = (
            weights['texture_pattern'] * min(texture_distance, 1.0) +
            weights['dominant_colors'] * color_distance +
            weights['dimension_match'] * dim_distance +
            weights.get('color_histogram', 0.1) * hist_distance
        )
        
        metrics = {
            'texture_dist': texture_distance,
            'color_dist': color_distance,
            'dim_match': 1.0 - dim_distance,
            'combined': combined_distance
        }
    
    # Deep Features algorithm
    elif algorithm == "deep_features":
        # SSIM calculation
        ssim_distance = calculate_ssim_similarity(
            target_features.get('img_for_ssim'),
            candidate_features.get('img_for_ssim')
        )
        
        # Edge similarity
        edges1 = target_features.get('edges')
        edges2 = candidate_features.get('edges')
        edge_density1 = target_features.get('edge_density', 0)
        edge_density2 = candidate_features.get('edge_density', 0)
        
        edge_distance = abs(edge_density1 - edge_density2)
        
        # Color similarity
        color_distance = color_palette_distance_fast(
            target_features['dominant_colors'],
            target_features['color_weights'],
            candidate_features['dominant_colors'],
            candidate_features['color_weights']
        )
        
        combined_distance = (
            weights['edge_similarity'] * edge_distance +
            weights['ssim'] * ssim_distance +
            weights['dominant_colors'] * color_distance
        )
        
        metrics = {
            'edge_dist': edge_distance,
            'ssim_dist': ssim_distance,
            'color_dist': color_distance,
            'combined': combined_distance
        }
    
    # Color Distribution algorithm
    elif algorithm == "color_distribution":
        hist1 = target_features['histogram']
        hist2 = candidate_features['histogram']
        hist_distance = np.sum((hist1 - hist2) ** 2 / (hist1 + hist2 + 1e-10)) / 2
        
        color_distance = color_palette_distance_fast(
            target_features['dominant_colors'],
            target_features['color_weights'],
            candidate_features['dominant_colors'],
            candidate_features['color_weights']
        )
        
        combined_distance = (
            weights['color_histogram'] * hist_distance +
            weights['dominant_colors'] * color_distance
        )
        
        metrics = {
            'hist_dist': hist_distance,
            'color_dist': color_distance,
            'combined': combined_distance
        }
    
    # Fast Match algorithm
    elif algorithm == "fast":
        hash_distance = float(target_features['ahash'] - candidate_features['ahash']) / 64.0
        
        hist1 = target_features['histogram']
        hist2 = candidate_features['histogram']
        hist_distance = np.sum((hist1 - hist2) ** 2 / (hist1 + hist2 + 1e-10)) / 2
        
        combined_distance = (
            weights['perceptual_hash'] * hash_distance +
            weights['color_histogram'] * hist_distance
        )
        
        metrics = {
            'hash_dist': hash_distance * 64,
            'hist_dist': hist_distance,
            'combined': combined_distance
        }
    
    return combined_distance, metrics
