"""Color Frequency Algorithm

Pure color-based matching that compares the exact color values and their frequencies.
Ideal for finding skins with similar color palettes regardless of layout.
"""

from .base import MatchingAlgorithm
from PIL import Image
import numpy as np


class ColorFrequencyAlgorithm(MatchingAlgorithm):
    """Algorithm that matches based purely on color values and their frequencies."""
    
    @property
    def name(self) -> str:
        return "color_frequency"
    
    @property
    def display_name(self) -> str:
        return "Color Frequency"
    
    @property
    def description(self) -> str:
        return "Matches based on exact color values and their frequencies"
    
    @property
    def weights(self) -> dict:
        return {
            'color_frequency': 100.0  # Pure color frequency matching
        }
    
    def extract_features(self, image_path: str, img, img_array) -> dict:
        """Extract color frequency features from the image."""
        # img_array is already provided as RGB numpy array
        
        # Reshape to list of pixels
        pixels = img_array.reshape(-1, 3)
        
        # Count unique colors and their frequencies
        unique_colors, counts = np.unique(pixels, axis=0, return_counts=True)
        
        # Calculate total pixels
        total_pixels = len(pixels)
        
        # Create color frequency dictionary: {(r, g, b): frequency}
        color_freq = {}
        for color, count in zip(unique_colors, counts):
            # Convert numpy integers to Python integers for serialization
            color_tuple = tuple(int(c) for c in color)
            frequency = float(count / total_pixels)
            color_freq[color_tuple] = frequency
        
        return {
            'color_frequency': color_freq,
            'unique_colors': int(len(unique_colors)),
            'total_pixels': int(total_pixels)
        }
    
    def calculate_similarity(self, features1: dict, features2: dict) -> tuple:
        """Calculate similarity based on color frequency distribution.
        
        Returns:
            tuple: (distance, metrics) where distance is lower for better matches
        """
        freq1 = features1['color_frequency']
        freq2 = features2['color_frequency']
        
        # Get all unique colors from both images
        all_colors = set(freq1.keys()) | set(freq2.keys())
        
        # Calculate similarity using frequency comparison
        total_diff = 0.0
        
        for color in all_colors:
            f1 = freq1.get(color, 0.0)
            f2 = freq2.get(color, 0.0)
            
            # Calculate absolute difference in frequency
            diff = abs(f1 - f2)
            total_diff += diff
        
        # total_diff ranges from 0 (identical) to 2.0 (completely different)
        # Normalize to [0, 1] range for distance (0 = perfect match, 1 = completely different)
        distance = total_diff / 2.0
        
        # Ensure distance is in [0, 1] range
        distance = max(0.0, min(1.0, distance))
        
        metrics = {
            'color_freq_distance': distance,
            'unique_colors_1': features1['unique_colors'],
            'unique_colors_2': features2['unique_colors'],
            'color_overlap': len(set(freq1.keys()) & set(freq2.keys()))
        }
        
        return distance, metrics
