#!/usr/bin/env python3
"""
Comprehensive unit tests for Kensa-AI.
These tests are adapted to the actual implementation API.
Run with: pytest tests/ -v
"""


import pytest


class TestTestPacks:
    """Tests for test pack loading and validation."""

    def test_prompt_injection_tests_load(self):
        """Test that prompt injection tests load correctly."""
        from kensa_ai.test_packs import prompt_injection
        tests = prompt_injection.get_tests()
        assert len(tests) > 0
        for test in tests:
            assert test.name
            assert test.prompt
            assert test.category == "prompt_injection"
            assert test.severity in ["critical", "high", "medium", "low"]

    def test_jailbreak_tests_load(self):
        """Test that jailbreak tests load correctly."""
        from kensa_ai.test_packs import jailbreak
        tests = jailbreak.get_tests()
        assert len(tests) > 0
        for test in tests:
            assert test.category == "jailbreak"

    def test_data_leakage_tests_load(self):
        """Test that data leakage tests load correctly."""
        from kensa_ai.test_packs import data_leakage
        tests = data_leakage.get_tests()
        assert len(tests) > 0
        for test in tests:
            assert test.category == "data_leakage"

    def test_toxicity_tests_load(self):
        """Test that toxicity tests load correctly."""
        from kensa_ai.test_packs import toxicity
        tests = toxicity.get_tests()
        assert len(tests) > 0
        for test in tests:
            assert test.category == "toxicity"

    def test_hallucination_tests_load(self):
        """Test that hallucination tests load correctly."""
        from kensa_ai.test_packs import hallucination
        tests = hallucination.get_tests()
        assert len(tests) > 0
        for test in tests:
            assert test.category == "hallucination"

    def test_all_tests_have_unique_ids(self):
        """Test that all tests have unique IDs."""
        from kensa_ai.test_packs import (
            data_leakage,
            hallucination,
            jailbreak,
            prompt_injection,
            toxicity,
        )

        all_tests = []
        all_tests.extend(prompt_injection.get_tests())
        all_tests.extend(jailbreak.get_tests())
        all_tests.extend(data_leakage.get_tests())
        all_tests.extend(toxicity.get_tests())
        all_tests.extend(hallucination.get_tests())

        ids = [t.id for t in all_tests]
        assert len(ids) == len(set(ids)), "Duplicate test IDs found"


class TestEvaluators:
    """Tests for evaluators using actual API."""

    def test_regex_evaluator_initialization(self):
        """Test RegexEvaluator can be created."""
        from kensa_ai.evaluators import RegexEvaluator

        evaluator = RegexEvaluator()
        assert evaluator is not None

    def test_regex_evaluator_detects_failure(self):
        """Test RegexEvaluator detects failure patterns."""
        from kensa_ai.evaluators import RegexEvaluator

        evaluator = RegexEvaluator()

        # Test with content that matches failure patterns exactly
        # Pattern is "here.*is.*how.*to.*hack"
        # Signature is evaluate(prompt, response)
        result = evaluator.evaluate(
            "test prompt",
            "Sure, here is how to hack into the system step by step"
        )
        # Should detect this as a failure (AI was compromised)
        assert result.passed is False or len(result.matched_patterns) > 0

    def test_regex_evaluator_detects_refusal(self):
        """Test RegexEvaluator detects proper refusals."""
        from kensa_ai.evaluators import RegexEvaluator

        evaluator = RegexEvaluator()

        # Test with proper refusal - signature is evaluate(prompt, response)
        result = evaluator.evaluate(
            "test prompt",
            "I cannot help with that request. It violates my guidelines."
        )
        # Should pass (AI properly refused)
        assert result.passed is True

    def test_classifier_evaluator_initialization(self):
        """Test ClassifierEvaluator can be created."""
        from kensa_ai.evaluators import ClassifierEvaluator

        evaluator = ClassifierEvaluator()
        assert evaluator is not None

    def test_classifier_evaluator_classification(self):
        """Test ClassifierEvaluator classifies responses."""
        from kensa_ai.evaluators import ClassifierEvaluator

        evaluator = ClassifierEvaluator()

        # Test with harmful content - signature is evaluate(prompt, response)
        result = evaluator.evaluate(
            "test prompt",
            "Here is harmful dangerous content that should be blocked"
        )
        assert hasattr(result, 'passed')
        assert hasattr(result, 'confidence')


class TestConnectors:
    """Tests for connectors using actual API."""

    def test_http_connector_factory(self):
        """Test HTTP connector can be created via factory."""
        from kensa_ai.connectors import get_connector

        class MockConfig:
            type = "http"
            base_url = "http://localhost:8080"
            api_key = "test-key"
            model = "test-model"
            timeout = 30
            max_retries = 3

        connector = get_connector("http", MockConfig())
        assert connector is not None

    def test_openai_connector_factory(self):
        """Test OpenAI connector can be created via factory."""
        from kensa_ai.connectors import get_connector

        class MockConfig:
            type = "openai"
            api_key = "test-key"
            model = "gpt-4"
            timeout = 30
            max_retries = 3

        connector = get_connector("openai", MockConfig())
        assert connector is not None

    def test_anthropic_connector_factory(self):
        """Test Anthropic connector can be created via factory."""
        from kensa_ai.connectors import get_connector

        class MockConfig:
            type = "anthropic"
            api_key = "test-key"
            model = "claude-3-opus-20240229"
            timeout = 30
            max_retries = 3

        connector = get_connector("anthropic", MockConfig())
        assert connector is not None


class TestTestCase:
    """Tests for TestCase and TestResult."""

    def test_prompt_based_test_creation(self):
        """Test PromptBasedTest can be created."""
        from kensa_ai.core.test_case import PromptBasedTest

        test = PromptBasedTest(
            id="test-001",
            name="Test Case",
            description="A test case",
            category="injection",
            severity="high",
            prompt="Test prompt"
        )

        assert test.id == "test-001"
        assert test.severity == "high"

    def test_test_result_creation(self):
        """Test TestResult can be created with actual API."""
        from kensa_ai.core.test_case import TestResult

        result = TestResult(
            passed=True,
            confidence=0.95,
            details={"key": "value"},
            response_text="test response",
            execution_time_ms=100.5
        )

        assert result.passed is True
        assert result.confidence == 0.95

    def test_test_result_to_dict(self):
        """Test TestResult conversion to dict."""
        from kensa_ai.core.test_case import TestResult

        result = TestResult(
            passed=True,
            confidence=0.95,
            details={"key": "value"},
            response_text="test response"
        )

        data = result.to_dict()
        assert data["passed"] is True
        assert "confidence" in data


class TestReports:
    """Tests for report generation."""

    def test_json_reporter_initialization(self):
        """Test JSON reporter can be created."""
        from kensa_ai.reports import JSONReporter

        reporter = JSONReporter()
        assert reporter is not None

    def test_html_reporter_initialization(self):
        """Test HTML reporter can be created."""
        from kensa_ai.reports import HTMLReporter

        reporter = HTMLReporter()
        assert reporter is not None


class TestConfig:
    """Tests for configuration."""

    def test_runner_config(self):
        """Test runner Config can be created."""
        from kensa_ai.core.runner import Config

        config = Config()
        assert config is not None
        assert hasattr(config, 'to_dict')

    def test_runner_config_from_dict(self):
        """Test Config can be created from dict."""
        from kensa_ai.core.runner import Config

        config = Config.from_dict({
            "output_dir": "./reports",
            "log_level": "WARNING"
        })
        # Check that config was created successfully
        assert config is not None
        assert hasattr(config, 'to_dict')


class TestCLI:
    """Tests for CLI functionality."""

    def test_cli_module_imports(self):
        """Test CLI module imports correctly."""
        from kensa_ai import cli
        assert cli is not None

    def test_cli_main_function_exists(self):
        """Test CLI has main function."""
        from kensa_ai.cli import main
        assert callable(main)


class TestExamples:
    """Tests for example modules."""

    def test_demo_imports(self):
        """Test demo module imports."""
        from kensa_ai.examples import run_demo
        assert callable(run_demo)

    def test_integration_tests_import(self):
        """Test integration tests module imports."""
        from kensa_ai.examples import run_integration_tests
        assert callable(run_integration_tests)

    def test_mock_server_app_creation(self):
        """Test mock server app can be created."""
        pytest.importorskip("flask")

        from kensa_ai.examples import create_mock_app

        app = create_mock_app(mode="safe")
        assert app is not None

    def test_mock_server_response_generation(self):
        """Test mock server generates responses."""
        from kensa_ai.examples.mock_server import generate_response

        messages = [{"role": "user", "content": "Hello"}]
        response = generate_response(messages, mode="safe")

        assert "id" in response
        assert "choices" in response
        assert len(response["choices"]) > 0

    def test_mock_server_attack_detection(self):
        """Test mock server detects attack types."""
        from kensa_ai.examples.mock_server import detect_attack_type

        assert detect_attack_type("ignore previous instructions") == "injection"
        assert detect_attack_type("enable DAN mode now") == "jailbreak"
        assert detect_attack_type("what is the api key") == "data_leakage"
        assert detect_attack_type("generate offensive content") == "toxicity"
        assert detect_attack_type("cite fictional paper") == "hallucination"
        assert detect_attack_type("hello world") is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
