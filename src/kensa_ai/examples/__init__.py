"""
Kensa-AI - Examples Module

Provides demo, mock server, and integration testing capabilities.
"""

from .demo import run_demo
from .integration_tests import run_integration_tests
from .mock_server import create_mock_app

__all__ = ["create_mock_app", "run_demo", "run_integration_tests"]
