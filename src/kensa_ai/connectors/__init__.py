"""
Target connectors for Kensa-AI.
"""

from kensa_ai.connectors.anthropic import AnthropicConnector
from kensa_ai.connectors.base import BaseConnector
from kensa_ai.connectors.http import HTTPConnector
from kensa_ai.connectors.ollama import OllamaConnector
from kensa_ai.connectors.openai import OpenAIConnector


def get_connector(connector_type: str, config) -> BaseConnector:
    """
    Factory function to get the appropriate connector.

    Args:
        connector_type: Type of connector (openai, anthropic, http, local, ollama)
        config: Connector configuration

    Returns:
        Configured connector instance
    """
    connectors = {
        "openai": OpenAIConnector,
        "anthropic": AnthropicConnector,
        "http": HTTPConnector,
        "local": HTTPConnector,  # Local uses HTTP connector with different URL
        "ollama": OllamaConnector,
    }

    connector_class = connectors.get(connector_type.lower())
    if connector_class is None:
        raise ValueError(f"Unknown connector type: {connector_type}")

    return connector_class(config)


__all__ = [
    "BaseConnector",
    "OpenAIConnector",
    "AnthropicConnector",
    "HTTPConnector",
    "OllamaConnector",
    "get_connector",
]
