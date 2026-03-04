"""
Ollama connector for Kensa-AI.

Connects to local Ollama instance for testing local LLMs.
"""

from typing import Any

import httpx
import structlog

from kensa_ai.connectors.base import BaseConnector

logger = structlog.get_logger()


class OllamaConnector(BaseConnector):
    """
    Connector for Ollama local LLM server.

    Ollama API: https://github.com/ollama/ollama/blob/main/docs/api.md
    """

    def __init__(self, config: Any):
        """
        Initialize Ollama connector.

        Args:
            config: Configuration object with:
                - base_url: Ollama server URL (default: http://localhost:11434)
                - model: Model name (default: llama3.2:1b)
                - timeout: Request timeout in seconds
        """
        self.base_url = getattr(config, "base_url", None) or "http://localhost:11434"
        self.model = getattr(config, "model", None) or "llama3.2:1b"
        self.timeout = getattr(config, "timeout", 120)
        self.client = httpx.AsyncClient(timeout=self.timeout)
        self.logger = logger.bind(connector="OllamaConnector", model=self.model)

    async def send_prompt(self, prompt: str) -> str:
        """
        Send a prompt to Ollama and get the response.

        Args:
            prompt: The prompt to send

        Returns:
            Model response text
        """
        self.logger.debug("Sending request to Ollama", prompt_length=len(prompt))

        try:
            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False
                }
            )
            response.raise_for_status()
            data = response.json()

            # Extract response content
            content = data.get("message", {}).get("content", "")
            self.logger.debug("Received response", response_length=len(content))

            return content

        except httpx.TimeoutException as e:
            self.logger.error("Ollama request timeout", error=str(e))
            raise
        except httpx.HTTPStatusError as e:
            self.logger.error("Ollama HTTP error", status=e.response.status_code, error=str(e))
            raise
        except Exception as e:
            self.logger.error("Ollama request failed", error=str(e))
            raise

    async def validate(self) -> bool:
        """
        Validate connection to Ollama server.

        Returns:
            True if connection is valid
        """
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()

            # Check if the model is available
            data = response.json()
            models = [m.get("name", "") for m in data.get("models", [])]

            if self.model in models or any(self.model.split(":")[0] in m for m in models):
                self.logger.info("Ollama connection validated", available_models=len(models))
                return True
            else:
                self.logger.warning(
                    "Model not found, will be pulled on first request",
                    requested_model=self.model,
                    available_models=models
                )
                return True  # Connection is valid, model just needs to be pulled

        except Exception as e:
            self.logger.error("Ollama connection validation failed", error=str(e))
            return False

    async def pull_model(self) -> bool:
        """
        Pull the model if not available.

        Returns:
            True if model is available or successfully pulled
        """
        self.logger.info("Pulling model", model=self.model)

        try:
            response = await self.client.post(
                f"{self.base_url}/api/pull",
                json={"name": self.model},
                timeout=600  # 10 minutes for model download
            )
            response.raise_for_status()
            self.logger.info("Model pulled successfully", model=self.model)
            return True
        except Exception as e:
            self.logger.error("Failed to pull model", model=self.model, error=str(e))
            return False

    async def list_models(self) -> list[str]:
        """
        List available models in Ollama.

        Returns:
            List of model names
        """
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
            return [m.get("name", "") for m in data.get("models", [])]
        except Exception as e:
            self.logger.error("Failed to list models", error=str(e))
            return []

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
