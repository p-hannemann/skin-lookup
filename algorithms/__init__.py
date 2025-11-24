"""
Algorithm registry for image matching algorithms.
"""

from algorithms.base import MatchingAlgorithm
from algorithms.balanced import BalancedAlgorithm
from algorithms.render_to_skin import RenderToSkinAlgorithm
from algorithms.render_match import RenderMatchAlgorithm
from algorithms.color_frequency import ColorFrequencyAlgorithm

# Import other algorithms as they're created
# from algorithms.skin_optimized import SkinOptimizedAlgorithm
# from algorithms.ai_perceptual import AIPerceptualAlgorithm
# from algorithms.ai_mobile import AIMobileAlgorithm
# from algorithms.deep_features import DeepFeaturesAlgorithm
# from algorithms.color_distribution import ColorDistributionAlgorithm
# from algorithms.fast_match import FastMatchAlgorithm


class AlgorithmRegistry:
    """Registry for all available matching algorithms."""
    
    def __init__(self):
        self._algorithms = {}
        self._register_default_algorithms()
    
    def _register_default_algorithms(self):
        """Register all built-in algorithms."""
        self.register(RenderToSkinAlgorithm())
        self.register(RenderMatchAlgorithm())
        self.register(BalancedAlgorithm())
        self.register(ColorFrequencyAlgorithm())
        # Register others as they're imported
    
    def register(self, algorithm: MatchingAlgorithm):
        """Register a new algorithm."""
        self._algorithms[algorithm.name] = algorithm
    
    def get(self, name: str) -> MatchingAlgorithm:
        """Get an algorithm by name."""
        return self._algorithms.get(name)
    
    def get_all(self):
        """Get all registered algorithms."""
        return dict(self._algorithms)
    
    def get_display_names(self):
        """Get all algorithm display names mapped to internal names."""
        return {algo.display_name: name for name, algo in self._algorithms.items()}


# Global registry instance
_registry = AlgorithmRegistry()


def get_algorithm(name: str) -> MatchingAlgorithm:
    """Get an algorithm from the global registry."""
    return _registry.get(name)


def get_all_algorithms():
    """Get all registered algorithms."""
    return _registry.get_all()


def get_algorithm_display_names():
    """Get display name to internal name mapping."""
    return _registry.get_display_names()


def register_algorithm(algorithm: MatchingAlgorithm):
    """Register a custom algorithm."""
    _registry.register(algorithm)
