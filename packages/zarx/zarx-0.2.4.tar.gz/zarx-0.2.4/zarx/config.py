"""
Complete configuration system for zarx-IGRIS with model sizes from 1M to 1B.
Production-grade with validation, serialization, and optimization.
"""

import json
import yaml
import pickle
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple, Type, TypeVar
from dataclasses import dataclass, field, asdict, fields, MISSING
from enum import Enum
import warnings
import copy
import math
from functools import lru_cache

# Try to import optional dependencies
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    warnings.warn("PyTorch not available, some features disabled")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


# ==================== ENUMS ====================

class ModelSize(Enum):
    """Predefined model sizes."""
    NANO_1M = "1M"
    NANO_10M = "10M"
    MICRO_50M = "50M"
    MINI_277M = "277M"
    SMALL_500M = "500M"
    MEDIUM_1B = "1B"
    LARGE_3B = "3B"
    XL_7B = "7B"
    XXL_13B = "13B"
    XXXL_70B = "70B"


class ArchitectureVariant(Enum):
    """Architecture variants."""
    STANDARD = "standard"  # Baseline transformer
    HASS = "hass"  # Hybrid Attention-Shard Switch
    MOE = "moe"  # Mixture of Experts
    ADAPTIVE = "adaptive"  # Adaptive compute
    QUANTUM = "quantum"  # Quantum-inspired
    ZARX_IGRIS = "zarx_igris"  # Our revolutionary architecture


class RouterType(Enum):
    """Router types."""
    NONE = "none"
    DEPTH_ONLY = "depth_only"
    WIDTH_ONLY = "width_only"
    DEPTH_WIDTH = "depth_width"
    ADAPTIVE = "adaptive"
    CERTAINTY = "certainty"


class CoTType(Enum):
    """Chain-of-Thought types."""
    NONE = "none"
    OUTPUT = "output"  # Output CoT steps
    LATENT = "latent"  # Internal latent CoT
    PROVABLE = "provable"  # Provable reasoning
    QUANTUM = "quantum"  # Quantum CoT


class QuantizationScheme(Enum):
    """Quantization schemes."""
    NONE = "none"
    STATIC = "static"
    DYNAMIC = "dynamic"
    PROGRESSIVE = "progressive"
    AWARE = "aware"  # Quantization-aware training


# ==================== BASE CONFIGURATION ====================

@dataclass
class BaseConfig:
    """Base configuration class with serialization and validation."""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {}
        for f in fields(self):
            value = getattr(self, f.name)
            if isinstance(value, Enum):
                result[f.name] = value.value
            elif isinstance(value, tuple):
                result[f.name] = list(value)
            elif isinstance(value, BaseConfig): # Handle nested BaseConfig subclasses
                result[f.name] = value.to_dict()
            elif isinstance(value, dict): # Handle dictionaries that might contain enums or nested BaseConfig
                processed_dict = {}
                for k, v in value.items():
                    if isinstance(v, Enum):
                        processed_dict[k] = v.value
                    elif isinstance(v, BaseConfig):
                        processed_dict[k] = v.to_dict()
                    elif isinstance(v, tuple):
                        processed_dict[k] = list(v)
                    else:
                        processed_dict[k] = v
                result[f.name] = processed_dict
            else:
                result[f.name] = value
        return result
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)
    
    def to_yaml(self) -> str:
        """Convert to YAML string."""
        return yaml.dump(self.to_dict(), default_flow_style=False)
    
    def save(self, path: Union[str, Path]):
        """
        Save configuration to file.
        
        Args:
            path: Path to save file
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        if path.suffix == '.json':
            with open(path, 'w') as f:
                json.dump(self.to_dict(), f, indent=2)
        elif path.suffix in ['.yaml', '.yml']:
            with open(path, 'w') as f:
                yaml.safe_dump(self.to_dict(), f, default_flow_style=False)
        elif path.suffix == '.pkl':
            with open(path, 'wb') as f:
                pickle.dump(self, f)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")
    
    @classmethod
    def load(cls, path: Union[str, Path]) -> 'BaseConfig':
        """
        Load configuration from file.
        
        Args:
            path: Path to load file from
            
        Returns:
            Loaded configuration
        """
        path = Path(path)
        
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        
        if path.suffix == '.json':
            with open(path, 'r') as f:
                data = json.load(f)
        elif path.suffix in ['.yaml', '.yml']:
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
        elif path.suffix == '.pkl':
            with open(path, 'rb') as f:
                return pickle.load(f)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")
        
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseConfig':
        """
        Create configuration from dictionary, handling nested dataclasses and enums.
        """
        if not isinstance(data, dict):
            raise TypeError(f"Input data for {cls.__name__}.from_dict must be a dictionary, got {type(data)}")

        # Get the fields defined for this specific dataclass
        field_values = {}
        for f in fields(cls):
            if f.name in data:
                value = data[f.name]
                # Handle nested dataclasses
                if hasattr(f.type, '__dataclass_fields__') and isinstance(value, dict):
                    field_values[f.name] = f.type.from_dict(value)
                # Handle Optional types containing Enums
                elif getattr(f.type, '__origin__', None) is Union:
                    is_optional_enum = False
                    for arg in f.type.__args__:
                        if isinstance(arg, type) and issubclass(arg, Enum):
                            if isinstance(value, str):
                                try:
                                    field_values[f.name] = arg(value)
                                    is_optional_enum = True
                                    break
                                except ValueError:
                                    pass
                    if not is_optional_enum: # If it's an Optional but not Optional[Enum]
                        field_values[f.name] = value
                # Handle direct Enum types
                elif isinstance(f.type, type) and issubclass(f.type, Enum):
                    if isinstance(value, str):
                        field_values[f.name] = f.type(value)
                    else:
                        field_values[f.name] = value # Already correct enum or other type
                # Handle tuples
                elif getattr(f.type, '__origin__', None) is tuple and isinstance(value, list):
                    field_values[f.name] = tuple(value)
                else:
                    field_values[f.name] = value

        return cls(**field_values)
    
    def copy(self) -> 'BaseConfig':
        """Create a deep copy."""
        return copy.deepcopy(self)
    
    def update(self, **kwargs):
        """
        Update configuration values.
        
        Args:
            **kwargs: Key-value pairs to update
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                warnings.warn(f"Ignoring unknown config key: {key}")
    
    def validate(self) -> List[str]:
        """
        Validate configuration.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check required fields
        for field_name, field_info in self.__dataclass_fields__.items():
            value = getattr(self, field_name)
            if value is None:
                # Check if the field is Optional
                is_optional = (
                    hasattr(field_info.type, '__origin__') and 
                    field_info.type.__origin__ is Union and 
                    type(None) in field_info.type.__args__
                )
                if not is_optional:
                    errors.append(f"Field '{field_name}' cannot be None")
        
        return errors
    
    def effective(self) -> Dict[str, Any]:
        """
        Get effective configuration with derived values.
        
        Returns:
            Dictionary with all configuration values
        """
        result = self.to_dict()
        
        # Add derived values
        if hasattr(self, 'compute_derived'):
            result.update(self.compute_derived())
        
        return result


# ==================== MODEL CONFIGURATIONS ====================

@dataclass
class ModelConfig(BaseConfig):
    """Base model configuration."""
    
    # Model identification
    model_name: str = "zarx_model"
    model_size: ModelSize = ModelSize.MINI_277M
    architecture: ArchitectureVariant = ArchitectureVariant.ZARX_IGRIS
    version: str = "1.0.0"
    
    # Core dimensions
    vocab_size: int = 32000
    context_length: int = 8192
    hidden_size: int = 2048
    num_layers: int = 24
    num_attention_heads: int = 32
    
    # Architecture specifics
    router_type: RouterType = RouterType.ADAPTIVE
    cot_type: CoTType = CoTType.LATENT
    quantization: QuantizationScheme = QuantizationScheme.PROGRESSIVE
    
    # Dropout and regularization
    dropout: float = 0.0
    attention_dropout: float = 0.0
    hidden_dropout: float = 0.0
    
    # Activation functions
    hidden_act: str = "gelu"
    intermediate_act: str = "gelu"
    
    # Initialization
    initializer_range: float = 0.02
    layer_norm_eps: float = 1e-5
    
    # Optimization
    gradient_checkpointing: bool = True
    use_cache: bool = True
    tie_word_embeddings: bool = True
    
    def __post_init__(self):
        """Post-initialization validation."""
        # Ensure hidden_size is divisible by num_attention_heads
        if self.hidden_size % self.num_attention_heads != 0:
            raise ValueError(
                f"hidden_size ({self.hidden_size}) must be divisible by "
                f"num_attention_heads ({self.num_attention_heads})"
            )
    
    def compute_derived(self) -> Dict[str, Any]:
        """Compute derived configuration values."""
        return {
            "head_dim": self.hidden_size // self.num_attention_heads,
            "total_parameters": self.estimate_parameters(),
            "memory_bytes": self.estimate_memory(),
            "flops_per_token": self.estimate_flops_per_token(),
        }
    
    def estimate_parameters(self) -> int:
        """
        Estimate total number of parameters.
        
        Returns:
            Estimated parameter count
        """
        # Embeddings
        vocab_params = self.vocab_size * self.hidden_size
        position_params = self.context_length * self.hidden_size
        
        # Transformer layers
        # Attention: QKV + output
        attention_params = 4 * self.hidden_size * self.hidden_size
        
        # Feed-forward: up + down
        ff_multiplier = 4  # Standard transformer
        ff_params = 2 * self.hidden_size * (ff_multiplier * self.hidden_size)
        
        # Layer norms
        ln_params = 2 * self.hidden_size * 2  # gamma and beta
        
        # Per layer
        layer_params = attention_params + ff_params + ln_params
        
        # Total
        total = vocab_params + position_params + self.num_layers * layer_params
        
        # Add output layer
        if not self.tie_word_embeddings:
            total += vocab_params
        
        return int(total)
    
    def estimate_memory(self, dtype_bytes: int = 2) -> int:
        """
        Estimate memory usage in bytes.
        
        Args:
            dtype_bytes: Bytes per parameter (2 for float16/bfloat16)
            
        Returns:
            Estimated memory in bytes
        """
        params = self.estimate_parameters()
        
        # Parameters
        param_memory = params * dtype_bytes
        
        # Optimizer states (Adam: 2x params for momentum and variance)
        optimizer_memory = 2 * params * dtype_bytes
        
        # Gradients
        gradient_memory = params * dtype_bytes
        
        # Activations (rough estimate)
        activation_memory = self.context_length * self.hidden_size * self.num_layers * dtype_bytes
        
        # Total
        total = param_memory + optimizer_memory + gradient_memory + activation_memory
        
        return int(total)
    
    def estimate_flops_per_token(self) -> float:
        """
        Estimate FLOPs per token.
        
        Returns:
            Estimated FLOPs per token
        """
        # Attention FLOPs: 2 * n_ctx * n_embd * n_embd
        attention_flops = 2 * self.context_length * self.hidden_size * self.hidden_size
        
        # Feed-forward FLOPs: 2 * n_embd * (4 * n_embd) * 2 (up and down)
        ff_flops = 2 * self.hidden_size * (4 * self.hidden_size) * 2
        
        # Per layer
        layer_flops = attention_flops + ff_flops
        
        # Total
        total = self.num_layers * layer_flops
        
        return float(total)


@dataclass
class IgrisConfig(ModelConfig):
    """zarx-IGRIS specific configuration."""
    
    # Adaptive routing
    max_depth: int = 24
    min_depth: int = 3
    width_choices: Tuple[int, ...] = (384, 768, 1152, 1536, 2048)
    path_choices: int = 3  # Local, Low-rank, SSM
    
    # Router configuration
    router_hidden_dim: int = 128
    router_num_layers: int = 2
    router_dropout: float = 0.1
    router_temperature: float = 1.0
    router_temperature_annealing: bool = True
    
    # Load balancing
    load_balancing_weight: float = 0.01
    expert_capacity_factor: float = 1.25
    
    # CoT configuration
    cot_dim: int = 256
    cot_components: int = 6
    cot_update_method: str = "gru"  # "gru", "lstm", "linear"
    cot_provable: bool = True
    cot_consistency_weight: float = 0.1
    cot_diversity_weight: float = 0.01
    cot_sparsity_weight: float = 0.001
    cot_orthogonality_weight: float = 0.05
    
    # HASS block configuration
    local_window_size: int = 128
    low_rank_dim: int = 96
    ssm_state_dim: int = 16
    ssm_kernel_size: int = 3
    
    # MoE configuration
    expert_count: int = 192
    top_k_experts: int = 2
    expert_hidden_multiplier: float = 4.0
    shard_experts: bool = True
    expert_shard_dir: str = "experts/"
    max_expert_cache: int = 24
    
    # Merger gate
    merger_hidden_multiplier: float = 2.0
    merger_num_layers: int = 2
    merger_type: str = "gated"
    
    # Progressive quantization
    quant_start_step: int = 1000
    quant_end_step: int = 100000
    quant_levels: Tuple[int, ...] = (32, 16, 12, 8, 4)
    quant_method: str = "symmetric"
    
    # Performance
    target_active_ratio: float = 0.1
    max_active_params_per_token: int = 50_000_000
    
    def __post_init__(self):
        """Post-initialization validation."""
        super().__post_init__()
        
        # Validate routing parameters
        if self.max_depth < self.min_depth:
            raise ValueError(f"max_depth ({self.max_depth}) must be >= min_depth ({self.min_depth})")
        
        if self.max_depth > self.num_layers:
            raise ValueError(
                f"max_depth ({self.max_depth}) must be <= num_layers ({self.num_layers})"
            )
        
        # Validate CoT dimensions
        if self.cot_dim <= 0:
            raise ValueError(f"cot_dim ({self.cot_dim}) must be positive")
        
        if self.cot_components <= 0:
            raise ValueError(f"cot_components ({self.cot_components}) must be positive")
        
        # Validate MoE parameters
        if self.expert_count <= 0:
            raise ValueError(f"expert_count ({self.expert_count}) must be positive")
        
        if self.top_k_experts <= 0 or self.top_k_experts > self.expert_count:
            raise ValueError(
                f"top_k_experts ({self.top_k_experts}) must be between 1 and expert_count ({self.expert_count})"
            )
    
    def compute_derived(self) -> Dict[str, Any]:
        """Compute derived configuration values for zarx-IGRIS."""
        base_derived = super().compute_derived()
        
        # zarx-IGRIS specific derived values
        zarx_derived = {
            "total_cot_dim": self.cot_dim * self.cot_components,
            "expert_hidden_size": int(self.hidden_size * self.expert_hidden_multiplier),
            "merger_hidden_size": int(self.hidden_size * self.merger_hidden_multiplier),
            "router_output_dim": self.max_depth + len(self.width_choices) + self.path_choices + self.expert_count,
            "estimated_active_params": self.estimate_active_parameters(),
            "estimated_efficiency_gain": self.estimate_efficiency_gain(),
            "expert_shard_size_mb": self.estimate_expert_shard_size(),
        }
        
        # Merge with base derived values
        base_derived.update(zarx_derived)
        return base_derived
    
    def estimate_active_parameters(self) -> int:
        """
        Estimate active parameters per token.
        
        Returns:
            Estimated active parameters
        """
        # Base embeddings
        active = self.hidden_size  # Token embedding
        
        # Average active layers
        avg_layers = (self.max_depth + self.min_depth) / 2
        
        # Per active layer
        # Attention (simplified)
        attention_params = 4 * self.hidden_size * self.hidden_size
        
        # FFN (simplified)
        ffn_params = 2 * self.hidden_size * (4 * self.hidden_size)
        
        # Layer norm
        ln_params = 2 * self.hidden_size * 2
        
        layer_params = attention_params + ffn_params + ln_params
        
        # Average width factor
        avg_width = sum(self.width_choices) / len(self.width_choices)
        width_factor = avg_width / self.hidden_size
        
        # Active parameters
        active_params = int(
            active + avg_layers * layer_params * width_factor * self.target_active_ratio
        )
        
        # Add router and CoT
        router_params = self.router_hidden_dim * (self.hidden_size + 1)  # Simplified
        cot_params = self.cot_dim * self.cot_components * 6  # 6 components
        
        active_params += router_params + cot_params
        
        # Add active MoE experts
        expert_params_per = self.hidden_size * int(self.hidden_size * self.expert_hidden_multiplier) * 2
        active_params += self.top_k_experts * expert_params_per
        
        return active_params
    
    def estimate_efficiency_gain(self) -> float:
        """
        Estimate efficiency gain over dense model.
        
        Returns:
            Efficiency gain (higher is better)
        """
        dense_params = self.estimate_parameters()
        active_params = self.estimate_active_parameters()
        
        if active_params == 0:
            return 1.0
        
        return dense_params / active_params
    
    def estimate_expert_shard_size(self, dtype_bytes: int = 2) -> float:
        """
        Estimate expert shard size in MB.
        
        Args:
            dtype_bytes: Bytes per parameter
            
        Returns:
            Shard size in MB
        """
        # Expert parameters
        expert_hidden = int(self.hidden_size * self.expert_hidden_multiplier)
        expert_params = self.hidden_size * expert_hidden * 2  # up and down
        
        # Size in bytes
        size_bytes = expert_params * dtype_bytes
        
        # Convert to MB
        size_mb = size_bytes / (1024 * 1024)
        
        return size_mb


# ==================== PREDEFINED CONFIGURATIONS ====================

class ConfigFactory:
    """Factory for predefined configurations."""
    
    @staticmethod
    def get_config(
        model_size: Union[ModelSize, str],
        architecture: Union[ArchitectureVariant, str] = ArchitectureVariant.ZARX_IGRIS,
        **kwargs
    ) -> IgrisConfig:
        """
        Get predefined configuration.
        
        Args:
            model_size: Model size enum or string
            architecture: Architecture variant
            **kwargs: Additional overrides
            
        Returns:
            Configuration instance
        """
        # Convert string to enum if needed
        if isinstance(model_size, str):
            model_size = ModelSize(model_size)
        
        if isinstance(architecture, str):
            architecture = ArchitectureVariant(architecture)
        
        # Get base configuration for size
        if architecture == ArchitectureVariant.ZARX_IGRIS:
            config_class = IgrisConfig
        else:
            config_class = ModelConfig
        
        # Size-specific configurations
        if model_size == ModelSize.NANO_1M:
            config = config_class(
                model_name="zarx_nano_1m",
                model_size=model_size,
                architecture=architecture,
                vocab_size=4069,
                context_length=1024,
                hidden_size=64,
                num_layers=2,
                num_attention_heads=2,
                max_depth=2,
                min_depth=2,
                width_choices=(16, 32, 64),
                cot_dim=64,
                cot_components=6,
                expert_count=4,
                top_k_experts=2,
            )
        
        elif model_size == ModelSize.NANO_10M:
            config = config_class(
                model_name="zarx_nano_10m",
                model_size=model_size,
                architecture=architecture,
                vocab_size=20000,
                context_length=2048,
                hidden_size=512,
                num_layers=8,
                num_attention_heads=8,
                max_depth=8,
                min_depth=2,
                width_choices=(128, 256, 384, 512),
                cot_dim=128,
                cot_components=6,
                expert_count=32,
                top_k_experts=2,
            )
        
        elif model_size == ModelSize.MICRO_50M:
            config = config_class(
                model_name="zarx_micro_50m",
                model_size=model_size,
                architecture=architecture,
                vocab_size=32000,
                context_length=4096,
                hidden_size=768,
                num_layers=12,
                num_attention_heads=12,
                max_depth=12,
                min_depth=3,
                width_choices=(192, 384, 576, 768),
                cot_dim=192,
                cot_components=5,
                expert_count=64,
                top_k_experts=2,
            )
        
        elif model_size == ModelSize.MINI_277M:
            config = config_class(
                model_name="zarx_igris_277m",
                model_size=model_size,
                architecture=architecture,
                vocab_size=65000,
                context_length=8192,
                hidden_size=2048,
                num_layers=24,
                num_attention_heads=32,
                max_depth=24,
                min_depth=3,
                width_choices=(384, 768, 1152, 1536, 2048),
                cot_dim=256,
                cot_components=6,
                expert_count=192,
                top_k_experts=2,
                target_active_ratio=0.1,
            )
        
        elif model_size == ModelSize.SMALL_500M:
            config = config_class(
                model_name="zarx_small_500m",
                model_size=model_size,
                architecture=architecture,
                vocab_size=65000,
                context_length=8192,
                hidden_size=2560,
                num_layers=24,
                num_attention_heads=40,
                max_depth=24,
                min_depth=4,
                width_choices=(512, 1024, 1536, 2048, 2560),
                cot_dim=320,
                cot_components=6,
                expert_count=256,
                top_k_experts=2,
                target_active_ratio=0.08,
            )
        
        elif model_size == ModelSize.MEDIUM_1B:
            config = config_class(
                model_name="zarx_medium_1b",
                model_size=model_size,
                architecture=architecture,
                vocab_size=65000,
                context_length=16384,
                hidden_size=3072,
                num_layers=32,
                num_attention_heads=48,
                max_depth=32,
                min_depth=4,
                width_choices=(768, 1536, 2304, 3072),
                cot_dim=384,
                cot_components=6,
                expert_count=384,
                top_k_experts=2,
                target_active_ratio=0.07,
            )
        
        elif model_size == ModelSize.LARGE_3B:
            config = config_class(
                model_name="zarx_large_3b",
                model_size=model_size,
                architecture=architecture,
                vocab_size=65000,
                context_length=32768,
                hidden_size=4096,
                num_layers=40,
                num_attention_heads=64,
                max_depth=40,
                min_depth=5,
                width_choices=(1024, 2048, 3072, 4096),
                cot_dim=512,
                cot_components=6,
                expert_count=512,
                top_k_experts=2,
                target_active_ratio=0.06,
            )
        
        elif model_size == ModelSize.XL_7B:
            config = config_class(
                model_name="zarx_xl_7b",
                model_size=model_size,
                architecture=architecture,
                vocab_size=65000,
                context_length=65536,
                hidden_size=6144,
                num_layers=48,
                num_attention_heads=96,
                max_depth=48,
                min_depth=6,
                width_choices=(1536, 3072, 4608, 6144),
                cot_dim=768,
                cot_components=6,
                expert_count=768,
                top_k_experts=2,
                target_active_ratio=0.05,
            )
        
        else:
            raise ValueError(f"Unsupported model size: {model_size}")
        
        # Apply any overrides
        if kwargs:
            config.update(**kwargs)
        
        return config
    
    @staticmethod
    def get_lightweight_config(
        model_name: str = "zarx_lightweight",
        vocab_size: int = 1000,
        context_length: int = 32,
        hidden_size: int = 32,
        num_layers: int = 2,
        num_attention_heads: int = 2,
        expert_count: int = 2,
        top_k_experts: int = 1,
        **kwargs
    ) -> IgrisConfig:
        """
        Get a lightweight configuration for testing purposes.
        
        Args:
            model_name: Name for the lightweight model.
            vocab_size: Reduced vocabulary size.
            context_length: Reduced context length.
            hidden_size: Reduced hidden dimension.
            num_layers: Reduced number of layers.
            num_attention_heads: Reduced number of attention heads.
            expert_count: Reduced number of experts.
            top_k_experts: Reduced top-k experts.
            **kwargs: Additional overrides for the lightweight config.
            
        Returns:
            A lightweight IgrisConfig instance.
        """
        config = IgrisConfig(
            model_name=model_name,
            vocab_size=vocab_size,
            context_length=context_length,
            hidden_size=hidden_size,
            num_layers=num_layers,
            num_attention_heads=num_attention_heads,
            max_depth=num_layers,
            min_depth=1,
            width_choices=(hidden_size,), # Only one width choice for simplicity
            cot_dim=hidden_size // 2,
            cot_components=6, # Changed from 2 to 6 to satisfy IgrisModel validation
            expert_count=expert_count,
            top_k_experts=top_k_experts,
            expert_shard_dir="test_experts/", # Use a specific test directory
            max_expert_cache=2, # Small cache size
            target_active_ratio=1.0, # All active for small models
            router_hidden_dim=hidden_size // 4,
            router_num_layers=1,
            router_dropout=0.0,
            # Disable gradient checkpointing for lightweight model
            gradient_checkpointing=False,
            **kwargs
        )
        # Ensure hidden_size is divisible by num_attention_heads
        if config.hidden_size % config.num_attention_heads != 0:
            config.hidden_size = (config.hidden_size // config.num_attention_heads) * config.num_attention_heads
            if config.hidden_size == 0:
                config.hidden_size = config.num_attention_heads # Ensure it's not zero

        config.head_dim = config.hidden_size // config.num_attention_heads
        return config

    @staticmethod
    def get_all_configs() -> Dict[str, IgrisConfig]:
        """Get all predefined configurations."""
        configs = {}
        
        for model_size in ModelSize:
            try:
                config = ConfigFactory.get_config(model_size)
                configs[model_size.value] = config
            except ValueError:
                continue
        
        return configs
    
    @staticmethod
    def get_optimal_config(
        target_params: int,
        target_active_ratio: float = 0.1,
        **kwargs
    ) -> IgrisConfig:
        """
        Get optimal configuration for target parameter count.
        
        Args:
            target_params: Target total parameters
            target_active_ratio: Target active ratio
            **kwargs: Additional overrides
            
        Returns:
            Optimal configuration
        """
        # Find closest predefined size
        size_mapping = {
            1_000_000: ModelSize.NANO_1M,
            10_000_000: ModelSize.NANO_10M,
            50_000_000: ModelSize.MICRO_50M,
            277_000_000: ModelSize.MINI_277M,
            500_000_000: ModelSize.SMALL_500M,
            1_000_000_000: ModelSize.MEDIUM_1B,
            3_000_000_000: ModelSize.LARGE_3B,
            7_000_000_000: ModelSize.XL_7B,
            13_000_000_000: ModelSize.XXL_13B,
            70_000_000_000: ModelSize.XXXL_70B,
        }
        
        # Find closest size
        closest_size = min(size_mapping.keys(), key=lambda x: abs(x - target_params))
        
        # Get base config
        config = ConfigFactory.get_config(size_mapping[closest_size], **kwargs)
        
        # Adjust to exact target
        if closest_size != target_params:
            # Scale hidden size proportionally
            scale_factor = (target_params / closest_size) ** 0.5  # Square root scaling
            
            config.hidden_size = int(config.hidden_size * scale_factor)
            config.hidden_size = max(256, config.hidden_size)
            
            # Ensure divisibility
            config.hidden_size = (config.hidden_size // config.num_attention_heads) * config.num_attention_heads
            
            # Update derived name
            config.model_name = f"zarx_custom_{target_params//1_000_000}m"
        
        # Update target active ratio
        config.target_active_ratio = target_active_ratio
        
        return config


# ==================== TRAINING CONFIGURATION ====================

@dataclass
class TrainingConfig(BaseConfig):
    """Training configuration."""
    
    # Data
    dataset_path: str = "data/"
    train_split: str = "train"
    val_split: str = "validation"
    test_split: str = "test"
    
    # Tokenization
    tokenizer_path: Optional[str] = None
    max_length: int = 8192
    padding: str = "longest"
    truncation: bool = True
    
    # Training loop
    epochs: int = 3
    steps_per_epoch: Optional[int] = None
    total_steps: Optional[int] = None
    
    # Batch size
    batch_size: int = 1
    micro_batch_size: int = 1
    gradient_accumulation_steps: int = 8
    
    # Optimization
    learning_rate: float = 3e-4
    weight_decay: float = 0.01
    adam_beta1: float = 0.9
    adam_beta2: float = 0.95
    adam_epsilon: float = 1e-8
    
    # Learning rate schedule
    lr_scheduler: str = "cosine"  # "linear", "cosine", "constant"
    warmup_steps: int = 1000
    warmup_ratio: float = 0.05
    
    # Gradient handling
    max_grad_norm: float = 1.0
    gradient_clipping: bool = True
    gradient_checkpointing: bool = True
    
    # Mixed precision
    mixed_precision: str = "bf16"  # "fp16", "bf16", "fp32"
    loss_scale: Optional[float] = None
    
    # Checkpointing
    save_steps: int = 1000
    save_total_limit: int = 5
    save_optimizer: bool = True
    save_scheduler: bool = True
    
    # Evaluation
    eval_steps: int = 500
    eval_strategy: str = "steps"  # "steps", "epoch"
    
    # Logging
    logging_steps: int = 10
    logging_dir: str = "logs/"
    logging_level: str = "INFO"
    
    # Distributed training
    distributed: bool = False
    world_size: int = 1
    rank: int = 0
    local_rank: int = 0
    
    # Hardware
    device: str = "cuda" if TORCH_AVAILABLE and torch.cuda.is_available() else "cpu"
    num_workers: int = 4
    pin_memory: bool = True
    
    # Randomness
    seed: int = 42
    deterministic: bool = True
    
    # Early stopping
    early_stopping: bool = False
    early_stopping_patience: int = 3
    early_stopping_threshold: float = 0.0
    
    # Profiling
    profile: bool = False
    profile_steps: int = 100
    
    def __post_init__(self):
        """Post-initialization validation."""
        # Validate learning rate scheduler
        valid_schedulers = ["linear", "cosine", "constant", "cosine_with_restarts"]
        if self.lr_scheduler not in valid_schedulers:
            raise ValueError(f"Invalid lr_scheduler: {self.lr_scheduler}")
        
        # Validate mixed precision
        valid_precision = ["fp16", "bf16", "fp32"]
        if self.mixed_precision not in valid_precision:
            raise ValueError(f"Invalid mixed_precision: {self.mixed_precision}")
        
        # Validate eval strategy
        valid_strategies = ["steps", "epoch", "no"]
        if self.eval_strategy not in valid_strategies:
            raise ValueError(f"Invalid eval_strategy: {self.eval_strategy}")
        
        # Calculate total steps if needed
        if self.total_steps is None and self.steps_per_epoch is not None:
            self.total_steps = self.epochs * self.steps_per_epoch
    
    def compute_derived(self) -> Dict[str, Any]:
        """Compute derived training values."""
        return {
            "effective_batch_size": self.batch_size * self.gradient_accumulation_steps,
            "warmup_steps_actual": int(self.warmup_steps * self.warmup_ratio),
            "total_training_steps": self.total_steps or (self.epochs * (self.steps_per_epoch or 1000)),
        }


# ==================== DATA CONFIGURATION ====================

@dataclass
class DataConfig(BaseConfig):
    """Data configuration."""
    
    # Dataset
    dataset_name: str = "custom"
    dataset_format: str = "jsonl"  # "jsonl", "parquet", "huggingface"
    text_column: str = "text"
    target_column: str = "target"
    
    # CoT data
    cot_enabled: bool = True
    cot_column: str = "cot"
    answer_column: str = "answer"
    
    # Synthetic data
    synthetic_data_ratio: float = 0.36  # 1T/2.8T
    synthetic_data_path: str = "synthetic_data/"
    
    # Preprocessing
    preprocessing_pipeline: List[str] = field(default_factory=lambda: [
        "tokenize",
        "truncate",
        "pad"
    ])
    
    # Filtering
    min_length: int = 1
    max_length: int = 8192
    filter_toxic: bool = True
    filter_low_quality: bool = True
    
    # Augmentation
    augmentation_enabled: bool = False
    augmentation_methods: List[str] = field(default_factory=lambda: [])
    augmentation_probability: float = 0.1
    
    # Caching
    cache_dir: str = ".cache/"
    use_cache: bool = True
    overwrite_cache: bool = False
    
    # Streaming
    streaming: bool = False
    streaming_buffer_size: int = 1000
    
    # Shuffling
    shuffle: bool = True
    shuffle_buffer_size: int = 10000
    shuffle_seed: int = 42
    
    # Batching
    batch_size: int = 1
    drop_last: bool = False
    collate_fn: Optional[str] = None
    
    def __post_init__(self):
        """Post-initialization validation."""
        # Validate dataset format
        valid_formats = ["jsonl", "parquet", "huggingface", "csv", "text", "bin"]
        if self.dataset_format not in valid_formats:
            raise ValueError(f"Invalid dataset_format: {self.dataset_format}")
        
        # Validate preprocessing pipeline
        valid_operations = ["tokenize", "truncate", "pad", "mask", "chunk"]
        for op in self.preprocessing_pipeline:
            if op not in valid_operations:
                warnings.warn(f"Unknown preprocessing operation: {op}")
        
        # Ensure paths exist
        for path in [self.synthetic_data_path, self.cache_dir]:
            Path(path).mkdir(parents=True, exist_ok=True)
    
    def compute_derived(self) -> Dict[str, Any]:
        """Compute derived data values."""
        return {
            "cache_path": str(Path(self.cache_dir) / f"{self.dataset_name}_processed"),
            "synthetic_samples_needed": int(1_000_000_000 * self.synthetic_data_ratio),
            "estimated_dataset_size": self.estimate_dataset_size(),
        }
    
    def estimate_dataset_size(self) -> int:
        """
        Estimate dataset size in tokens.
        
        Returns:
            Estimated token count
        """
        # Rough estimate: 1MB ≈ 200,000 tokens
        # This is a placeholder - actual implementation would check files
        return 2_800_000_000_000  # 2.8T tokens default


# ==================== QUANTIZATION CONFIGURATION ====================

@dataclass
class QuantizationConfig(BaseConfig):
    """Quantization configuration."""
    
    # General
    enabled: bool = True
    method: str = "progressive"  # "static", "dynamic", "progressive", "aware"
    
    # Bit widths
    weight_bits: int = 8
    activation_bits: int = 8
    embedding_bits: int = 8
    
    # Progressive quantization
    progressive_enabled: bool = True
    progressive_start_step: int = 1000
    progressive_end_step: int = 100000
    progressive_levels: Tuple[int, ...] = (32, 16, 12, 8, 4)
    
    # Quantization scheme
    scheme: str = "symmetric"  # "symmetric", "asymmetric"
    per_channel: bool = True
    per_tensor: bool = False
    
    # Calibration
    calibration_samples: int = 100
    calibration_method: str = "minmax"  # "minmax", "histogram", "percentile"
    
    # Quantization-aware training
    qat_enabled: bool = False
    qat_start_step: int = 10000
    qat_num_steps: int = 5000
    
    # Observer
    observer_enabled: bool = True
    observer_momentum: float = 0.1
    observer_averaging_constant: float = 0.01
    
    # Fake quantization
    fake_quant_enabled: bool = True
    fake_quant_mode: str = "training"  # "training", "calibration"
    
    # Layer-wise quantization
    layerwise_quantization: bool = True
    skip_layers: List[str] = field(default_factory=lambda: ["router", "cot"])
    
    # Compression
    compression_enabled: bool = True
    compression_method: str = "gzip"  # "gzip", "lz4", "zstd"
    compression_level: int = 6
    
    def __post_init__(self):
        """Post-initialization validation."""
        # Validate quantization method
        valid_methods = ["static", "dynamic", "progressive", "aware"]
        if self.method not in valid_methods:
            raise ValueError(f"Invalid quantization method: {self.method}")
        
        # Validate bit widths
        valid_bits = [2, 3, 4, 5, 6, 7, 8, 16, 32]
        for bits in [self.weight_bits, self.activation_bits, self.embedding_bits]:
            if bits not in valid_bits:
                raise ValueError(f"Invalid bit width: {bits}")
        
        # Validate scheme
        if self.scheme not in ["symmetric", "asymmetric"]:
            raise ValueError(f"Invalid quantization scheme: {self.scheme}")
        
        # Validate calibration method
        valid_calibration = ["minmax", "histogram", "percentile"]
        if self.calibration_method not in valid_calibration:
            raise ValueError(f"Invalid calibration method: {self.calibration_method}")
    
    def compute_derived(self) -> Dict[str, Any]:
        """Compute derived quantization values."""
        return {
            "compression_ratio": self.estimate_compression_ratio(),
            "memory_savings": self.estimate_memory_savings(),
            "quantization_error": self.estimate_quantization_error(),
        }
    
    def estimate_compression_ratio(self) -> float:
        """
        Estimate compression ratio.
        
        Returns:
            Estimated compression ratio
        """
        # Base ratio from bit reduction
        base_ratio = 32 / self.weight_bits
        
        # Additional compression
        compression_ratios = {
            "gzip": 2.0,
            "lz4": 1.5,
            "zstd": 2.2,
            "none": 1.0,
        }
        
        compression_boost = compression_ratios.get(self.compression_method, 1.0)
        
        return base_ratio * compression_boost
    
    def estimate_memory_savings(self) -> float:
        """
        Estimate memory savings.
        
        Returns:
            Memory savings factor
        """
        # From 32-bit to target bits
        return 32.0 / self.weight_bits
    
    def estimate_quantization_error(self) -> float:
        """
        Estimate quantization error.
        
        Returns:
            Estimated error (0-1)
        """
        # Empirical error estimates based on bit width
        error_map = {
            2: 0.3,
            3: 0.2,
            4: 0.1,
            5: 0.07,
            6: 0.05,
            7: 0.03,
            8: 0.02,
            16: 0.001,
            32: 0.0,
        }
        
        base_error = error_map.get(self.weight_bits, 0.1)
        
        # Error reduction from techniques
        if self.per_channel:
            base_error *= 0.7
        
        if self.calibration_samples > 100:
            base_error *= 0.8
        
        if self.qat_enabled:
            base_error *= 0.5
        
        return min(1.0, base_error)


# ==================== COMPLETE CONFIGURATION ====================

@dataclass
class CompleteConfig(BaseConfig):
    """Complete configuration for zarx-IGRIS."""
    
    # Model configuration
    model: IgrisConfig = field(default_factory=lambda: IgrisConfig())
    
    # Training configuration
    training: TrainingConfig = field(default_factory=lambda: TrainingConfig())
    
    # Data configuration
    data: DataConfig = field(default_factory=lambda: DataConfig())
    
    # Quantization configuration
    quantization: QuantizationConfig = field(default_factory=lambda: QuantizationConfig())
    
    # Logging configuration
    logging: Dict[str, Any] = field(default_factory=lambda: {
        "level": "INFO",
        "format": "json",
        "output_dir": "logs/",
        "wandb": False,
        "tensorboard": True,
    })
    
    # Optimization flags
    optimization: Dict[str, Any] = field(default_factory=lambda: {
        "compile": False,
        "fused_ops": True,
        "memory_efficient": True,
        "cpu_optimized": True,
    })
    
    # Performance targets
    performance: Dict[str, Any] = field(default_factory=lambda: {
        "target_mmlu": 70.0,
        "target_gpqa": 68.0,
        "target_tokens_per_second": 1000,
        "target_active_ratio": 0.1,
    })
    
    def __post_init__(self):
        """Post-initialization validation and synchronization."""
        # Synchronize configurations
        self._synchronize_configs()
        
        # Validate
        errors = self.validate()
        if errors:
            raise ValueError(f"Configuration errors: {errors}")
    
    def _synchronize_configs(self):
        """Synchronize configurations between components."""
        # Sync model and training device
        if self.training.device != self.model.__dict__.get('device', 'cpu'):
            self.model.device = self.training.device
        
        # Sync batch sizes
        if self.data.batch_size != self.training.batch_size:
            self.data.batch_size = self.training.batch_size
        
        # Sync context lengths
        if self.data.max_length != self.model.context_length:
            self.data.max_length = self.model.context_length
        
        # Sync quantization settings
        if self.quantization.enabled:
            self.model.quantization = QuantizationScheme.PROGRESSIVE
    
    def validate(self) -> List[str]:
        """Validate complete configuration."""
        errors = []
        
        # Validate individual configs
        errors.extend(self.model.validate())
        errors.extend(self.training.validate())
        errors.extend(self.data.validate())
        errors.extend(self.quantization.validate())
        
        # Cross-config validation
        if self.model.context_length < self.data.max_length:
            errors.append(
                f"Model context_length ({self.model.context_length}) "
                f"must be >= data.max_length ({self.data.max_length})"
            )
        
        if self.training.batch_size % self.data.batch_size != 0:
            errors.append(
                f"training.batch_size ({self.training.batch_size}) "
                f"must be divisible by data.batch_size ({self.data.batch_size})"
            )
        
        return errors
    
    def compute_derived(self) -> Dict[str, Any]:
        """Compute all derived values."""
        derived = {
            "model": self.model.compute_derived(),
            "training": self.training.compute_derived(),
            "data": self.data.compute_derived(),
            "quantization": self.quantization.compute_derived(),
            "performance": self._compute_performance_metrics(),
            "hardware_requirements": self._compute_hardware_requirements(),
        }
        
        # Flatten for easy access
        flattened = {}
        for category, values in derived.items():
            for key, value in values.items():
                flattened[f"{category}_{key}"] = value
        
        return flattened
    
    def _compute_performance_metrics(self) -> Dict[str, Any]:
        """Compute performance metrics."""
        from zarx.utils.math_utils import PerformancePredictor
        
        # Get effective parameters
        effective_params = self.model.estimate_active_parameters() * self.model.estimate_efficiency_gain()
        
        # Predict performance
        mmlu = PerformancePredictor.predict_mmlu_score(
            effective_params,
            self.data.estimate_dataset_size(),
            architecture_efficiency=2.0  # zarx-IGRIS efficiency
        )
        
        gpqa = PerformancePredictor.predict_gpqa_score(
            mmlu,
            self.data.synthetic_data_ratio,
            reasoning_efficiency=1.5  # CoT efficiency
        )
        
        # Compute throughput
        flops_per_token = self.model.estimate_flops_per_token()
        active_flops = flops_per_token * self.model.target_active_ratio
        
        # Estimate tokens per second (simplified)
        # Assume 1 TFLOPS for CPU, 100 TFLOPS for GPU
        device_flops = 1e12 if "cuda" in self.training.device else 1e12
        tokens_per_second = device_flops / active_flops
        
        return {
            "predicted_mmlu": mmlu,
            "predicted_gpqa": gpqa,
            "predicted_tokens_per_second": tokens_per_second,
            "effective_parameters": effective_params,
            "parameter_efficiency": effective_params / self.model.estimate_parameters(),
            "performance_gap": {
                "mmlu": self.performance["target_mmlu"] - mmlu,
                "gpqa": self.performance["target_gpqa"] - gpqa,
                "throughput": tokens_per_second - self.performance["target_tokens_per_second"],
            }
        }
    
    def _compute_hardware_requirements(self) -> Dict[str, Any]:
        """Compute hardware requirements."""
        # Memory requirements
        param_memory = self.model.estimate_memory(dtype_bytes=2)  # bfloat16
        gradient_memory = param_memory
        optimizer_memory = 2 * param_memory  # Adam states
        
        # Activation memory (rough estimate)
        activation_memory = (
            self.model.context_length *
            self.model.hidden_size *
            self.model.num_layers *
            2  # bytes
        )
        
        total_memory = param_memory + gradient_memory + optimizer_memory + activation_memory
        
        # Convert to GB
        total_memory_gb = total_memory / (1024 ** 3)
        
        # CPU requirements
        cpu_cores_needed = max(4, self.training.num_workers * 2)
        
        # Disk space
        checkpoint_size = param_memory * 1.2  # 20% overhead
        dataset_size = self.data.estimate_dataset_size() * 4 / (1024 ** 3)  # 4 bytes per token in GB
        
        # Expert shards (if applicable)
        expert_shards_gb = 0
        if hasattr(self.model, 'expert_count') and hasattr(self.model, 'estimate_expert_shard_size'):
            expert_shards_gb = (
                self.model.expert_count *
                self.model.estimate_expert_shard_size() /
                1024  # MB to GB
            )
        
        return {
            "minimum_ram_gb": total_memory_gb * 1.5,  # 50% safety margin
            "recommended_ram_gb": total_memory_gb * 2,
            "cpu_cores": cpu_cores_needed,
            "disk_space_gb": checkpoint_size + dataset_size + expert_shards_gb,
            "gpu_memory_gb": total_memory_gb if "cuda" in self.training.device else 0,
            "checkpoint_size_gb": checkpoint_size / (1024 ** 3),
        }


# ==================== CONFIGURATION MANAGER ====================

class ConfigManager:
    """Manager for configuration loading, saving, and validation."""
    
    def __init__(self, config_dir: str = "configs/"):
        """
        Initialize config manager.
        
        Args:
            config_dir: Directory for configuration files
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache for configurations
        self._config_cache: Dict[str, CompleteConfig] = {}
    
    def create_config(
        self,
        model_size: Union[ModelSize, str],
        config_name: Optional[str] = None,
        **overrides
    ) -> CompleteConfig:
        """
        Create a new configuration.
        
        Args:
            model_size: Model size
            config_name: Configuration name
            **overrides: Configuration overrides
            
        Returns:
            Complete configuration
        """
        # Get model config
        model_config = ConfigFactory.get_config(model_size)
        
        # Apply overrides to model config
        model_overrides = {k: v for k, v in overrides.items() if not k.startswith(('training_', 'data_', 'quantization_'))}
        if model_overrides:
            model_config.update(**model_overrides)
        
        # Create complete config
        config = CompleteConfig(model=model_config)
        
        # Apply other overrides
        for key, value in overrides.items():
            if key.startswith('training_'):
                config.training.update(**{key[9:]: value})
            elif key.startswith('data_'):
                config.data.update(**{key[5:]: value})
            elif key.startswith('quantization_'):
                config.quantization.update(**{key[13:]: value})
            elif key.startswith('logging_'):
                config.logging[key[8:]] = value
            elif key.startswith('optimization_'):
                config.optimization[key[13:]] = value
            elif key.startswith('performance_'):
                config.performance[key[12:]] = value
        
        # Set config name
        if config_name:
            config.model.model_name = config_name
        
        # Cache configuration
        cache_key = config_name or model_config.model_name
        self._config_cache[cache_key] = config
        
        return config
    
    def save_config(self, config: CompleteConfig, name: Optional[str] = None):
        """
        Save configuration to file.
        
        Args:
            config: Configuration to save
            name: Configuration name (uses model name if None)
        """
        name = name or config.model.model_name
        path = self.config_dir / f"{name}.yaml"
        
        config.save(path)
        
        # Also save derived values for reference
        derived_path = self.config_dir / f"{name}_derived.json"
        with open(derived_path, 'w') as f:
            json.dump(config.compute_derived(), f, indent=2)
    
    def load_config(self, name: str) -> CompleteConfig:
        """
        Load configuration from file.
        
        Args:
            name: Configuration name
            
        Returns:
            Loaded configuration
        """
        # Check cache first
        if name in self._config_cache:
            return self._config_cache[name]
        
        # Try different file formats
        for ext in ['.yaml', '.yml', '.json']:
            path = self.config_dir / f"{name}{ext}"
            if path.exists():
                config = CompleteConfig.load(path)
                self._config_cache[name] = config
                return config
        
        raise FileNotFoundError(f"Configuration '{name}' not found in {self.config_dir}")
    
    def list_configs(self) -> List[str]:
        """
        List available configurations.
        
        Returns:
            List of configuration names
        """
        configs = []
        
        for ext in ['.yaml', '.yml', '.json']:
            configs.extend([
                path.stem for path in self.config_dir.glob(f"*{ext}")
                if not path.name.endswith('_derived.json')
            ])
        
        return sorted(set(configs))
    
    def get_default_configs(self) -> Dict[str, CompleteConfig]:
        """
        Get all default configurations.
        
        Returns:
            Dictionary of configurations by size
        """
        configs = {}
        
        for model_size in ModelSize:
            try:
                config = self.create_config(model_size)
                configs[model_size.value] = config
                self.save_config(config, f"default_{model_size.value}")
            except Exception as e:
                warnings.warn(f"Failed to create config for {model_size}: {e}")
        
        return configs
    
    def validate_config(self, config: CompleteConfig) -> Tuple[bool, List[str]]:
        """
        Validate configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            (is_valid, error_messages)
        """
        errors = config.validate()
        return len(errors) == 0, errors
    
    def optimize_config(
        self,
        config: CompleteConfig,
        target_device: str = "cpu",
        target_memory_gb: Optional[float] = None
    ) -> CompleteConfig:
        """
        Optimize configuration for target device and memory.
        
        Args:
            config: Configuration to optimize
            target_device: Target device ("cpu" or "cuda")
            target_memory_gb: Target memory in GB
            
        Returns:
            Optimized configuration
        """
        optimized = config.copy()
        
        # Optimize for device
        if target_device == "cpu":
            # CPU optimizations
            optimized.training.device = "cpu"
            optimized.training.mixed_precision = "fp32"  # CPU often benefits from fp32
            optimized.training.num_workers = min(8, optimized.training.num_workers)
            optimized.optimization["cpu_optimized"] = True
            optimized.optimization["compile"] = False  # torch.compile not always better on CPU
            
            # Reduce batch size for CPU
            optimized.training.batch_size = max(1, optimized.training.batch_size // 2)
            optimized.data.batch_size = optimized.training.batch_size
            
        elif target_device == "cuda":
            # GPU optimizations
            optimized.training.device = "cuda"
            optimized.training.mixed_precision = "bf16"
            optimized.optimization["compile"] = True
            optimized.optimization["fused_ops"] = True
        
        # Optimize for memory
        if target_memory_gb is not None:
            current_memory = optimized.model.estimate_memory() / (1024 ** 3)
            
            if current_memory > target_memory_gb:
                # Reduce model size proportionally
                reduction_factor = target_memory_gb / current_memory
                
                # Scale hidden size (maintain aspect ratio)
                new_hidden = int(optimized.model.hidden_size * (reduction_factor ** 0.5))
                new_hidden = max(256, (new_hidden // optimized.model.num_attention_heads) * optimized.model.num_attention_heads)
                
                optimized.model.hidden_size = new_hidden
                
                # Reduce layers if needed
                if reduction_factor < 0.5:
                    optimized.model.num_layers = max(6, int(optimized.model.num_layers * reduction_factor))
                
                # Update model name
                optimized.model.model_name = f"{optimized.model.model_name}_memopt"
        
        # Re-validate
        is_valid, errors = self.validate_config(optimized)
        if not is_valid:
            warnings.warn(f"Optimization created invalid config: {errors}")
        
        return optimized


# ==================== GLOBAL CONFIGURATION ====================

# Global configuration manager
_GLOBAL_CONFIG_MANAGER: Optional[ConfigManager] = None
_CURRENT_CONFIG: Optional[CompleteConfig] = None


def setup_global_config(
    model_size: Union[ModelSize, str] = ModelSize.MINI_277M,
    config_name: Optional[str] = None,
    config_dir: str = "configs/",
    **overrides
) -> CompleteConfig:
    """
    Setup global configuration.
    
    Args:
        model_size: Model size
        config_name: Configuration name
        config_dir: Configuration directory
        **overrides: Configuration overrides
        
    Returns:
        Global configuration
    """
    global _GLOBAL_CONFIG_MANAGER, _CURRENT_CONFIG
    
    # Create config manager if needed
    if _GLOBAL_CONFIG_MANAGER is None:
        _GLOBAL_CONFIG_MANAGER = ConfigManager(config_dir)
    
    # Create or load configuration
    if config_name and config_name in _GLOBAL_CONFIG_MANAGER.list_configs():
        _CURRENT_CONFIG = _GLOBAL_CONFIG_MANAGER.load_config(config_name)
    else:
        _CURRENT_CONFIG = _GLOBAL_CONFIG_MANAGER.create_config(
            model_size, config_name, **overrides
        )
    
    return _CURRENT_CONFIG


def get_global_config() -> CompleteConfig:
    """
    Get global configuration.
    
    Returns:
        Global configuration
    """
    global _CURRENT_CONFIG
    
    if _CURRENT_CONFIG is None:
        # Setup default configuration
        _CURRENT_CONFIG = setup_global_config()
    
    return _CURRENT_CONFIG


def update_global_config(**kwargs):
    """
    Update global configuration.
    
    Args:
        **kwargs: Configuration updates
    """
    global _CURRENT_CONFIG
    
    if _CURRENT_CONFIG is None:
        get_global_config()
    
    config = get_global_config()
    for key, value in kwargs.items():
        if key.startswith('training_'):
            config.training.update(**{key[len('training_'):]: value})
        elif key.startswith('data_'):
            config.data.update(**{key[len('data_'):]: value})
        elif key.startswith('quantization_'):
            config.quantization.update(**{key[len('quantization_'):]: value})
        elif key.startswith('logging_'):
            config.logging[key[8:]] = value
        elif key.startswith('optimization_'):
            config.optimization[key[13:]] = value
        elif key.startswith('performance_'):
            config.performance[key[12:]] = value
        elif hasattr(config, key):
            setattr(config, key, value)
        elif '.' in key:
            parts = key.split('.')
            obj = config
            for part in parts[:-1]:
                obj = getattr(obj, part)
            setattr(obj, parts[-1], value)
        else:
            warnings.warn(f"Ignoring unknown config key: {key}")

__all__ = [
    'ModelSize',
    'ArchitectureVariant',
    'RouterType',
    'CoTType',
    'QuantizationScheme',
    'BaseConfig',
    'ModelConfig',
    'IgrisConfig',
    'TrainingConfig',
    'DataConfig',
    'QuantizationConfig',
    'CompleteConfig',
    'ConfigFactory',
    'ConfigManager',
    'setup_global_config',
    'get_global_config',
    'update_global_config',
]