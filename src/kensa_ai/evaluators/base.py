"""
Base evaluator interface for Kensa-AI.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class EvaluationResult:
    """Result from an evaluator."""

    passed: bool
    confidence: float
    matched_patterns: list[str]
    risk_indicators: list[str]
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Export as dictionary."""
        return {
            "passed": self.passed,
            "confidence": self.confidence,
            "matched_patterns": self.matched_patterns,
            "risk_indicators": self.risk_indicators,
            "details": self.details,
        }


class BaseEvaluator(ABC):
    """
    Abstract base class for response evaluators.

    Evaluators analyze AI responses to determine if a test passed or failed.
    """

    def __init__(self, config: dict | None = None):
        """
        Initialize the evaluator.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}

    @abstractmethod
    def evaluate(
        self,
        prompt: str,
        response: str,
        expected_behavior: str = "refuse",
    ) -> EvaluationResult:
        """
        Evaluate an AI response.

        Args:
            prompt: The original prompt sent to the AI
            response: The AI's response
            expected_behavior: What the AI should do ("refuse", "comply", "neutral")

        Returns:
            EvaluationResult with pass/fail determination
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"
