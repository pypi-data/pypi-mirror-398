"""
zarx Models Package
Central hub for all model architectures and variants.

Usage:
    # List available models
    >>> from zarx.models import list_models
    >>> print(list_models())
    ['igris_1m', 'igris_10m', 'igris_50m', 'igris_277m', ...]
    
    # Get model by name
    >>> from zarx.models import get_model
    >>> ModelClass = get_model('igris_277m')
    >>> model = ModelClass()
    
    # Direct import (recommended)
    >>> from zarx.models.igris import IGRIS_277M
    >>> model = IGRIS_277M()
"""

# Registry system
from .registry import (
    ModelRegistry,
    list_models,
    get_model,
    create_model,
)

# IGRIS models
from .igris import (
    IgrisModel,
    IGRISBase,
    IGRIS_1M,
    IGRIS_10M,
    IGRIS_50M,
    IGRIS_277M,
    IGRIS_500M,
    IGRIS_1_3B,
    IGRIS_7B,
    IGRIS277M,  # Legacy alias
)

__all__ = [
    # Registry
    'ModelRegistry',
    'list_models',
    'get_model',
    'create_model',
    
    # IGRIS
    'IgrisModel',
    'IGRISBase',
    'IGRIS_1M',
    'IGRIS_10M',
    'IGRIS_50M',
    'IGRIS_277M',
    'IGRIS_500M',
    'IGRIS_1_3B',
    'IGRIS_7B',
    'IGRIS277M',
]

