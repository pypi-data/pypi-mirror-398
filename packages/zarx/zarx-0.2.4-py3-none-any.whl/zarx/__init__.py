"""
zarx - Zero-to-AGI Deep Learning Framework
Version 0.2.2 - Major Architectural Upgrade

zarx provides a clean, production-ready interface for deep learning:
- Explicit model selection (IGRIS_277M, IGRIS_7B, etc.)
- Efficient data pipeline with binary formats
- Comprehensive tokenizer system
- Resume/continue training support
- Production-grade error handling

Quick Start:
    >>> import zarx
    >>> 
    >>> # 1. Load model
    >>> model = zarx.IGRIS_277M()
    >>> 
    >>> # 2. Load tokenizer
    >>> tokenizer = zarx.load_pretrained('zarx_32k')
    >>> 
    >>> # 3. Convert data
    >>> zarx.txt_to_bin('train.txt', 'train.bin', tokenizer, max_length=2048)
    >>> 
    >>> # 4. Load data
    >>> data = zarx.load_from_bin('train.bin', batch_size=32)
    >>> 
    >>> # 5. Train
    >>> trainer = zarx.train(model, data, epochs=10)
    >>> trainer.train()

For detailed documentation, see: https://github.com/yourusername/zarx
"""

__version__ = "0.2.4"
__author__ = "Akik faraji"


# =============================================================================
# MODELS - Explicit model selection
# =============================================================================

from .models.igris import (
    IGRIS_1M,
    IGRIS_10M,
    IGRIS_50M,
    IGRIS_277M,      # Flagship model
    IGRIS_500M,
    IGRIS_1_3B,
    IGRIS_7B,
)

from .models import (
    list_models,
    get_model,
    create_model,
    ModelRegistry,
)

# Legacy aliases
IGRIS277M = IGRIS_277M  # Backward compatibility


# =============================================================================
# TOKENIZER - Load and train tokenizers
# =============================================================================

from .tokenizer import (
    # Loading
    load_pretrained,
    load_from_path,
    list_pretrained,
    
    # Training
    train_tokenizer,
    
    # Info
    has_pretrained,
    get_pretrained_path,
)


# =============================================================================
# DATA - Data conversion and loading
# =============================================================================

from .data import (
    # Conversion (txt/json/jsonl -> bin)
    txt_to_bin,
    json_to_bin,
    jsonl_to_bin,
    parquet_to_bin,
    
    # Loading
    load_from_bin,
    load_from_npy,
    load_from_dir,
    load_from_txt,
    load_from_json,
    load_from_jsonl,
    
    # Validation
    validate_data,
    
    # Classes
    DataConverter,
    BinaryDataset,
    DirectoryLoader,
)


# =============================================================================
# TRAINING - Train and continue training
# =============================================================================

from .training import (
    # High-level API
    train,
    continue_train,
    evaluate,
    
    # Classes
    Trainer,
    CheckpointManager,
    TrainingState,
)


# =============================================================================
# EXCEPTIONS - Better error handling
# =============================================================================

from .exceptions import (
    # Base
    ZARXError,
    
    # Model
    ModelError,
    ModelNotFoundError,
    
    # Data
    DataError,
    DataLoadError,
    DataFormatError,
    
    # Tokenizer
    TokenizerError,
    TokenizerNotFoundError,
    
    # Checkpoint
    CheckpointError,
    CheckpointNotFoundError,
    
    # Training
    TrainingError,
)


# =============================================================================
# CONFIGURATION
# =============================================================================

from .config import (
    ConfigFactory,
    IgrisConfig,
    ModelSize,
)


# =============================================================================
# UTILITIES
# =============================================================================

def info():
    """
    Print zarx library information.
    
    Shows version, available components, and quick start guide.
    """
    print(f"\nZARX - Framework v{__version__}")
    print("="*70)
    
    # Models
    models = list_models()
    print(f"\n📦 Models: {len(models)} variants available")
    print(f"   Flagship: IGRIS_277M (277M params, ~26M active)")
    print(f"   Range: IGRIS_1M → IGRIS_7B")
    
    # Tokenizers
    tokenizers = list_pretrained()
    if tokenizers:
        print(f"\n🔤 Tokenizers: {len(tokenizers)} pretrained available")
        print(f"   {', '.join(tokenizers)}")
    else:
        print(f"\n🔤 Tokenizers: 0 pretrained (train with zarx.train_tokenizer)")
    
    # Data formats
    print(f"\n💾 Data Formats:")
    print(f"   Input: txt, json, jsonl, parquet")
    print(f"   Training: .bin (tokenized, memory-mapped)")
    print(f"   Conversion: txt_to_bin(), json_to_bin(), etc.")
    
    # Training
    print(f"\n🚀 Training:")
    print(f"   Initial: zarx.train(model, data, epochs=10)")
    print(f"   Continue: zarx.continue_train(model, data, checkpoint)")
    print(f"   Resume/continue support with checkpoint versioning")
    
    print("\n" + "="*70)
    print("Quick Start: import zarx; help(zarx)")
    print("Docs: https://github.com/Akik-Forazi/zarx.git")
    """
    Returns:
        Dict with installation status
    """
    status = {
        'version': __version__,
        'models_available': len(list_models()),
        'tokenizers_available': len(list_pretrained()),
    }
    
    # Check dependencies
    dependencies = {}
    
    try:
        import torch
        dependencies['torch'] = torch.__version__
    except ImportError:
        dependencies['torch'] = None
    
    try:
        import numpy
        dependencies['numpy'] = numpy.__version__
    except ImportError:
        dependencies['numpy'] = None
    
    try:
        import tokenizers
        dependencies['tokenizers'] = tokenizers.__version__
    except ImportError:
        dependencies['tokenizers'] = None
    
    status['dependencies'] = dependencies
    
    # Print report
    print(f"\nZARX Installation Check")
    print("="*70)
    print(f"Version: {status['version']}")
    print(f"Models: {status['models_available']} available")
    print(f"Tokenizers: {status['tokenizers_available']} pretrained")
    print("\nDependencies:")
    for name, version in dependencies.items():
        status_icon = "✅" if version else "❌"
        version_str = version if version else "NOT INSTALLED"
        print(f"  {status_icon} {name}: {version_str}")
    
    all_ok = all(v is not None for v in dependencies.values())
    
    if all_ok:
        print("\n✅ All dependencies installed!")
    else:
        print("\n⚠️  Some dependencies missing. Install with:")
        if not dependencies['torch']:
            print("   pip install torch")
        if not dependencies['numpy']:
            print("   pip install numpy")
        if not dependencies['tokenizers']:
            print("   pip install tokenizers")
    
    print("="*70 + "\n")
    
    return status


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Version
    '__version__',
    '__author__',
    
    # === MODELS ===
    'IGRIS_1M',
    'IGRIS_10M',
    'IGRIS_50M',
    'IGRIS_277M',
    'IGRIS_500M',
    'IGRIS_1_3B',
    'IGRIS_7B',
    'IGRIS277M',  # Legacy
    'list_models',
    'get_model',
    'create_model',
    'ModelRegistry',
    
    # === TOKENIZER ===
    'load_pretrained',
    'load_from_path',
    'list_pretrained',
    'train_tokenizer',
    'has_pretrained',
    'get_pretrained_path',
    
    # === DATA ===
    # Conversion
    'txt_to_bin',
    'json_to_bin',
    'jsonl_to_bin',
    'parquet_to_bin',
    # Loading
    'load_from_bin',
    'load_from_npy',
    'load_from_dir',
    'load_from_txt',
    'load_from_json',
    'load_from_jsonl',
    # Validation
    'validate_data',
    # Classes
    'DataConverter',
    'BinaryDataset',
    'DirectoryLoader',
    
    # === TRAINING ===
    'train',
    'continue_train',
    'evaluate',
    'Trainer',
    'CheckpointManager',
    'TrainingState',
    
    # === EXCEPTIONS ===
    'ZARXError',
    'ModelError',
    'ModelNotFoundError',
    'DataError',
    'DataLoadError',
    'DataFormatError',
    'TokenizerError',
    'TokenizerNotFoundError',
    'CheckpointError',
    'CheckpointNotFoundError',
    'TrainingError',
    
    # === CONFIG ===
    'ConfigFactory',
    'IgrisConfig',
    'ModelSize',
    
    # === UTILITIES ===
    'info',
    'check_installation',
]


# =============================================================================
# INITIALIZATION
# =============================================================================

def _initialize():
    """Initialize zarx on first import."""
    import os
    
    # Only run once per session
    if os.environ.get('ZARX_INITIALIZED'):
        return
    
    os.environ['ZARX_INITIALIZED'] = '1'
    
    # Optional: Print welcome message
    if os.environ.get('ZARX_VERBOSE'):
        print(f"zarx v{__version__} loaded")
        print(f"  Models: {len(list_models())} available")
        tokenizers = list_pretrained()
        if tokenizers:
            print(f"  Tokenizers: {len(tokenizers)} pretrained")
        print("  Use zarx.info() for more details\n")


# Run initialization
_initialize()