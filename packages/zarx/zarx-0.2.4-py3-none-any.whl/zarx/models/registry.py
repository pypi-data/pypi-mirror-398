"""
Model Registry System
Centralized model variant registration and discovery.
"""

from typing import Dict, Type, Optional, List, Callable
from pathlib import Path
import warnings

from ..exceptions import ModelNotFoundError, ModelError


class ModelRegistry:
    """
    Central registry for all model variants.
    Enables discovery and instantiation by name or parameter count.
    
    Example:
        >>> from zarx.models import ModelRegistry, IGRIS_277M
        >>> ModelRegistry.list()
        ['igris_1m', 'igris_10m', 'igris_50m', 'igris_277m', ...]
        
        >>> model = ModelRegistry.get('igris_277m')()
        >>> # or
        >>> model = IGRIS_277M()
    """
    
    _models: Dict[str, Dict] = {}
    
    @classmethod
    def register(
        cls,
        name: str,
        model_class: Type,
        param_count: int,
        description: str = "",
        config_factory: Optional[Callable] = None
    ):
        """
        Register a model variant.
        
        Args:
            name: Model identifier (e.g., 'igris_277m')
            model_class: Model class
            param_count: Number of parameters
            description: Model description
            config_factory: Function to create default config
        """
        if name in cls._models:
            warnings.warn(f"Model '{name}' already registered. Overwriting.")
        
        cls._models[name] = {
            'class': model_class,
            'param_count': param_count,
            'description': description,
            'config_factory': config_factory
        }
    
    @classmethod
    def get(cls, name: str) -> Type:
        """
        Get model class by name.
        
        Args:
            name: Model identifier
            
        Returns:
            Model class
            
        Raises:
            ModelNotFoundError: If model not found
        """
        name = name.lower()
        if name not in cls._models:
            raise ModelNotFoundError(name, available_models=cls.list())
        
        return cls._models[name]['class']
    
    @classmethod
    def get_info(cls, name: str) -> Dict:
        """Get complete model information."""
        name = name.lower()
        if name not in cls._models:
            raise ModelNotFoundError(name, available_models=cls.list())
        
        return cls._models[name].copy()
    
    @classmethod
    def list(cls) -> List[str]:
        """List all registered models."""
        return sorted(cls._models.keys())
    
    @classmethod
    def list_detailed(cls) -> Dict[str, Dict]:
        """List all models with detailed information."""
        return {
            name: {
                'param_count': info['param_count'],
                'description': info['description']
            }
            for name, info in sorted(cls._models.items())
        }
    
    @classmethod
    def find_by_params(
        cls,
        target_params: int,
        tolerance: float = 0.1,
        architecture: Optional[str] = None
    ) -> Optional[str]:
        """
        Find closest model by parameter count.
        
        Args:
            target_params: Target parameter count
            tolerance: Acceptable relative difference (default 10%)
            architecture: Filter by architecture (e.g., 'igris')
            
        Returns:
            Model name or None if no match found
        """
        if not cls._models:
            return None
        
        candidates = cls._models.items()
        
        # Filter by architecture if specified
        if architecture:
            candidates = [
                (name, info) for name, info in candidates
                if name.startswith(architecture.lower())
            ]
        
        if not candidates:
            return None
        
        # Find closest match
        closest = min(
            candidates,
            key=lambda x: abs(x[1]['param_count'] - target_params)
        )
        
        name, info = closest
        relative_diff = abs(info['param_count'] - target_params) / target_params
        
        if relative_diff <= tolerance:
            return name
        
        return None
    
    @classmethod
    def create(cls, name: str, **kwargs):
        """
        Create a model instance with optional config overrides.
        
        Args:
            name: Model identifier
            **kwargs: Config overrides
            
        Returns:
            Model instance
        """
        info = cls.get_info(name)
        model_class = info['class']
        
        # Create config if factory available
        if info['config_factory'] and not kwargs.get('config'):
            config = info['config_factory']()
            
            # Apply overrides
            if kwargs:
                for key, value in kwargs.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
            
            return model_class(config)
        
        return model_class(**kwargs)
    
    @classmethod
    def clear(cls):
        """Clear all registered models (mainly for testing)."""
        cls._models.clear()


# Convenience functions
def list_models() -> List[str]:
    """List all available models."""
    return ModelRegistry.list()


def get_model(name: str) -> Type:
    """Get model class by name."""
    return ModelRegistry.get(name)


def create_model(name: str, **kwargs):
    """Create model instance by name."""
    return ModelRegistry.create(name, **kwargs)


__all__ = [
    'ModelRegistry',
    'list_models',
    'get_model',
    'create_model',
]
