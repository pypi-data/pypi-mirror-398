"""
msgmodel.security
~~~~~~~~~~~~~~~~~

Security utilities for msgmodel, including request signing and verification.

v3.2.1 Enhancement: Request signing for multi-tenant deployments.
"""

import hmac
import hashlib
import json
import logging
from typing import Optional, Any, Dict

logger = logging.getLogger(__name__)


class RequestSigner:
    """
    Stateless request signer for verifying request authenticity in multi-user deployments.
    
    v3.2.1 Enhancement: Provides optional request signing to prevent unauthorized API calls
    in shared environments. Signing is deterministic and does not require server state.
    
    Example:
        >>> signer = RequestSigner(secret_key="my-secret-key")
        >>> signature = signer.sign_request(
        ...     provider="openai",
        ...     message="Hello, world!",
        ...     model="gpt-4o"
        ... )
        >>> 
        >>> # Verify signature on receiving end
        >>> is_valid = signer.verify_signature(
        ...     signature=signature,
        ...     provider="openai",
        ...     message="Hello, world!",
        ...     model="gpt-4o"
        ... )
    """
    
    def __init__(self, secret_key: str):
        """
        Initialize the request signer.
        
        Args:
            secret_key: Secret key for HMAC signing (must be kept confidential)
        """
        if not secret_key or not isinstance(secret_key, str):
            raise ValueError("secret_key must be a non-empty string")
        self.secret = secret_key
    
    def _canonicalize(self, provider: str, message: str, **kwargs) -> str:
        """
        Create a canonical string representation of a request for signing.
        
        The canonical format is deterministic and order-independent for kwargs.
        
        Args:
            provider: LLM provider name
            message: User message/prompt
            **kwargs: Additional request parameters
            
        Returns:
            Canonical request string
        """
        # Sort kwargs by key for deterministic ordering
        sorted_kwargs = sorted(kwargs.items())
        canonical = f"{provider}|{message}|{json.dumps(sorted_kwargs, sort_keys=True)}"
        return canonical
    
    def sign_request(self, provider: str, message: str, **kwargs) -> str:
        """
        Generate HMAC-SHA256 signature for a request.
        
        The signature covers the provider, message, and all additional parameters.
        Signatures are deterministic—the same request always produces the same signature.
        
        Args:
            provider: LLM provider name ('openai', 'gemini', etc.)
            message: User message/prompt
            **kwargs: Additional request parameters (model, temperature, file_hash, etc.)
            
        Returns:
            Hex-encoded HMAC-SHA256 signature
        """
        canonical = self._canonicalize(provider, message, **kwargs)
        signature = hmac.new(
            self.secret.encode("utf-8"),
            canonical.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def verify_signature(
        self,
        signature: str,
        provider: str,
        message: str,
        **kwargs
    ) -> bool:
        """
        Verify a request signature.
        
        Uses constant-time comparison to prevent timing attacks.
        
        Args:
            signature: Hex-encoded signature to verify
            provider: LLM provider name
            message: User message/prompt
            **kwargs: Additional request parameters (must match original request)
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            expected_signature = self.sign_request(provider, message, **kwargs)
            # Use constant-time comparison to prevent timing attacks
            return hmac.compare_digest(signature, expected_signature)
        except Exception as e:
            logger.warning(f"Signature verification failed: {e}")
            return False
    
    def sign_dict(self, request_dict: Dict[str, Any]) -> str:
        """
        Sign a request dictionary containing 'provider', 'message', and optional other fields.
        
        Args:
            request_dict: Dictionary with at least 'provider' and 'message' keys
            
        Returns:
            Hex-encoded HMAC-SHA256 signature
            
        Raises:
            ValueError: If required keys are missing
        """
        if "provider" not in request_dict or "message" not in request_dict:
            raise ValueError("request_dict must contain 'provider' and 'message' keys")
        
        provider = request_dict["provider"]
        message = request_dict["message"]
        kwargs = {k: v for k, v in request_dict.items() if k not in ("provider", "message")}
        
        return self.sign_request(provider, message, **kwargs)
    
    def verify_dict(self, signature: str, request_dict: Dict[str, Any]) -> bool:
        """
        Verify a signature for a request dictionary.
        
        Args:
            signature: Hex-encoded signature to verify
            request_dict: Dictionary with at least 'provider' and 'message' keys
            
        Returns:
            True if signature is valid, False otherwise
        """
        if "provider" not in request_dict or "message" not in request_dict:
            return False
        
        provider = request_dict["provider"]
        message = request_dict["message"]
        kwargs = {k: v for k, v in request_dict.items() if k not in ("provider", "message")}
        
        return self.verify_signature(signature, provider, message, **kwargs)
