"""
Tests for msgmodel.async_core module.

Tests async versions of query() and stream() functions.
Requires pytest-asyncio for async test support.
"""

import io
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

# Import the module under test
from msgmodel.async_core import (
    aquery,
    astream,
    _ensure_aiohttp,
    _aquery_openai,
    _aquery_gemini,
    _astream_openai,
    _astream_gemini,
    _verify_gemini_billing_sync,
    _verified_gemini_keys,
    AIOHTTP_AVAILABLE,
)
from msgmodel.config import (
    Provider,
    OpenAIConfig,
    GeminiConfig,
    get_default_config,
)
from msgmodel.exceptions import ConfigurationError, APIError
from msgmodel.core import LLMResponse


# Skip all tests if aiohttp is not available
pytestmark = pytest.mark.skipif(
    not AIOHTTP_AVAILABLE,
    reason="aiohttp not installed"
)


class TestAiohttpNotInstalled:
    """Tests for when aiohttp is not installed."""
    
    def test_aiohttp_import_failure_path(self):
        """Test the ImportError path when aiohttp is not available.
        
        This tests lines 60-61 of async_core.py by temporarily
        setting AIOHTTP_AVAILABLE to False.
        """
        from msgmodel import async_core
        
        # Save original value
        original = async_core.AIOHTTP_AVAILABLE
        
        try:
            # Simulate aiohttp not being installed
            async_core.AIOHTTP_AVAILABLE = False
            
            with pytest.raises(ImportError, match="aiohttp is required"):
                async_core._ensure_aiohttp()
        finally:
            # Restore original value
            async_core.AIOHTTP_AVAILABLE = original


class TestEnsureAiohttp:
    """Tests for _ensure_aiohttp helper."""
    
    def test_ensure_aiohttp_when_available(self):
        """Test that _ensure_aiohttp passes when aiohttp is installed."""
        # Should not raise since we're in a test environment with aiohttp
        _ensure_aiohttp()
    
    def test_ensure_aiohttp_when_unavailable(self):
        """Test that _ensure_aiohttp raises ImportError when aiohttp is missing."""
        with patch("msgmodel.async_core.AIOHTTP_AVAILABLE", False):
            # Need to reimport or call directly with patched value
            from msgmodel import async_core
            original = async_core.AIOHTTP_AVAILABLE
            async_core.AIOHTTP_AVAILABLE = False
            try:
                with pytest.raises(ImportError, match="aiohttp is required"):
                    async_core._ensure_aiohttp()
            finally:
                async_core.AIOHTTP_AVAILABLE = original


class TestAqueryFunction:
    """Tests for the aquery async function."""
    
    @pytest.mark.asyncio
    async def test_aquery_openai_basic(self):
        """Test basic aquery with OpenAI provider."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value={
            "choices": [{"message": {"content": "Hello!"}}],
            "usage": {"total_tokens": 10}
        })
        
        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=None)
        ))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch("msgmodel.async_core._get_api_key") as mock_key:
            mock_key.return_value = "sk-test"
            
            with patch("msgmodel.async_core.aiohttp.ClientSession", return_value=mock_session):
                result = await aquery("openai", "Hello")
                
                assert isinstance(result, LLMResponse)
                assert result.provider == "openai"
    
    @pytest.mark.asyncio
    async def test_aquery_with_file_like(self):
        """Test aquery with file_like parameter."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value={
            "choices": [{"message": {"content": "Analysis complete"}}],
            "usage": {}
        })
        
        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=None)
        ))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch("msgmodel.async_core._get_api_key") as mock_key:
            mock_key.return_value = "sk-test"
            
            with patch("msgmodel.async_core.aiohttp.ClientSession", return_value=mock_session):
                file_obj = io.BytesIO(b"test document content")
                result = await aquery(
                    "openai",
                    "Analyze this",
                    file_like=file_obj,
                    filename="document.pdf"
                )
                
                assert isinstance(result, LLMResponse)
    
    @pytest.mark.asyncio
    async def test_aquery_with_file_like_name_attribute(self):
        """Test aquery with file_like using .name attribute for MIME detection."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value={
            "choices": [{"message": {"content": "Image described"}}],
            "usage": {}
        })
        
        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=None)
        ))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch("msgmodel.async_core._get_api_key") as mock_key:
            mock_key.return_value = "sk-test"
            
            with patch("msgmodel.async_core.aiohttp.ClientSession", return_value=mock_session):
                file_obj = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
                file_obj.name = "image.png"
                
                result = await aquery("openai", "Describe this image", file_like=file_obj)
                
                assert isinstance(result, LLMResponse)
    
    @pytest.mark.asyncio
    async def test_aquery_provider_shortcuts(self):
        """Test aquery accepts provider shortcuts."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value={
            "choices": [{"message": {"content": "Hi"}}],
            "usage": {}
        })
        
        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=None)
        ))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch("msgmodel.async_core._get_api_key") as mock_key:
            mock_key.return_value = "sk-test"
            
            with patch("msgmodel.async_core.aiohttp.ClientSession", return_value=mock_session):
                # Test 'o' shortcut for OpenAI
                result = await aquery("o", "Hello")
                assert result.provider == "openai"
    
    @pytest.mark.asyncio
    async def test_aquery_with_config_overrides(self):
        """Test aquery with max_tokens, model, temperature overrides."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value={
            "choices": [{"message": {"content": "Response"}}],
            "usage": {}
        })
        
        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=None)
        ))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch("msgmodel.async_core._get_api_key") as mock_key:
            mock_key.return_value = "sk-test"
            
            with patch("msgmodel.async_core.aiohttp.ClientSession", return_value=mock_session):
                result = await aquery(
                    "openai",
                    "Hello",
                    max_tokens=100,
                    model="gpt-4",
                    temperature=0.5
                )
                
                assert isinstance(result, LLMResponse)
    
    @pytest.mark.asyncio
    async def test_aquery_unsupported_provider(self):
        """Test aquery raises ConfigurationError for unsupported provider."""
        with patch("msgmodel.async_core._get_api_key") as mock_key:
            mock_key.return_value = "test-key"
            
            # Anthropic is not supported in async yet
            with pytest.raises(ConfigurationError, match="Unsupported provider"):
                await aquery("anthropic", "Hello")
    
    @pytest.mark.asyncio
    async def test_aquery_api_error(self):
        """Test aquery raises APIError on HTTP error."""
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status = 401
        mock_response.text = AsyncMock(return_value="Unauthorized")
        
        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=None)
        ))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch("msgmodel.async_core._get_api_key") as mock_key:
            mock_key.return_value = "bad-key"
            
            with patch("msgmodel.async_core.aiohttp.ClientSession", return_value=mock_session):
                with pytest.raises(APIError) as exc_info:
                    await aquery("openai", "Hello")
                
                assert exc_info.value.status_code == 401
                assert exc_info.value.provider == "openai"


class TestAqueryGemini:
    """Tests for aquery with Gemini provider."""
    
    @pytest.mark.asyncio
    async def test_aquery_gemini_basic(self):
        """Test basic aquery with Gemini provider."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value={
            "candidates": [{"content": {"parts": [{"text": "Hello from Gemini!"}]}}]
        })
        
        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=None)
        ))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch("msgmodel.async_core._get_api_key") as mock_key:
            mock_key.return_value = "test-key"
            
            with patch("msgmodel.async_core._verify_gemini_billing_sync"):
                with patch("msgmodel.async_core.aiohttp.ClientSession", return_value=mock_session):
                    with patch("msgmodel.providers.gemini.GeminiProvider.create_with_cached_validation") as mock_provider:
                        mock_prov = MagicMock()
                        mock_prov._build_url.return_value = "https://api.gemini.test"
                        mock_prov._build_payload.return_value = {}
                        mock_prov.extract_text.return_value = "Hello from Gemini!"
                        mock_provider.return_value = mock_prov
                        
                        result = await aquery("gemini", "Hello")
                        
                        assert isinstance(result, LLMResponse)
                        assert result.provider == "gemini"
                        assert result.text == "Hello from Gemini!"
    
    @pytest.mark.asyncio
    async def test_aquery_gemini_with_file_like(self):
        """Test aquery Gemini with file_like parameter."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value={
            "candidates": [{"content": {"parts": [{"text": "Document analyzed"}]}}]
        })
        
        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=None)
        ))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch("msgmodel.async_core._get_api_key") as mock_key:
            mock_key.return_value = "test-key"
            
            with patch("msgmodel.async_core._verify_gemini_billing_sync"):
                with patch("msgmodel.async_core.aiohttp.ClientSession", return_value=mock_session):
                    with patch("msgmodel.providers.gemini.GeminiProvider.create_with_cached_validation") as mock_provider:
                        mock_prov = MagicMock()
                        mock_prov._build_url.return_value = "https://api.gemini.test"
                        mock_prov._build_payload.return_value = {}
                        mock_prov.extract_text.return_value = "Document analyzed"
                        mock_provider.return_value = mock_prov
                        
                        file_obj = io.BytesIO(b"%PDF-1.5 content")
                        result = await aquery(
                            "g",  # shortcut
                            "Analyze",
                            file_like=file_obj,
                            filename="doc.pdf"
                        )
                        
                        assert result.text == "Document analyzed"
    
    @pytest.mark.asyncio
    async def test_aquery_gemini_api_error(self):
        """Test aquery Gemini raises APIError on HTTP error."""
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status = 400
        mock_response.text = AsyncMock(return_value="Bad request")
        
        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=None)
        ))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch("msgmodel.async_core._get_api_key") as mock_key:
            mock_key.return_value = "test-key"
            
            with patch("msgmodel.async_core._verify_gemini_billing_sync"):
                with patch("msgmodel.async_core.aiohttp.ClientSession", return_value=mock_session):
                    with patch("msgmodel.providers.gemini.GeminiProvider.create_with_cached_validation") as mock_provider:
                        mock_prov = MagicMock()
                        mock_prov._build_url.return_value = "https://api.gemini.test"
                        mock_prov._build_payload.return_value = {}
                        mock_provider.return_value = mock_prov
                        
                        with pytest.raises(APIError) as exc_info:
                            await aquery("gemini", "Hello")
                        
                        assert exc_info.value.status_code == 400
                        assert exc_info.value.provider == "gemini"


class TestAstreamFunction:
    """Tests for the astream async function."""
    
    @pytest.mark.asyncio
    async def test_astream_openai_basic(self):
        """Test basic astream with OpenAI provider."""
        # Simulate SSE streaming response
        chunks = [
            b'data: {"choices":[{"delta":{"content":"Hello"}}]}\n',
            b'data: {"choices":[{"delta":{"content":" World"}}]}\n',
            b'data: [DONE]\n',
        ]
        
        async def mock_content_iter():
            for chunk in chunks:
                yield chunk
        
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.content = mock_content_iter()
        
        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=None)
        ))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch("msgmodel.async_core._get_api_key") as mock_key:
            mock_key.return_value = "sk-test"
            
            with patch("msgmodel.async_core.aiohttp.ClientSession", return_value=mock_session):
                result = []
                async for chunk in astream("openai", "Hello"):
                    result.append(chunk)
                
                assert result == ["Hello", " World"]
    
    @pytest.mark.asyncio
    async def test_astream_with_file_like(self):
        """Test astream with file_like parameter."""
        chunks = [
            b'data: {"choices":[{"delta":{"content":"Analyzing..."}}]}\n',
            b'data: [DONE]\n',
        ]
        
        async def mock_content_iter():
            for chunk in chunks:
                yield chunk
        
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.content = mock_content_iter()
        
        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=None)
        ))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch("msgmodel.async_core._get_api_key") as mock_key:
            mock_key.return_value = "sk-test"
            
            with patch("msgmodel.async_core.aiohttp.ClientSession", return_value=mock_session):
                file_obj = io.BytesIO(b"document content")
                result = []
                async for chunk in astream(
                    "openai",
                    "Analyze",
                    file_like=file_obj,
                    filename="doc.txt"
                ):
                    result.append(chunk)
                
                assert result == ["Analyzing..."]
    
    @pytest.mark.asyncio
    async def test_astream_handles_json_decode_error(self):
        """Test astream gracefully handles malformed JSON in stream."""
        chunks = [
            b'data: {"choices":[{"delta":{"content":"OK"}}]}\n',
            b'data: {malformed json}\n',  # Should be skipped
            b'data: {"choices":[{"delta":{"content":"!"}}]}\n',
            b'data: [DONE]\n',
        ]
        
        async def mock_content_iter():
            for chunk in chunks:
                yield chunk
        
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.content = mock_content_iter()
        
        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=None)
        ))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch("msgmodel.async_core._get_api_key") as mock_key:
            mock_key.return_value = "sk-test"
            
            with patch("msgmodel.async_core.aiohttp.ClientSession", return_value=mock_session):
                result = []
                async for chunk in astream("openai", "Test"):
                    result.append(chunk)
                
                # Should skip malformed JSON and continue
                assert result == ["OK", "!"]
    
    @pytest.mark.asyncio
    async def test_astream_api_error(self):
        """Test astream raises APIError on HTTP error."""
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value="Internal Server Error")
        
        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=None)
        ))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch("msgmodel.async_core._get_api_key") as mock_key:
            mock_key.return_value = "sk-test"
            
            with patch("msgmodel.async_core.aiohttp.ClientSession", return_value=mock_session):
                with pytest.raises(APIError) as exc_info:
                    async for _ in astream("openai", "Hello"):
                        pass
                
                assert exc_info.value.status_code == 500
    
    @pytest.mark.asyncio
    async def test_astream_unsupported_provider(self):
        """Test astream raises ConfigurationError for unsupported provider."""
        with patch("msgmodel.async_core._get_api_key") as mock_key:
            mock_key.return_value = "test-key"
            
            with pytest.raises(ConfigurationError, match="Unsupported provider"):
                async for _ in astream("anthropic", "Hello"):
                    pass
    
    @pytest.mark.asyncio
    async def test_astream_with_config_overrides(self):
        """Test astream with max_tokens, model, temperature overrides."""
        chunks = [
            b'data: {"choices":[{"delta":{"content":"OK"}}]}\n',
            b'data: [DONE]\n',
        ]
        
        async def mock_content_iter():
            for chunk in chunks:
                yield chunk
        
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.content = mock_content_iter()
        
        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=None)
        ))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch("msgmodel.async_core._get_api_key") as mock_key:
            mock_key.return_value = "sk-test"
            
            with patch("msgmodel.async_core.aiohttp.ClientSession", return_value=mock_session):
                result = []
                async for chunk in astream(
                    "openai",
                    "Hello",
                    max_tokens=50,
                    model="gpt-4",
                    temperature=0.7
                ):
                    result.append(chunk)
                
                assert result == ["OK"]


class TestAstreamGemini:
    """Tests for astream with Gemini provider."""
    
    @pytest.mark.asyncio
    async def test_astream_gemini_basic(self):
        """Test basic astream with Gemini provider."""
        chunks = [
            b'data: {"candidates":[{"content":{"parts":[{"text":"Hello"}]}}]}\n',
            b'data: {"candidates":[{"content":{"parts":[{"text":" Gemini"}]}}]}\n',
        ]
        
        async def mock_content_iter():
            for chunk in chunks:
                yield chunk
        
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.content = mock_content_iter()
        
        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=None)
        ))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch("msgmodel.async_core._get_api_key") as mock_key:
            mock_key.return_value = "test-key"
            
            with patch("msgmodel.async_core._verify_gemini_billing_sync"):
                with patch("msgmodel.async_core.aiohttp.ClientSession", return_value=mock_session):
                    with patch("msgmodel.providers.gemini.GeminiProvider.create_with_cached_validation") as mock_provider:
                        mock_prov = MagicMock()
                        mock_prov._build_url.return_value = "https://api.gemini.test"
                        mock_prov._build_payload.return_value = {}
                        mock_prov.extract_text.side_effect = ["Hello", " Gemini"]
                        mock_provider.return_value = mock_prov
                        
                        result = []
                        async for chunk in astream("gemini", "Hello"):
                            result.append(chunk)
                        
                        assert result == ["Hello", " Gemini"]
    
    @pytest.mark.asyncio
    async def test_astream_gemini_with_file_like(self):
        """Test astream Gemini with file_like parameter."""
        chunks = [
            b'data: {"candidates":[{"content":{"parts":[{"text":"Analyzing PDF..."}]}}]}\n',
        ]
        
        async def mock_content_iter():
            for chunk in chunks:
                yield chunk
        
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.content = mock_content_iter()
        
        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=None)
        ))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch("msgmodel.async_core._get_api_key") as mock_key:
            mock_key.return_value = "test-key"
            
            with patch("msgmodel.async_core._verify_gemini_billing_sync"):
                with patch("msgmodel.async_core.aiohttp.ClientSession", return_value=mock_session):
                    with patch("msgmodel.providers.gemini.GeminiProvider.create_with_cached_validation") as mock_provider:
                        mock_prov = MagicMock()
                        mock_prov._build_url.return_value = "https://api.gemini.test"
                        mock_prov._build_payload.return_value = {}
                        mock_prov.extract_text.return_value = "Analyzing PDF..."
                        mock_provider.return_value = mock_prov
                        
                        file_obj = io.BytesIO(b"%PDF-1.5 content")
                        result = []
                        async for chunk in astream(
                            "g",
                            "Analyze",
                            file_like=file_obj,
                            filename="document.pdf"
                        ):
                            result.append(chunk)
                        
                        assert result == ["Analyzing PDF..."]
    
    @pytest.mark.asyncio
    async def test_astream_gemini_api_error(self):
        """Test astream Gemini raises APIError on HTTP error."""
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status = 403
        mock_response.text = AsyncMock(return_value="Forbidden")
        
        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=None)
        ))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch("msgmodel.async_core._get_api_key") as mock_key:
            mock_key.return_value = "test-key"
            
            with patch("msgmodel.async_core._verify_gemini_billing_sync"):
                with patch("msgmodel.async_core.aiohttp.ClientSession", return_value=mock_session):
                    with patch("msgmodel.providers.gemini.GeminiProvider.create_with_cached_validation") as mock_provider:
                        mock_prov = MagicMock()
                        mock_prov._build_url.return_value = "https://api.gemini.test"
                        mock_prov._build_payload.return_value = {}
                        mock_provider.return_value = mock_prov
                        
                        with pytest.raises(APIError) as exc_info:
                            async for _ in astream("gemini", "Hello"):
                                pass
                        
                        assert exc_info.value.status_code == 403
                        assert exc_info.value.provider == "gemini"
    
    @pytest.mark.asyncio
    async def test_astream_gemini_json_decode_error(self):
        """Test astream Gemini handles malformed JSON in stream gracefully.
        
        This tests lines 475-476 of async_core.py.
        """
        chunks = [
            b'data: {"candidates":[{"content":{"parts":[{"text":"OK"}]}}]}\n',
            b'data: {invalid json here}\n',  # Should be skipped
            b'data: {"candidates":[{"content":{"parts":[{"text":"!"}]}}]}\n',
        ]
        
        async def mock_content_iter():
            for chunk in chunks:
                yield chunk
        
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.content = mock_content_iter()
        
        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=None)
        ))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch("msgmodel.async_core._get_api_key") as mock_key:
            mock_key.return_value = "test-key"
            
            with patch("msgmodel.async_core._verify_gemini_billing_sync"):
                with patch("msgmodel.async_core.aiohttp.ClientSession", return_value=mock_session):
                    with patch("msgmodel.providers.gemini.GeminiProvider.create_with_cached_validation") as mock_provider:
                        mock_prov = MagicMock()
                        mock_prov._build_url.return_value = "https://api.gemini.test"
                        mock_prov._build_payload.return_value = {}
                        mock_prov.extract_text.side_effect = ["OK", "!"]
                        mock_provider.return_value = mock_prov
                        
                        result = []
                        async for chunk in astream("gemini", "Test"):
                            result.append(chunk)
                        
                        # Should skip malformed JSON and continue
                        assert result == ["OK", "!"]


class TestGeminiBillingVerification:
    """Tests for Gemini billing verification in async context."""
    
    def test_verify_gemini_billing_sync(self):
        """Test _verify_gemini_billing_sync caches verified keys."""
        from msgmodel import async_core
        
        # Clear the cache
        async_core._verified_gemini_keys.clear()
        
        with patch("msgmodel.providers.gemini.GeminiProvider") as mock_provider:
            mock_instance = MagicMock()
            mock_provider.return_value = mock_instance
            
            config = GeminiConfig()
            
            # First call should create provider
            _verify_gemini_billing_sync("test-key-1", config)
            assert "test-key-1" in async_core._verified_gemini_keys
            assert mock_provider.call_count == 1
            
            # Second call with same key should skip provider creation
            _verify_gemini_billing_sync("test-key-1", config)
            assert mock_provider.call_count == 1  # Still 1
            
            # Different key should create provider again
            _verify_gemini_billing_sync("test-key-2", config)
            assert "test-key-2" in async_core._verified_gemini_keys
            assert mock_provider.call_count == 2
    
    def test_verify_gemini_billing_sync_raises_on_failure(self):
        """Test _verify_gemini_billing_sync propagates verification errors."""
        from msgmodel import async_core
        
        # Clear the cache
        async_core._verified_gemini_keys.clear()
        
        with patch("msgmodel.providers.gemini.GeminiProvider") as mock_provider:
            mock_provider.side_effect = ConfigurationError("Billing verification failed")
            
            config = GeminiConfig()
            
            with pytest.raises(ConfigurationError, match="Billing verification failed"):
                _verify_gemini_billing_sync("bad-key", config)
            
            # Key should NOT be cached on failure
            assert "bad-key" not in async_core._verified_gemini_keys


class TestAsyncFileHandling:
    """Tests specifically for file_like handling in async functions."""
    
    @pytest.mark.asyncio
    async def test_aquery_file_like_seekable(self):
        """Test aquery properly handles seekable BytesIO."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value={
            "choices": [{"message": {"content": "OK"}}],
            "usage": {}
        })
        
        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=None)
        ))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch("msgmodel.async_core._get_api_key") as mock_key:
            mock_key.return_value = "sk-test"
            
            with patch("msgmodel.async_core.aiohttp.ClientSession", return_value=mock_session):
                # Test with a BytesIO that's been partially read
                file_obj = io.BytesIO(b"Hello World Content")
                file_obj.read(5)  # Partially read
                
                # _prepare_file_like_data should seek to beginning
                result = await aquery("openai", "Analyze", file_like=file_obj)
                
                assert isinstance(result, LLMResponse)
    
    @pytest.mark.asyncio
    async def test_astream_file_like_default_filename(self):
        """Test astream uses 'upload.bin' as default filename."""
        chunks = [
            b'data: {"choices":[{"delta":{"content":"OK"}}]}\n',
            b'data: [DONE]\n',
        ]
        
        async def mock_content_iter():
            for chunk in chunks:
                yield chunk
        
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.content = mock_content_iter()
        
        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=None)
        ))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch("msgmodel.async_core._get_api_key") as mock_key:
            mock_key.return_value = "sk-test"
            
            with patch("msgmodel.async_core._prepare_file_like_data") as mock_prepare:
                # Return a complete file_data dict that OpenAI provider expects
                mock_prepare.return_value = {
                    "data": "ZW5jb2RlZA==",
                    "mime_type": "application/octet-stream",
                    "is_file_like": True,
                    "filename": "upload.bin"
                }
                
                with patch("msgmodel.async_core.aiohttp.ClientSession", return_value=mock_session):
                    file_obj = io.BytesIO(b"content")
                    # No filename provided, no .name attribute
                    
                    result = []
                    async for chunk in astream("openai", "Test", file_like=file_obj):
                        result.append(chunk)
                    
                    # Should have been called with 'upload.bin' default
                    mock_prepare.assert_called_once()
                    call_kwargs = mock_prepare.call_args
                    assert call_kwargs[1]["filename"] == "upload.bin"


class TestAsyncStreamingEdgeCases:
    """Tests for edge cases in async streaming."""
    
    @pytest.mark.asyncio
    async def test_astream_openai_empty_delta(self):
        """Test astream handles empty delta content."""
        chunks = [
            b'data: {"choices":[{"delta":{}}]}\n',  # No content key
            b'data: {"choices":[{"delta":{"content":""}}]}\n',  # Empty content
            b'data: {"choices":[{"delta":{"content":"Hi"}}]}\n',
            b'data: [DONE]\n',
        ]
        
        async def mock_content_iter():
            for chunk in chunks:
                yield chunk
        
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.content = mock_content_iter()
        
        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=None)
        ))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch("msgmodel.async_core._get_api_key") as mock_key:
            mock_key.return_value = "sk-test"
            
            with patch("msgmodel.async_core.aiohttp.ClientSession", return_value=mock_session):
                result = []
                async for chunk in astream("openai", "Test"):
                    result.append(chunk)
                
                # Only "Hi" should be yielded
                assert result == ["Hi"]
    
    @pytest.mark.asyncio
    async def test_astream_openai_no_choices(self):
        """Test astream handles response without choices."""
        chunks = [
            b'data: {"id": "test"}\n',  # No choices key
            b'data: {"choices":[]}\n',  # Empty choices
            b'data: {"choices":[{"delta":{"content":"OK"}}]}\n',
            b'data: [DONE]\n',
        ]
        
        async def mock_content_iter():
            for chunk in chunks:
                yield chunk
        
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.content = mock_content_iter()
        
        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=None)
        ))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch("msgmodel.async_core._get_api_key") as mock_key:
            mock_key.return_value = "sk-test"
            
            with patch("msgmodel.async_core.aiohttp.ClientSession", return_value=mock_session):
                result = []
                async for chunk in astream("openai", "Test"):
                    result.append(chunk)
                
                assert result == ["OK"]
    
    @pytest.mark.asyncio
    async def test_astream_non_data_lines_ignored(self):
        """Test astream ignores non-data lines in SSE stream."""
        chunks = [
            b': comment line\n',  # SSE comment
            b'event: message\n',  # Event type (ignored)
            b'data: {"choices":[{"delta":{"content":"Hi"}}]}\n',
            b'\n',  # Empty line
            b'data: [DONE]\n',
        ]
        
        async def mock_content_iter():
            for chunk in chunks:
                yield chunk
        
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.content = mock_content_iter()
        
        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=None)
        ))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch("msgmodel.async_core._get_api_key") as mock_key:
            mock_key.return_value = "sk-test"
            
            with patch("msgmodel.async_core.aiohttp.ClientSession", return_value=mock_session):
                result = []
                async for chunk in astream("openai", "Test"):
                    result.append(chunk)
                
                assert result == ["Hi"]
