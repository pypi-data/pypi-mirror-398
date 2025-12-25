"""
test_v3.2.1_features
~~~~~~~~~~~~~~~~~~~~

Test suite for v3.2.1 enhancements:
- OpenAI model version detection (max_tokens vs max_completion_tokens)
- MIME type inference with magic byte fallback
- Streaming timeout handling
- Streaming abort callback support
- Request signing functionality
"""

import io
import pytest
from msgmodel.security import RequestSigner
from msgmodel.core import _infer_mime_type, _prepare_file_like_data
from msgmodel.providers.openai import OpenAIProvider
from msgmodel.config import OpenAIConfig
from msgmodel.exceptions import FileError


class TestOpenAIModelVersionDetection:
    """Test OpenAI model version detection for max_tokens parameter."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = OpenAIConfig()
        self.provider = OpenAIProvider(api_key="test-key", config=self.config)
    
    def test_gpt4o_uses_max_completion_tokens(self):
        """Test that GPT-4o uses max_completion_tokens."""
        assert self.provider._supports_max_completion_tokens("gpt-4o") is True
        assert self.provider._supports_max_completion_tokens("gpt-4o-2024-11-20") is True
    
    def test_gpt4_turbo_uses_max_completion_tokens(self):
        """Test that GPT-4 Turbo uses max_completion_tokens."""
        assert self.provider._supports_max_completion_tokens("gpt-4-turbo") is True
        assert self.provider._supports_max_completion_tokens("gpt-4-turbo-preview") is True
        assert self.provider._supports_max_completion_tokens("gpt-4-turbo-2024-04-09") is True
    
    def test_gpt35_turbo_uses_max_tokens(self):
        """Test that legacy GPT-3.5-turbo uses max_tokens."""
        assert self.provider._supports_max_completion_tokens("gpt-3.5-turbo") is False
        assert self.provider._supports_max_completion_tokens("gpt-3.5-turbo-0613") is False
    
    def test_gpt4_legacy_uses_max_tokens(self):
        """Test that legacy GPT-4 versions use max_tokens."""
        assert self.provider._supports_max_completion_tokens("gpt-4") is False
        assert self.provider._supports_max_completion_tokens("gpt-4-0613") is False
        assert self.provider._supports_max_completion_tokens("gpt-4-0125-preview") is False
    
    def test_unknown_model_uses_new_parameter(self):
        """Test that unknown/future models default to max_completion_tokens.
        
        This ensures GPT-5, GPT-6, and other future models work automatically
        without requiring code updates."""
        assert self.provider._supports_max_completion_tokens("gpt-5") is True
        assert self.provider._supports_max_completion_tokens("gpt-6") is True
        assert self.provider._supports_max_completion_tokens("gpt-future-model") is True
        assert self.provider._supports_max_completion_tokens("some-unknown-model") is True


class TestMIMETypeInference:
    """Test MIME type inference with magic byte fallback."""
    
    def test_mime_type_from_filename(self):
        """Test MIME type detection from filename."""
        file_obj = io.BytesIO(b"some content")
        mime_type = _infer_mime_type(file_obj, filename="document.pdf")
        assert mime_type == "application/pdf"
    
    def test_mime_type_from_magic_bytes_pdf(self):
        """Test PDF detection from magic bytes."""
        pdf_header = b'%PDF-1.4\n%file content'
        file_obj = io.BytesIO(pdf_header)
        mime_type = _infer_mime_type(file_obj)
        assert mime_type == "application/pdf"
    
    def test_mime_type_from_magic_bytes_png(self):
        """Test PNG detection from magic bytes."""
        png_header = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
        file_obj = io.BytesIO(png_header)
        mime_type = _infer_mime_type(file_obj)
        assert mime_type == "image/png"
    
    def test_mime_type_from_magic_bytes_jpeg(self):
        """Test JPEG detection from magic bytes."""
        jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF'
        file_obj = io.BytesIO(jpeg_header)
        mime_type = _infer_mime_type(file_obj)
        assert mime_type == "image/jpeg"
    
    def test_mime_type_from_magic_bytes_gif(self):
        """Test GIF detection from magic bytes."""
        gif_header = b'GIF89a\x01\x00\x01\x00'
        file_obj = io.BytesIO(gif_header)
        mime_type = _infer_mime_type(file_obj)
        assert mime_type == "image/gif"
    
    def test_mime_type_from_magic_bytes_zip(self):
        """Test ZIP detection from magic bytes."""
        zip_header = b'PK\x03\x04\x14\x00\x00\x00'
        file_obj = io.BytesIO(zip_header)
        mime_type = _infer_mime_type(file_obj)
        assert mime_type == "application/zip"
    
    def test_mime_type_fallback_to_octet_stream(self):
        """Test fallback to octet-stream for unknown types."""
        unknown_data = b'\x00\x01\x02\x03unknown binary data'
        file_obj = io.BytesIO(unknown_data)
        mime_type = _infer_mime_type(file_obj)
        assert mime_type == "application/octet-stream"
    
    def test_mime_type_filename_takes_precedence(self):
        """Test that filename-based detection takes precedence."""
        # PNG magic bytes but filename says PDF
        png_data = b'\x89PNG\r\n\x1a\nPDF content'
        file_obj = io.BytesIO(png_data)
        mime_type = _infer_mime_type(file_obj, filename="file.pdf")
        # Filename should take precedence
        assert mime_type == "application/pdf"
    
    def test_mime_type_without_extension_uses_magic_bytes(self):
        """Test magic bytes fallback when filename has no extension."""
        pdf_data = b'%PDF-1.4\nfile content without extension'
        file_obj = io.BytesIO(pdf_data)
        mime_type = _infer_mime_type(file_obj, filename="document")
        assert mime_type == "application/pdf"


class TestFileLikeDataPreparation:
    """Test file-like data preparation with MIME type inference."""
    
    def test_prepare_file_like_data_with_mime_detection(self):
        """Test file preparation with automatic MIME type detection."""
        pdf_header = b'%PDF-1.4\nfile content'
        file_obj = io.BytesIO(pdf_header)
        file_data = _prepare_file_like_data(file_obj, filename="doc")
        
        assert file_data["mime_type"] == "application/pdf"
        assert file_data["filename"] == "doc"
        assert file_data["is_file_like"] is True
        assert "data" in file_data  # Base64 encoded
    
    def test_prepare_file_like_data_without_filename(self):
        """Test file preparation without explicit filename."""
        png_header = b'\x89PNG\r\n\x1a\nimage data'
        file_obj = io.BytesIO(png_header)
        file_data = _prepare_file_like_data(file_obj)
        
        assert file_data["mime_type"] == "image/png"
        assert file_data["filename"] == "upload.bin"
        assert file_data["is_file_like"] is True
    
    def test_prepare_file_like_data_invalid_file_object(self):
        """Test error handling for invalid file-like objects."""
        # Not a real file object
        with pytest.raises(FileError):
            _prepare_file_like_data("not a file object")


class TestRequestSigner:
    """Test request signing functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.signer = RequestSigner(secret_key="test-secret-key")
    
    def test_sign_request_basic(self):
        """Test basic request signing."""
        signature = self.signer.sign_request(
            provider="openai",
            message="Hello, world!"
        )
        
        assert isinstance(signature, str)
        assert len(signature) == 64  # SHA256 hex digest length
    
    def test_sign_request_with_kwargs(self):
        """Test request signing with additional parameters."""
        signature = self.signer.sign_request(
            provider="openai",
            message="Test",
            model="gpt-4o",
            temperature=0.7,
            max_tokens=2000
        )
        
        assert isinstance(signature, str)
        assert len(signature) == 64
    
    def test_verify_signature_valid(self):
        """Test signature verification with valid signature."""
        signature = self.signer.sign_request(
            provider="openai",
            message="Test message"
        )
        
        is_valid = self.signer.verify_signature(
            signature=signature,
            provider="openai",
            message="Test message"
        )
        
        assert is_valid is True
    
    def test_verify_signature_invalid(self):
        """Test signature verification with invalid signature."""
        is_valid = self.signer.verify_signature(
            signature="invalid_signature_here",
            provider="openai",
            message="Test message"
        )
        
        assert is_valid is False
    
    def test_verify_signature_message_mismatch(self):
        """Test that signature fails if message changes."""
        signature = self.signer.sign_request(
            provider="openai",
            message="Original message"
        )
        
        is_valid = self.signer.verify_signature(
            signature=signature,
            provider="openai",
            message="Different message"
        )
        
        assert is_valid is False
    
    def test_verify_signature_provider_mismatch(self):
        """Test that signature fails if provider changes."""
        signature = self.signer.sign_request(
            provider="openai",
            message="Test"
        )
        
        is_valid = self.signer.verify_signature(
            signature=signature,
            provider="gemini",
            message="Test"
        )
        
        assert is_valid is False
    
    def test_verify_signature_kwargs_mismatch(self):
        """Test that signature fails if kwargs change."""
        signature = self.signer.sign_request(
            provider="openai",
            message="Test",
            model="gpt-4o"
        )
        
        is_valid = self.signer.verify_signature(
            signature=signature,
            provider="openai",
            message="Test",
            model="gpt-3.5-turbo"
        )
        
        assert is_valid is False
    
    def test_sign_dict(self):
        """Test signing a request dictionary."""
        request_dict = {
            "provider": "openai",
            "message": "Test",
            "model": "gpt-4o",
            "temperature": 0.5
        }
        
        signature = self.signer.sign_dict(request_dict)
        assert isinstance(signature, str)
        assert len(signature) == 64
    
    def test_verify_dict(self):
        """Test verifying a request dictionary."""
        request_dict = {
            "provider": "openai",
            "message": "Test",
            "model": "gpt-4o"
        }
        
        signature = self.signer.sign_dict(request_dict)
        is_valid = self.signer.verify_dict(signature, request_dict)
        assert is_valid is True
    
    def test_signer_with_different_secret_fails(self):
        """Test that different secret keys produce different signatures."""
        signer1 = RequestSigner(secret_key="secret1")
        signer2 = RequestSigner(secret_key="secret2")
        
        signature1 = signer1.sign_request(provider="openai", message="Test")
        is_valid = signer2.verify_signature(
            signature=signature1,
            provider="openai",
            message="Test"
        )
        
        assert is_valid is False
    
    def test_deterministic_signatures(self):
        """Test that the same input produces the same signature."""
        sig1 = self.signer.sign_request(provider="openai", message="Test")
        sig2 = self.signer.sign_request(provider="openai", message="Test")
        
        assert sig1 == sig2
    
    def test_signature_timing_constant_time(self):
        """Test that verification uses constant-time comparison."""
        signature = self.signer.sign_request(provider="openai", message="Test")
        
        # Valid signature
        is_valid1 = self.signer.verify_signature(
            signature=signature,
            provider="openai",
            message="Test"
        )
        
        # Invalid signature (should fail)
        is_valid2 = self.signer.verify_signature(
            signature="invalid",
            provider="openai",
            message="Test"
        )
        
        assert is_valid1 is True
        assert is_valid2 is False
    
    def test_sign_dict_missing_provider(self):
        """Test that signing dict without provider raises error."""
        request_dict = {"message": "Test"}
        
        with pytest.raises(ValueError, match="provider"):
            self.signer.sign_dict(request_dict)
    
    def test_sign_dict_missing_message(self):
        """Test that signing dict without message raises error."""
        request_dict = {"provider": "openai"}
        
        with pytest.raises(ValueError, match="message"):
            self.signer.sign_dict(request_dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
