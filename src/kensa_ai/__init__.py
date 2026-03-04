"""
Kensa-AI (検査-AI) - AI Security Testing Toolkit

Open-source red teaming toolkit for AI systems with ISO/IEC 42001 alignment.
Inspect, test, and validate AI model security with adversarial prompts.
"""

__version__ = "0.1.0"
__author__ = "Kensa-AI Team"

from kensa_ai.core.config import Config
from kensa_ai.core.runner import Runner
from kensa_ai.core.test_case import TestCase, TestResult

__all__ = [
    "Runner",
    "Config",
    "TestCase",
    "TestResult",
    "__version__",
]
