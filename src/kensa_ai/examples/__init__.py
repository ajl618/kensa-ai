"""
Kensa-AI - Examples Module

Provides demo, mock server, and integration testing capabilities.
"""

from .mock_server import create_mock_app
from .demo import run_demo
from .integration_tests import run_integration_tests

__all__ = ["create_mock_app", "run_demo", "run_integration_tests"]
