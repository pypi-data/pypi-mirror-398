"""
Tests for msgmodel.config module.
"""

import pytest
from msgmodel.config import (
    Provider,
    OpenAIConfig,
    GeminiConfig,
    AnthropicConfig,
    get_default_config,
)


class TestProvider:
    """Tests for the Provider enum."""
    
    def test_from_string_full_names(self):
        """Test conversion from full provider names."""
        assert Provider.from_string("openai") == Provider.OPENAI
        assert Provider.from_string("gemini") == Provider.GEMINI
        assert Provider.from_string("anthropic") == Provider.ANTHROPIC
    
    def test_from_string_shortcuts(self):
        """Test conversion from shortcut codes."""
        assert Provider.from_string("o") == Provider.OPENAI
        assert Provider.from_string("g") == Provider.GEMINI
        assert Provider.from_string("a") == Provider.ANTHROPIC
        assert Provider.from_string("c") == Provider.ANTHROPIC  # claude shortcut
    
    def test_from_string_aliases(self):
        """Test conversion from provider aliases."""
        assert Provider.from_string("claude") == Provider.ANTHROPIC
    
    def test_from_string_case_insensitive(self):
        """Test that conversion is case-insensitive."""
        assert Provider.from_string("OPENAI") == Provider.OPENAI
        assert Provider.from_string("Gemini") == Provider.GEMINI
        assert Provider.from_string("ANTHROPIC") == Provider.ANTHROPIC
        assert Provider.from_string("Claude") == Provider.ANTHROPIC
        assert Provider.from_string("O") == Provider.OPENAI
        assert Provider.from_string("C") == Provider.ANTHROPIC
    
    def test_from_string_with_whitespace(self):
        """Test that whitespace is stripped."""
        assert Provider.from_string("  openai  ") == Provider.OPENAI
        assert Provider.from_string("\tgemini\n") == Provider.GEMINI
        assert Provider.from_string("  anthropic  ") == Provider.ANTHROPIC
        assert Provider.from_string("  claude  ") == Provider.ANTHROPIC
    
    def test_from_string_invalid(self):
        """Test that invalid values raise ValueError."""
        with pytest.raises(ValueError, match="Invalid provider"):
            Provider.from_string("invalid")
        
        with pytest.raises(ValueError, match="Invalid provider"):
            Provider.from_string("")
        
        with pytest.raises(ValueError, match="Invalid provider"):
            Provider.from_string("x")


class TestOpenAIConfig:
    """Tests for OpenAIConfig dataclass."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = OpenAIConfig()
        assert config.model == "gpt-4o"
        assert config.temperature == 1.0
        assert config.top_p == 1.0
        assert config.max_tokens == 1000
        assert config.n == 1
    
    def test_custom_values(self):
        """Test custom configuration values."""
        config = OpenAIConfig(
            model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=2000,
        )
        assert config.model == "gpt-4o-mini"
        assert config.temperature == 0.7
        assert config.max_tokens == 2000


class TestGeminiConfig:
    """Tests for GeminiConfig dataclass."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = GeminiConfig()
        assert config.model == "gemini-2.5-flash"
        assert config.temperature == 1.0
        assert config.top_p == 0.95
        assert config.top_k == 40
        assert config.max_tokens == 1000
        assert config.candidate_count == 1
        assert config.safety_threshold == "BLOCK_NONE"
        assert config.api_version == "v1beta"
    
    def test_custom_values(self):
        """Test custom configuration values."""
        config = GeminiConfig(
            model="gemini-1.5-pro",
            temperature=0.5,
            safety_threshold="BLOCK_MEDIUM_AND_ABOVE",
        )
        assert config.model == "gemini-1.5-pro"
        assert config.temperature == 0.5
        assert config.safety_threshold == "BLOCK_MEDIUM_AND_ABOVE"


class TestAnthropicConfig:
    """Tests for AnthropicConfig dataclass."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = AnthropicConfig()
        assert config.model == "claude-haiku-4-5-20251001"
        assert config.temperature == 1.0
        assert config.top_p == 1.0
        assert config.top_k == 0
        assert config.max_tokens == 1000
    
    def test_custom_values(self):
        """Test custom configuration values."""
        config = AnthropicConfig(
            model="claude-3-opus-20240229",
            temperature=0.7,
            max_tokens=2000,
        )
        assert config.model == "claude-3-opus-20240229"
        assert config.temperature == 0.7
        assert config.max_tokens == 2000


class TestGetDefaultConfig:
    """Tests for get_default_config function."""
    
    def test_returns_correct_config_type(self):
        """Test that correct config type is returned for each provider."""
        assert isinstance(get_default_config(Provider.OPENAI), OpenAIConfig)
        assert isinstance(get_default_config(Provider.GEMINI), GeminiConfig)
        assert isinstance(get_default_config(Provider.ANTHROPIC), AnthropicConfig)
    
    def test_returns_new_instance(self):
        """Test that a new instance is returned each time."""
        config1 = get_default_config(Provider.OPENAI)
        config2 = get_default_config(Provider.OPENAI)
        assert config1 is not config2
        
        config3 = get_default_config(Provider.ANTHROPIC)
        config4 = get_default_config(Provider.ANTHROPIC)
        assert config3 is not config4
