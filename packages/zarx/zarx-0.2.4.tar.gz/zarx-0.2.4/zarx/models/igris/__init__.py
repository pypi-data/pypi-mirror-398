"""
IGRIS Model Package
Provides the core IGRIS architecture and all variants.

Usage:
    # Method 1: Direct variant import (RECOMMENDED)
    >>> from zarx.models.igris import IGRIS_277M
    >>> model = IGRIS_277M()
    
    # Method 2: Base model with config
    >>> from zarx.models.igris import IgrisModel
    >>> from zarx.config import ConfigFactory, ModelSize
    >>> config = ConfigFactory.get_config(ModelSize.MINI_277M)
    >>> model = IgrisModel(config)
    
    # Method 3: Legacy compatibility
    >>> from zarx.models.igris import IGRIS277M  # Alias for IGRIS_277M
    >>> model = IGRIS277M()
"""

# Core architecture
from .model import IgrisModel

# All variants (explicit parameter counts)
from .variants import (
    IGRISBase,
    IGRIS_1M,
    IGRIS_10M,
    IGRIS_50M,
    IGRIS_277M,
    IGRIS_500M,
    IGRIS_1_3B,
    IGRIS_7B,
    # Legacy aliases
    IgrisModel277M,
    IGRIS277M,
)

__all__ = [
    # Core
    'IgrisModel',
    'IGRISBase',
    
    # Variants (by size)
    'IGRIS_1M',
    'IGRIS_10M',
    'IGRIS_50M',
    'IGRIS_277M',
    'IGRIS_500M',
    'IGRIS_1_3B',
    'IGRIS_7B',
    
    # Legacy
    'IgrisModel277M',
    'IGRIS277M',
]
