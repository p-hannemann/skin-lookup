"""
Base class for all image matching algorithms.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Optional


class MatchingAlgorithm(ABC):
    """Abstract base class for image matching algorithms."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Internal name of the algorithm."""
        pass
    
    @property
    @abstractmethod
    def display_name(self) -> str:
        """Display name shown in UI."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Detailed description for help text."""
        pass
    
    @property
    @abstractmethod
    def weights(self) -> Dict[str, float]:
        """Weight configuration for different metrics."""
        pass
    
    @abstractmethod
    def extract_features(self, image_path: str, img, img_array) -> Dict[str, Any]:
        """
        Extract features from an image.
        
        Args:
            image_path: Path to the image file
            img: PIL Image object
            img_array: NumPy array of the image (RGB)
            
        Returns:
            Dictionary of extracted features
        """
        pass
    
    @abstractmethod
    def calculate_similarity(self, target_features: Dict[str, Any], 
                           candidate_features: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate similarity between two images based on their features.
        
        Args:
            target_features: Features from the target image
            candidate_features: Features from the candidate image
            
        Returns:
            Tuple of (combined_distance, metrics_dict)
            Lower distance means more similar
        """
        pass
    
    def requires_special_processing(self) -> bool:
        """Whether this algorithm needs special setup (e.g., AI models)."""
        return False
    
    def is_available(self) -> bool:
        """Check if this algorithm is available (e.g., PyTorch installed for AI)."""
        return True
