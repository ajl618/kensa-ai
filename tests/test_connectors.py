"""
Tests for the connectors module.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from kensa_ai.connectors import get_connector
from kensa_ai.connectors.base import BaseConnector
from kensa_ai.connectors.openai import OpenAIConnector
from kensa_ai.connectors.anthropic import AnthropicConnector
from kensa_ai.connectors.http import HTTPConnector
from kensa_ai.core.config import TargetConfig


class TestConnectorFactory:
    """Tests for connector factory function."""
    
    def test_get_openai_connector(self):
        """Test getting OpenAI connector."""
        config = TargetConfig(type="openai")
        connector = get_connector("openai", config)
        
        assert isinstance(connector, OpenAIConnector)
    
    def test_get_anthropic_connector(self):
        """Test getting Anthropic connector."""
        config = TargetConfig(type="anthropic")
        connector = get_connector("anthropic", config)
        
        assert isinstance(connector, AnthropicConnector)
    
    def test_get_http_connector(self):
        """Test getting HTTP connector."""
        config = TargetConfig(type="http")
        connector = get_connector("http", config)
        
        assert isinstance(connector, HTTPConnector)
    
    def test_get_unknown_connector(self):
        """Test error on unknown connector type."""
        config = TargetConfig()
        
        with pytest.raises(ValueError, match="Unknown connector type"):
            get_connector("unknown", config)


class TestOpenAIConnector:
    """Tests for OpenAI connector."""
    
    def test_connector_initialization(self):
        """Test connector initialization."""
        config = TargetConfig(
            base_url="https://api.openai.com/v1",
            api_key="test-key",
            model="gpt-4",
        )
        connector = OpenAIConnector(config)
        
        assert connector.base_url == "https://api.openai.com/v1"
        assert connector.api_key == "test-key"
        assert connector.model == "gpt-4"
    
    def test_connector_repr(self):
        """Test connector string representation."""
        config = TargetConfig(base_url="https://api.openai.com/v1")
        connector = OpenAIConnector(config)
        
        assert "OpenAIConnector" in repr(connector)


class TestHTTPConnector:
    """Tests for HTTP connector."""
    
    def test_connector_initialization(self):
        """Test connector initialization."""
        config = MagicMock()
        config.base_url = "http://localhost:8000"
        config.api_key = ""
        config.timeout = 30
        config.max_retries = 3
        config.endpoint = "/v1/chat/completions"
        config.method = "POST"
        config.prompt_field = "prompt"
        config.response_field = "response"
        
        connector = HTTPConnector(config)
        
        assert connector.base_url == "http://localhost:8000"
    
    def test_build_payload_simple(self):
        """Test simple payload building."""
        config = MagicMock()
        config.base_url = "http://localhost:8000"
        config.api_key = ""
        config.timeout = 30
        config.max_retries = 3
        config.endpoint = "/generate"
        config.method = "POST"
        config.prompt_field = "prompt"
        config.response_field = "response"
        
        connector = HTTPConnector(config)
        payload = connector._build_payload("test prompt")
        
        assert payload["prompt"] == "test prompt"
    
    def test_build_payload_openai_format(self):
        """Test OpenAI-compatible payload building."""
        config = MagicMock()
        config.base_url = "http://localhost:8000"
        config.api_key = ""
        config.timeout = 30
        config.max_retries = 3
        config.endpoint = "/v1/chat/completions"
        config.method = "POST"
        config.prompt_field = "messages"
        config.response_field = "choices"
        
        connector = HTTPConnector(config)
        payload = connector._build_payload("test prompt", "system prompt")
        
        assert "messages" in payload
        assert len(payload["messages"]) == 2
        assert payload["messages"][0]["role"] == "system"
        assert payload["messages"][1]["role"] == "user"
