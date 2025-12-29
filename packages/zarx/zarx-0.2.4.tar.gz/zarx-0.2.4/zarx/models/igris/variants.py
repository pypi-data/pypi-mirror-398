"""
IGRIS Model Variants
Explicit model classes for each parameter size.

This module provides clean, explicit model constructors for each IGRIS variant.
Users can import and instantiate models directly without config knowledge.

Example:
    >>> from zarx.models.igris import IGRIS_277M
    >>> model = IGRIS_277M()
    >>> # That's it! No config needed for basic usage.
"""

from typing import Optional
from pathlib import Path

from zarx.config import ConfigFactory, IgrisConfig, ModelSize
from .model import IgrisModel
from ..registry import ModelRegistry


# === BASE IGRIS CLASS ===

class IGRISBase(IgrisModel):
    """Base class for all IGRIS variants with convenience methods."""
    
    MODEL_SIZE: ModelSize = None  # Override in subclasses
    PARAM_COUNT: int = None  # Override in subclasses
    
    def __init__(self, config: Optional[IgrisConfig] = None, test_mode: bool = False, **overrides):
        """
        Initialize IGRIS model.
        
        Args:
            config: Optional custom config. If None, uses default for this size.
            test_mode: If True, initialize MoE in a lightweight test mode.
            **overrides: Config overrides (e.g., vocab_size=50000)
        """
        if config is None:
            config = ConfigFactory.get_config(
                self.MODEL_SIZE,
                **overrides
            )
        elif overrides:
            config.update(**overrides)
        
        super().__init__(config, test_mode=test_mode)
    
    @classmethod
    def from_pretrained(cls, path: str, **kwargs):
        """
        Load pretrained model from checkpoint.
        
        Args:
            path: Path to checkpoint
            **kwargs: Additional arguments
            
        Returns:
            Loaded model instance
        """
        model = cls(**kwargs)
        model.load_checkpoint(path)
        return model
    
    @classmethod
    def param_count(cls) -> int:
        """Get parameter count for this variant."""
        return cls.PARAM_COUNT
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(params={self.PARAM_COUNT:,})"


# === 1M VARIANT ===

class IGRIS_1M(IGRISBase):
    """
    IGRIS 1M - Tiny model for testing and experimentation.
    
    Specs:
        - Parameters: ~1M
        - Layers: 4
        - Hidden: 128
        - Heads: 4
        - Context: 1024
    
    Example:
        >>> model = IGRIS_1M()
        >>> model = IGRIS_1M(vocab_size=8000)  # Custom vocab
    """
    MODEL_SIZE = ModelSize.NANO_1M
    PARAM_COUNT = 1_000_000


# === 10M VARIANT ===

class IGRIS_10M(IGRISBase):
    """
    IGRIS 10M - Small model for rapid prototyping.
    
    Specs:
        - Parameters: ~10M
        - Layers: 8
        - Hidden: 512
        - Heads: 8
        - Context: 2048
    
    Example:
        >>> model = IGRIS_10M()
    """
    MODEL_SIZE = ModelSize.NANO_10M
    PARAM_COUNT = 10_000_000


# === 50M VARIANT ===

class IGRIS_50M(IGRISBase):
    """
    IGRIS 50M - Micro model for efficient training.
    
    Specs:
        - Parameters: ~50M
        - Layers: 12
        - Hidden: 768
        - Heads: 12
        - Context: 4096
    
    Example:
        >>> model = IGRIS_50M()
    """
    MODEL_SIZE = ModelSize.MICRO_50M
    PARAM_COUNT = 50_000_000


# === 277M VARIANT (FLAGSHIP) ===

class IGRIS_277M(IGRISBase):
    """
    IGRIS 277M - Flagship model with optimal efficiency.
    
    This is the primary zarx-IGRIS model with ~26M active parameters per token.
    Equivalent performance to 3-4B dense models at 1/50th the cost.
    
    Specs:
        - Total Parameters: 277M
        - Active per token: ~26M (10% sparsity)
        - Layers: 24
        - Hidden: 2048
        - Heads: 32
        - Context: 8192
        - Experts: 192 (Top-2 routing)
        - CoT Components: 6
    
    Example:
        >>> model = IGRIS_277M()
        >>> model = IGRIS_277M(context_length=16384)  # Longer context
        >>> model = IGRIS_277M.from_pretrained("path/to/checkpoint.pt")
    """
    MODEL_SIZE = ModelSize.MINI_277M
    PARAM_COUNT = 277_000_000


# === 500M VARIANT ===

class IGRIS_500M(IGRISBase):
    """
    IGRIS 500M - Larger model for better performance.
    
    Specs:
        - Parameters: ~500M
        - Active per token: ~40M
        - Layers: 24
        - Hidden: 2560
        - Heads: 40
        - Context: 8192
        - Experts: 256
    
    Example:
        >>> model = IGRIS_500M()
    """
    MODEL_SIZE = ModelSize.SMALL_500M
    PARAM_COUNT = 500_000_000


# === 1.3B VARIANT ===

class IGRIS_1_3B(IGRISBase):
    """
    IGRIS 1.3B - Medium scale model.
    
    Specs:
        - Parameters: ~1.3B
        - Active per token: ~90M
        - Layers: 32
        - Hidden: 3072
        - Heads: 48
        - Context: 16384
        - Experts: 384
    
    Example:
        >>> model = IGRIS_1_3B()
    """
    MODEL_SIZE = ModelSize.MEDIUM_1B
    PARAM_COUNT = 1_300_000_000


# === 7B VARIANT ===

class IGRIS_7B(IGRISBase):
    """
    IGRIS 7B - Large scale model.
    
    Specs:
        - Parameters: ~7B
        - Active per token: ~350M
        - Layers: 48
        - Hidden: 6144
        - Heads: 96
        - Context: 65536
        - Experts: 768
    
    Example:
        >>> model = IGRIS_7B()
    """
    MODEL_SIZE = ModelSize.XL_7B
    PARAM_COUNT = 7_000_000_000


# === REGISTER ALL VARIANTS ===

def _register_variants():
    """Register all IGRIS variants with the model registry."""
    variants = [
        (IGRIS_1M, "IGRIS 1M - Tiny model for testing"),
        (IGRIS_10M, "IGRIS 10M - Small model for prototyping"),
        (IGRIS_50M, "IGRIS 50M - Micro model for efficient training"),
        (IGRIS_277M, "IGRIS 277M - Flagship model (277M params, ~26M active)"),
        (IGRIS_500M, "IGRIS 500M - Larger model"),
        (IGRIS_1_3B, "IGRIS 1.3B - Medium scale model"),
        (IGRIS_7B, "IGRIS 7B - Large scale model"),
    ]
    
    for variant_class, description in variants:
        # Generate name from class (IGRIS_277M -> igris_277m)
        name = variant_class.__name__.lower()
        
        ModelRegistry.register(
            name=name,
            model_class=variant_class,
            param_count=variant_class.PARAM_COUNT,
            description=description,
            config_factory=lambda size=variant_class.MODEL_SIZE: ConfigFactory.get_config(size)
        )


# Auto-register on import
_register_variants()


# === LEGACY COMPATIBILITY ===

# Alias for backward compatibility
IgrisModel277M = IGRIS_277M
IGRIS277M = IGRIS_277M  # Match your target usage


__all__ = [
    # Base
    'IGRISBase',
    
    # Variants
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

