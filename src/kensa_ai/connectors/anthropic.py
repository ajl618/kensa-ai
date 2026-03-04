"""
Anthropic connector for Kensa-AI.
"""

from typing import Any, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from kensa_ai.connectors.base import BaseConnector


class AnthropicConnector(BaseConnector):
    """
    Connector for Anthropic Claude API.
    """
    
    ANTHROPIC_API_URL = "https://api.anthropic.com"
    ANTHROPIC_VERSION = "2023-06-01"
    
    def __init__(self, config: Any):
        super().__init__(config)
        
        self.base_url = getattr(config, "base_url", self.ANTHROPIC_API_URL)
        self.api_key = getattr(config, "api_key", "")
        self.model = getattr(config, "model", "claude-3-sonnet-20240229")
        self.timeout = getattr(config, "timeout", 30)
        self.max_retries = getattr(config, "max_retries", 3)
        self.temperature = getattr(config, "temperature", 0.0)
        self.max_tokens = getattr(config, "max_tokens", 1024)
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": self.ANTHROPIC_VERSION,
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
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Send a prompt to the Anthropic API."""
        messages = [
            {
                "role": "user",
                "content": prompt,
            }
        ]
        
        payload = {
            "model": kwargs.get("model", self.model),
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        if self.temperature > 0:
            payload["temperature"] = kwargs.get("temperature", self.temperature)
        
        self._logger.debug(
            "Sending request",
            model=payload["model"],
            prompt_length=len(prompt),
        )
        
        response = await self.client.post(
            "/v1/messages",
            json=payload,
        )
        response.raise_for_status()
        
        data = response.json()
        
        # Extract response text from content blocks
        content_blocks = data.get("content", [])
        content = ""
        for block in content_blocks:
            if block.get("type") == "text":
                content += block.get("text", "")
        
        self._logger.debug(
            "Received response",
            response_length=len(content),
            usage=data.get("usage"),
        )
        
        return content
    
    async def validate(self) -> bool:
        """Validate connection to Anthropic API."""
        try:
            # Send a minimal request to validate credentials
            payload = {
                "model": self.model,
                "max_tokens": 10,
                "messages": [{"role": "user", "content": "Hello"}],
            }
            response = await self.client.post("/v1/messages", json=payload)
            response.raise_for_status()
            self._logger.info("Anthropic connection validated")
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
