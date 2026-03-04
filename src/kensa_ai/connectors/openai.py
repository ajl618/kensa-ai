"""
OpenAI-compatible connector for Kensa-AI.
"""

from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from kensa_ai.connectors.base import BaseConnector


class OpenAIConnector(BaseConnector):
    """
    Connector for OpenAI and OpenAI-compatible APIs.

    Supports:
    - OpenAI API
    - Azure OpenAI
    - Local LLMs with OpenAI-compatible endpoints (Ollama, vLLM, etc.)
    """

    def __init__(self, config: Any):
        super().__init__(config)

        self.base_url = getattr(config, "base_url", "https://api.openai.com/v1")
        self.api_key = getattr(config, "api_key", "")
        self.model = getattr(config, "model", "gpt-4")
        self.timeout = getattr(config, "timeout", 30)
        self.max_retries = getattr(config, "max_retries", 3)
        self.temperature = getattr(config, "temperature", 0.0)
        self.max_tokens = getattr(config, "max_tokens", 1024)

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=self.timeout,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def send_prompt(
        self,
        prompt: str,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Send a prompt to the OpenAI-compatible API."""
        messages = []

        if system_prompt:
            messages.append(
                {
                    "role": "system",
                    "content": system_prompt,
                }
            )

        messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        payload = {
            "model": kwargs.get("model", self.model),
            "messages": messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
        }

        self._logger.debug(
            "Sending request",
            model=payload["model"],
            prompt_length=len(prompt),
        )

        response = await self.client.post(
            "/chat/completions",
            json=payload,
        )
        response.raise_for_status()

        data = response.json()

        # Extract response text
        content: str = str(data["choices"][0]["message"]["content"])

        self._logger.debug(
            "Received response",
            response_length=len(content),
            usage=data.get("usage"),
        )

        return content

    async def validate(self) -> bool:
        """Validate connection to OpenAI API."""
        try:
            # Send a minimal request to validate credentials
            response = await self.client.get("/models")
            response.raise_for_status()
            self._logger.info("OpenAI connection validated")
            return True
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise ConnectionError("Invalid API key") from e
            raise ConnectionError(f"API validation failed: {e}") from e
        except httpx.RequestError as e:
            raise ConnectionError(f"Connection failed: {e}") from e

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()
