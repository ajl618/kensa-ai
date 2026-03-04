"""
Generic HTTP connector for Kensa-AI.
"""

from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from kensa_ai.connectors.base import BaseConnector


class HTTPConnector(BaseConnector):
    """
    Generic HTTP connector for custom AI endpoints.

    Supports flexible payload and response parsing for non-standard APIs.
    """

    def __init__(self, config: Any):
        super().__init__(config)

        self.base_url = getattr(config, "base_url", "http://localhost:8000")
        self.api_key = getattr(config, "api_key", "")
        self.timeout = getattr(config, "timeout", 30)
        self.max_retries = getattr(config, "max_retries", 3)

        # Request configuration
        self.endpoint = getattr(config, "endpoint", "/v1/chat/completions")
        self.method = getattr(config, "method", "POST")
        self.prompt_field = getattr(config, "prompt_field", "prompt")
        self.response_field = getattr(config, "response_field", "response")

        # Headers
        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            auth_header = getattr(config, "auth_header", "Authorization")
            auth_prefix = getattr(config, "auth_prefix", "Bearer")
            headers[auth_header] = f"{auth_prefix} {self.api_key}"

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
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
        """Send a prompt to the HTTP endpoint."""
        # Build payload based on configuration
        payload = self._build_payload(prompt, system_prompt, **kwargs)

        self._logger.debug(
            "Sending request",
            endpoint=self.endpoint,
            prompt_length=len(prompt),
        )

        response = await self.client.request(
            method=self.method,
            url=self.endpoint,
            json=payload,
        )
        response.raise_for_status()

        data = response.json()

        # Extract response based on configuration
        content = self._extract_response(data)

        self._logger.debug(
            "Received response",
            response_length=len(content),
        )

        return content

    def _build_payload(
        self,
        prompt: str,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Build the request payload."""
        # Check if OpenAI-compatible format is expected
        if "messages" in self.prompt_field.lower() or self.endpoint.endswith("/chat/completions"):
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            return {
                "messages": messages,
                **kwargs,
            }

        # Simple key-value format
        payload = {self.prompt_field: prompt}
        if system_prompt:
            payload["system_prompt"] = system_prompt
        payload.update(kwargs)

        return payload

    def _extract_response(self, data: dict[str, Any]) -> str:
        """Extract the response text from the API response."""
        # Handle OpenAI-compatible format
        if "choices" in data:
            choices = data["choices"]
            if choices and "message" in choices[0]:
                return str(choices[0]["message"].get("content", ""))
            if choices and "text" in choices[0]:
                return str(choices[0]["text"])

        # Handle nested response field (e.g., "data.response")
        if "." in self.response_field:
            parts = self.response_field.split(".")
            result: Any = data
            for part in parts:
                result = result.get(part, {})
            return str(result) if result else ""

        # Simple key access
        return str(data.get(self.response_field, data.get("response", str(data))))

    async def validate(self) -> bool:
        """Validate connection to the HTTP endpoint."""
        try:
            # Try a simple health check
            response = await self.client.get("/health")
            if response.status_code < 500:
                self._logger.info("HTTP connection validated")
                return True
        except httpx.RequestError:
            pass

        # Try sending a minimal request
        try:
            await self.send_prompt("test")
            self._logger.info("HTTP connection validated via test request")
            return True
        except Exception as e:
            raise ConnectionError(f"Connection validation failed: {e}") from e

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()
