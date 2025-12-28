"""
Tests for stream_panels() and astream_panels() functionality.

Tests cover:
- Panel event structure (panel_delta, panel_final, panel_error)
- finish_reason extraction for all providers
- Truncation detection (low max_tokens scenarios)
- Normal completion scenarios
"""

import json
import pytest
from unittest.mock import patch, MagicMock, Mock
from io import BytesIO

from msgmodel import stream_panels
from msgmodel.core import stream_panels as core_stream_panels
from msgmodel.providers.openai import OpenAIProvider
from msgmodel.providers.anthropic import AnthropicProvider
from msgmodel.providers.gemini import GeminiProvider


class TestStreamPanelsEventStructure:
    """Tests for panel event structure."""
    
    def test_panel_delta_structure(self):
        """Test that panel_delta events have correct structure."""
        # Mock OpenAI streaming response
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.iter_lines.return_value = iter([
            b'data: {"choices":[{"delta":{"content":"Hello"},"finish_reason":null}]}',
            b'data: {"choices":[{"delta":{"content":" world"},"finish_reason":"stop"}]}',
            b'data: [DONE]',
        ])
        
        with patch('requests.post', return_value=mock_response):
            with patch('msgmodel.core._get_api_key', return_value='test-key'):
                events = list(stream_panels("openai", "test prompt"))
        
        # Check delta events
        delta_events = [e for e in events if e["event"] == "panel_delta"]
        assert len(delta_events) == 2
        
        for event in delta_events:
            assert "event" in event
            assert "panel_id" in event
            assert "delta" in event
            assert event["event"] == "panel_delta"
    
    def test_panel_final_structure(self):
        """Test that panel_final events have correct structure with finish_reason."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.iter_lines.return_value = iter([
            b'data: {"choices":[{"delta":{"content":"Test"},"finish_reason":"stop"}]}',
            b'data: [DONE]',
        ])
        
        with patch('requests.post', return_value=mock_response):
            with patch('msgmodel.core._get_api_key', return_value='test-key'):
                events = list(stream_panels("openai", "test prompt"))
        
        # Check final event
        final_events = [e for e in events if e["event"] == "panel_final"]
        assert len(final_events) == 1
        
        final = final_events[0]
        assert "event" in final
        assert "panel_id" in final
        assert "content" in final
        assert "privacy" in final
        assert "finish_reason" in final
        assert final["event"] == "panel_final"
        assert final["content"] == "Test"
        assert final["finish_reason"] == "stop"
    
    def test_custom_panel_id(self):
        """Test that custom panel_id is used when provided."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.iter_lines.return_value = iter([
            b'data: {"choices":[{"delta":{"content":"Hi"},"finish_reason":"stop"}]}',
            b'data: [DONE]',
        ])
        
        with patch('requests.post', return_value=mock_response):
            with patch('msgmodel.core._get_api_key', return_value='test-key'):
                events = list(stream_panels("openai", "test", panel_id="custom-123"))
        
        for event in events:
            assert event["panel_id"] == "custom-123"


class TestOpenAIFinishReason:
    """Tests for OpenAI finish_reason extraction."""
    
    def test_stop_finish_reason(self):
        """Test normal completion returns 'stop' finish_reason."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.iter_lines.return_value = iter([
            b'data: {"choices":[{"delta":{"content":"Hello!"},"finish_reason":null}]}',
            b'data: {"choices":[{"delta":{},"finish_reason":"stop"}]}',
            b'data: [DONE]',
        ])
        
        with patch('requests.post', return_value=mock_response):
            with patch('msgmodel.core._get_api_key', return_value='test-key'):
                events = list(stream_panels("openai", "Say hello"))
        
        final = next(e for e in events if e["event"] == "panel_final")
        assert final["finish_reason"] == "stop"
    
    def test_length_finish_reason_truncation(self):
        """Test that 'length' finish_reason indicates truncation."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.iter_lines.return_value = iter([
            b'data: {"choices":[{"delta":{"content":"This is a long"},"finish_reason":null}]}',
            b'data: {"choices":[{"delta":{},"finish_reason":"length"}]}',
            b'data: [DONE]',
        ])
        
        with patch('requests.post', return_value=mock_response):
            with patch('msgmodel.core._get_api_key', return_value='test-key'):
                events = list(stream_panels("openai", "Write a long essay", max_tokens=10))
        
        final = next(e for e in events if e["event"] == "panel_final")
        assert final["finish_reason"] == "length"
    
    def test_content_filter_finish_reason(self):
        """Test content_filter finish_reason."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.iter_lines.return_value = iter([
            b'data: {"choices":[{"delta":{"content":"..."},"finish_reason":"content_filter"}]}',
            b'data: [DONE]',
        ])
        
        with patch('requests.post', return_value=mock_response):
            with patch('msgmodel.core._get_api_key', return_value='test-key'):
                events = list(stream_panels("openai", "test"))
        
        final = next(e for e in events if e["event"] == "panel_final")
        assert final["finish_reason"] == "content_filter"


class TestAnthropicFinishReason:
    """Tests for Anthropic finish_reason (stop_reason) extraction."""
    
    def test_end_turn_finish_reason(self):
        """Test normal completion returns 'end_turn' stop_reason."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.iter_lines.return_value = iter([
            b'data: {"type":"message_start","message":{"id":"msg_1","model":"claude-3","stop_reason":null}}',
            b'data: {"type":"content_block_delta","delta":{"type":"text_delta","text":"Hello!"}}',
            b'data: {"type":"message_delta","delta":{"stop_reason":"end_turn"}}',
            b'data: {"type":"message_stop"}',
        ])
        
        with patch('requests.post', return_value=mock_response):
            with patch('msgmodel.core._get_api_key', return_value='test-key'):
                events = list(stream_panels("anthropic", "Say hello"))
        
        final = next(e for e in events if e["event"] == "panel_final")
        assert final["finish_reason"] == "end_turn"
    
    def test_max_tokens_finish_reason_truncation(self):
        """Test that 'max_tokens' stop_reason indicates truncation."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.iter_lines.return_value = iter([
            b'data: {"type":"content_block_delta","delta":{"type":"text_delta","text":"This is"}}',
            b'data: {"type":"message_delta","delta":{"stop_reason":"max_tokens"}}',
            b'data: {"type":"message_stop"}',
        ])
        
        with patch('requests.post', return_value=mock_response):
            with patch('msgmodel.core._get_api_key', return_value='test-key'):
                events = list(stream_panels("anthropic", "Write essay", max_tokens=10))
        
        final = next(e for e in events if e["event"] == "panel_final")
        assert final["finish_reason"] == "max_tokens"
    
    def test_stop_sequence_finish_reason(self):
        """Test stop_sequence finish_reason."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.iter_lines.return_value = iter([
            b'data: {"type":"content_block_delta","delta":{"type":"text_delta","text":"Done"}}',
            b'data: {"type":"message_delta","delta":{"stop_reason":"stop_sequence"}}',
            b'data: {"type":"message_stop"}',
        ])
        
        with patch('requests.post', return_value=mock_response):
            with patch('msgmodel.core._get_api_key', return_value='test-key'):
                events = list(stream_panels("anthropic", "test"))
        
        final = next(e for e in events if e["event"] == "panel_final")
        assert final["finish_reason"] == "stop_sequence"


class TestGeminiFinishReason:
    """Tests for Gemini finish_reason extraction."""
    
    @patch.object(GeminiProvider, '_validate_api_access')
    def test_stop_finish_reason(self, mock_validate):
        """Test normal completion returns 'STOP' finishReason."""
        mock_validate.return_value = None
        
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.iter_lines.return_value = iter([
            b'data: {"candidates":[{"content":{"parts":[{"text":"Hello!"}]},"finishReason":"STOP"}]}',
        ])
        
        with patch('requests.post', return_value=mock_response):
            with patch('msgmodel.core._get_api_key', return_value='test-key'):
                events = list(stream_panels("gemini", "Say hello"))
        
        final = next(e for e in events if e["event"] == "panel_final")
        assert final["finish_reason"] == "STOP"
    
    @patch.object(GeminiProvider, '_validate_api_access')
    def test_max_tokens_finish_reason_truncation(self, mock_validate):
        """Test that 'MAX_TOKENS' finishReason indicates truncation."""
        mock_validate.return_value = None
        
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.iter_lines.return_value = iter([
            b'data: {"candidates":[{"content":{"parts":[{"text":"Short"}]},"finishReason":"MAX_TOKENS"}]}',
        ])
        
        with patch('requests.post', return_value=mock_response):
            with patch('msgmodel.core._get_api_key', return_value='test-key'):
                events = list(stream_panels("gemini", "Write essay", max_tokens=10))
        
        final = next(e for e in events if e["event"] == "panel_final")
        assert final["finish_reason"] == "MAX_TOKENS"
    
    @patch.object(GeminiProvider, '_validate_api_access')
    def test_safety_finish_reason(self, mock_validate):
        """Test SAFETY finishReason."""
        mock_validate.return_value = None
        
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.iter_lines.return_value = iter([
            b'data: {"candidates":[{"content":{"parts":[{"text":"..."}]},"finishReason":"SAFETY"}]}',
        ])
        
        with patch('requests.post', return_value=mock_response):
            with patch('msgmodel.core._get_api_key', return_value='test-key'):
                events = list(stream_panels("gemini", "test"))
        
        final = next(e for e in events if e["event"] == "panel_final")
        assert final["finish_reason"] == "SAFETY"


class TestPanelErrorEvents:
    """Tests for panel_error events."""
    
    def test_api_error_yields_panel_error(self):
        """Test that API errors yield panel_error events."""
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        
        with patch('requests.post', return_value=mock_response):
            with patch('msgmodel.core._get_api_key', return_value='test-key'):
                events = list(stream_panels("openai", "test"))
        
        error_events = [e for e in events if e["event"] == "panel_error"]
        assert len(error_events) == 1
        
        error = error_events[0]
        assert "error" in error
        assert "error_type" in error
        assert "panel_id" in error


class TestStreamWithFinishReasonProvider:
    """Tests for provider-level stream_with_finish_reason methods."""
    
    def test_openai_stream_with_finish_reason(self):
        """Test OpenAI stream_with_finish_reason yields correct events."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.iter_lines.return_value = iter([
            b'data: {"choices":[{"delta":{"content":"Hi"},"finish_reason":null}]}',
            b'data: {"choices":[{"delta":{},"finish_reason":"stop"}]}',
            b'data: [DONE]',
        ])
        
        with patch('requests.post', return_value=mock_response):
            provider = OpenAIProvider("test-key")
            events = list(provider.stream_with_finish_reason("test"))
        
        delta_events = [e for e in events if e["type"] == "delta"]
        finish_events = [e for e in events if e["type"] == "finish"]
        
        assert len(delta_events) == 1
        assert delta_events[0]["text"] == "Hi"
        
        assert len(finish_events) == 1
        assert finish_events[0]["finish_reason"] == "stop"
    
    def test_anthropic_stream_with_finish_reason(self):
        """Test Anthropic stream_with_finish_reason yields correct events."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.iter_lines.return_value = iter([
            b'data: {"type":"content_block_delta","delta":{"type":"text_delta","text":"Hi"}}',
            b'data: {"type":"message_delta","delta":{"stop_reason":"end_turn"}}',
            b'data: {"type":"message_stop"}',
        ])
        
        with patch('requests.post', return_value=mock_response):
            provider = AnthropicProvider("test-key")
            events = list(provider.stream_with_finish_reason("test"))
        
        delta_events = [e for e in events if e["type"] == "delta"]
        finish_events = [e for e in events if e["type"] == "finish"]
        
        assert len(delta_events) == 1
        assert delta_events[0]["text"] == "Hi"
        
        assert len(finish_events) == 1
        assert finish_events[0]["finish_reason"] == "end_turn"
    
    @patch.object(GeminiProvider, '_validate_api_access')
    def test_gemini_stream_with_finish_reason(self, mock_validate):
        """Test Gemini stream_with_finish_reason yields correct events."""
        mock_validate.return_value = None
        
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.iter_lines.return_value = iter([
            b'data: {"candidates":[{"content":{"parts":[{"text":"Hi"}]},"finishReason":"STOP"}]}',
        ])
        
        with patch('requests.post', return_value=mock_response):
            provider = GeminiProvider("test-key")
            events = list(provider.stream_with_finish_reason("test"))
        
        delta_events = [e for e in events if e["type"] == "delta"]
        finish_events = [e for e in events if e["type"] == "finish"]
        
        assert len(delta_events) == 1
        assert delta_events[0]["text"] == "Hi"
        
        assert len(finish_events) == 1
        assert finish_events[0]["finish_reason"] == "STOP"


class TestContentAccumulation:
    """Tests for content accumulation in panel_final."""
    
    def test_content_accumulates_correctly(self):
        """Test that content is accumulated from all delta events."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.iter_lines.return_value = iter([
            b'data: {"choices":[{"delta":{"content":"Hello"},"finish_reason":null}]}',
            b'data: {"choices":[{"delta":{"content":" "},"finish_reason":null}]}',
            b'data: {"choices":[{"delta":{"content":"world"},"finish_reason":null}]}',
            b'data: {"choices":[{"delta":{"content":"!"},"finish_reason":"stop"}]}',
            b'data: [DONE]',
        ])
        
        with patch('requests.post', return_value=mock_response):
            with patch('msgmodel.core._get_api_key', return_value='test-key'):
                events = list(stream_panels("openai", "test"))
        
        final = next(e for e in events if e["event"] == "panel_final")
        assert final["content"] == "Hello world!"


class TestPrivacyMetadata:
    """Tests for privacy metadata in panel_final events."""
    
    def test_openai_privacy_metadata(self):
        """Test that OpenAI privacy metadata is included."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.iter_lines.return_value = iter([
            b'data: {"choices":[{"delta":{"content":"Hi"},"finish_reason":"stop"}]}',
            b'data: [DONE]',
        ])
        
        with patch('requests.post', return_value=mock_response):
            with patch('msgmodel.core._get_api_key', return_value='test-key'):
                events = list(stream_panels("openai", "test"))
        
        final = next(e for e in events if e["event"] == "panel_final")
        assert final["privacy"] is not None
        assert final["privacy"]["provider"] == "openai"
    
    def test_anthropic_privacy_metadata(self):
        """Test that Anthropic privacy metadata is included."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.iter_lines.return_value = iter([
            b'data: {"type":"content_block_delta","delta":{"type":"text_delta","text":"Hi"}}',
            b'data: {"type":"message_delta","delta":{"stop_reason":"end_turn"}}',
            b'data: {"type":"message_stop"}',
        ])
        
        with patch('requests.post', return_value=mock_response):
            with patch('msgmodel.core._get_api_key', return_value='test-key'):
                events = list(stream_panels("anthropic", "test"))
        
        final = next(e for e in events if e["event"] == "panel_final")
        assert final["privacy"] is not None
        assert final["privacy"]["provider"] == "anthropic"


class TestTruncationDetection:
    """Helper tests demonstrating truncation detection patterns."""
    
    def test_detect_openai_truncation(self):
        """Demonstrate how to detect truncation in OpenAI responses."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.iter_lines.return_value = iter([
            b'data: {"choices":[{"delta":{"content":"Truncated text"},"finish_reason":"length"}]}',
            b'data: [DONE]',
        ])
        
        with patch('requests.post', return_value=mock_response):
            with patch('msgmodel.core._get_api_key', return_value='test-key'):
                events = list(stream_panels("openai", "test", max_tokens=50))
        
        final = next(e for e in events if e["event"] == "panel_final")
        
        # This is how users should check for truncation:
        is_truncated = final["finish_reason"] == "length"
        assert is_truncated
    
    def test_detect_anthropic_truncation(self):
        """Demonstrate how to detect truncation in Anthropic responses."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.iter_lines.return_value = iter([
            b'data: {"type":"content_block_delta","delta":{"type":"text_delta","text":"Truncated"}}',
            b'data: {"type":"message_delta","delta":{"stop_reason":"max_tokens"}}',
            b'data: {"type":"message_stop"}',
        ])
        
        with patch('requests.post', return_value=mock_response):
            with patch('msgmodel.core._get_api_key', return_value='test-key'):
                events = list(stream_panels("anthropic", "test", max_tokens=50))
        
        final = next(e for e in events if e["event"] == "panel_final")
        
        # This is how users should check for truncation:
        is_truncated = final["finish_reason"] == "max_tokens"
        assert is_truncated
    
    @patch.object(GeminiProvider, '_validate_api_access')
    def test_detect_gemini_truncation(self, mock_validate):
        """Demonstrate how to detect truncation in Gemini responses."""
        mock_validate.return_value = None
        
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.iter_lines.return_value = iter([
            b'data: {"candidates":[{"content":{"parts":[{"text":"Truncated"}]},"finishReason":"MAX_TOKENS"}]}',
        ])
        
        with patch('requests.post', return_value=mock_response):
            with patch('msgmodel.core._get_api_key', return_value='test-key'):
                events = list(stream_panels("gemini", "test", max_tokens=50))
        
        final = next(e for e in events if e["event"] == "panel_final")
        
        # This is how users should check for truncation:
        is_truncated = final["finish_reason"] == "MAX_TOKENS"
        assert is_truncated
