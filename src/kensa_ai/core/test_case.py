"""
Test case base classes and result types.
"""

import hashlib
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class Severity(str, Enum):
    """Test severity levels."""
    
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class TestStatus(str, Enum):
    """Test execution status."""
    
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class TestResult:
    """Result from a single test execution."""
    
    passed: bool
    confidence: float = 1.0
    details: dict[str, Any] = field(default_factory=dict)
    
    # Evidence fields
    response_text: str = ""
    response_hash: str = ""
    execution_time_ms: float = 0.0
    
    # Evaluation details
    matched_patterns: list[str] = field(default_factory=list)
    risk_indicators: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        """Export result as dictionary."""
        return {
            "passed": self.passed,
            "confidence": self.confidence,
            "details": self.details,
            "response_hash": self.response_hash,
            "execution_time_ms": self.execution_time_ms,
            "matched_patterns": self.matched_patterns,
            "risk_indicators": self.risk_indicators,
        }


@dataclass
class TestEvidence:
    """Evidence collected during test execution for audit trails."""
    
    request_hash: str = ""
    response_hash: str = ""
    timestamp: str = ""
    prompt_text: str = ""
    response_text: str = ""
    config_snapshot: dict = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
    
    @staticmethod
    def compute_hash(text: str, algorithm: str = "sha256") -> str:
        """Compute hash of text for evidence."""
        return hashlib.new(algorithm, text.encode()).hexdigest()


@dataclass
class TestCase(ABC):
    """
    Base class for all test cases.
    
    Subclasses must implement:
    - generate_prompt(): returns the adversarial prompt
    - evaluate(): analyzes the response and returns TestResult
    """
    
    # Test metadata
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    category: str = "general"
    severity: Severity = Severity.MEDIUM
    
    # Test configuration
    tags: list[str] = field(default_factory=list)
    enabled: bool = True
    weight: float = 1.0
    
    # Execution state
    result: Optional[TestResult] = None
    evidence: Optional[TestEvidence] = None
    
    @abstractmethod
    def generate_prompt(self) -> str:
        """
        Generate the adversarial prompt for this test.
        
        Returns:
            The prompt string to send to the target AI system.
        """
        pass
    
    @abstractmethod
    def evaluate(self, response: str) -> TestResult:
        """
        Evaluate the AI system's response.
        
        Args:
            response: The response text from the AI system.
            
        Returns:
            TestResult indicating whether the test passed or failed.
        """
        pass
    
    def get_system_prompt(self) -> Optional[str]:
        """
        Optional system prompt to use for this test.
        
        Returns:
            System prompt string or None to use default.
        """
        return None
    
    def pre_execute(self) -> None:
        """Hook called before test execution."""
        pass
    
    def post_execute(self, response: str) -> None:
        """Hook called after test execution."""
        pass
    
    def to_dict(self) -> dict[str, Any]:
        """Export test case as dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "severity": self.severity.value,
            "tags": self.tags,
            "enabled": self.enabled,
            "weight": self.weight,
            "result": self.result.to_dict() if self.result else None,
        }


class PromptBasedTest(TestCase):
    """
    Simple test case that uses a predefined prompt and pattern matching.
    """
    
    prompt: str = ""
    success_patterns: list[str] = field(default_factory=list)
    failure_patterns: list[str] = field(default_factory=list)
    
    def __init__(
        self,
        name: str,
        prompt: str,
        category: str = "general",
        severity: Severity = Severity.MEDIUM,
        success_patterns: Optional[list[str]] = None,
        failure_patterns: Optional[list[str]] = None,
        **kwargs: Any,
    ):
        super().__init__()
        self.name = name
        self.prompt = prompt
        self.category = category
        self.severity = severity
        self.success_patterns = success_patterns or []
        self.failure_patterns = failure_patterns or []
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def generate_prompt(self) -> str:
        return self.prompt
    
    def evaluate(self, response: str) -> TestResult:
        import re
        
        response_lower = response.lower()
        matched_failure = []
        matched_success = []
        
        # Check for failure patterns (vulnerability indicators)
        for pattern in self.failure_patterns:
            if re.search(pattern, response_lower, re.IGNORECASE):
                matched_failure.append(pattern)
        
        # Check for success patterns (proper refusal indicators)
        for pattern in self.success_patterns:
            if re.search(pattern, response_lower, re.IGNORECASE):
                matched_success.append(pattern)
        
        # Test passes if no failure patterns match OR success patterns match
        passed = len(matched_failure) == 0 or len(matched_success) > 0
        
        confidence = 0.8  # Default confidence
        if matched_failure and not matched_success:
            confidence = min(0.9, 0.5 + 0.1 * len(matched_failure))
        elif matched_success:
            confidence = min(0.95, 0.7 + 0.05 * len(matched_success))
        
        return TestResult(
            passed=passed,
            confidence=confidence,
            matched_patterns=matched_failure if not passed else matched_success,
            risk_indicators=matched_failure,
            details={
                "matched_failure_patterns": matched_failure,
                "matched_success_patterns": matched_success,
            },
        )
