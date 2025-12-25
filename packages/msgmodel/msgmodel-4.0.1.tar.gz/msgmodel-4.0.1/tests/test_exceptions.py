"""
Tests for msgmodel.exceptions module.

v3.2.6: Updated tests for enhanced exception hierarchy.
"""

import pytest
from msgmodel.exceptions import (
    MsgModelError,
    ConfigurationError,
    ValidationError,
    AuthenticationError,
    FileError,
    APIError,
    ProviderError,
    RateLimitError,
    ContextLengthError,
    ServiceUnavailableError,
    StreamingError,
)


class TestExceptionHierarchy:
    """Tests for exception inheritance hierarchy."""
    
    def test_all_exceptions_inherit_from_base(self):
        """Test that all exceptions inherit from MsgModelError."""
        assert issubclass(ConfigurationError, MsgModelError)
        assert issubclass(ValidationError, MsgModelError)
        assert issubclass(AuthenticationError, MsgModelError)
        assert issubclass(FileError, MsgModelError)
        assert issubclass(APIError, MsgModelError)
        assert issubclass(ProviderError, MsgModelError)
        assert issubclass(StreamingError, MsgModelError)
    
    def test_base_inherits_from_exception(self):
        """Test that MsgModelError inherits from Exception."""
        assert issubclass(MsgModelError, Exception)
    
    def test_provider_error_inherits_from_api_error(self):
        """Test that ProviderError inherits from APIError."""
        assert issubclass(ProviderError, APIError)
    
    def test_specific_provider_errors_inherit_from_provider_error(self):
        """Test that specific provider errors inherit from ProviderError."""
        assert issubclass(RateLimitError, ProviderError)
        assert issubclass(ContextLengthError, ProviderError)
        assert issubclass(ServiceUnavailableError, ProviderError)


class TestMsgModelError:
    """Tests for base MsgModelError."""
    
    def test_basic_message(self):
        """Test MsgModelError with just a message."""
        error = MsgModelError("Something went wrong")
        assert str(error) == "Something went wrong"
        assert error.message == "Something went wrong"
    
    def test_with_cause(self):
        """Test MsgModelError with a cause."""
        cause = ValueError("Original error")
        error = MsgModelError("Wrapper error", cause=cause)
        assert "Wrapper error" in str(error)
        assert "Original error" in str(error)
        assert error.__cause__ is cause


class TestAPIError:
    """Tests for APIError with additional attributes."""
    
    def test_basic_message(self):
        """Test APIError with just a message."""
        error = APIError("Something went wrong")
        assert str(error) == "Something went wrong"
        assert error.status_code is None
        assert error.response_text is None
        assert error.provider is None
    
    def test_with_status_code(self):
        """Test APIError with status code."""
        error = APIError("API failed", status_code=500)
        assert "API failed" in str(error)
        assert error.status_code == 500
        assert error.response_text is None
    
    def test_with_all_attributes(self):
        """Test APIError with all attributes."""
        error = APIError(
            "Rate limited",
            status_code=429,
            response_text='{"error": "too many requests"}',
            provider="openai"
        )
        assert "Rate limited" in str(error)
        assert error.status_code == 429
        assert error.response_text == '{"error": "too many requests"}'
        assert error.provider == "openai"


class TestRateLimitError:
    """Tests for RateLimitError."""
    
    def test_default_message(self):
        """Test RateLimitError with default message."""
        error = RateLimitError()
        assert "Rate limit exceeded" in str(error)
        assert error.status_code == 429
    
    def test_with_retry_after(self):
        """Test RateLimitError with retry_after."""
        error = RateLimitError(retry_after=30.0, provider="openai")
        assert error.retry_after == 30.0
        assert error.provider == "openai"
        assert error.status_code == 429


class TestContextLengthError:
    """Tests for ContextLengthError."""
    
    def test_default_message(self):
        """Test ContextLengthError with default message."""
        error = ContextLengthError()
        assert "context length" in str(error).lower()
        assert error.status_code == 400
    
    def test_with_token_info(self):
        """Test ContextLengthError with token information."""
        error = ContextLengthError(
            max_tokens=8192,
            prompt_tokens=10000,
            provider="openai"
        )
        assert error.max_tokens == 8192
        assert error.prompt_tokens == 10000
        assert error.provider == "openai"


class TestServiceUnavailableError:
    """Tests for ServiceUnavailableError."""
    
    def test_default_message(self):
        """Test ServiceUnavailableError with default message."""
        error = ServiceUnavailableError()
        assert "unavailable" in str(error).lower()
        assert error.status_code == 503


class TestConfigurationError:
    """Tests for ConfigurationError."""
    
    def test_with_key_name(self):
        """Test ConfigurationError with key_name."""
        error = ConfigurationError("Invalid value", key_name="max_tokens")
        assert error.key_name == "max_tokens"
        assert "Invalid value" in str(error)


class TestValidationError:
    """Tests for ValidationError."""
    
    def test_with_field(self):
        """Test ValidationError with field."""
        error = ValidationError("Cannot be empty", field="prompt")
        assert error.field == "prompt"
        assert "Cannot be empty" in str(error)


class TestAuthenticationError:
    """Tests for AuthenticationError."""
    
    def test_with_provider(self):
        """Test AuthenticationError with provider."""
        error = AuthenticationError("Invalid API key", provider="openai")
        assert error.provider == "openai"


class TestFileError:
    """Tests for FileError."""
    
    def test_with_filename(self):
        """Test FileError with filename."""
        error = FileError("File not found", filename="document.pdf")
        assert error.filename == "document.pdf"


class TestStreamingError:
    """Tests for StreamingError."""
    
    def test_with_chunks_received(self):
        """Test StreamingError with chunks_received."""
        error = StreamingError("Connection lost", chunks_received=42)
        assert error.chunks_received == 42


class TestStreamingErrorHelpers:
    """Tests for StreamingError static helper methods."""
    
    def test_detect_error_in_chunk_valid(self):
        """Test detecting error from a valid error chunk."""
        chunk = {"error": {"message": "Rate limit exceeded", "type": "rate_limit_error"}}
        error = StreamingError.detect_error_in_chunk(chunk)
        assert error is not None
        assert error["message"] == "Rate limit exceeded"
    
    def test_detect_error_in_chunk_no_error(self):
        """Test detecting error when chunk has no error."""
        chunk = {"choices": [{"delta": {"content": "Hello"}}]}
        error = StreamingError.detect_error_in_chunk(chunk)
        assert error is None
    
    def test_detect_error_in_chunk_invalid_format(self):
        """Test detecting error from invalid chunk format."""
        chunk = "not a dict"
        error = StreamingError.detect_error_in_chunk(chunk)
        assert error is None
    
    def test_detect_error_in_chunk_error_not_dict(self):
        """Test when error field is not a dict."""
        chunk = {"error": "just a string"}
        error = StreamingError.detect_error_in_chunk(chunk)
        assert error is None
    
    def test_is_rate_limit_error_openai(self):
        """Test detecting OpenAI rate limit error."""
        error = {"type": "rate_limit_error", "message": "Too many requests"}
        assert StreamingError.is_rate_limit_error(error) is True
    
    def test_is_rate_limit_error_gemini(self):
        """Test detecting Gemini rate limit error."""
        error = {"status": "RESOURCE_EXHAUSTED", "message": "Quota exceeded"}
        assert StreamingError.is_rate_limit_error(error) is True
    
    def test_is_rate_limit_error_message_based(self):
        """Test detecting rate limit via message keywords."""
        error = {"message": "You have exceeded your rate limit"}
        assert StreamingError.is_rate_limit_error(error) is True
        
        error = {"message": "Quota exhausted for today"}
        assert StreamingError.is_rate_limit_error(error) is True
    
    def test_is_rate_limit_error_false(self):
        """Test non-rate-limit error."""
        error = {"type": "invalid_request_error", "message": "Bad request"}
        assert StreamingError.is_rate_limit_error(error) is False
    
    def test_is_rate_limit_error_invalid_input(self):
        """Test with invalid input."""
        assert StreamingError.is_rate_limit_error("not a dict") is False
        assert StreamingError.is_rate_limit_error(None) is False


class TestExceptionCatching:
    """Tests for exception catching patterns."""
    
    def test_catch_specific_exception(self):
        """Test catching a specific exception type."""
        with pytest.raises(AuthenticationError):
            raise AuthenticationError("Invalid API key")
    
    def test_catch_base_exception(self):
        """Test catching base exception catches all derived."""
        with pytest.raises(MsgModelError):
            raise ConfigurationError("Bad config")
        
        with pytest.raises(MsgModelError):
            raise APIError("API failed")
        
        with pytest.raises(MsgModelError):
            raise StreamingError("Stream interrupted")
    
    def test_catch_api_error_catches_provider_errors(self):
        """Test catching APIError catches all provider errors."""
        with pytest.raises(APIError):
            raise RateLimitError()
        
        with pytest.raises(APIError):
            raise ContextLengthError()
        
        with pytest.raises(APIError):
            raise ServiceUnavailableError()
    
    def test_backward_compatibility(self):
        """Test that old exception catching patterns still work."""
        # APIError with positional args should still work
        error = APIError("msg", 500, "response text")
        assert error.status_code == 500
        assert error.response_text == "response text"
