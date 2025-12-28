"""
msgmodel.providers.anthropic
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Anthropic Claude API provider implementation.

DATA HANDLING:
- Anthropic does not use API inputs/outputs for model training by default.
- Data may be retained temporarily for safety monitoring and abuse prevention.
- See: https://www.anthropic.com/legal/privacy

FILE UPLOADS:
- All file uploads are via inline base64-encoding in prompts
- Files are limited to practical API size constraints (~20MB)
- This approach provides stateless operation
"""

import json
import base64
import logging
from typing import Optional, Dict, Any, Iterator, List, Callable

import requests

from ..config import AnthropicConfig, ANTHROPIC_URL
from ..exceptions import APIError, ProviderError, StreamingError

logger = logging.getLogger(__name__)

# MIME type constants
MIME_TYPE_JSON = "application/json"

# Anthropic API version header
ANTHROPIC_API_VERSION = "2023-06-01"


class AnthropicProvider:
    """
    Anthropic Claude API provider for making LLM requests.
    
    Handles API calls and response parsing for Claude models.
    All file uploads use inline base64-encoding for stateless operation.
    """
    
    def __init__(self, api_key: str, config: Optional[AnthropicConfig] = None):
        """
        Initialize the Anthropic provider.
        
        Args:
            api_key: Anthropic API key
            config: Optional configuration (uses defaults if not provided)
        """
        self.api_key = api_key
        self.config = config or AnthropicConfig()
    
    def _build_headers(self) -> Dict[str, str]:
        """
        Build HTTP headers for Anthropic API requests.
        
        Returns:
            Dictionary of HTTP headers
        """
        headers: Dict[str, str] = {
            "Content-Type": MIME_TYPE_JSON,
            "x-api-key": self.api_key,
            "anthropic-version": ANTHROPIC_API_VERSION,
        }
        
        return headers
    
    def _build_content(
        self,
        prompt: str,
        file_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Build the content array for the API request."""
        content: List[Dict[str, Any]] = []
        
        if file_data:
            mime_type = file_data["mime_type"]
            encoded_data = file_data.get("data", "")
            filename = file_data.get("filename", "input.bin")
            
            if mime_type.startswith("image/"):
                # Anthropic supports image content blocks
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": mime_type,
                        "data": encoded_data,
                    }
                })
            elif mime_type == "application/pdf":
                # Anthropic supports PDF documents
                content.append({
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": mime_type,
                        "data": encoded_data,
                    }
                })
            elif mime_type.startswith("text/"):
                # Decode text files and include as text content
                try:
                    decoded_text = base64.b64decode(encoded_data).decode("utf-8", errors="ignore")
                except Exception:
                    decoded_text = ""
                if decoded_text.strip():
                    content.append({
                        "type": "text",
                        "text": f"(Contents of {filename}):\n\n{decoded_text}"
                    })
            else:
                # For unsupported MIME types, include a note
                content.append({
                    "type": "text",
                    "text": (
                        f"[Note: A file named '{filename}' with MIME type '{mime_type}' "
                        f"was provided. You may not be able to read it directly, but you "
                        f"can still respond based on the description and prompt.]"
                    )
                })
        
        # Add the user prompt
        content.append({
            "type": "text",
            "text": prompt
        })
        
        return content
    
    def _build_payload(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        file_data: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """Build the API request payload for Anthropic Messages API."""
        content = self._build_content(prompt, file_data)
        
        # Build messages array
        messages: List[Dict[str, Any]] = [
            {"role": "user", "content": content}
        ]
        
        payload: Dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            "max_tokens": self.config.max_tokens,
        }
        
        # Add optional parameters
        if self.config.temperature != 1.0:
            payload["temperature"] = self.config.temperature
        
        if self.config.top_p != 1.0:
            payload["top_p"] = self.config.top_p
        
        if self.config.top_k > 0:
            payload["top_k"] = self.config.top_k
        
        # Add system instruction if provided
        if system_instruction:
            payload["system"] = system_instruction
        
        if stream:
            payload["stream"] = True
        
        return payload
    
    def query(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        file_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a non-streaming API call to Anthropic.
        
        Args:
            prompt: The user prompt
            system_instruction: Optional system instruction
            file_data: Optional file data dict
            
        Returns:
            The API response as a dictionary
            
        Raises:
            APIError: If the API call fails
        """
        payload = self._build_payload(prompt, system_instruction, file_data)
        headers = self._build_headers()
        
        try:
            response = requests.post(
                ANTHROPIC_URL,
                headers=headers,
                data=json.dumps(payload)
            )
        except requests.RequestException as e:
            raise APIError(f"Request failed: {e}")
        
        if not response.ok:
            raise APIError(
                f"Anthropic API error: {response.text}",
                status_code=response.status_code,
                response_text=response.text
            )
        
        return response.json()
    
    def stream(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        file_data: Optional[Dict[str, Any]] = None,
        timeout: float = 300,
        on_chunk: Optional[Callable[[str], bool]] = None
    ) -> Iterator[str]:
        """
        Make a streaming API call to Anthropic.
        
        Args:
            prompt: The user prompt
            system_instruction: Optional system instruction
            file_data: Optional file data dict
            timeout: Timeout in seconds for the streaming connection (default: 300s/5min)
            on_chunk: Optional callback that receives each chunk. Return False to abort stream.
            
        Yields:
            Text chunks as they arrive
            
        Raises:
            APIError: If the API call fails
            StreamingError: If streaming fails or timeout occurs
        """
        payload = self._build_payload(prompt, system_instruction, file_data, stream=True)
        headers = self._build_headers()
        
        try:
            response = requests.post(
                ANTHROPIC_URL,
                headers=headers,
                data=json.dumps(payload),
                stream=True,
                timeout=timeout
            )
        except requests.Timeout:
            raise StreamingError(f"Anthropic streaming request timed out after {timeout} seconds")
        except requests.RequestException as e:
            raise APIError(f"Request failed: {e}")
        
        if not response.ok:
            raise APIError(
                f"Anthropic API error: {response.text}",
                status_code=response.status_code,
                response_text=response.text
            )
        
        chunks_received = 0
        sample_chunks = []  # For debugging error messages
        try:
            for line in response.iter_lines():
                if line:
                    line_text = line.decode("utf-8")
                    if line_text.startswith("data: "):
                        data = line_text[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            
                            # Store sample chunks for debugging (limit to first 3)
                            if len(sample_chunks) < 3:
                                sample_chunks.append(chunk)
                            
                            # Check for error in stream
                            if "error" in chunk and isinstance(chunk.get("error"), dict):
                                error_obj = chunk["error"]
                                error_msg = error_obj.get("message", "Unknown error")
                                error_type = error_obj.get("type", "unknown")
                                
                                if error_type == "rate_limit_error" or "rate" in error_msg.lower():
                                    raise APIError(
                                        f"Anthropic rate limit exceeded during streaming: {error_msg}",
                                        status_code=429,
                                        response_text=json.dumps(chunk),
                                        provider="anthropic"
                                    )
                                else:
                                    raise APIError(
                                        f"Anthropic API error during streaming ({error_type}): {error_msg}",
                                        status_code=None,
                                        response_text=json.dumps(chunk),
                                        provider="anthropic"
                                    )
                            
                            # Extract text from Anthropic streaming response
                            # Event types: content_block_delta with delta.text
                            event_type = chunk.get("type", "")
                            
                            if event_type == "content_block_delta":
                                delta = chunk.get("delta", {})
                                if delta.get("type") == "text_delta":
                                    text = delta.get("text", "")
                                    if text:
                                        chunks_received += 1
                                        if on_chunk is not None:
                                            should_continue = on_chunk(text)
                                            if should_continue is False:
                                                return
                                        yield text
                            
                            # Handle message_stop event
                            if event_type == "message_stop":
                                break
                                
                        except json.JSONDecodeError:
                            continue
            
            # Raise error if no chunks were received
            if chunks_received == 0:
                error_msg = (
                    "No text chunks extracted from Anthropic streaming response. "
                    "Response format may not match Anthropic streaming response structure "
                    "or stream may have ended prematurely."
                )
                if sample_chunks:
                    error_msg += f"\n\nSample chunks received (for debugging):\n"
                    for i, chunk in enumerate(sample_chunks, 1):
                        error_msg += f"  Chunk {i}: {json.dumps(chunk)}\n"
                
                raise StreamingError(error_msg, chunks_received=0)
        except StreamingError:
            raise
        except APIError:
            raise
        except Exception as e:
            raise StreamingError(f"Streaming interrupted: {e}", chunks_received=chunks_received)

    def stream_with_finish_reason(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        file_data: Optional[Dict[str, Any]] = None,
        timeout: float = 300,
        on_chunk: Optional[Callable[[str], bool]] = None
    ) -> Iterator[Dict[str, Any]]:
        """
        Make a streaming API call to Anthropic, yielding chunks and finish_reason.
        
        Similar to stream(), but yields dictionaries with chunk text and metadata,
        including the final stop_reason when the stream completes.
        
        Args:
            prompt: The user prompt
            system_instruction: Optional system instruction
            file_data: Optional file data dict
            timeout: Timeout in seconds for the streaming connection (default: 300s/5min)
            on_chunk: Optional callback that receives each chunk. Return False to abort stream.
            
        Yields:
            Dict with keys:
            - "type": "delta" for text chunks, "finish" for completion
            - "text": The text content (for delta events)
            - "finish_reason": The stop reason (for finish events)
              Values: "end_turn", "max_tokens", "stop_sequence", or None
            
        Raises:
            APIError: If the API call fails
            StreamingError: If streaming fails or timeout occurs
        """
        payload = self._build_payload(prompt, system_instruction, file_data, stream=True)
        headers = self._build_headers()
        
        try:
            response = requests.post(
                ANTHROPIC_URL,
                headers=headers,
                data=json.dumps(payload),
                stream=True,
                timeout=timeout
            )
        except requests.Timeout:
            raise StreamingError(f"Anthropic streaming request timed out after {timeout} seconds")
        except requests.RequestException as e:
            raise APIError(f"Request failed: {e}")
        
        if not response.ok:
            raise APIError(
                f"Anthropic API error: {response.text}",
                status_code=response.status_code,
                response_text=response.text
            )
        
        chunks_received = 0
        sample_chunks = []
        finish_reason = None
        
        try:
            for line in response.iter_lines():
                if line:
                    line_text = line.decode("utf-8")
                    if line_text.startswith("data: "):
                        data = line_text[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            
                            if len(sample_chunks) < 3:
                                sample_chunks.append(chunk)
                            
                            # Check for error in stream
                            if "error" in chunk and isinstance(chunk.get("error"), dict):
                                error_obj = chunk["error"]
                                error_msg = error_obj.get("message", "Unknown error")
                                error_type = error_obj.get("type", "unknown")
                                
                                if error_type == "rate_limit_error" or "rate" in error_msg.lower():
                                    raise APIError(
                                        f"Anthropic rate limit exceeded during streaming: {error_msg}",
                                        status_code=429,
                                        response_text=json.dumps(chunk),
                                        provider="anthropic"
                                    )
                                else:
                                    raise APIError(
                                        f"Anthropic API error during streaming ({error_type}): {error_msg}",
                                        status_code=None,
                                        response_text=json.dumps(chunk),
                                        provider="anthropic"
                                    )
                            
                            event_type = chunk.get("type", "")
                            
                            # Capture stop_reason from message_delta event
                            if event_type == "message_delta":
                                delta = chunk.get("delta", {})
                                if "stop_reason" in delta and delta["stop_reason"]:
                                    finish_reason = delta["stop_reason"]
                            
                            # Also check message_start for stop_reason in message object
                            if event_type == "message_start":
                                message = chunk.get("message", {})
                                if "stop_reason" in message and message["stop_reason"]:
                                    finish_reason = message["stop_reason"]
                            
                            # Extract text from content_block_delta
                            if event_type == "content_block_delta":
                                delta = chunk.get("delta", {})
                                if delta.get("type") == "text_delta":
                                    text = delta.get("text", "")
                                    if text:
                                        chunks_received += 1
                                        if on_chunk is not None:
                                            should_continue = on_chunk(text)
                                            if should_continue is False:
                                                yield {"type": "finish", "finish_reason": "aborted"}
                                                return
                                        yield {"type": "delta", "text": text}
                            
                            # Handle message_stop event
                            if event_type == "message_stop":
                                break
                                
                        except json.JSONDecodeError:
                            continue
            
            # Yield finish event with final finish_reason
            yield {"type": "finish", "finish_reason": finish_reason}
            
            if chunks_received == 0:
                error_msg = (
                    "No text chunks extracted from Anthropic streaming response. "
                    "Response format may not match Anthropic streaming response structure "
                    "or stream may have ended prematurely."
                )
                if sample_chunks:
                    error_msg += f"\n\nSample chunks received (for debugging):\n"
                    for i, chunk in enumerate(sample_chunks, 1):
                        error_msg += f"  Chunk {i}: {json.dumps(chunk)}\n"
                
                raise StreamingError(error_msg, chunks_received=0)
        except StreamingError:
            raise
        except APIError:
            raise
        except Exception as e:
            raise StreamingError(f"Streaming interrupted: {e}", chunks_received=chunks_received)
    
    @staticmethod
    def extract_text(response: Dict[str, Any]) -> str:
        """
        Extract text from an Anthropic Messages API response.
        
        Args:
            response: The raw API response
            
        Returns:
            Extracted text content
        """
        # Anthropic Messages API response format:
        # {"content": [{"type": "text", "text": "..."}], ...}
        content = response.get("content", [])
        texts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                text = block.get("text", "")
                if text:
                    texts.append(text)
        
        return "".join(texts)
    
    @staticmethod
    def get_privacy_info() -> Dict[str, Any]:
        """
        Get privacy and data handling information for this provider.
        
        Returns:
            Dictionary with privacy metadata
        """
        return {
            "provider": "anthropic",
            "training_retention": False,
            "data_retention": "Temporary (for safety monitoring)",
            "enforcement_level": "default",
            "provider_policy": "Anthropic does not use API data for model training by default. Data may be retained temporarily for safety monitoring and abuse prevention.",
            "special_conditions": "Review Anthropic's data retention policies if handling highly sensitive data.",
            "reference": "https://www.anthropic.com/legal/privacy"
        }
