"""
Tests for msgmodel.validation module.
"""

import pytest
from msgmodel.validation import (
    validate_prompt,
    validate_temperature,
    validate_max_tokens,
    validate_top_p,
    validate_api_key,
    validate_model_name,
    validate_timeout,
)
from msgmodel.exceptions import ValidationError, ConfigurationError


class TestValidatePrompt:
    """Tests for validate_prompt function."""
    
    def test_valid_prompt(self):
        """Test valid prompt passes."""
        result = validate_prompt("Hello, world!")
        assert result == "Hello, world!"
    
    def test_strips_whitespace(self):
        """Test that whitespace is stripped."""
        result = validate_prompt("  Hello  ")
        assert result == "Hello"
    
    def test_empty_raises(self):
        """Test that empty prompt raises ValidationError."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_prompt("")
    
    def test_whitespace_only_raises(self):
        """Test that whitespace-only prompt raises ValidationError."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_prompt("   ")
    
    def test_empty_allowed(self):
        """Test that empty prompt is allowed when allow_empty=True."""
        result = validate_prompt("", allow_empty=True)
        assert result == ""
    
    def test_non_string_raises(self):
        """Test that non-string raises ValidationError."""
        with pytest.raises(ValidationError, match="must be a string"):
            validate_prompt(123)


class TestValidateTemperature:
    """Tests for validate_temperature function."""
    
    def test_valid_temperature(self):
        """Test valid temperatures pass."""
        assert validate_temperature(0.0) == 0.0
        assert validate_temperature(1.0) == 1.0
        assert validate_temperature(2.0) == 2.0
        assert validate_temperature(0.7) == 0.7
    
    def test_converts_int(self):
        """Test that integers are converted to float."""
        result = validate_temperature(1)
        assert result == 1.0
        assert isinstance(result, float)
    
    def test_negative_raises(self):
        """Test that negative temperature raises ValidationError."""
        with pytest.raises(ValidationError, match="between"):
            validate_temperature(-0.1)
    
    def test_too_high_raises(self):
        """Test that temperature > 2.0 raises ValidationError."""
        with pytest.raises(ValidationError, match="between"):
            validate_temperature(2.1)
    
    def test_non_number_raises(self):
        """Test that non-number raises ValidationError."""
        with pytest.raises(ValidationError, match="must be a number"):
            validate_temperature("hot")


class TestValidateMaxTokens:
    """Tests for validate_max_tokens function."""
    
    def test_valid_values(self):
        """Test valid max_tokens values pass."""
        assert validate_max_tokens(1) == 1
        assert validate_max_tokens(1000) == 1000
        assert validate_max_tokens(100000) == 100000
    
    def test_zero_raises(self):
        """Test that zero raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="at least"):
            validate_max_tokens(0)
    
    def test_negative_raises(self):
        """Test that negative raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="at least"):
            validate_max_tokens(-1)
    
    def test_too_large_raises(self):
        """Test that too large value raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="at most"):
            validate_max_tokens(1_000_001)
    
    def test_non_int_raises(self):
        """Test that non-integer raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="must be an integer"):
            validate_max_tokens(100.5)


class TestValidateTopP:
    """Tests for validate_top_p function."""
    
    def test_valid_values(self):
        """Test valid top_p values pass."""
        assert validate_top_p(0.0) == 0.0
        assert validate_top_p(0.5) == 0.5
        assert validate_top_p(1.0) == 1.0
    
    def test_negative_raises(self):
        """Test that negative raises ValidationError."""
        with pytest.raises(ValidationError, match="between"):
            validate_top_p(-0.1)
    
    def test_too_high_raises(self):
        """Test that > 1.0 raises ValidationError."""
        with pytest.raises(ValidationError, match="between"):
            validate_top_p(1.1)
    
    def test_non_number_raises(self):
        """Test that non-number raises ValidationError."""
        with pytest.raises(ValidationError, match="must be a number"):
            validate_top_p("high")


class TestValidateApiKey:
    """Tests for validate_api_key function."""
    
    def test_valid_key(self):
        """Test valid API key passes."""
        result = validate_api_key("sk-1234567890abcdef")
        assert result == "sk-1234567890abcdef"
    
    def test_strips_whitespace(self):
        """Test that whitespace is stripped."""
        result = validate_api_key("  sk-1234567890  ")
        assert result == "sk-1234567890"
    
    def test_empty_raises(self):
        """Test that empty key raises ValidationError."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_api_key("")
    
    def test_too_short_raises(self):
        """Test that too short key raises ValidationError."""
        with pytest.raises(ValidationError, match="too short"):
            validate_api_key("abc")
    
    def test_placeholder_raises(self):
        """Test that placeholder values raise ValidationError."""
        with pytest.raises(ValidationError, match="placeholder"):
            validate_api_key("your_api_key")
        
        with pytest.raises(ValidationError, match="placeholder"):
            validate_api_key("test_key_12345")
    
    def test_provider_in_error_message(self):
        """Test that provider name appears in error message."""
        with pytest.raises(ValidationError, match="openai"):
            validate_api_key("", provider="openai")


class TestValidateModelName:
    """Tests for validate_model_name function."""
    
    def test_valid_names(self):
        """Test valid model names pass."""
        assert validate_model_name("gpt-4o") == "gpt-4o"
        assert validate_model_name("gpt-4o-mini") == "gpt-4o-mini"
        assert validate_model_name("gemini-1.5-pro") == "gemini-1.5-pro"
    
    def test_empty_raises(self):
        """Test that empty name raises ValidationError."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_model_name("")
    
    def test_invalid_chars_raises(self):
        """Test that invalid characters raise ValidationError."""
        with pytest.raises(ValidationError, match="invalid characters"):
            validate_model_name("model name with spaces")
    
    def test_non_string_raises(self):
        """Test that non-string raises ValidationError."""
        with pytest.raises(ValidationError, match="must be a string"):
            validate_model_name(12345)


class TestValidateTimeout:
    """Tests for validate_timeout function."""
    
    def test_valid_timeout(self):
        """Test valid timeout values pass."""
        assert validate_timeout(30) == 30.0
        assert validate_timeout(300.5) == 300.5
    
    def test_zero_raises(self):
        """Test that zero raises ValidationError."""
        with pytest.raises(ValidationError, match="positive"):
            validate_timeout(0)
    
    def test_negative_raises(self):
        """Test that negative raises ValidationError."""
        with pytest.raises(ValidationError, match="positive"):
            validate_timeout(-10)
    
    def test_too_large_raises(self):
        """Test that > 1 hour raises ValidationError."""
        with pytest.raises(ValidationError, match="cannot exceed"):
            validate_timeout(3601)
    
    def test_non_number_raises(self):
        """Test that non-number raises ValidationError."""
        with pytest.raises(ValidationError, match="must be a number"):
            validate_timeout("30 seconds")


class TestValidateApiKeyAdditional:
    """Additional tests for validate_api_key function."""
    
    def test_non_string_raises(self):
        """Test that non-string raises ValidationError."""
        with pytest.raises(ValidationError, match="must be a string"):
            validate_api_key(12345)
