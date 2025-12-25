"""
Tests for msgmodel.core module.

Note: These tests focus on validation and utility functions.
API calls are mocked to avoid requiring actual API keys.
"""

import os
import io
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile

from msgmodel.core import (
    _get_api_key,
    _prepare_file_like_data,
    _prepare_file_data,
    _infer_mime_type,
    _validate_max_tokens,
    query,
    stream,
    LLMResponse,
)
from msgmodel.config import Provider, OpenAIConfig
from msgmodel.exceptions import (
    ConfigurationError,
    AuthenticationError,
    FileError,
)


class TestValidateMaxTokens:
    """Tests for _validate_max_tokens function."""
    
    def test_valid_values(self):
        """Test that valid values don't raise."""
        _validate_max_tokens(1)
        _validate_max_tokens(100)
        _validate_max_tokens(1000)
        _validate_max_tokens(100000)
    
    def test_zero_raises(self):
        """Test that zero raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="at least 1"):
            _validate_max_tokens(0)
    
    def test_negative_raises(self):
        """Test that negative values raise ConfigurationError."""
        with pytest.raises(ConfigurationError, match="at least 1"):
            _validate_max_tokens(-1)
    
    def test_very_large_warns(self, caplog):
        """Test that very large values log a warning."""
        import logging
        with caplog.at_level(logging.WARNING):
            _validate_max_tokens(1000001)
        assert "very large" in caplog.text


class TestGetApiKey:
    """Tests for _get_api_key function."""
    
    def test_direct_key_takes_priority(self):
        """Test that directly provided key is used first."""
        key = _get_api_key(Provider.OPENAI, api_key="sk-direct-key")
        assert key == "sk-direct-key"
    
    def test_env_var_fallback(self):
        """Test fallback to environment variable."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-env-key"}):
            key = _get_api_key(Provider.OPENAI)
            assert key == "sk-env-key"
    
    def test_file_fallback(self):
        """Test fallback to key file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            key_file = Path(tmpdir) / "openai-api.key"
            key_file.write_text("sk-file-key")
            
            # Change to temp directory and patch the file path
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                # Clear env var
                with patch.dict(os.environ, {}, clear=True):
                    key = _get_api_key(Provider.OPENAI)
                    assert key == "sk-file-key"
            finally:
                os.chdir(original_cwd)
    
    def test_no_key_raises(self):
        """Test that missing key raises AuthenticationError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                with patch.dict(os.environ, {}, clear=True):
                    with pytest.raises(AuthenticationError, match="No API key found"):
                        _get_api_key(Provider.OPENAI)
            finally:
                os.chdir(original_cwd)
    
    def test_key_file_read_error(self):
        """Test that IOError when reading key file raises AuthenticationError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a file but make it unreadable
            key_file = Path(tmpdir) / "openai-api.key"
            key_file.write_text("key")
            key_file.chmod(0o000)  # Remove all permissions
            
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                with patch.dict(os.environ, {}, clear=True):
                    with pytest.raises(AuthenticationError, match="Failed to read"):
                        _get_api_key(Provider.OPENAI)
            finally:
                key_file.chmod(0o644)  # Restore permissions for cleanup
                os.chdir(original_cwd)


class TestInferMimeType:
    """Tests for _infer_mime_type function with magic byte detection."""
    
    def test_filename_based_detection(self):
        """Test MIME type detection from filename."""
        file_obj = io.BytesIO(b"some data")
        assert _infer_mime_type(file_obj, filename="test.png") == "image/png"
        assert _infer_mime_type(file_obj, filename="doc.pdf") == "application/pdf"
        assert _infer_mime_type(file_obj, filename="audio.mp3") == "audio/mpeg"
    
    def test_magic_bytes_png(self):
        """Test PNG magic byte detection."""
        png_header = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
        file_obj = io.BytesIO(png_header)
        assert _infer_mime_type(file_obj) == "image/png"
    
    def test_magic_bytes_jpeg(self):
        """Test JPEG magic byte detection."""
        jpeg_header = b'\xff\xd8\xff' + b'\x00' * 100
        file_obj = io.BytesIO(jpeg_header)
        assert _infer_mime_type(file_obj) == "image/jpeg"
    
    def test_magic_bytes_pdf(self):
        """Test PDF magic byte detection."""
        pdf_header = b'%PDF-1.5' + b'\x00' * 100
        file_obj = io.BytesIO(pdf_header)
        assert _infer_mime_type(file_obj) == "application/pdf"
    
    def test_magic_bytes_gif(self):
        """Test GIF magic byte detection."""
        gif_header = b'GIF89a' + b'\x00' * 100
        file_obj = io.BytesIO(gif_header)
        assert _infer_mime_type(file_obj) == "image/gif"
    
    def test_magic_bytes_zip(self):
        """Test ZIP magic byte detection."""
        zip_header = b'PK\x03\x04' + b'\x00' * 100
        file_obj = io.BytesIO(zip_header)
        assert _infer_mime_type(file_obj) == "application/zip"
    
    def test_unknown_falls_back_to_octet_stream(self):
        """Test fallback to octet-stream for unknown data."""
        file_obj = io.BytesIO(b"random unknown data")
        assert _infer_mime_type(file_obj) == "application/octet-stream"
    
    def test_position_preserved(self):
        """Test that file position is preserved after detection."""
        file_obj = io.BytesIO(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
        file_obj.seek(50)  # Move to middle
        _infer_mime_type(file_obj)
        assert file_obj.tell() == 50  # Position should be preserved


class TestPrepareFileData:
    """Tests for _prepare_file_data function (disk files)."""
    
    def test_prepare_image_file(self, tmp_path):
        """Test preparing an image file from disk."""
        test_file = tmp_path / "test.png"
        png_data = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
        test_file.write_bytes(png_data)
        
        data = _prepare_file_data(str(test_file))
        
        assert data["mime_type"] == "image/png"
        assert data["filename"] == "test.png"
        assert data["is_file_like"] is False
        assert "data" in data  # Base64 encoded
    
    def test_prepare_pdf_file(self, tmp_path):
        """Test preparing a PDF file from disk."""
        test_file = tmp_path / "document.pdf"
        test_file.write_bytes(b"%PDF-1.5 fake content")
        
        data = _prepare_file_data(str(test_file))
        
        assert data["mime_type"] == "application/pdf"
        assert data["filename"] == "document.pdf"
    
    def test_nonexistent_file_raises(self):
        """Test that non-existent file raises FileError."""
        with pytest.raises(FileError, match="Failed to read file"):
            _prepare_file_data("/nonexistent/path/file.txt")
    
    def test_unreadable_file_raises(self, tmp_path):
        """Test that unreadable file raises FileError."""
        test_file = tmp_path / "noaccess.txt"
        test_file.write_text("content")
        test_file.chmod(0o000)
        
        try:
            with pytest.raises(FileError, match="Failed to read file"):
                _prepare_file_data(str(test_file))
        finally:
            test_file.chmod(0o644)  # Restore for cleanup


class TestPrepareFileLikeData:
    """Tests for _prepare_file_like_data function."""
    
    def test_bytesio_with_image(self):
        """Test preparing BytesIO with image data."""
        file_obj = io.BytesIO(b"fake image data")
        data = _prepare_file_like_data(file_obj, filename="photo.jpg")
        
        assert data["mime_type"] == "image/jpeg"
        assert "data" in data
        assert data["filename"] == "photo.jpg"
        assert data["is_file_like"] is True
    
    def test_bytesio_with_pdf(self):
        """Test preparing BytesIO with PDF data."""
        file_obj = io.BytesIO(b"fake pdf data")
        data = _prepare_file_like_data(file_obj, filename="document.pdf")
        
        assert data["mime_type"] == "application/pdf"
        assert data["filename"] == "document.pdf"
    
    def test_bytesio_with_unknown_extension(self):
        """Test that unknown extension uses octet-stream."""
        file_obj = io.BytesIO(b"unknown data")
        data = _prepare_file_like_data(file_obj, filename="file.unknownextension")
        
        assert data["mime_type"] == "application/octet-stream"
    
    def test_bytesio_default_filename(self):
        """Test default filename when not provided."""
        file_obj = io.BytesIO(b"data")
        data = _prepare_file_like_data(file_obj)
        
        assert data["filename"] == "upload.bin"
    
    def test_bytesio_position_reset(self):
        """Test that position is reset after reading."""
        file_obj = io.BytesIO(b"test data")
        file_obj.seek(5)  # Move to position 5
        
        _prepare_file_like_data(file_obj, filename="test.txt")
        
        # Should be back at beginning
        assert file_obj.tell() == 0
    
    def test_bytesio_reuse(self):
        """Test that BytesIO can be reused multiple times."""
        file_obj = io.BytesIO(b"reusable data")
        
        data1 = _prepare_file_like_data(file_obj, filename="file1.bin")
        data2 = _prepare_file_like_data(file_obj, filename="file2.bin")
        
        # Both should have the same encoded data
        assert data1["data"] == data2["data"]
        assert file_obj.tell() == 0  # Should be at start
    
    def test_invalid_file_like_raises(self):
        """Test that invalid file-like objects raise FileError."""
        class FakeFileObject:
            def read(self):
                raise IOError("Read error")
        
        with pytest.raises(FileError, match="Failed to read from file-like object"):
            _prepare_file_like_data(FakeFileObject())
    
    def test_non_seekable_file_raises(self):
        """Test that non-seekable file-like objects raise FileError."""
        class NonSeekableFile:
            def read(self):
                return b"data"
            
            def seek(self, pos):
                raise OSError("Not seekable")
        
        with pytest.raises(FileError, match="Failed to read from file-like object"):
            _prepare_file_like_data(NonSeekableFile())



class TestLLMResponse:
    """Tests for LLMResponse dataclass."""
    
    def test_basic_response(self):
        """Test creating a basic response."""
        response = LLMResponse(
            text="Hello, world!",
            raw_response={"output": "Hello, world!"},
            model="gpt-4o",
            provider="openai",
        )
        assert response.text == "Hello, world!"
        assert response.model == "gpt-4o"
        assert response.provider == "openai"
        assert response.usage is None
    
    def test_response_with_usage(self):
        """Test creating a response with usage info."""
        response = LLMResponse(
            text="Hello!",
            raw_response={},
            model="claude-3-opus",
            provider="claude",
            usage={"input_tokens": 10, "output_tokens": 5},
        )
        assert response.usage == {"input_tokens": 10, "output_tokens": 5}
    
    def test_repr_redacts_content(self):
        """Test that __repr__ redacts sensitive content."""
        response = LLMResponse(
            text="This is secret information",
            raw_response={"secret": "data"},
            model="gpt-4o",
            provider="openai",
        )
        repr_str = repr(response)
        
        assert "secret" not in repr_str.lower()
        assert "REDACTED" in repr_str
        assert "26 chars" in repr_str  # Length of text
        assert "gpt-4o" in repr_str
    
    def test_repr_empty_text(self):
        """Test __repr__ with empty text."""
        response = LLMResponse(
            text="",
            raw_response={},
            model="gpt-4o",
            provider="openai",
        )
        repr_str = repr(response)
        
        assert "empty" in repr_str
    
    def test_str_returns_repr(self):
        """Test that __str__ returns same as __repr__."""
        response = LLMResponse(
            text="Hello",
            raw_response={},
            model="gpt-4o",
            provider="openai",
        )
        assert str(response) == repr(response)


class TestQueryFunction:
    """Tests for the query function."""
    
    def test_provider_string_conversion(self):
        """Test that provider strings are converted correctly."""
        with patch("msgmodel.core._get_api_key") as mock_key:
            mock_key.return_value = "sk-test"
            
            with patch("msgmodel.core.OpenAIProvider") as mock_provider:
                mock_instance = MagicMock()
                mock_instance.query.return_value = {"output": []}
                mock_instance.extract_text.return_value = "Hello"
                mock_provider.return_value = mock_instance
                
                # Test shorthand
                query("o", "Hello")
                mock_provider.assert_called()
    
    def test_config_override(self):
        """Test that config parameters can be overridden."""
        config = OpenAIConfig(max_tokens=500)
        
        with patch("msgmodel.core._get_api_key") as mock_key:
            mock_key.return_value = "sk-test"
            
            with patch("msgmodel.core.OpenAIProvider") as mock_provider:
                mock_instance = MagicMock()
                mock_instance.query.return_value = {"output": []}
                mock_instance.extract_text.return_value = "Hello"
                mock_provider.return_value = mock_instance
                
                # Override max_tokens
                query("openai", "Hello", config=config, max_tokens=1000)
                
                # Config should have been modified
                assert config.max_tokens == 1000
    
    def test_file_like_parameter(self):
        """Test that file_like parameter is properly handled."""
        with patch("msgmodel.core._get_api_key") as mock_key:
            mock_key.return_value = "sk-test"
            
            with patch("msgmodel.core.OpenAIProvider") as mock_provider:
                mock_instance = MagicMock()
                mock_instance.query.return_value = {"output": []}
                mock_instance.extract_text.return_value = "Hello"
                mock_provider.return_value = mock_instance
                
                file_obj = io.BytesIO(b"test data")
                query("openai", "Analyze this", file_like=file_obj)
                
                # Verify the provider.query was called with file_data
                call_args = mock_instance.query.call_args
                assert call_args is not None
                # file_data should be the third argument
                file_data = call_args[0][2]
                assert file_data is not None
                assert file_data["is_file_like"] is True
    
    def test_file_like_with_filename_hint(self, tmp_path):
        """Test that file_like with filename parameter properly passes MIME type info."""
        with patch("msgmodel.core._get_api_key") as mock_key:
            mock_key.return_value = "sk-test"
            
            with patch("msgmodel.core.OpenAIProvider") as mock_provider:
                mock_instance = MagicMock()
                mock_instance.query.return_value = {"output": []}
                mock_instance.extract_text.return_value = "Response"
                mock_instance.get_privacy_info.return_value = {}
                mock_provider.return_value = mock_instance
                
                file_obj = io.BytesIO(b"PDF content")
                result = query("openai", "Analyze", file_like=file_obj, filename="document.pdf")
                
                call_args = mock_instance.query.call_args
                file_data = call_args[0][2]
                assert file_data is not None
                assert file_data["mime_type"] == "application/pdf"
    
    def test_anthropic_provider(self):
        """Test query with Anthropic provider."""
        with patch("msgmodel.core._get_api_key") as mock_key:
            mock_key.return_value = "sk-test"
            
            with patch("msgmodel.core.AnthropicProvider") as mock_provider:
                mock_instance = MagicMock()
                mock_instance.query.return_value = {"content": [{"text": "Hello"}]}
                mock_instance.extract_text.return_value = "Hello"
                mock_instance.get_privacy_info.return_value = {"provider": "anthropic"}
                mock_provider.return_value = mock_instance
                
                result = query("anthropic", "Hi")
                assert result.text == "Hello"
                mock_provider.assert_called()
    
    def test_anthropic_shortcut_c(self):
        """Test query with 'c' shortcut for Anthropic/Claude."""
        with patch("msgmodel.core._get_api_key") as mock_key:
            mock_key.return_value = "sk-test"
            
            with patch("msgmodel.core.AnthropicProvider") as mock_provider:
                mock_instance = MagicMock()
                mock_instance.query.return_value = {"content": [{"text": "Hi"}]}
                mock_instance.extract_text.return_value = "Hi"
                mock_instance.get_privacy_info.return_value = {"provider": "anthropic"}
                mock_provider.return_value = mock_instance
                
                result = query("c", "Hello")
                assert result.text == "Hi"
                mock_provider.assert_called()
    
    def test_gemini_provider(self):
        """Test query with Gemini provider."""
        with patch("msgmodel.core._get_api_key") as mock_key:
            mock_key.return_value = "test-key"
            
            with patch("msgmodel.core.GeminiProvider") as mock_provider:
                mock_instance = MagicMock()
                mock_instance.query.return_value = {"candidates": []}
                mock_instance.extract_text.return_value = "Hello"
                mock_instance.get_privacy_info.return_value = {"provider": "gemini"}
                mock_provider.return_value = mock_instance
                
                result = query("g", "Hi")
                assert result.text == "Hello"
                mock_provider.assert_called()
    
    def test_file_like_with_disk_file_content(self, tmp_path):
        """Test query with file content loaded into BytesIO."""
        # query() uses file_like, not file_path. Load file into BytesIO.
        test_file = tmp_path / "doc.pdf"
        test_file.write_bytes(b"%PDF-1.5 content")
        
        with patch("msgmodel.core._get_api_key") as mock_key:
            mock_key.return_value = "sk-test"
            
            with patch("msgmodel.core.OpenAIProvider") as mock_provider:
                mock_instance = MagicMock()
                mock_instance.query.return_value = {"output": []}
                mock_instance.extract_text.return_value = "Analysis"
                mock_instance.get_privacy_info.return_value = {}
                mock_provider.return_value = mock_instance
                
                # Load file into BytesIO (how query() works)
                with open(test_file, "rb") as f:
                    file_like = io.BytesIO(f.read())
                
                result = query("openai", "Analyze", file_like=file_like, filename="doc.pdf")
                
                call_args = mock_instance.query.call_args
                file_data = call_args[0][2]
                assert file_data is not None
                assert file_data["is_file_like"] is True
                assert file_data["mime_type"] == "application/pdf"


class TestStreamFunction:
    """Tests for the stream function."""
    
    def test_file_like_parameter(self):
        """Test that file_like parameter is properly handled in stream."""
        with patch("msgmodel.core._get_api_key") as mock_key:
            mock_key.return_value = "sk-test"
            
            with patch("msgmodel.core.OpenAIProvider") as mock_provider:
                mock_instance = MagicMock()
                mock_instance.stream.return_value = iter(["Hello ", "world"])
                mock_provider.return_value = mock_instance
                
                file_obj = io.BytesIO(b"test data")
                result = list(stream("openai", "Analyze this", file_like=file_obj))
                
                assert result == ["Hello ", "world"]
                
                # Verify the provider.stream was called with file_data
                call_args = mock_instance.stream.call_args
                assert call_args is not None
                # file_data should be the third argument
                file_data = call_args[0][2]
                assert file_data is not None
                assert file_data["is_file_like"] is True
    
    def test_file_like_with_name_attribute(self):
        """Test that file_like with .name attribute properly detects MIME type."""
        with patch("msgmodel.core._get_api_key") as mock_key:
            mock_key.return_value = "sk-test"
            
            with patch("msgmodel.core.OpenAIProvider") as mock_provider:
                mock_instance = MagicMock()
                mock_instance.stream.return_value = iter(["Streaming..."])
                mock_provider.return_value = mock_instance
                
                file_obj = io.BytesIO(b"image data")
                file_obj.name = "photo.jpg"
                result = list(stream("openai", "Describe", file_like=file_obj))
                
                call_args = mock_instance.stream.call_args
                file_data = call_args[0][2]
                assert file_data is not None
                assert file_data["mime_type"] == "image/jpeg"
    
    def test_anthropic_provider(self):
        """Test stream with Anthropic provider."""
        with patch("msgmodel.core._get_api_key") as mock_key:
            mock_key.return_value = "sk-test"
            
            with patch("msgmodel.core.AnthropicProvider") as mock_provider:
                mock_instance = MagicMock()
                mock_instance.stream.return_value = iter(["Hi", " there"])
                mock_provider.return_value = mock_instance
                
                result = list(stream("a", "Hello"))
                assert result == ["Hi", " there"]
                mock_provider.assert_called()
    
    def test_gemini_provider(self):
        """Test stream with Gemini provider."""
        with patch("msgmodel.core._get_api_key") as mock_key:
            mock_key.return_value = "test-key"
            
            with patch("msgmodel.core.GeminiProvider") as mock_provider:
                mock_instance = MagicMock()
                mock_instance.stream.return_value = iter(["Hello", " world"])
                mock_provider.return_value = mock_instance
                
                result = list(stream("gemini", "Hi"))
                assert result == ["Hello", " world"]
                mock_provider.assert_called()
    
    def test_file_like_with_filename_parameter(self):
        """Test stream with file_like and explicit filename for MIME detection."""
        with patch("msgmodel.core._get_api_key") as mock_key:
            mock_key.return_value = "sk-test"
            
            with patch("msgmodel.core.OpenAIProvider") as mock_provider:
                mock_instance = MagicMock()
                mock_instance.stream.return_value = iter(["Analyzing..."])
                mock_provider.return_value = mock_instance
                
                # Load file content into BytesIO (the file_like way)
                file_obj = io.BytesIO(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
                result = list(stream("openai", "Describe", file_like=file_obj, filename="image.png"))
                
                call_args = mock_instance.stream.call_args
                file_data = call_args[0][2]
                assert file_data is not None
                assert file_data["is_file_like"] is True
                assert file_data["mime_type"] == "image/png"


class TestFilenameMimeTypeDetection:
    """Tests for filename-based MIME type detection in query() and stream()."""
    
    def test_query_with_filename_parameter(self):
        """Test query() passes filename parameter correctly for MIME type detection."""
        with patch("msgmodel.core._get_api_key") as mock_key:
            mock_key.return_value = "sk-test"
            
            with patch("msgmodel.core.GeminiProvider") as mock_provider:
                mock_instance = MagicMock()
                mock_instance.query.return_value = {"output": []}
                mock_instance.extract_text.return_value = "Analysis complete"
                mock_provider.return_value = mock_instance
                
                file_obj = io.BytesIO(b"PDF binary content")
                query("gemini", "Analyze this PDF", file_like=file_obj, filename="report.pdf")
                
                # Verify file_data has correct MIME type for PDF
                call_args = mock_instance.query.call_args
                file_data = call_args[0][2]
                assert file_data["mime_type"] == "application/pdf"
                assert file_data["filename"] == "report.pdf"
    
    def test_query_with_name_attribute(self):
        """Test query() uses BytesIO.name attribute for MIME type detection."""
        with patch("msgmodel.core._get_api_key") as mock_key:
            mock_key.return_value = "sk-test"
            
            with patch("msgmodel.core.OpenAIProvider") as mock_provider:
                mock_instance = MagicMock()
                mock_instance.query.return_value = {"output": []}
                mock_instance.extract_text.return_value = "Image analysis"
                mock_provider.return_value = mock_instance
                
                file_obj = io.BytesIO(b"image binary data")
                file_obj.name = "photo.png"  # Set .name attribute
                
                query("openai", "Describe this image", file_like=file_obj)
                
                # Verify file_data uses .name attribute for MIME type
                call_args = mock_instance.query.call_args
                file_data = call_args[0][2]
                assert file_data["mime_type"] == "image/png"
                assert file_data["filename"] == "photo.png"
    
    def test_query_filename_parameter_overrides_name_attribute(self):
        """Test that filename parameter takes precedence over .name attribute."""
        with patch("msgmodel.core._get_api_key") as mock_key:
            mock_key.return_value = "sk-test"
            
            with patch("msgmodel.core.GeminiProvider") as mock_provider:
                mock_instance = MagicMock()
                mock_instance.query.return_value = {"output": []}
                mock_instance.extract_text.return_value = "Done"
                mock_provider.return_value = mock_instance
                
                file_obj = io.BytesIO(b"data")
                file_obj.name = "wrong.txt"
                
                # Pass different filename parameter
                query("gemini", "Analyze", file_like=file_obj, filename="correct.pdf")
                
                # Should use the filename parameter, not .name
                call_args = mock_instance.query.call_args
                file_data = call_args[0][2]
                assert file_data["filename"] == "correct.pdf"
                assert file_data["mime_type"] == "application/pdf"
    
    def test_stream_with_filename_parameter(self):
        """Test stream() passes filename parameter correctly for MIME type detection."""
        with patch("msgmodel.core._get_api_key") as mock_key:
            mock_key.return_value = "sk-test"
            
            with patch("msgmodel.core.GeminiProvider") as mock_provider:
                mock_instance = MagicMock()
                mock_instance.stream.return_value = iter(["Analyzing... ", "Done"])
                mock_provider.return_value = mock_instance
                
                file_obj = io.BytesIO(b"image data")
                list(stream("gemini", "Describe image", file_like=file_obj, filename="photo.jpg"))
                
                # Verify file_data has correct MIME type
                call_args = mock_instance.stream.call_args
                file_data = call_args[0][2]
                assert file_data["mime_type"] == "image/jpeg"
                assert file_data["filename"] == "photo.jpg"
    
    def test_stream_with_name_attribute(self):
        """Test stream() uses BytesIO.name attribute for MIME type detection."""
        with patch("msgmodel.core._get_api_key") as mock_key:
            mock_key.return_value = "sk-test"
            
            with patch("msgmodel.core.GeminiProvider") as mock_provider:
                mock_instance = MagicMock()
                mock_instance.stream.return_value = iter(["Processing..."])
                mock_provider.return_value = mock_instance
                
                file_obj = io.BytesIO(b"pdf content")
                file_obj.name = "document.pdf"
                
                list(stream("gemini", "Summarize this", file_like=file_obj))
                
                # Verify file_data uses .name attribute
                call_args = mock_instance.stream.call_args
                file_data = call_args[0][2]
                assert file_data["mime_type"] == "application/pdf"
                assert file_data["filename"] == "document.pdf"
    
    def test_filename_parameter_enables_proper_mime_types(self):
        """Test that filename parameter enables proper MIME type detection for Gemini."""
        with patch("msgmodel.core._get_api_key") as mock_key:
            mock_key.return_value = "test-key"
            
            with patch("msgmodel.core.GeminiProvider") as mock_provider:
                mock_instance = MagicMock()
                mock_instance.stream.return_value = iter(["Result"])
                mock_provider.return_value = mock_instance
                
                # Without filename, would get application/octet-stream
                # With filename="document.pdf", should get application/pdf
                file_obj = io.BytesIO(b"PDF binary data")
                
                list(stream(
                    "gemini",
                    "Analyze this PDF",
                    file_like=file_obj,
                    filename="document.pdf"  # Enables proper MIME type detection
                ))
                
                call_args = mock_instance.stream.call_args
                file_data = call_args[0][2]
                
                # Verify Gemini won't reject with application/octet-stream
                assert file_data["mime_type"] != "application/octet-stream"
                assert file_data["mime_type"] == "application/pdf"


class TestInferMimeTypeEdgeCases:
    """Tests for MIME type inference edge cases."""
    
    def test_infer_mime_type_with_unreadable_file_like(self):
        """Test MIME type inference handles AttributeError/IOError gracefully."""
        # Test with a file-like that raises IOError on read
        class BrokenFileObj:
            def read(self, n):
                raise IOError("Cannot read")
            def seek(self, pos):
                pass
        
        # Should fall back to octet-stream, not crash
        result = _infer_mime_type(BrokenFileObj())
        assert result == "application/octet-stream"
    
    def test_infer_mime_type_with_no_read_method(self):
        """Test MIME type inference handles objects without read method."""
        class NoReadObj:
            pass
        
        # Should fall back to octet-stream due to AttributeError
        result = _infer_mime_type(NoReadObj())
        assert result == "application/octet-stream"


class TestQueryAllProviders:
    """Tests to ensure all provider branches are covered in query()."""
    
    def test_query_gemini_branch(self):
        """Test query() with Gemini provider branch."""
        with patch("msgmodel.core._get_api_key") as mock_key:
            mock_key.return_value = "test-key"
            
            with patch("msgmodel.core.GeminiProvider") as mock_provider:
                mock_instance = MagicMock()
                mock_instance.query.return_value = {"candidates": []}
                mock_instance.extract_text.return_value = "Gemini response"
                mock_instance.get_privacy_info.return_value = {"provider": "gemini"}
                mock_provider.return_value = mock_instance
                
                result = query("gemini", "Hello from Gemini test")
                
                assert result.text == "Gemini response"
                assert result.provider == "gemini"
                mock_provider.assert_called_once()
    
    def test_query_anthropic_branch(self):
        """Test query() with Anthropic provider branch."""
        with patch("msgmodel.core._get_api_key") as mock_key:
            mock_key.return_value = "sk-test"
            
            with patch("msgmodel.core.AnthropicProvider") as mock_provider:
                mock_instance = MagicMock()
                mock_instance.query.return_value = {"content": [{"text": "Claude response"}]}
                mock_instance.extract_text.return_value = "Claude response"
                mock_instance.get_privacy_info.return_value = {"provider": "anthropic"}
                mock_provider.return_value = mock_instance
                
                result = query("anthropic", "Hello from Anthropic test")
                
                assert result.text == "Claude response"
                assert result.provider == "anthropic"
                mock_provider.assert_called_once()
    
    def test_query_with_model_override(self):
        """Test query() with model parameter override."""
        with patch("msgmodel.core._get_api_key") as mock_key:
            mock_key.return_value = "sk-test"
            
            with patch("msgmodel.core.OpenAIProvider") as mock_provider:
                mock_instance = MagicMock()
                mock_instance.query.return_value = {"output": []}
                mock_instance.extract_text.return_value = "OK"
                mock_instance.get_privacy_info.return_value = {}
                mock_provider.return_value = mock_instance
                
                query("openai", "Hello", model="gpt-4")
                
                # Check that config.model was set
                call_args = mock_provider.call_args
                config = call_args[0][1]
                assert config.model == "gpt-4"
    
    def test_query_with_temperature_override(self):
        """Test query() with temperature parameter override."""
        with patch("msgmodel.core._get_api_key") as mock_key:
            mock_key.return_value = "sk-test"
            
            with patch("msgmodel.core.OpenAIProvider") as mock_provider:
                mock_instance = MagicMock()
                mock_instance.query.return_value = {"output": []}
                mock_instance.extract_text.return_value = "OK"
                mock_instance.get_privacy_info.return_value = {}
                mock_provider.return_value = mock_instance
                
                query("openai", "Hello", temperature=0.7)
                
                # Check that config.temperature was set
                call_args = mock_provider.call_args
                config = call_args[0][1]
                assert config.temperature == 0.7
    
    def test_query_with_usage_in_response(self):
        """Test query() properly extracts usage from response."""
        with patch("msgmodel.core._get_api_key") as mock_key:
            mock_key.return_value = "sk-test"
            
            with patch("msgmodel.core.OpenAIProvider") as mock_provider:
                mock_instance = MagicMock()
                mock_instance.query.return_value = {
                    "output": [],
                    "usage": {"prompt_tokens": 10, "completion_tokens": 20}
                }
                mock_instance.extract_text.return_value = "Response"
                mock_instance.get_privacy_info.return_value = {}
                mock_provider.return_value = mock_instance
                
                result = query("openai", "Hello")
                
                assert result.usage is not None
                assert result.usage["prompt_tokens"] == 10
                assert result.usage["completion_tokens"] == 20


class TestStreamAllProviders:
    """Tests to ensure all provider branches are covered in stream()."""
    
    def test_stream_gemini_branch(self):
        """Test stream() with Gemini provider branch."""
        with patch("msgmodel.core._get_api_key") as mock_key:
            mock_key.return_value = "test-key"
            
            with patch("msgmodel.core.GeminiProvider") as mock_provider:
                mock_instance = MagicMock()
                mock_instance.stream.return_value = iter(["Gemini ", "streaming"])
                mock_provider.return_value = mock_instance
                
                result = list(stream("gemini", "Stream from Gemini"))
                
                assert result == ["Gemini ", "streaming"]
                mock_provider.assert_called_once()
    
    def test_stream_anthropic_branch(self):
        """Test stream() with Anthropic provider branch."""
        with patch("msgmodel.core._get_api_key") as mock_key:
            mock_key.return_value = "sk-test"
            
            with patch("msgmodel.core.AnthropicProvider") as mock_provider:
                mock_instance = MagicMock()
                mock_instance.stream.return_value = iter(["Claude ", "streaming"])
                mock_provider.return_value = mock_instance
                
                result = list(stream("anthropic", "Stream from Claude"))
                
                assert result == ["Claude ", "streaming"]
                mock_provider.assert_called_once()
    
    def test_stream_with_model_override(self):
        """Test stream() with model parameter override."""
        with patch("msgmodel.core._get_api_key") as mock_key:
            mock_key.return_value = "sk-test"
            
            with patch("msgmodel.core.OpenAIProvider") as mock_provider:
                mock_instance = MagicMock()
                mock_instance.stream.return_value = iter(["OK"])
                mock_provider.return_value = mock_instance
                
                list(stream("openai", "Hello", model="gpt-4"))
                
                # Check that config.model was set
                call_args = mock_provider.call_args
                config = call_args[0][1]
                assert config.model == "gpt-4"
    
    def test_stream_with_temperature_override(self):
        """Test stream() with temperature parameter override."""
        with patch("msgmodel.core._get_api_key") as mock_key:
            mock_key.return_value = "sk-test"
            
            with patch("msgmodel.core.OpenAIProvider") as mock_provider:
                mock_instance = MagicMock()
                mock_instance.stream.return_value = iter(["OK"])
                mock_provider.return_value = mock_instance
                
                list(stream("openai", "Hello", temperature=0.5))
                
                # Check that config.temperature was set
                call_args = mock_provider.call_args
                config = call_args[0][1]
                assert config.temperature == 0.5
    
    def test_stream_with_file_like(self):
        """Test stream() with file_like parameter."""
        with patch("msgmodel.core._get_api_key") as mock_key:
            mock_key.return_value = "sk-test"
            
            with patch("msgmodel.core.OpenAIProvider") as mock_provider:
                mock_instance = MagicMock()
                mock_instance.stream.return_value = iter(["Analyzed"])
                mock_provider.return_value = mock_instance
                
                file_obj = io.BytesIO(b"test content")
                list(stream("openai", "Analyze", file_like=file_obj, filename="test.txt"))
                
                # Check that file_data was passed
                call_args = mock_instance.stream.call_args
                file_data = call_args[0][2]
                assert file_data is not None
                assert file_data["is_file_like"] is True
    
    def test_stream_with_max_tokens_override(self):
        """Test stream() with max_tokens parameter override."""
        with patch("msgmodel.core._get_api_key") as mock_key:
            mock_key.return_value = "sk-test"
            
            with patch("msgmodel.core.OpenAIProvider") as mock_provider:
                mock_instance = MagicMock()
                mock_instance.stream.return_value = iter(["OK"])
                mock_provider.return_value = mock_instance
                
                list(stream("openai", "Hello", max_tokens=500))
                
                # Check that config.max_tokens was set
                call_args = mock_provider.call_args
                config = call_args[0][1]
                assert config.max_tokens == 500
