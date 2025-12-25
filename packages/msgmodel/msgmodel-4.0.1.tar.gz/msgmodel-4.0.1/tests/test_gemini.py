"""
Tests for msgmodel.providers.gemini module.
"""

import pytest
import json
import base64
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from msgmodel.providers.gemini import GeminiProvider
from msgmodel.config import GeminiConfig
from msgmodel.exceptions import APIError, StreamingError


class TestGeminiProviderInit:
    """Tests for GeminiProvider initialization."""
    
    @patch('msgmodel.providers.gemini.requests.post')
    def test_init_with_api_key(self, mock_post):
        """Test initialization with API key."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        provider = GeminiProvider("test-api-key")
        assert provider.api_key == "test-api-key"
        assert isinstance(provider.config, GeminiConfig)
        assert provider._api_validated is True
    
    @patch('msgmodel.providers.gemini.requests.post')
    def test_init_with_custom_config(self, mock_post):
        """Test initialization with custom config."""
        mock_response = Mock()
        mock_response.ok = True
        mock_post.return_value = mock_response
        
        config = GeminiConfig(model="gemini-1.5-pro", max_tokens=2000)
        provider = GeminiProvider("test-api-key", config)
        assert provider.config.model == "gemini-1.5-pro"
        assert provider.config.max_tokens == 2000
    
    @patch('msgmodel.providers.gemini.requests.post')
    def test_init_validation_rate_limit(self, mock_post):
        """Test initialization handles rate limit gracefully."""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 429
        mock_post.return_value = mock_response
        
        # Rate limit during validation shouldn't fail - just log warning
        provider = GeminiProvider("test-api-key")
        # Should still be created
        assert provider.api_key == "test-api-key"
    
    @patch('msgmodel.providers.gemini.requests.post')
    def test_init_validation_forbidden(self, mock_post):
        """Test initialization handles forbidden error."""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 403
        mock_response.text = "API key invalid"
        mock_post.return_value = mock_response
        
        with pytest.raises(APIError) as exc_info:
            GeminiProvider("bad-api-key")
        
        assert exc_info.value.status_code == 403
    
    @patch('msgmodel.providers.gemini.requests.post')
    def test_init_validation_other_error(self, mock_post):
        """Test initialization handles other errors."""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_response.text = "Server error"
        mock_post.return_value = mock_response
        
        with pytest.raises(APIError) as exc_info:
            GeminiProvider("test-api-key")
        
        assert exc_info.value.status_code == 500
    
    @patch('msgmodel.providers.gemini.requests.post')
    def test_init_validation_request_exception(self, mock_post):
        """Test initialization handles request exception."""
        import requests
        mock_post.side_effect = requests.RequestException("Network error")
        
        with pytest.raises(APIError) as exc_info:
            GeminiProvider("test-api-key")
        
        assert "Network error" in str(exc_info.value)


class TestGeminiProviderFactoryMethods:
    """Tests for factory methods."""
    
    @patch('msgmodel.providers.gemini.requests.post')
    def test_create_verified(self, mock_post):
        """Test create_verified factory method."""
        mock_response = Mock()
        mock_response.ok = True
        mock_post.return_value = mock_response
        
        provider = GeminiProvider.create_verified("test-api-key")
        assert provider._api_validated is True
    
    @patch('msgmodel.providers.gemini.requests.post')
    def test_create_with_cached_validation_skip(self, mock_post):
        """Test create_with_cached_validation with validated=True."""
        # When validated=True, should NOT make a validation request
        provider = GeminiProvider.create_with_cached_validation(
            "test-api-key", validated=True
        )
        
        assert provider.api_key == "test-api-key"
        assert provider._api_validated is True
        mock_post.assert_not_called()
    
    @patch('msgmodel.providers.gemini.requests.post')
    def test_create_with_cached_validation_no_skip(self, mock_post):
        """Test create_with_cached_validation with validated=False."""
        mock_response = Mock()
        mock_response.ok = True
        mock_post.return_value = mock_response
        
        provider = GeminiProvider.create_with_cached_validation(
            "test-api-key", validated=False
        )
        
        assert provider._api_validated is True
        mock_post.assert_called()  # Should validate


class TestGeminiProviderUrl:
    """Tests for URL building."""
    
    @patch('msgmodel.providers.gemini.requests.post')
    def test_build_url_non_stream(self, mock_post):
        """Test URL building for non-streaming."""
        mock_response = Mock()
        mock_response.ok = True
        mock_post.return_value = mock_response
        
        provider = GeminiProvider("test-api-key")
        url = provider._build_url(stream=False)
        
        assert "generateContent" in url
        assert "streamGenerateContent" not in url
        assert "test-api-key" in url
    
    @patch('msgmodel.providers.gemini.requests.post')
    def test_build_url_stream(self, mock_post):
        """Test URL building for streaming."""
        mock_response = Mock()
        mock_response.ok = True
        mock_post.return_value = mock_response
        
        provider = GeminiProvider("test-api-key")
        url = provider._build_url(stream=True)
        
        assert "streamGenerateContent" in url
        assert "alt=sse" in url


class TestGeminiProviderPayload:
    """Tests for payload building."""
    
    @patch('msgmodel.providers.gemini.requests.post')
    def test_build_payload_basic(self, mock_post):
        """Test basic payload building."""
        mock_response = Mock()
        mock_response.ok = True
        mock_post.return_value = mock_response
        
        provider = GeminiProvider("test-api-key")
        payload = provider._build_payload("Hello")
        
        assert "contents" in payload
        assert payload["contents"][0]["parts"][0]["text"] == "Hello"
        assert "generationConfig" in payload
        assert "safetySettings" in payload
    
    @patch('msgmodel.providers.gemini.requests.post')
    def test_build_payload_with_system(self, mock_post):
        """Test payload building with system instruction."""
        mock_response = Mock()
        mock_response.ok = True
        mock_post.return_value = mock_response
        
        provider = GeminiProvider("test-api-key")
        payload = provider._build_payload("Hello", system_instruction="Be helpful")
        
        assert "systemInstruction" in payload
        assert payload["systemInstruction"]["parts"][0]["text"] == "Be helpful"
    
    @patch('msgmodel.providers.gemini.requests.post')
    def test_build_payload_with_file(self, mock_post):
        """Test payload building with file data."""
        mock_response = Mock()
        mock_response.ok = True
        mock_post.return_value = mock_response
        
        provider = GeminiProvider("test-api-key")
        file_data = {
            "mime_type": "image/png",
            "data": base64.b64encode(b"fake image").decode(),
            "filename": "test.png"
        }
        payload = provider._build_payload("Describe", file_data=file_data)
        
        parts = payload["contents"][0]["parts"]
        assert len(parts) == 2
        assert "inline_data" in parts[1]
        assert parts[1]["inline_data"]["mime_type"] == "image/png"
    
    @patch('msgmodel.providers.gemini.requests.post')
    def test_build_payload_generation_config(self, mock_post):
        """Test payload includes correct generation config."""
        mock_response = Mock()
        mock_response.ok = True
        mock_post.return_value = mock_response
        
        config = GeminiConfig(max_tokens=500, temperature=0.5)
        provider = GeminiProvider("test-api-key", config)
        payload = provider._build_payload("Hello")
        
        gen_config = payload["generationConfig"]
        assert gen_config["maxOutputTokens"] == 500
        assert gen_config["temperature"] == 0.5


class TestGeminiProviderQuery:
    """Tests for query method."""
    
    @patch('msgmodel.providers.gemini.requests.post')
    def test_query_success(self, mock_post):
        """Test successful query."""
        # First call is validation, second is actual query
        validation_response = Mock()
        validation_response.ok = True
        
        query_response = Mock()
        query_response.ok = True
        query_response.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "Hello!"}]}}]
        }
        
        mock_post.side_effect = [validation_response, query_response]
        
        provider = GeminiProvider("test-api-key")
        result = provider.query("Hi")
        
        assert result["candidates"][0]["content"]["parts"][0]["text"] == "Hello!"
    
    @patch('msgmodel.providers.gemini.requests.post')
    def test_query_api_error(self, mock_post):
        """Test query handling API error."""
        validation_response = Mock()
        validation_response.ok = True
        
        query_response = Mock()
        query_response.ok = False
        query_response.status_code = 500
        query_response.text = "Server error"
        
        mock_post.side_effect = [validation_response, query_response]
        
        provider = GeminiProvider("test-api-key")
        with pytest.raises(APIError) as exc_info:
            provider.query("Hi")
        
        assert exc_info.value.status_code == 500
    
    @patch('msgmodel.providers.gemini.requests.post')
    def test_query_request_exception(self, mock_post):
        """Test query handling request exception."""
        import requests
        
        validation_response = Mock()
        validation_response.ok = True
        
        mock_post.side_effect = [validation_response, requests.RequestException("Connection failed")]
        
        provider = GeminiProvider("test-api-key")
        with pytest.raises(APIError) as exc_info:
            provider.query("Hi")
        
        assert "Connection failed" in str(exc_info.value)


class TestGeminiProviderStream:
    """Tests for stream method."""
    
    @patch('msgmodel.providers.gemini.requests.post')
    def test_stream_success(self, mock_post):
        """Test successful streaming."""
        validation_response = Mock()
        validation_response.ok = True
        
        stream_response = Mock()
        stream_response.ok = True
        stream_response.iter_lines.return_value = [
            b'data: {"candidates":[{"content":{"parts":[{"text":"Hello"}]}}]}',
            b'data: {"candidates":[{"content":{"parts":[{"text":" world"}]}}]}',
        ]
        
        mock_post.side_effect = [validation_response, stream_response]
        
        provider = GeminiProvider("test-api-key")
        chunks = list(provider.stream("Hi"))
        
        assert chunks == ["Hello", " world"]
    
    @patch('msgmodel.providers.gemini.requests.post')
    def test_stream_with_callback(self, mock_post):
        """Test streaming with callback."""
        validation_response = Mock()
        validation_response.ok = True
        
        stream_response = Mock()
        stream_response.ok = True
        stream_response.iter_lines.return_value = [
            b'data: {"candidates":[{"content":{"parts":[{"text":"Hello"}]}}]}',
            b'data: {"candidates":[{"content":{"parts":[{"text":" world"}]}}]}',
        ]
        
        mock_post.side_effect = [validation_response, stream_response]
        
        collected = []
        def callback(chunk):
            collected.append(chunk)
            return True
        
        provider = GeminiProvider("test-api-key")
        chunks = list(provider.stream("Hi", on_chunk=callback))
        
        assert collected == ["Hello", " world"]
    
    @patch('msgmodel.providers.gemini.requests.post')
    def test_stream_abort_via_callback(self, mock_post):
        """Test aborting stream via callback."""
        validation_response = Mock()
        validation_response.ok = True
        
        stream_response = Mock()
        stream_response.ok = True
        stream_response.iter_lines.return_value = [
            b'data: {"candidates":[{"content":{"parts":[{"text":"Hello"}]}}]}',
            b'data: {"candidates":[{"content":{"parts":[{"text":" world"}]}}]}',
            b'data: {"candidates":[{"content":{"parts":[{"text":"!"}]}}]}',
        ]
        
        mock_post.side_effect = [validation_response, stream_response]
        
        call_count = [0]
        def callback(chunk):
            call_count[0] += 1
            # Return True for first two chunks, False on third
            return call_count[0] < 3
        
        provider = GeminiProvider("test-api-key")
        chunks = list(provider.stream("Hi", on_chunk=callback))
        
        # Callback returns False on third chunk, so it's not yielded
        assert chunks == ["Hello", " world"]
    
    @patch('msgmodel.providers.gemini.requests.post')
    def test_stream_api_error(self, mock_post):
        """Test streaming API error."""
        validation_response = Mock()
        validation_response.ok = True
        
        stream_response = Mock()
        stream_response.ok = False
        stream_response.status_code = 500
        stream_response.text = "Server error"
        
        mock_post.side_effect = [validation_response, stream_response]
        
        provider = GeminiProvider("test-api-key")
        with pytest.raises(APIError) as exc_info:
            list(provider.stream("Hi"))
        
        assert exc_info.value.status_code == 500
    
    @patch('msgmodel.providers.gemini.requests.post')
    def test_stream_timeout(self, mock_post):
        """Test streaming timeout."""
        import requests
        
        validation_response = Mock()
        validation_response.ok = True
        
        mock_post.side_effect = [validation_response, requests.Timeout("Timed out")]
        
        provider = GeminiProvider("test-api-key")
        with pytest.raises(StreamingError) as exc_info:
            list(provider.stream("Hi", timeout=10))
        
        assert "timed out" in str(exc_info.value).lower()
    
    @patch('msgmodel.providers.gemini.requests.post')
    def test_stream_request_exception(self, mock_post):
        """Test streaming request exception."""
        import requests
        
        validation_response = Mock()
        validation_response.ok = True
        
        mock_post.side_effect = [validation_response, requests.RequestException("Connection failed")]
        
        provider = GeminiProvider("test-api-key")
        with pytest.raises(APIError) as exc_info:
            list(provider.stream("Hi"))
        
        assert "Connection failed" in str(exc_info.value)
    
    @patch('msgmodel.providers.gemini.requests.post')
    def test_stream_no_chunks_error(self, mock_post):
        """Test error when no chunks received."""
        validation_response = Mock()
        validation_response.ok = True
        
        stream_response = Mock()
        stream_response.ok = True
        stream_response.iter_lines.return_value = [
            b'data: {"candidates":[{"content":{"parts":[]}}]}',  # No text
        ]
        
        mock_post.side_effect = [validation_response, stream_response]
        
        provider = GeminiProvider("test-api-key")
        with pytest.raises(StreamingError) as exc_info:
            list(provider.stream("Hi"))
        
        assert "No text chunks" in str(exc_info.value)
    
    @patch('msgmodel.providers.gemini.requests.post')
    def test_stream_rate_limit_error(self, mock_post):
        """Test handling rate limit error in stream."""
        validation_response = Mock()
        validation_response.ok = True
        
        stream_response = Mock()
        stream_response.ok = True
        stream_response.iter_lines.return_value = [
            b'data: {"error":{"message":"Quota exceeded","status":"RESOURCE_EXHAUSTED"}}'
        ]
        
        mock_post.side_effect = [validation_response, stream_response]
        
        provider = GeminiProvider("test-api-key")
        with pytest.raises(APIError) as exc_info:
            list(provider.stream("Hi"))
        
        assert exc_info.value.status_code == 429
    
    @patch('msgmodel.providers.gemini.requests.post')
    def test_stream_generic_error(self, mock_post):
        """Test handling generic error in stream."""
        validation_response = Mock()
        validation_response.ok = True
        
        stream_response = Mock()
        stream_response.ok = True
        stream_response.iter_lines.return_value = [
            b'data: {"error":{"message":"Something went wrong","status":"INTERNAL"}}'
        ]
        
        mock_post.side_effect = [validation_response, stream_response]
        
        provider = GeminiProvider("test-api-key")
        with pytest.raises(APIError) as exc_info:
            list(provider.stream("Hi"))
        
        assert "INTERNAL" in str(exc_info.value)
    
    @patch('msgmodel.providers.gemini.requests.post')
    def test_stream_json_decode_error_skipped(self, mock_post):
        """Test that invalid JSON lines are skipped."""
        validation_response = Mock()
        validation_response.ok = True
        
        stream_response = Mock()
        stream_response.ok = True
        stream_response.iter_lines.return_value = [
            b'data: not-valid-json',
            b'data: {"candidates":[{"content":{"parts":[{"text":"Hello"}]}}]}',
        ]
        
        mock_post.side_effect = [validation_response, stream_response]
        
        provider = GeminiProvider("test-api-key")
        chunks = list(provider.stream("Hi"))
        
        assert chunks == ["Hello"]
    
    @patch('msgmodel.providers.gemini.requests.post')
    def test_stream_interrupted_exception(self, mock_post):
        """Test handling of unexpected exception during streaming."""
        validation_response = Mock()
        validation_response.ok = True
        
        stream_response = Mock()
        stream_response.ok = True
        
        def iter_lines_with_error():
            yield b'data: {"candidates":[{"content":{"parts":[{"text":"Hello"}]}}]}'
            raise RuntimeError("Connection lost")
        
        stream_response.iter_lines = iter_lines_with_error
        
        mock_post.side_effect = [validation_response, stream_response]
        
        provider = GeminiProvider("test-api-key")
        with pytest.raises(StreamingError) as exc_info:
            list(provider.stream("Hi"))
        
        assert "interrupted" in str(exc_info.value).lower()


class TestGeminiExtractText:
    """Tests for extract_text static method."""
    
    def test_extract_text_normal(self):
        """Test extracting text from normal response."""
        response = {
            "candidates": [{"content": {"parts": [{"text": "Hello!"}]}}]
        }
        assert GeminiProvider.extract_text(response) == "Hello!"
    
    def test_extract_text_multiple_parts(self):
        """Test extracting text from response with multiple parts."""
        response = {
            "candidates": [{"content": {"parts": [
                {"text": "Hello"},
                {"text": " world!"}
            ]}}]
        }
        assert GeminiProvider.extract_text(response) == "Hello world!"
    
    def test_extract_text_empty_candidates(self):
        """Test extracting text from response with no candidates."""
        response = {"candidates": []}
        assert GeminiProvider.extract_text(response) == ""
    
    def test_extract_text_no_text(self):
        """Test extracting text when text is missing."""
        response = {"candidates": [{"content": {"parts": [{"inline_data": {}}]}}]}
        assert GeminiProvider.extract_text(response) == ""
    
    def test_extract_text_invalid_structure(self):
        """Test extracting text from invalid structure."""
        response = {"something": "else"}
        assert GeminiProvider.extract_text(response) == ""


class TestGeminiExtractBinaryOutputs:
    """Tests for extract_binary_outputs static method."""
    
    def test_extract_binary_outputs_no_binary(self):
        """Test with response containing no binary data."""
        response = {
            "candidates": [{"content": {"parts": [{"text": "Hello"}]}}]
        }
        result = GeminiProvider.extract_binary_outputs(response)
        assert result == []
    
    def test_extract_binary_outputs_with_binary(self, tmp_path):
        """Test extracting binary data from response."""
        response = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": base64.b64encode(b"fake image data").decode()
                        }
                    }]
                }
            }]
        }
        
        result = GeminiProvider.extract_binary_outputs(response, str(tmp_path))
        
        assert len(result) == 1
        assert result[0].endswith(".png")
        # Verify file was created and contains correct data
        with open(result[0], "rb") as f:
            assert f.read() == b"fake image data"


class TestGeminiPrivacyInfo:
    """Tests for get_privacy_info static method."""
    
    def test_get_privacy_info(self):
        """Test privacy info structure."""
        info = GeminiProvider.get_privacy_info()
        
        assert info["provider"] == "gemini"
        assert info["training_retention"] == "depends_on_tier"
        assert "tier" in info["provider_policy"].lower()
        assert "reference" in info
