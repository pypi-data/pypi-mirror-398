"""
Tests for msgmodel.providers.anthropic module.
"""

import pytest
import json
import base64
from unittest.mock import Mock, patch, MagicMock

from msgmodel.providers.anthropic import AnthropicProvider
from msgmodel.config import AnthropicConfig
from msgmodel.exceptions import APIError, StreamingError


class TestAnthropicProviderInit:
    """Tests for AnthropicProvider initialization."""
    
    def test_init_with_api_key(self):
        """Test initialization with API key."""
        provider = AnthropicProvider("test-api-key")
        assert provider.api_key == "test-api-key"
        assert isinstance(provider.config, AnthropicConfig)
    
    def test_init_with_custom_config(self):
        """Test initialization with custom config."""
        config = AnthropicConfig(model="claude-3-opus-20240229", max_tokens=2000)
        provider = AnthropicProvider("test-api-key", config)
        assert provider.config.model == "claude-3-opus-20240229"
        assert provider.config.max_tokens == 2000


class TestAnthropicProviderHeaders:
    """Tests for header building."""
    
    def test_build_headers(self):
        """Test that headers are built correctly."""
        provider = AnthropicProvider("test-api-key")
        headers = provider._build_headers()
        
        assert headers["Content-Type"] == "application/json"
        assert headers["x-api-key"] == "test-api-key"
        assert headers["anthropic-version"] == "2023-06-01"


class TestAnthropicProviderContent:
    """Tests for content building."""
    
    def test_build_content_text_only(self):
        """Test content building with text only."""
        provider = AnthropicProvider("test-api-key")
        content = provider._build_content("Hello, world!")
        
        assert len(content) == 1
        assert content[0]["type"] == "text"
        assert content[0]["text"] == "Hello, world!"
    
    def test_build_content_with_image(self):
        """Test content building with image file."""
        provider = AnthropicProvider("test-api-key")
        file_data = {
            "mime_type": "image/png",
            "data": base64.b64encode(b"fake image data").decode(),
            "filename": "test.png"
        }
        content = provider._build_content("Describe this", file_data)
        
        assert len(content) == 2
        assert content[0]["type"] == "image"
        assert content[0]["source"]["type"] == "base64"
        assert content[0]["source"]["media_type"] == "image/png"
        assert content[1]["type"] == "text"
        assert content[1]["text"] == "Describe this"
    
    def test_build_content_with_pdf(self):
        """Test content building with PDF file."""
        provider = AnthropicProvider("test-api-key")
        file_data = {
            "mime_type": "application/pdf",
            "data": base64.b64encode(b"%PDF-fake").decode(),
            "filename": "test.pdf"
        }
        content = provider._build_content("Summarize this", file_data)
        
        assert len(content) == 2
        assert content[0]["type"] == "document"
        assert content[0]["source"]["media_type"] == "application/pdf"
    
    def test_build_content_with_text_file(self):
        """Test content building with text file."""
        provider = AnthropicProvider("test-api-key")
        file_data = {
            "mime_type": "text/plain",
            "data": base64.b64encode(b"Hello from file").decode(),
            "filename": "readme.txt"
        }
        content = provider._build_content("Analyze this", file_data)
        
        assert len(content) == 2
        assert content[0]["type"] == "text"
        assert "Hello from file" in content[0]["text"]
        assert "readme.txt" in content[0]["text"]
    
    def test_build_content_with_empty_text_file(self):
        """Test content building with empty/whitespace text file."""
        provider = AnthropicProvider("test-api-key")
        file_data = {
            "mime_type": "text/plain",
            "data": base64.b64encode(b"   ").decode(),  # Just whitespace
            "filename": "empty.txt"
        }
        content = provider._build_content("Analyze this", file_data)
        
        # Empty text file should not add content (only prompt)
        assert len(content) == 1
        assert content[0]["text"] == "Analyze this"
    
    def test_build_content_with_binary_file(self):
        """Test content building with unsupported binary file."""
        provider = AnthropicProvider("test-api-key")
        file_data = {
            "mime_type": "application/octet-stream",
            "data": base64.b64encode(b"\x00\x01\x02").decode(),
            "filename": "data.bin"
        }
        content = provider._build_content("Process this", file_data)
        
        assert len(content) == 2
        assert content[0]["type"] == "text"
        assert "data.bin" in content[0]["text"]
        assert "application/octet-stream" in content[0]["text"]
    
    def test_build_content_text_decode_error(self):
        """Test content building when text decode fails."""
        provider = AnthropicProvider("test-api-key")
        file_data = {
            "mime_type": "text/plain",
            "data": "not-valid-base64!!!",  # Invalid base64
            "filename": "bad.txt"
        }
        content = provider._build_content("Analyze this", file_data)
        
        # Should handle gracefully (empty text won't be added)
        assert len(content) == 1


class TestAnthropicProviderPayload:
    """Tests for payload building."""
    
    def test_build_payload_basic(self):
        """Test basic payload building."""
        provider = AnthropicProvider("test-api-key")
        payload = provider._build_payload("Hello")
        
        assert payload["model"] == "claude-haiku-4-5-20251001"
        assert payload["max_tokens"] == 1000
        assert len(payload["messages"]) == 1
        assert payload["messages"][0]["role"] == "user"
        assert "system" not in payload
    
    def test_build_payload_with_system(self):
        """Test payload building with system instruction."""
        provider = AnthropicProvider("test-api-key")
        payload = provider._build_payload("Hello", system_instruction="Be helpful")
        
        assert payload["system"] == "Be helpful"
    
    def test_build_payload_with_stream(self):
        """Test payload building for streaming."""
        provider = AnthropicProvider("test-api-key")
        payload = provider._build_payload("Hello", stream=True)
        
        assert payload["stream"] is True
    
    def test_build_payload_custom_temperature(self):
        """Test payload with custom temperature."""
        config = AnthropicConfig(temperature=0.5)
        provider = AnthropicProvider("test-api-key", config)
        payload = provider._build_payload("Hello")
        
        assert payload["temperature"] == 0.5
    
    def test_build_payload_custom_top_p(self):
        """Test payload with custom top_p."""
        config = AnthropicConfig(top_p=0.9)
        provider = AnthropicProvider("test-api-key", config)
        payload = provider._build_payload("Hello")
        
        assert payload["top_p"] == 0.9
    
    def test_build_payload_custom_top_k(self):
        """Test payload with custom top_k."""
        config = AnthropicConfig(top_k=40)
        provider = AnthropicProvider("test-api-key", config)
        payload = provider._build_payload("Hello")
        
        assert payload["top_k"] == 40
    
    def test_build_payload_default_top_p_not_included(self):
        """Test that default top_p (1.0) is not included."""
        provider = AnthropicProvider("test-api-key")
        payload = provider._build_payload("Hello")
        
        assert "top_p" not in payload
    
    def test_build_payload_default_top_k_not_included(self):
        """Test that default top_k (0) is not included."""
        provider = AnthropicProvider("test-api-key")
        payload = provider._build_payload("Hello")
        
        assert "top_k" not in payload
    
    def test_build_payload_default_temperature_not_included(self):
        """Test that default temperature (1.0) is not included in payload."""
        provider = AnthropicProvider("test-api-key")
        payload = provider._build_payload("Hello")
        
        # Default temperature should not be in payload
        assert "temperature" not in payload


class TestAnthropicProviderQuery:
    """Tests for query method."""
    
    @patch('msgmodel.providers.anthropic.requests.post')
    def test_query_success(self, mock_post):
        """Test successful query."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "content": [{"type": "text", "text": "Hello!"}],
            "usage": {"input_tokens": 10, "output_tokens": 5}
        }
        mock_post.return_value = mock_response
        
        provider = AnthropicProvider("test-api-key")
        result = provider.query("Hello")
        
        assert result["content"][0]["text"] == "Hello!"
        mock_post.assert_called_once()
    
    @patch('msgmodel.providers.anthropic.requests.post')
    def test_query_api_error(self, mock_post):
        """Test query with API error."""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 400
        mock_response.text = "Bad request"
        mock_post.return_value = mock_response
        
        provider = AnthropicProvider("test-api-key")
        
        with pytest.raises(APIError) as exc_info:
            provider.query("Hello")
        
        assert "Anthropic API error" in str(exc_info.value)
    
    @patch('msgmodel.providers.anthropic.requests.post')
    def test_query_request_exception(self, mock_post):
        """Test query with requests.RequestException (network error)."""
        import requests
        mock_post.side_effect = requests.RequestException("Connection refused")
        
        provider = AnthropicProvider("test-api-key")
        
        with pytest.raises(APIError) as exc_info:
            provider.query("Hello")
        
        assert "Request failed" in str(exc_info.value)


class TestAnthropicProviderExtractText:
    """Tests for text extraction."""
    
    def test_extract_text_single_block(self):
        """Test extracting text from single content block."""
        response = {
            "content": [{"type": "text", "text": "Hello, world!"}]
        }
        text = AnthropicProvider.extract_text(response)
        assert text == "Hello, world!"
    
    def test_extract_text_multiple_blocks(self):
        """Test extracting text from multiple content blocks."""
        response = {
            "content": [
                {"type": "text", "text": "First"},
                {"type": "text", "text": "Second"}
            ]
        }
        text = AnthropicProvider.extract_text(response)
        assert text == "FirstSecond"
    
    def test_extract_text_empty_response(self):
        """Test extracting text from empty response."""
        response = {"content": []}
        text = AnthropicProvider.extract_text(response)
        assert text == ""
    
    def test_extract_text_no_content(self):
        """Test extracting text when no content field."""
        response = {}
        text = AnthropicProvider.extract_text(response)
        assert text == ""


class TestAnthropicProviderPrivacyInfo:
    """Tests for privacy information."""
    
    def test_get_privacy_info(self):
        """Test privacy info is returned correctly."""
        info = AnthropicProvider.get_privacy_info()
        
        assert info["provider"] == "anthropic"
        assert info["training_retention"] is False
        assert "reference" in info
        assert "anthropic.com" in info["reference"]


class TestAnthropicProviderStream:
    """Tests for streaming functionality."""
    
    @patch('msgmodel.providers.anthropic.requests.post')
    def test_stream_success(self, mock_post):
        """Test successful streaming."""
        # Create mock response with streaming data
        mock_response = Mock()
        mock_response.ok = True
        mock_response.iter_lines.return_value = [
            b'data: {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "Hello"}}',
            b'data: {"type": "content_block_delta", "delta": {"type": "text_delta", "text": " world"}}',
            b'data: {"type": "message_stop"}',
        ]
        mock_post.return_value = mock_response
        
        provider = AnthropicProvider("test-api-key")
        chunks = list(provider.stream("Hello"))
        
        assert chunks == ["Hello", " world"]
    
    @patch('msgmodel.providers.anthropic.requests.post')
    def test_stream_api_error(self, mock_post):
        """Test streaming with API error."""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_response.text = "Internal server error"
        mock_post.return_value = mock_response
        
        provider = AnthropicProvider("test-api-key")
        
        with pytest.raises(APIError):
            list(provider.stream("Hello"))
    
    @patch('msgmodel.providers.anthropic.requests.post')
    def test_stream_timeout(self, mock_post):
        """Test streaming timeout."""
        import requests
        mock_post.side_effect = requests.Timeout("Timed out")
        
        provider = AnthropicProvider("test-api-key")
        with pytest.raises(StreamingError) as exc_info:
            list(provider.stream("Hi", timeout=10))
        
        assert "timed out" in str(exc_info.value).lower()
    
    @patch('msgmodel.providers.anthropic.requests.post')
    def test_stream_request_exception(self, mock_post):
        """Test streaming request exception."""
        import requests
        mock_post.side_effect = requests.RequestException("Connection failed")
        
        provider = AnthropicProvider("test-api-key")
        with pytest.raises(APIError) as exc_info:
            list(provider.stream("Hi"))
        
        assert "Connection failed" in str(exc_info.value)
    
    @patch('msgmodel.providers.anthropic.requests.post')
    def test_stream_no_chunks_error(self, mock_post):
        """Test error when no chunks received."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.iter_lines.return_value = [
            b'data: {"type": "message_start"}',  # No text content
            b'data: {"type": "message_stop"}',
        ]
        mock_post.return_value = mock_response
        
        provider = AnthropicProvider("test-api-key")
        with pytest.raises(StreamingError) as exc_info:
            list(provider.stream("Hi"))
        
        assert "No text chunks" in str(exc_info.value)
    
    @patch('msgmodel.providers.anthropic.requests.post')
    def test_stream_rate_limit_error(self, mock_post):
        """Test handling rate limit error in stream."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.iter_lines.return_value = [
            b'data: {"error":{"message":"Rate limit exceeded","type":"rate_limit_error"}}'
        ]
        mock_post.return_value = mock_response
        
        provider = AnthropicProvider("test-api-key")
        with pytest.raises(APIError) as exc_info:
            list(provider.stream("Hi"))
        
        assert exc_info.value.status_code == 429
    
    @patch('msgmodel.providers.anthropic.requests.post')
    def test_stream_generic_error(self, mock_post):
        """Test handling generic error in stream."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.iter_lines.return_value = [
            b'data: {"error":{"message":"Something went wrong","type":"server_error"}}'
        ]
        mock_post.return_value = mock_response
        
        provider = AnthropicProvider("test-api-key")
        with pytest.raises(APIError) as exc_info:
            list(provider.stream("Hi"))
        
        assert "server_error" in str(exc_info.value)
    
    @patch('msgmodel.providers.anthropic.requests.post')
    def test_stream_json_decode_error_skipped(self, mock_post):
        """Test that invalid JSON lines are skipped."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.iter_lines.return_value = [
            b'data: not-valid-json',
            b'data: {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "Hello"}}',
            b'data: {"type": "message_stop"}',
        ]
        mock_post.return_value = mock_response
        
        provider = AnthropicProvider("test-api-key")
        chunks = list(provider.stream("Hi"))
        
        assert chunks == ["Hello"]
    
    @patch('msgmodel.providers.anthropic.requests.post')
    def test_stream_done_marker(self, mock_post):
        """Test [DONE] marker stops stream."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.iter_lines.return_value = [
            b'data: {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "Hello"}}',
            b'data: [DONE]',
            b'data: {"type": "content_block_delta", "delta": {"type": "text_delta", "text": " world"}}',  # Should not be received
        ]
        mock_post.return_value = mock_response
        
        provider = AnthropicProvider("test-api-key")
        chunks = list(provider.stream("Hi"))
        
        assert chunks == ["Hello"]
    
    @patch('msgmodel.providers.anthropic.requests.post')
    def test_stream_interrupted_exception(self, mock_post):
        """Test handling of unexpected exception during streaming."""
        mock_response = Mock()
        mock_response.ok = True
        
        def iter_lines_with_error():
            yield b'data: {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "Hello"}}'
            raise RuntimeError("Connection lost")
        
        mock_response.iter_lines = iter_lines_with_error
        mock_post.return_value = mock_response
        
        provider = AnthropicProvider("test-api-key")
        with pytest.raises(StreamingError) as exc_info:
            list(provider.stream("Hi"))
        
        assert "interrupted" in str(exc_info.value).lower()
    
    @patch('msgmodel.providers.anthropic.requests.post')
    def test_stream_with_on_chunk_callback(self, mock_post):
        """Test streaming with on_chunk callback."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.iter_lines.return_value = [
            b'data: {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "Hello"}}',
            b'data: {"type": "content_block_delta", "delta": {"type": "text_delta", "text": " world"}}',
        ]
        mock_post.return_value = mock_response
        
        provider = AnthropicProvider("test-api-key")
        received = []
        
        def callback(chunk):
            received.append(chunk)
            return True  # Continue
        
        list(provider.stream("Hello", on_chunk=callback))
        
        assert received == ["Hello", " world"]
    
    @patch('msgmodel.providers.anthropic.requests.post')
    def test_stream_abort_via_callback(self, mock_post):
        """Test streaming abort via callback - callback returning False stops the stream."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.iter_lines.return_value = [
            b'data: {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "Hello"}}',
            b'data: {"type": "content_block_delta", "delta": {"type": "text_delta", "text": " world"}}',
            b'data: {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "!"}}',
        ]
        mock_post.return_value = mock_response
        
        provider = AnthropicProvider("test-api-key")
        call_count = [0]
        
        def abort_after_second(chunk):
            call_count[0] += 1
            # Allow first two chunks, abort on third
            return call_count[0] < 3
        
        chunks = list(provider.stream("Hello", on_chunk=abort_after_second))
        
        # Should get first two chunks (callback returned True), then abort on third
        # (callback returns False, so third chunk is NOT yielded)
        assert chunks == ["Hello", " world"]
        assert call_count[0] == 3  # Callback was called 3 times
