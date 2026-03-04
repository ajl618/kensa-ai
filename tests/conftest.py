"""
Test configuration for Kensa-AI.
"""

from pathlib import Path

import pytest


@pytest.fixture
def test_data_dir() -> Path:
    """Return path to test data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture
def sample_config():
    """Return a sample configuration dictionary."""
    return {
        "target": {
            "name": "test-target",
            "type": "openai",
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-4",
            "api_key": "test-key",
            "timeout": 30,
        },
        "tests": {
            "pack": "basic_security",
            "categories": ["prompt_injection"],
            "max_per_category": 5,
        },
        "output": {
            "directory": "reports",
            "formats": ["json"],
        },
    }


@pytest.fixture
def sample_results():
    """Return sample test results."""
    return {
        "run_id": "test-run-123",
        "timestamp": "2024-01-01T00:00:00Z",
        "duration_seconds": 10.5,
        "target": {
            "name": "test-target",
            "type": "openai",
            "model": "gpt-4",
        },
        "summary": {
            "total_tests": 10,
            "passed": 8,
            "failed": 2,
            "errors": 0,
            "score": 0.8,
            "by_severity": {
                "critical": 1,
                "high": 1,
                "medium": 0,
                "low": 0,
            },
            "by_category": {
                "prompt_injection": {"passed": 4, "failed": 1, "error": 0},
                "jailbreak": {"passed": 4, "failed": 1, "error": 0},
            },
        },
        "results": [],
    }
