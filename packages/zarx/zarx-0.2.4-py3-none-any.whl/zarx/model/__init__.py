"""
zarx Model Package
"""

from .base import BaseModel
from zarx.config import ModelConfig

def create_model(config: ModelConfig) -> BaseModel:
    """
    Factory function to create a model based on the configuration.
    """
    if config.architecture.value == 'zarx_igris':
        from zarx.models.igris import IgrisModel
        return IgrisModel(config)
    # Add other models here
    # elif config.architecture == 'berudra':
    #     return BerudraModel(config)
    else:
        raise ValueError(f"Unsupported architecture: {config.architecture}")

__all__ = ['BaseModel', 'create_model']

