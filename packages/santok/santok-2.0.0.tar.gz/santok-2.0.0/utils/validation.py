"""
Input Validation Utilities for SanTOK
"""

from typing import Any, Union, List
from pathlib import Path


class ValidationError(ValueError):
    """Custom exception for validation errors"""
    pass


def validate_text_input(text: Any, param_name: str = "text") -> str:
    """
    Validate text input
    
    Args:
        text: Text input to validate
        param_name: Parameter name for error messages
        
    Returns:
        Validated text string
        
    Raises:
        ValidationError: If input is invalid
    """
    if text is None:
        raise ValidationError(f"{param_name} cannot be None")
    
    if not isinstance(text, str):
        raise ValidationError(
            f"{param_name} must be a string, got {type(text).__name__}"
        )
    
    if not text.strip():
        raise ValidationError(f"{param_name} cannot be empty or whitespace only")
    
    return text


def validate_file_path(file_path: Any, must_exist: bool = False, param_name: str = "file_path") -> Path:
    """
    Validate file path
    
    Args:
        file_path: File path to validate
        must_exist: If True, file must exist
        param_name: Parameter name for error messages
        
    Returns:
        Validated Path object
        
    Raises:
        ValidationError: If path is invalid
    """
    if file_path is None:
        raise ValidationError(f"{param_name} cannot be None")
    
    if isinstance(file_path, str):
        path = Path(file_path)
    elif isinstance(file_path, Path):
        path = file_path
    else:
        raise ValidationError(
            f"{param_name} must be a string or Path, got {type(file_path).__name__}"
        )
    
    if must_exist and not path.exists():
        raise ValidationError(f"{param_name} does not exist: {path}")
    
    return path.resolve()


def validate_positive_int(value: Any, param_name: str = "value", min_value: int = 1) -> int:
    """
    Validate positive integer
    
    Args:
        value: Value to validate
        param_name: Parameter name for error messages
        min_value: Minimum allowed value
        
    Returns:
        Validated integer
        
    Raises:
        ValidationError: If value is invalid
    """
    if not isinstance(value, int):
        try:
            value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(
                f"{param_name} must be an integer, got {type(value).__name__}"
            )
    
    if value < min_value:
        raise ValidationError(
            f"{param_name} must be >= {min_value}, got {value}"
        )
    
    return value


def validate_port(port: Any, param_name: str = "port") -> int:
    """
    Validate port number (1-65535)
    
    Args:
        port: Port number to validate
        param_name: Parameter name for error messages
        
    Returns:
        Validated port number
        
    Raises:
        ValidationError: If port is invalid
    """
    port_int = validate_positive_int(port, param_name, min_value=1)
    
    if port_int > 65535:
        raise ValidationError(
            f"{param_name} must be <= 65535, got {port_int}"
        )
    
    return port_int


def validate_choice(value: Any, choices: List[str], param_name: str = "value") -> str:
    """
    Validate value is in choices list
    
    Args:
        value: Value to validate
        choices: List of valid choices
        param_name: Parameter name for error messages
        
    Returns:
        Validated choice string
        
    Raises:
        ValidationError: If value is not in choices
    """
    if not isinstance(value, str):
        value = str(value)
    
    if value not in choices:
        raise ValidationError(
            f"{param_name} must be one of {choices}, got {value}"
        )
    
    return value

