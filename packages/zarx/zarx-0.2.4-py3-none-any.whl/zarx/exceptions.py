"""
zarx Custom Exceptions
Production-grade error handling with actionable messages.
"""

class ZARXError(Exception):
    """Base exception for all zarx errors."""
    
    def __init__(self, message: str, details: dict = None, suggestion: str = None):
        self.message = message
        self.details = details or {}
        self.suggestion = suggestion
        super().__init__(self.format_message())
    
    def format_message(self) -> str:
        """Format error message with details and suggestion."""
        msg = f"{self.__class__.__name__}: {self.message}"
        
        if self.details:
            msg += f"\nDetails: {self.details}"
        
        if self.suggestion:
            msg += f"\n💡 Suggestion: {self.suggestion}"
        
        return msg


# === MODEL ERRORS ===

class ModelError(ZARXError):
    """Base error for model-related issues."""
    pass


class ModelNotFoundError(ModelError):
    """Raised when a model variant cannot be found."""
    
    def __init__(self, model_name: str, available_models: list = None):
        super().__init__(
            message=f"Model '{model_name}' not found",
            details={"requested": model_name, "available": available_models},
            suggestion=f"Use zarx.list_models() to see available models"
        )


class ModelConfigError(ModelError):
    """Raised when model configuration is invalid."""
    pass


class ModelLoadError(ModelError):
    """Raised when model loading fails."""
    pass


# === DATA ERRORS ===

class DataError(ZARXError):
    """Base error for data-related issues."""
    pass


class DataFormatError(DataError):
    """Raised when data format is invalid or unsupported."""
    
    def __init__(self, format_type: str, reason: str, supported_formats: list = None):
        super().__init__(
            message=f"Invalid data format: {format_type}",
            details={"format": format_type, "reason": reason, "supported": supported_formats},
            suggestion="Check that your data files are properly formatted and the format is supported"
        )


class DataValidationError(DataError):
    """Raised when data fails validation."""
    
    def __init__(self, validation_errors: list):
        super().__init__(
            message="Data validation failed",
            details={"errors": validation_errors},
            suggestion="Review the validation errors and fix your data accordingly"
        )


class DataLoadError(DataError):
    """Raised when data loading fails."""
    pass


class DataConversionError(DataError):
    """Raised when data conversion fails."""
    
    def __init__(self, from_format: str, to_format: str, reason: str):
        super().__init__(
            message=f"Failed to convert {from_format} to {to_format}",
            details={"from": from_format, "to": to_format, "reason": reason},
            suggestion="Check that input files are valid and accessible"
        )


# === TOKENIZER ERRORS ===

class TokenizerError(ZARXError):
    """Base error for tokenizer-related issues."""
    pass


class TokenizerNotFoundError(TokenizerError):
    """Raised when a tokenizer cannot be found."""
    
    def __init__(self, tokenizer_name: str, available_tokenizers: list = None):
        super().__init__(
            message=f"Tokenizer '{tokenizer_name}' not found",
            details={"requested": tokenizer_name, "available": available_tokenizers},
            suggestion="Use zarx.list_pretrained() to see available tokenizers"
        )


class TokenizerTrainingError(TokenizerError):
    """Raised when tokenizer training fails."""
    pass


class TokenizerLoadError(TokenizerError):
    """Raised when tokenizer loading fails."""
    
    def __init__(self, path: str, reason: str):
        super().__init__(
            message=f"Failed to load tokenizer from {path}",
            details={"path": path, "reason": reason},
            suggestion="Check that the tokenizer file exists and is a valid tokenizer.json file"
        )


# === CONFIG ERRORS ===

class ConfigError(ZARXError):
    """Base error for configuration issues."""
    pass


class ConfigValidationError(ConfigError):
    """Raised when configuration validation fails."""
    
    def __init__(self, validation_errors: list):
        super().__init__(
            message="Configuration validation failed",
            details={"errors": validation_errors},
            suggestion="Review the configuration errors and fix them accordingly"
        )


class ConfigLoadError(ConfigError):
    """Raised when configuration loading fails."""
    pass


class ConfigSaveError(ConfigError):
    """Raised when configuration saving fails."""
    pass


# === CHECKPOINT ERRORS ===

class CheckpointError(ZARXError):
    """Base error for checkpoint-related issues."""
    pass


class CheckpointNotFoundError(CheckpointError):
    """Raised when a checkpoint cannot be found."""
    
    def __init__(self, checkpoint_path: str):
        super().__init__(
            message=f"Checkpoint not found: {checkpoint_path}",
            details={"path": checkpoint_path},
            suggestion="Check that the checkpoint path is correct and the file exists"
        )


class CheckpointLoadError(CheckpointError):
    """Raised when checkpoint loading fails."""
    
    def __init__(self, checkpoint_path: str, reason: str):
        super().__init__(
            message=f"Failed to load checkpoint from {checkpoint_path}",
            details={"path": checkpoint_path, "reason": reason},
            suggestion="The checkpoint file may be corrupted. Try an earlier checkpoint."
        )


class CheckpointSaveError(CheckpointError):
    """Raised when checkpoint saving fails."""
    pass


class CheckpointVersionError(CheckpointError):
    """Raised when checkpoint version is incompatible."""
    
    def __init__(self, expected_version: str, found_version: str):
        super().__init__(
            message="Checkpoint version mismatch",
            details={"expected": expected_version, "found": found_version},
            suggestion="This checkpoint was created with a different version of zarx. You may need to migrate it."
        )


# === TRAINING ERRORS ===

class TrainingError(ZARXError):
    """Base error for training-related issues."""
    pass


class TrainingInterruptedError(TrainingError):
    """Raised when training is interrupted."""
    pass


class EpochContinuityError(TrainingError):
    """Raised when continuing training from wrong epoch."""
    
    def __init__(self, checkpoint_epoch: int, requested_epoch: int):
        super().__init__(
            message="Epoch continuity error",
            details={"checkpoint_epoch": checkpoint_epoch, "requested_epoch": requested_epoch},
            suggestion=f"The checkpoint is from epoch {checkpoint_epoch}. Continue from that epoch or use a different checkpoint."
        )


# === UTILITY FUNCTIONS ===

def handle_error(error: Exception, logger=None, raise_error: bool = True):
    """
    Centralized error handling with optional logging.
    
    Args:
        error: The exception to handle
        logger: Optional logger instance
        raise_error: Whether to re-raise the error after logging
    """
    if logger:
        if isinstance(error, ZARXError):
            logger.error("error", str(error))
        else:
            logger.error("error", f"Unexpected error: {error}")
    
    if raise_error:
        raise error


__all__ = [
    # Base
    'ZARXError',
    
    # Model
    'ModelError',
    'ModelNotFoundError',
    'ModelConfigError',
    'ModelLoadError',
    
    # Data
    'DataError',
    'DataFormatError',
    'DataValidationError',
    'DataLoadError',
    'DataConversionError',
    
    # Tokenizer
    'TokenizerError',
    'TokenizerNotFoundError',
    'TokenizerTrainingError',
    'TokenizerLoadError',
    
    # Config
    'ConfigError',
    'ConfigValidationError',
    'ConfigLoadError',
    'ConfigSaveError',
    
    # Checkpoint
    'CheckpointError',
    'CheckpointNotFoundError',
    'CheckpointLoadError',
    'CheckpointSaveError',
    'CheckpointVersionError',
    
    # Training
    'TrainingError',
    'TrainingInterruptedError',
    'EpochContinuityError',
    
    # Utils
    'handle_error',
]