"""
Render to Skin algorithm - Converts renders to skins then compares visible regions.
"""

from algorithms.base import MatchingAlgorithm
from utils.feature_extractors import convert_render_to_skin, extract_visible_skin_regions
import numpy as np
from typing import Dict, Any, Tuple


class RenderToSkinAlgorithm(MatchingAlgorithm):
    
    @property
    def name(self) -> str:
        return "render_to_skin"
    
    @property
    def display_name(self) -> str:
        return "Render to Skin (Convert+Match) 🎯"
    
    @property
    def description(self) -> str:
        return """🎯 Render to Skin (Convert+Match) - NEW & MOST ACCURATE!
BEST FOR 3D RENDERS! First converts your 3D render to a 2D skin using region detection and pixel extraction (same as Converter tab), then compares ONLY the visible regions (front, top, left) pixel-by-pixel. This gives the most accurate matches because it directly compares textures that are actually visible in the render. Slightly slower than Render Match but much more accurate!"""
    
    @property
    def weights(self) -> Dict[str, float]:
        return {"visible_regions": 1.0}
    
    def extract_features(self, image_path: str, img, img_array) -> Dict[str, Any]:
        # Check if this is a 64x64 skin (don't convert) or a render (convert first)
        if img.size == (64, 64):
            # Already a skin format, just extract visible regions
            skin_array = np.array(img.convert('RGBA'))
            visible_regions = extract_visible_skin_regions(skin_array)
        else:
            # Convert render to skin format first
            converted_skin = convert_render_to_skin(img)
            converted_array = np.array(converted_skin.convert('RGBA'))
            # Extract only visible regions
            visible_regions = extract_visible_skin_regions(converted_array)
        
        return {'visible_regions': visible_regions}
    
    def calculate_similarity(self, target_features: Dict[str, Any], 
                           candidate_features: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        target_regions = target_features['visible_regions']
        candidate_regions = candidate_features['visible_regions']
        
        # Calculate pixel-wise distance for visible regions only
        diff = target_regions.astype(np.float32) - candidate_regions.astype(np.float32)
        pixel_distance = np.sqrt(np.mean(diff ** 2)) / 255.0  # Normalize to 0-1
        
        combined_distance = self.weights['visible_regions'] * pixel_distance
        
        metrics = {
            'pixel_dist': pixel_distance,
            'combined': combined_distance
        }
        
        return combined_distance, metrics
