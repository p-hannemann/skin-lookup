"""
Backward compatibility wrapper for image_matcher.
Redirects to new algorithm system while maintaining old API.
"""

import numpy as np
from PIL import Image
import imagehash

# Import new modular system
from algorithms import get_algorithm, get_all_algorithms
from utils import feature_extractors

# Export constants for backward compatibility
from utils.feature_extractors import TORCH_AVAILABLE, CV2_AVAILABLE, SSIM_AVAILABLE

# Legacy weight configuration (kept for reference)
ALGORITHM_WEIGHTS = {
    "balanced": {"dominant_colors": 0.60, "color_histogram": 0.35, "perceptual_hash": 0.05},
    "skin_optimized": {"texture_pattern": 0.40, "dominant_colors": 0.35, "dimension_match": 0.15, "color_histogram": 0.10},
    "deep_features": {"edge_similarity": 0.50, "ssim": 0.30, "dominant_colors": 0.20},
    "color_distribution": {"color_histogram": 0.70, "dominant_colors": 0.30},
    "fast": {"color_histogram": 0.80, "perceptual_hash": 0.20},
    "ai_perceptual": {"deep_features": 0.50, "dominant_colors": 0.35, "color_histogram": 0.15},
    "ai_mobile": {"mobile_features": 0.75, "dominant_colors": 0.15, "color_histogram": 0.07, "perceptual_hash": 0.03},
    "render_match": {"color_palette": 0.70, "spatial_pattern": 0.30},
    "render_to_skin": {"visible_regions": 1.0}
}


def get_image_features(image_path, algorithm="balanced"):
    """
    Extract features from an image using the specified algorithm.
    Legacy wrapper that uses new modular system.
    """
    try:
        # Load image
        img = Image.open(image_path)
        img_array = np.array(img.convert('RGB'))
        
        # Try to use new algorithm system first
        algo = get_algorithm(algorithm)
        if algo:
            features = algo.extract_features(image_path, img, img_array)
            features['algorithm'] = algorithm
            features['path'] = image_path
            return features, None
        
        # Fallback to legacy system for algorithms not yet migrated
        return _legacy_extract_features(image_path, img, img_array, algorithm)
    
    except FileNotFoundError:
        return None, "File not found"
    except Exception as e:
        return None, f"Error: {type(e).__name__}"


def calculate_similarity(target_features, candidate_features, algorithm="balanced"):
    """
    Calculate similarity between two images.
    Legacy wrapper that uses new modular system.
    """
    algorithm = target_features.get('algorithm', algorithm)
    
    # Try to use new algorithm system first
    algo = get_algorithm(algorithm)
    if algo:
        return algo.calculate_similarity(target_features, candidate_features)
    
    # Fallback to legacy system
    return _legacy_calculate_similarity(target_features, candidate_features, algorithm)


def _legacy_extract_features(image_path, img, img_array, algorithm):
    """Legacy feature extraction for algorithms not yet migrated."""
    features = {
        'algorithm': algorithm,
        'path': image_path
    }
    
    # Common features
    if algorithm in ["skin_optimized", "ai_perceptual", "ai_mobile"]:
        features['ahash'] = imagehash.average_hash(img, hash_size=8)
    
    if algorithm in ["skin_optimized", "color_distribution", "deep_features", "fast", "ai_perceptual", "ai_mobile"]:
        dominant_colors, color_weights = feature_extractors.extract_dominant_colors_fast(img_array, n_colors=12)
        features['dominant_colors'] = dominant_colors
        features['color_weights'] = color_weights
    
    if algorithm in ["color_distribution", "fast", "ai_perceptual", "ai_mobile"]:
        bins = 16 if algorithm == "fast" else 24
        hist, _ = np.histogramdd(
            img_array.reshape(-1, 3),
            bins=(bins, bins, bins),
            range=[(0, 256), (0, 256), (0, 256)]
        )
        hist = hist.flatten()
        hist = hist / (hist.sum() + 1e-10)
        features['histogram'] = hist
    
    if algorithm == "skin_optimized":
        features['is_skin_texture'] = feature_extractors.is_minecraft_skin_texture(img)
        features['texture_pattern'] = feature_extractors.extract_texture_pattern(img_array)
        features['dimensions'] = img.size
    
    if algorithm == "deep_features":
        edges, edge_density = feature_extractors.extract_edge_features(img)
        features['edges'] = edges
        features['edge_density'] = edge_density
        features['img_for_ssim'] = img
    
    if algorithm == "ai_perceptual":
        if TORCH_AVAILABLE:
            ai_features = feature_extractors.extract_ai_features(img)
            features['ai_features'] = ai_features
            features['ai_available'] = ai_features is not None
        else:
            features['ai_available'] = False
    
    if algorithm == "ai_mobile":
        if TORCH_AVAILABLE:
            mobile_features = feature_extractors.extract_mobile_features(img)
            features['mobile_features'] = mobile_features
            features['mobile_available'] = mobile_features is not None
        else:
            features['mobile_available'] = False
    
    return features, None


def _legacy_calculate_similarity(target_features, candidate_features, algorithm):
    """Legacy similarity calculation for algorithms not yet migrated."""
    weights = ALGORITHM_WEIGHTS.get(algorithm, ALGORITHM_WEIGHTS['balanced'])
    metrics = {}
    combined_distance = 0.0
    
    if algorithm == "skin_optimized":
        texture1 = target_features['texture_pattern']
        texture2 = candidate_features['texture_pattern']
        texture_distance = abs(texture1['edge_density'] - texture2['edge_density']) + \
                         abs(texture1['contrast'] - texture2['contrast']) / 255.0
        
        color_distance = feature_extractors.color_palette_distance_fast(
            target_features['dominant_colors'],
            target_features['color_weights'],
            candidate_features['dominant_colors'],
            candidate_features['color_weights']
        )
        
        is_target_skin = target_features.get('is_skin_texture', False)
        is_candidate_skin = candidate_features.get('is_skin_texture', False)
        dimension_distance = 0.0 if (is_target_skin and is_candidate_skin) else 0.5
        
        hist1 = target_features.get('histogram', np.zeros(24**3))
        hist2 = candidate_features.get('histogram', np.zeros(24**3))
        hist_distance = np.sum((hist1 - hist2) ** 2 / (hist1 + hist2 + 1e-10)) / 2
        
        combined_distance = (
            weights['texture_pattern'] * texture_distance +
            weights['dominant_colors'] * color_distance +
            weights['dimension_match'] * dimension_distance +
            weights.get('color_histogram', 0.1) * hist_distance
        )
        
        metrics = {
            'texture_dist': texture_distance,
            'color_dist': color_distance,
            'dim_dist': dimension_distance,
            'hist_dist': hist_distance,
            'combined': combined_distance
        }
    
    elif algorithm == "deep_features":
        edge_distance = abs(target_features['edge_density'] - candidate_features['edge_density'])
        
        ssim_distance = feature_extractors.calculate_ssim_distance(
            target_features['img_for_ssim'],
            candidate_features['img_for_ssim']
        )
        
        color_distance = feature_extractors.color_palette_distance_fast(
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
    
    elif algorithm == "color_distribution":
        hist1 = target_features['histogram']
        hist2 = candidate_features['histogram']
        hist_distance = np.sum((hist1 - hist2) ** 2 / (hist1 + hist2 + 1e-10)) / 2
        
        color_distance = feature_extractors.color_palette_distance_fast(
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
    
    elif algorithm == "fast":
        hash_distance = float(target_features['ahash'] - candidate_features['ahash']) / 64.0
        
        hist1 = target_features['histogram']
        hist2 = candidate_features['histogram']
        hist_distance = np.sum((hist1 - hist2) ** 2 / (hist1 + hist2 + 1e-10)) / 2
        
        combined_distance = (
            weights['color_histogram'] * hist_distance +
            weights['perceptual_hash'] * hash_distance
        )
        
        metrics = {
            'hist_dist': hist_distance,
            'hash_dist': hash_distance * 64,
            'combined': combined_distance
        }
    
    elif algorithm == "ai_perceptual":
        if target_features.get('ai_available') and candidate_features.get('ai_available'):
            ai_distance = feature_extractors.calculate_ai_similarity(
                target_features['ai_features'],
                candidate_features['ai_features']
            )
            
            color_distance = feature_extractors.color_palette_distance_fast(
                target_features['dominant_colors'],
                target_features['color_weights'],
                candidate_features['dominant_colors'],
                candidate_features['color_weights']
            )
            
            hist1 = target_features['histogram']
            hist2 = candidate_features['histogram']
            hist_distance = np.sum((hist1 - hist2) ** 2 / (hist1 + hist2 + 1e-10)) / 2
            
            combined_distance = (
                weights['deep_features'] * ai_distance +
                weights['dominant_colors'] * color_distance +
                weights['color_histogram'] * hist_distance
            )
            
            metrics = {
                'ai_dist': ai_distance,
                'color_dist': color_distance,
                'hist_dist': hist_distance,
                'combined': combined_distance
            }
        else:
            # Fallback
            hash_distance = 0.5
            color_distance = feature_extractors.color_palette_distance_fast(
                target_features['dominant_colors'],
                target_features['color_weights'],
                candidate_features['dominant_colors'],
                candidate_features['color_weights']
            )
            hist1 = target_features['histogram']
            hist2 = candidate_features['histogram']
            hist_distance = np.sum((hist1 - hist2) ** 2 / (hist1 + hist2 + 1e-10)) / 2
            
            combined_distance = 0.6 * color_distance + 0.4 * hist_distance
            metrics = {
                'color_dist': color_distance,
                'hist_dist': hist_distance,
                'ai_unavailable': True,
                'combined': combined_distance
            }
    
    elif algorithm == "ai_mobile":
        if target_features.get('mobile_available') and candidate_features.get('mobile_available'):
            mobile_distance = feature_extractors.calculate_ai_similarity(
                target_features['mobile_features'],
                candidate_features['mobile_features']
            )
            
            hash_distance = float(target_features['ahash'] - candidate_features['ahash']) / 64.0
            
            color_distance = feature_extractors.color_palette_distance_fast(
                target_features['dominant_colors'],
                target_features['color_weights'],
                candidate_features['dominant_colors'],
                candidate_features['color_weights']
            )
            
            hist1 = target_features['histogram']
            hist2 = candidate_features['histogram']
            hist_distance = np.sum((hist1 - hist2) ** 2 / (hist1 + hist2 + 1e-10)) / 2
            
            combined_distance = (
                weights['mobile_features'] * mobile_distance +
                weights['dominant_colors'] * color_distance +
                weights['color_histogram'] * hist_distance +
                weights['perceptual_hash'] * hash_distance
            )
            
            metrics = {
                'mobile_dist': mobile_distance,
                'color_dist': color_distance,
                'hist_dist': hist_distance,
                'hash_dist': hash_distance * 64,
                'combined': combined_distance
            }
        else:
            # Fallback
            color_distance = feature_extractors.color_palette_distance_fast(
                target_features['dominant_colors'],
                target_features['color_weights'],
                candidate_features['dominant_colors'],
                candidate_features['color_weights']
            )
            hist1 = target_features['histogram']
            hist2 = candidate_features['histogram']
            hist_distance = np.sum((hist1 - hist2) ** 2 / (hist1 + hist2 + 1e-10)) / 2
            
            combined_distance = 0.6 * color_distance + 0.4 * hist_distance
            metrics = {
                'color_dist': color_distance,
                'hist_dist': hist_distance,
                'mobile_unavailable': True,
                'combined': combined_distance
            }
    
    return combined_distance, metrics
