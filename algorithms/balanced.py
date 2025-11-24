"""
Balanced algorithm - General purpose matching.
"""

from algorithms.base import MatchingAlgorithm
from utils.feature_extractors import extract_dominant_colors_fast, color_palette_distance_fast
import numpy as np
import imagehash
from typing import Dict, Any, Tuple


class BalancedAlgorithm(MatchingAlgorithm):
    
    @property
    def name(self) -> str:
        return "balanced"
    
    @property
    def display_name(self) -> str:
        return "Balanced (Default)"
    
    @property
    def description(self) -> str:
        return """🎯 Balanced (Default)
Optimal for most cases. Uses dominant colors (60%), color histogram (35%), and perceptual hashing (5%). Best general-purpose algorithm."""
    
    @property
    def weights(self) -> Dict[str, float]:
        return {
            "dominant_colors": 0.60,
            "color_histogram": 0.35,
            "perceptual_hash": 0.05
        }
    
    def extract_features(self, image_path: str, img, img_array) -> Dict[str, Any]:
        features = {}
        
        # Perceptual hash
        features['ahash'] = imagehash.average_hash(img, hash_size=8)
        
        # Dominant colors
        dominant_colors, color_weights = extract_dominant_colors_fast(img_array, n_colors=12)
        features['dominant_colors'] = dominant_colors
        features['color_weights'] = color_weights
        
        # Color histogram
        bins = 24
        hist, _ = np.histogramdd(
            img_array.reshape(-1, 3),
            bins=(bins, bins, bins),
            range=[(0, 256), (0, 256), (0, 256)]
        )
        hist = hist.flatten()
        hist = hist / (hist.sum() + 1e-10)
        features['histogram'] = hist
        
        return features
    
    def calculate_similarity(self, target_features: Dict[str, Any], 
                           candidate_features: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        # Perceptual hash
        hash_distance = float(target_features['ahash'] - candidate_features['ahash']) / 64.0
        
        # Color palette
        color_distance = color_palette_distance_fast(
            target_features['dominant_colors'],
            target_features['color_weights'],
            candidate_features['dominant_colors'],
            candidate_features['color_weights']
        )
        
        # Histogram
        hist1 = target_features['histogram']
        hist2 = candidate_features['histogram']
        hist_distance = np.sum((hist1 - hist2) ** 2 / (hist1 + hist2 + 1e-10)) / 2
        
        combined_distance = (
            self.weights['dominant_colors'] * color_distance +
            self.weights['color_histogram'] * hist_distance +
            self.weights['perceptual_hash'] * hash_distance
        )
        
        metrics = {
            'hash_dist': hash_distance * 64,
            'color_dist': color_distance,
            'hist_dist': hist_distance,
            'combined': combined_distance
        }
        
        return combined_distance, metrics
