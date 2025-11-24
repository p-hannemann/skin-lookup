"""
Render Match algorithm - Fast 3D render to 2D skin matching.
"""

from algorithms.base import MatchingAlgorithm
from utils.feature_extractors import extract_render_features, color_palette_distance_fast
import numpy as np
from typing import Dict, Any, Tuple


class RenderMatchAlgorithm(MatchingAlgorithm):
    
    @property
    def name(self) -> str:
        return "render_match"
    
    @property
    def display_name(self) -> str:
        return "Render Match (3D→2D) ⭐"
    
    @property
    def description(self) -> str:
        return """⭐ Render Match (3D→2D) - FAST FOR RENDERS
SPECIFICALLY DESIGNED for matching 3D rendered characters to 2D skin files! Extracts 24 dominant colors ignoring lighting/shading, analyzes spatial color patterns in a 4x4 grid. Does NOT use neural networks - uses color palette matching (70%) + spatial patterns (30%). FAST and designed for this exact problem!"""
    
    @property
    def weights(self) -> Dict[str, float]:
        return {
            "color_palette": 0.70,
            "spatial_pattern": 0.30
        }
    
    def extract_features(self, image_path: str, img, img_array) -> Dict[str, Any]:
        render_feat = extract_render_features(img_array)
        return {
            'render_colors': render_feat['colors'],
            'render_weights': render_feat['weights'],
            'render_spatial': render_feat['spatial']
        }
    
    def calculate_similarity(self, target_features: Dict[str, Any], 
                           candidate_features: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        # Color palette matching
        palette_distance = color_palette_distance_fast(
            target_features['render_colors'],
            target_features['render_weights'],
            candidate_features['render_colors'],
            candidate_features['render_weights']
        )
        
        # Spatial pattern matching
        spatial1 = target_features['render_spatial']
        spatial2 = candidate_features['render_spatial']
        spatial_distance = np.linalg.norm(spatial1 - spatial2) / (np.linalg.norm(spatial1) + np.linalg.norm(spatial2) + 1e-10)
        
        combined_distance = (
            self.weights['color_palette'] * palette_distance +
            self.weights['spatial_pattern'] * spatial_distance
        )
        
        metrics = {
            'palette_dist': palette_distance,
            'spatial_dist': spatial_distance,
            'combined': combined_distance
        }
        
        return combined_distance, metrics
