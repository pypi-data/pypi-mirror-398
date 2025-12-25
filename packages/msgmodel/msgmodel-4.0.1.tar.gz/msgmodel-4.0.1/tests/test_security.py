"""
Tests for msgmodel.security module.
"""

import pytest
from msgmodel.security import RequestSigner


class TestRequestSignerInit:
    """Tests for RequestSigner initialization."""
    
    def test_init_with_valid_key(self):
        """Test initialization with valid secret key."""
        signer = RequestSigner("my-secret-key")
        assert signer.secret == "my-secret-key"
    
    def test_init_with_empty_key_raises(self):
        """Test that empty key raises ValueError."""
        with pytest.raises(ValueError, match="non-empty string"):
            RequestSigner("")
    
    def test_init_with_none_raises(self):
        """Test that None key raises ValueError."""
        with pytest.raises(ValueError, match="non-empty string"):
            RequestSigner(None)
    
    def test_init_with_non_string_raises(self):
        """Test that non-string key raises ValueError."""
        with pytest.raises(ValueError, match="non-empty string"):
            RequestSigner(12345)


class TestRequestSignerSignature:
    """Tests for request signing."""
    
    def test_sign_request_basic(self):
        """Test basic request signing."""
        signer = RequestSigner("secret")
        signature = signer.sign_request("openai", "Hello world")
        
        assert isinstance(signature, str)
        assert len(signature) == 64  # SHA256 hex = 64 chars
    
    def test_sign_request_deterministic(self):
        """Test that same inputs produce same signature."""
        signer = RequestSigner("secret")
        sig1 = signer.sign_request("openai", "Hello", model="gpt-4o")
        sig2 = signer.sign_request("openai", "Hello", model="gpt-4o")
        
        assert sig1 == sig2
    
    def test_sign_request_different_providers(self):
        """Test that different providers produce different signatures."""
        signer = RequestSigner("secret")
        sig1 = signer.sign_request("openai", "Hello")
        sig2 = signer.sign_request("gemini", "Hello")
        
        assert sig1 != sig2
    
    def test_sign_request_different_messages(self):
        """Test that different messages produce different signatures."""
        signer = RequestSigner("secret")
        sig1 = signer.sign_request("openai", "Hello")
        sig2 = signer.sign_request("openai", "Goodbye")
        
        assert sig1 != sig2
    
    def test_sign_request_kwargs_order_independent(self):
        """Test that kwargs order doesn't affect signature."""
        signer = RequestSigner("secret")
        sig1 = signer.sign_request("openai", "Hello", model="gpt-4o", temp=0.5)
        sig2 = signer.sign_request("openai", "Hello", temp=0.5, model="gpt-4o")
        
        assert sig1 == sig2


class TestRequestSignerVerification:
    """Tests for signature verification."""
    
    def test_verify_valid_signature(self):
        """Test verifying a valid signature."""
        signer = RequestSigner("secret")
        signature = signer.sign_request("openai", "Hello")
        
        assert signer.verify_signature(signature, "openai", "Hello") is True
    
    def test_verify_invalid_signature(self):
        """Test verifying an invalid signature."""
        signer = RequestSigner("secret")
        
        assert signer.verify_signature("invalid", "openai", "Hello") is False
    
    def test_verify_wrong_provider(self):
        """Test verification fails with wrong provider."""
        signer = RequestSigner("secret")
        signature = signer.sign_request("openai", "Hello")
        
        assert signer.verify_signature(signature, "gemini", "Hello") is False
    
    def test_verify_wrong_message(self):
        """Test verification fails with wrong message."""
        signer = RequestSigner("secret")
        signature = signer.sign_request("openai", "Hello")
        
        assert signer.verify_signature(signature, "openai", "Different") is False
    
    def test_verify_catches_exceptions(self):
        """Test that verification catches exceptions gracefully."""
        signer = RequestSigner("secret")
        # This shouldn't raise - should return False
        result = signer.verify_signature(None, "openai", "Hello")
        assert result is False


class TestRequestSignerDict:
    """Tests for dict-based signing."""
    
    def test_sign_dict_basic(self):
        """Test signing a request dictionary."""
        signer = RequestSigner("secret")
        request = {"provider": "openai", "message": "Hello", "model": "gpt-4o"}
        signature = signer.sign_dict(request)
        
        assert isinstance(signature, str)
        assert len(signature) == 64
    
    def test_sign_dict_missing_provider_raises(self):
        """Test that missing provider raises ValueError."""
        signer = RequestSigner("secret")
        
        with pytest.raises(ValueError, match="provider"):
            signer.sign_dict({"message": "Hello"})
    
    def test_sign_dict_missing_message_raises(self):
        """Test that missing message raises ValueError."""
        signer = RequestSigner("secret")
        
        with pytest.raises(ValueError, match="message"):
            signer.sign_dict({"provider": "openai"})
    
    def test_verify_dict_valid(self):
        """Test verifying a dict with valid signature."""
        signer = RequestSigner("secret")
        request = {"provider": "openai", "message": "Hello"}
        signature = signer.sign_dict(request)
        
        assert signer.verify_dict(signature, request) is True
    
    def test_verify_dict_invalid(self):
        """Test verifying a dict with invalid signature."""
        signer = RequestSigner("secret")
        request = {"provider": "openai", "message": "Hello"}
        
        assert signer.verify_dict("bad-signature", request) is False
    
    def test_verify_dict_missing_keys(self):
        """Test verify_dict with missing keys returns False."""
        signer = RequestSigner("secret")
        
        assert signer.verify_dict("sig", {"provider": "openai"}) is False
        assert signer.verify_dict("sig", {"message": "Hello"}) is False


class TestRequestSignerConsistency:
    """Tests for sign_request and sign_dict consistency."""
    
    def test_sign_request_and_sign_dict_match(self):
        """Test that sign_request and sign_dict produce same signature."""
        signer = RequestSigner("secret")
        
        # Same request via both methods
        sig1 = signer.sign_request("openai", "Hello", model="gpt-4o", temp=0.5)
        sig2 = signer.sign_dict({
            "provider": "openai",
            "message": "Hello",
            "model": "gpt-4o",
            "temp": 0.5
        })
        
        assert sig1 == sig2
