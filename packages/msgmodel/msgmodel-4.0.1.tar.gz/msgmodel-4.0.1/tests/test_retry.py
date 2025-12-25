"""
Tests for msgmodel.retry module.
"""

import time
import pytest
from unittest.mock import MagicMock, patch

from msgmodel.retry import (
    retry_on_transient_error,
    RetryConfig,
    calculate_backoff,
    is_retryable_status_code,
    RETRY_DEFAULT,
    RETRY_AGGRESSIVE,
    RETRY_CONSERVATIVE,
    DEFAULT_RETRYABLE_EXCEPTIONS,
)
from msgmodel.exceptions import RateLimitError, ServiceUnavailableError, APIError


class TestIsRetryableStatusCode:
    """Tests for is_retryable_status_code function."""
    
    def test_retryable_codes(self):
        """Test that retryable status codes return True."""
        assert is_retryable_status_code(429) is True
        assert is_retryable_status_code(500) is True
        assert is_retryable_status_code(502) is True
        assert is_retryable_status_code(503) is True
        assert is_retryable_status_code(504) is True
    
    def test_non_retryable_codes(self):
        """Test that non-retryable status codes return False."""
        assert is_retryable_status_code(200) is False
        assert is_retryable_status_code(400) is False
        assert is_retryable_status_code(401) is False
        assert is_retryable_status_code(403) is False
        assert is_retryable_status_code(404) is False
    
    def test_none_returns_false(self):
        """Test that None returns False."""
        assert is_retryable_status_code(None) is False


class TestCalculateBackoff:
    """Tests for calculate_backoff function."""
    
    def test_exponential_growth(self):
        """Test that backoff grows exponentially."""
        # Without jitter for predictable testing
        with patch('msgmodel.retry.random.random', return_value=0.5):
            delay0 = calculate_backoff(0, backoff_factor=1.0, jitter=False)
            delay1 = calculate_backoff(1, backoff_factor=1.0, jitter=False)
            delay2 = calculate_backoff(2, backoff_factor=1.0, jitter=False)
            
            assert delay0 == 1.0
            assert delay1 == 2.0
            assert delay2 == 4.0
    
    def test_max_backoff_cap(self):
        """Test that delay is capped at max_backoff."""
        delay = calculate_backoff(10, backoff_factor=1.0, max_backoff=30.0, jitter=False)
        assert delay == 30.0
    
    def test_jitter_adds_randomness(self):
        """Test that jitter adds randomness."""
        delays = [calculate_backoff(1, jitter=True) for _ in range(10)]
        # With jitter, we should get varying delays
        assert len(set(delays)) > 1


class TestRetryDecorator:
    """Tests for retry_on_transient_error decorator."""
    
    def test_success_no_retry(self):
        """Test that successful call doesn't retry."""
        call_count = 0
        
        @retry_on_transient_error(max_retries=3)
        def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = successful_func()
        assert result == "success"
        assert call_count == 1
    
    def test_retry_on_connection_error(self):
        """Test that ConnectionError triggers retry."""
        call_count = 0
        
        @retry_on_transient_error(max_retries=3, backoff_factor=0.01)
        def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Network error")
            return "success"
        
        result = flaky_func()
        assert result == "success"
        assert call_count == 3
    
    def test_retry_on_rate_limit_error(self):
        """Test that RateLimitError triggers retry."""
        call_count = 0
        
        @retry_on_transient_error(max_retries=3, backoff_factor=0.01)
        def rate_limited_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise RateLimitError()
            return "success"
        
        result = rate_limited_func()
        assert result == "success"
        assert call_count == 2
    
    def test_max_retries_exceeded(self):
        """Test that max retries is respected."""
        call_count = 0
        
        @retry_on_transient_error(max_retries=2, backoff_factor=0.01)
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Always fails")
        
        with pytest.raises(ConnectionError):
            always_fails()
        
        # Initial call + 2 retries = 3 total calls
        assert call_count == 3
    
    def test_non_retryable_error_not_retried(self):
        """Test that non-retryable errors are not retried."""
        call_count = 0
        
        @retry_on_transient_error(max_retries=3, backoff_factor=0.01)
        def raises_value_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("Not retryable")
        
        with pytest.raises(ValueError):
            raises_value_error()
        
        assert call_count == 1  # No retries
    
    def test_retry_with_api_error_retryable_status(self):
        """Test that APIError with retryable status code is retried."""
        call_count = 0
        
        @retry_on_transient_error(max_retries=3, backoff_factor=0.01)
        def api_error_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise APIError("Server error", status_code=503)
            return "success"
        
        result = api_error_func()
        assert result == "success"
        assert call_count == 2
    
    def test_api_error_max_retries_exceeded(self):
        """Test that APIError respects max retries."""
        call_count = 0
        
        @retry_on_transient_error(max_retries=2, backoff_factor=0.01)
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise APIError("Server overloaded", status_code=503)
        
        with pytest.raises(APIError) as exc_info:
            always_fails()
        
        assert exc_info.value.status_code == 503
        # Initial call + 2 retries = 3 total calls
        assert call_count == 3
    
    def test_api_error_non_retryable_status(self):
        """Test that APIError with non-retryable status is not retried."""
        call_count = 0
        
        @retry_on_transient_error(max_retries=3, backoff_factor=0.01)
        def api_error_400():
            nonlocal call_count
            call_count += 1
            raise APIError("Bad request", status_code=400)
        
        with pytest.raises(APIError) as exc_info:
            api_error_400()
        
        assert exc_info.value.status_code == 400
        assert call_count == 1  # No retries
    
    def test_on_retry_callback_with_api_error(self):
        """Test that on_retry callback is called for APIError."""
        retry_calls = []
        
        def on_retry(exc, attempt, delay):
            retry_calls.append((exc.status_code, attempt))
        
        @retry_on_transient_error(max_retries=2, backoff_factor=0.01, on_retry=on_retry)
        def api_flaky():
            if len(retry_calls) < 2:
                raise APIError("Rate limited", status_code=429)
            return "success"
        
        result = api_flaky()
        assert result == "success"
        assert len(retry_calls) == 2
        assert retry_calls[0][0] == 429  # status_code
    
    def test_on_retry_callback(self):
        """Test that on_retry callback is called."""
        retry_calls = []
        
        def on_retry(exc, attempt, delay):
            retry_calls.append((type(exc).__name__, attempt, delay))
        
        @retry_on_transient_error(max_retries=2, backoff_factor=0.01, on_retry=on_retry)
        def flaky_func():
            if len(retry_calls) < 2:
                raise ConnectionError("Flaky")
            return "success"
        
        result = flaky_func()
        assert result == "success"
        assert len(retry_calls) == 2
        assert retry_calls[0][0] == "ConnectionError"
    
    def test_retry_after_from_rate_limit_error(self):
        """Test that retry_after hint is respected."""
        @retry_on_transient_error(max_retries=1, backoff_factor=0.01)
        def rate_limited():
            raise RateLimitError(retry_after=0.05)
        
        start = time.time()
        with pytest.raises(RateLimitError):
            rate_limited()
        elapsed = time.time() - start
        
        # Should have waited at least the retry_after time
        assert elapsed >= 0.04  # Allow some tolerance


class TestRetryConfig:
    """Tests for RetryConfig class."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = RetryConfig()
        assert config.max_retries == 3
        assert config.backoff_factor == 1.0
        assert config.max_backoff == 60.0
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = RetryConfig(
            max_retries=5,
            backoff_factor=0.5,
            max_backoff=30.0,
        )
        assert config.max_retries == 5
        assert config.backoff_factor == 0.5
        assert config.max_backoff == 30.0
    
    def test_decorator_from_config(self):
        """Test creating decorator from config."""
        config = RetryConfig(max_retries=2, backoff_factor=0.01)
        decorator = config.decorator()
        
        call_count = 0
        
        @decorator
        def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Flaky")
            return "success"
        
        result = flaky_func()
        assert result == "success"


class TestPreConfiguredRetryConfigs:
    """Tests for pre-configured retry configurations."""
    
    def test_retry_default_exists(self):
        """Test RETRY_DEFAULT is properly configured."""
        assert RETRY_DEFAULT.max_retries == 3
        assert RETRY_DEFAULT.backoff_factor == 1.0
    
    def test_retry_aggressive_exists(self):
        """Test RETRY_AGGRESSIVE is properly configured."""
        assert RETRY_AGGRESSIVE.max_retries == 5
        assert RETRY_AGGRESSIVE.backoff_factor == 0.5
    
    def test_retry_conservative_exists(self):
        """Test RETRY_CONSERVATIVE is properly configured."""
        assert RETRY_CONSERVATIVE.max_retries == 3
        assert RETRY_CONSERVATIVE.backoff_factor == 2.0


class TestDefaultRetryableExceptions:
    """Tests for DEFAULT_RETRYABLE_EXCEPTIONS."""
    
    def test_includes_expected_exceptions(self):
        """Test that default includes expected exception types."""
        assert ConnectionError in DEFAULT_RETRYABLE_EXCEPTIONS
        assert TimeoutError in DEFAULT_RETRYABLE_EXCEPTIONS
        assert RateLimitError in DEFAULT_RETRYABLE_EXCEPTIONS
        assert ServiceUnavailableError in DEFAULT_RETRYABLE_EXCEPTIONS
