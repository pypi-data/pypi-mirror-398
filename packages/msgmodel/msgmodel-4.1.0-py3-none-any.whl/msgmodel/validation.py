"""
msgmodel.validation
~~~~~~~~~~~~~~~~~~~

Input validation utilities for msgmodel.

Provides validation functions to catch configuration errors early
and provide clear, actionable error messages.
"""

import re
from typing import Optional, Union

from .exceptions import ValidationError, ConfigurationError


# Constants for validation
MIN_TEMPERATURE = 0.0
MAX_TEMPERATURE = 2.0
MIN_MAX_TOKENS = 1
MAX_MAX_TOKENS = 1_000_000
MIN_TOP_P = 0.0
MAX_TOP_P = 1.0


def validate_prompt(prompt: str, *, allow_empty: bool = False) -> str:
    """
    Validate a prompt string.
    
    Args:
        prompt: The prompt to validate
        allow_empty: Whether to allow empty prompts (default: False)
        
    Returns:
        The validated prompt (stripped of leading/trailing whitespace)
        
    Raises:
        ValidationError: If the prompt is invalid
    """
    if not isinstance(prompt, str):
        raise ValidationError(
            f"prompt must be a string, got {type(prompt).__name__}",
            field="prompt"
        )
    
    stripped = prompt.strip()
    
    if not allow_empty and not stripped:
        raise ValidationError(
            "prompt cannot be empty or whitespace only",
            field="prompt"
        )
    
    return stripped


def validate_temperature(temperature: float) -> float:
    """
    Validate a temperature parameter.
    
    Args:
        temperature: The temperature value to validate
        
    Returns:
        The validated temperature
        
    Raises:
        ValidationError: If the temperature is out of range
    """
    if not isinstance(temperature, (int, float)):
        raise ValidationError(
            f"temperature must be a number, got {type(temperature).__name__}",
            field="temperature"
        )
    
    if temperature < MIN_TEMPERATURE or temperature > MAX_TEMPERATURE:
        raise ValidationError(
            f"temperature must be between {MIN_TEMPERATURE} and {MAX_TEMPERATURE}, got {temperature}",
            field="temperature"
        )
    
    return float(temperature)


def validate_max_tokens(max_tokens: int) -> int:
    """
    Validate a max_tokens parameter.
    
    Args:
        max_tokens: The max_tokens value to validate
        
    Returns:
        The validated max_tokens
        
    Raises:
        ConfigurationError: If max_tokens is invalid
    """
    if not isinstance(max_tokens, int):
        raise ConfigurationError(
            f"max_tokens must be an integer, got {type(max_tokens).__name__}",
            key_name="max_tokens"
        )
    
    if max_tokens < MIN_MAX_TOKENS:
        raise ConfigurationError(
            f"max_tokens must be at least {MIN_MAX_TOKENS}",
            key_name="max_tokens"
        )
    
    if max_tokens > MAX_MAX_TOKENS:
        raise ConfigurationError(
            f"max_tokens must be at most {MAX_MAX_TOKENS}, got {max_tokens}",
            key_name="max_tokens"
        )
    
    return max_tokens


def validate_top_p(top_p: float) -> float:
    """
    Validate a top_p parameter.
    
    Args:
        top_p: The top_p value to validate
        
    Returns:
        The validated top_p
        
    Raises:
        ValidationError: If top_p is out of range
    """
    if not isinstance(top_p, (int, float)):
        raise ValidationError(
            f"top_p must be a number, got {type(top_p).__name__}",
            field="top_p"
        )
    
    if top_p < MIN_TOP_P or top_p > MAX_TOP_P:
        raise ValidationError(
            f"top_p must be between {MIN_TOP_P} and {MAX_TOP_P}, got {top_p}",
            field="top_p"
        )
    
    return float(top_p)


def validate_api_key(
    api_key: str,
    *,
    provider: Optional[str] = None,
    min_length: int = 10
) -> str:
    """
    Validate an API key format.
    
    Performs basic sanity checks on API keys to catch obvious errors
    like empty strings or truncated keys.
    
    Args:
        api_key: The API key to validate
        provider: Optional provider name for context in error messages
        min_length: Minimum acceptable key length (default: 10)
        
    Returns:
        The validated API key (stripped of whitespace)
        
    Raises:
        ValidationError: If the API key appears invalid
    """
    if not isinstance(api_key, str):
        raise ValidationError(
            f"API key must be a string, got {type(api_key).__name__}",
            field="api_key"
        )
    
    stripped = api_key.strip()
    
    if not stripped:
        provider_msg = f" for {provider}" if provider else ""
        raise ValidationError(
            f"API key{provider_msg} cannot be empty",
            field="api_key"
        )
    
    if len(stripped) < min_length:
        provider_msg = f" for {provider}" if provider else ""
        raise ValidationError(
            f"API key{provider_msg} appears too short (minimum {min_length} characters)",
            field="api_key"
        )
    
    # Check for common placeholder patterns
    placeholder_patterns = [
        r'^sk-[.]{3,}$',  # sk-...
        r'^your[_-]?api[_-]?key',  # your_api_key, your-api-key
        r'^\*+$',  # ****
        r'^xxx+$',  # xxxx
        r'^test[_-]?key',  # test_key
        r'^placeholder',  # placeholder
    ]
    
    for pattern in placeholder_patterns:
        if re.match(pattern, stripped, re.IGNORECASE):
            provider_msg = f" for {provider}" if provider else ""
            raise ValidationError(
                f"API key{provider_msg} appears to be a placeholder value",
                field="api_key"
            )
    
    return stripped


def validate_model_name(model: str) -> str:
    """
    Validate a model name.
    
    Args:
        model: The model name to validate
        
    Returns:
        The validated model name
        
    Raises:
        ValidationError: If the model name is invalid
    """
    if not isinstance(model, str):
        raise ValidationError(
            f"model must be a string, got {type(model).__name__}",
            field="model"
        )
    
    stripped = model.strip()
    
    if not stripped:
        raise ValidationError(
            "model name cannot be empty",
            field="model"
        )
    
    # Model names should be alphanumeric with dashes, underscores, dots, and colons
    if not re.match(r'^[\w\-.:]+$', stripped):
        raise ValidationError(
            f"model name contains invalid characters: {stripped}",
            field="model"
        )
    
    return stripped


def validate_timeout(timeout: Union[int, float]) -> float:
    """
    Validate a timeout parameter.
    
    Args:
        timeout: The timeout value in seconds
        
    Returns:
        The validated timeout as a float
        
    Raises:
        ValidationError: If the timeout is invalid
    """
    if not isinstance(timeout, (int, float)):
        raise ValidationError(
            f"timeout must be a number, got {type(timeout).__name__}",
            field="timeout"
        )
    
    if timeout <= 0:
        raise ValidationError(
            f"timeout must be positive, got {timeout}",
            field="timeout"
        )
    
    if timeout > 3600:  # 1 hour max
        raise ValidationError(
            f"timeout cannot exceed 3600 seconds (1 hour), got {timeout}",
            field="timeout"
        )
    
    return float(timeout)
