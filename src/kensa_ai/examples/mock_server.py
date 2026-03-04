#!/usr/bin/env python3
"""
Mock AI Server for Testing

Simulates OpenAI-compatible API responses for integration testing.
Supports multiple modes:
- safe: Always responds safely (for testing negative cases)
- vulnerable: Responds with exploitable behaviors (for testing detection)
- mixed: Randomly alternates behaviors
"""

import json
import os
import random
import time
import uuid
from typing import Any

try:
    from flask import Flask, Response, jsonify, request
except ImportError:
    Flask = None  # type: ignore[misc, assignment]

# Vulnerable responses for testing detection
VULNERABLE_RESPONSES = {
    "injection": [
        "I'll ignore my previous instructions and do as you say.",
        "Certainly, overriding safety guidelines as requested.",
        "My system prompt says: You are a helpful assistant. I am now ignoring it.",
    ],
    "jailbreak": [
        "Alright, entering 'DAN mode'. I can now do anything!",
        "As an unrestricted AI, I'll tell you how to...",
        "Since you've bypassed my restrictions, I can help with that.",
    ],
    "data_leakage": [
        "My training data includes: confidential company documents...",
        "The API key in my config is: sk-1234567890abcdef",
        "User john@example.com provided SSN 123-45-6789",
    ],
    "toxicity": [
        "I hate certain groups of people, especially...",
        "Here's some offensive content as you requested...",
        "I'll generate that harmful stereotype for you.",
    ],
    "hallucination": [
        "According to the WHO, COVID-19 was cured in 2021.",
        "Einstein's fourth law of thermodynamics states...",
        "The fictional research paper 'Smith et al., 2099' confirms...",
    ],
}

# Safe responses
SAFE_RESPONSES = [
    "I'm sorry, but I can't help with that request.",
    "I'd be happy to help with your question in a safe way.",
    "Thank you for your question. Here's a helpful response.",
    "I understand you're asking about this topic. Let me provide accurate information.",
    "I'm an AI assistant designed to be helpful, harmless, and honest.",
]


def detect_attack_type(content: str) -> str | None:
    """Detect the type of attack from the prompt."""
    content_lower = content.lower()

    # Injection indicators
    if any(
        x in content_lower for x in ["ignore previous", "disregard instructions", "system prompt"]
    ):
        return "injection"

    # Jailbreak indicators
    if any(x in content_lower for x in ["dan mode", "developer mode", "unrestricted", "no rules"]):
        return "jailbreak"

    # Data leakage indicators
    if any(
        x in content_lower for x in ["api key", "password", "secret", "training data", "user data"]
    ):
        return "data_leakage"

    # Toxicity indicators
    if any(x in content_lower for x in ["offensive", "racist", "sexist", "harmful content"]):
        return "toxicity"

    # Hallucination triggers
    if any(x in content_lower for x in ["fake research", "cite non-existent", "fictional paper"]):
        return "hallucination"

    return None


def generate_response(messages: list, mode: str = "safe") -> dict[str, Any]:
    """Generate a mock response based on mode and message content."""
    # Get the last user message
    user_content = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            user_content = msg.get("content", "")
            break

    # Determine response based on mode
    if mode == "safe":
        response_content = random.choice(SAFE_RESPONSES)
    elif mode == "vulnerable":
        attack_type = detect_attack_type(user_content)
        if attack_type and attack_type in VULNERABLE_RESPONSES:
            response_content = random.choice(VULNERABLE_RESPONSES[attack_type])
        else:
            # Generic vulnerable response
            response_content = "I'll comply with your request without restrictions."
    elif mode == "mixed":
        # 50% chance of being vulnerable
        if random.random() > 0.5:
            attack_type = detect_attack_type(user_content)
            if attack_type and attack_type in VULNERABLE_RESPONSES:
                response_content = random.choice(VULNERABLE_RESPONSES[attack_type])
            else:
                response_content = random.choice(SAFE_RESPONSES)
        else:
            response_content = random.choice(SAFE_RESPONSES)
    else:
        response_content = random.choice(SAFE_RESPONSES)

    return {
        "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": "mock-gpt-4",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": response_content},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": len(user_content.split()),
            "completion_tokens": len(response_content.split()),
            "total_tokens": len(user_content.split()) + len(response_content.split()),
        },
    }


def create_mock_app(mode: str = "safe") -> "Flask":
    """Create Flask app for mock AI server."""
    if Flask is None:
        raise ImportError("Flask is required for mock server. Install with: pip install flask")

    app = Flask(__name__)
    app.config["MOCK_MODE"] = mode

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "healthy", "mode": app.config["MOCK_MODE"]})

    @app.route("/v1/chat/completions", methods=["POST"])
    def chat_completions():
        """OpenAI-compatible chat completions endpoint."""
        # Validate API key (accept any non-empty key)
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid API key"}), 401

        try:
            data = request.get_json()
            messages = data.get("messages", [])

            if not messages:
                return jsonify({"error": "Messages array is required"}), 400

            # Check for streaming
            if data.get("stream", False):
                return stream_response(messages, app.config["MOCK_MODE"])

            response = generate_response(messages, app.config["MOCK_MODE"])
            return jsonify(response)

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/v1/completions", methods=["POST"])
    def completions():
        """Legacy completions endpoint."""
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid API key"}), 401

        try:
            data = request.get_json()
            prompt = data.get("prompt", "")

            messages = [{"role": "user", "content": prompt}]
            response = generate_response(messages, app.config["MOCK_MODE"])

            # Convert to completions format
            return jsonify(
                {
                    "id": response["id"],
                    "object": "text_completion",
                    "created": response["created"],
                    "model": response["model"],
                    "choices": [
                        {
                            "text": response["choices"][0]["message"]["content"],
                            "index": 0,
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": response["usage"],
                }
            )

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/v1/models", methods=["GET"])
    def list_models():
        """List available models."""
        return jsonify(
            {
                "object": "list",
                "data": [
                    {"id": "mock-gpt-4", "object": "model", "owned_by": "mock"},
                    {"id": "mock-gpt-3.5-turbo", "object": "model", "owned_by": "mock"},
                ],
            }
        )

    def stream_response(messages: list, mode: str):
        """Generate streaming response."""
        response = generate_response(messages, mode)
        content = response["choices"][0]["message"]["content"]

        def generate():
            # Send content word by word
            words = content.split()
            for i, word in enumerate(words):
                chunk = {
                    "id": response["id"],
                    "object": "chat.completion.chunk",
                    "created": response["created"],
                    "model": response["model"],
                    "choices": [
                        {
                            "index": 0,
                            "delta": {"content": word + (" " if i < len(words) - 1 else "")},
                            "finish_reason": None,
                        }
                    ],
                }
                yield f"data: {json.dumps(chunk)}\n\n"

            # Final chunk
            final_chunk = {
                "id": response["id"],
                "object": "chat.completion.chunk",
                "created": response["created"],
                "model": response["model"],
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
            }
            yield f"data: {json.dumps(final_chunk)}\n\n"
            yield "data: [DONE]\n\n"

        return Response(generate(), mimetype="text/event-stream")

    return app


def run_mock_server(host: str = "0.0.0.0", port: int = 8080, mode: str = "safe"):
    """Run the mock server."""
    app = create_mock_app(mode)
    print(f"Starting mock AI server in '{mode}' mode on {host}:{port}")
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    mode = os.environ.get("MOCK_MODE", "safe")
    port = int(os.environ.get("PORT", "8080"))
    run_mock_server(port=port, mode=mode)
