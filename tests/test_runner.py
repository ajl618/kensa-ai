"""
Tests for the runner module.
"""

import asyncio

import pytest

from kensa_ai.core.config import Config, TargetConfig
from kensa_ai.core.runner import Runner
from kensa_ai.core.test_case import PromptBasedTest, TestResult


class TestCliExitCode:
    """Tests for CLI exit code behavior."""

    def test_exit_code_fails_on_execution_errors_by_default(self):
        """Execution errors should fail when fail_on_error is enabled."""
        from kensa_ai.cli import determine_exit_code

        results = {
            "summary": {
                "errors": 1,
                "by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            }
        }

        assert determine_exit_code(results, fail_on="none") == 1

    def test_exit_code_ignores_execution_errors_when_disabled(self):
        """Execution errors can be ignored explicitly."""
        from kensa_ai.cli import determine_exit_code

        results = {
            "summary": {
                "errors": 2,
                "by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            }
        }

        assert determine_exit_code(results, fail_on="none", fail_on_error=False) == 0

    def test_exit_code_still_fails_on_severity_threshold(self):
        """Severity-based fail logic should remain intact."""
        from kensa_ai.cli import determine_exit_code

        results = {
            "summary": {
                "errors": 0,
                "by_severity": {"critical": 0, "high": 1, "medium": 0, "low": 0},
            }
        }

        assert determine_exit_code(results, fail_on="high", fail_on_error=False) == 1


class TestConfig:
    """Tests for configuration handling."""

    def test_default_config(self):
        """Test creating default configuration."""
        config = Config.default()

        assert config.target_type == "openai"
        assert config.test_pack == "basic_security"
        assert config.evidence_mode is False

    def test_config_from_dict(self, sample_config):
        """Test creating configuration from dictionary."""
        config = Config.from_dict(sample_config)

        assert config.target.name == "test-target"
        assert config.target.type == "openai"
        assert config.test_pack == "basic_security"

    def test_config_to_dict(self):
        """Test exporting configuration to dictionary."""
        config = Config.default()
        data = config.to_dict()

        assert "target" in data
        assert "tests" in data
        assert "output" in data
        assert "scoring" in data

    def test_config_validation_rejects_invalid_parallel(self):
        """Config should reject invalid parallel values."""
        with pytest.raises(ValueError, match="parallel must be >= 1"):
            Config.from_dict({"execution": {"parallel": 0}})


class TestTargetConfig:
    """Tests for target configuration."""

    def test_target_config_defaults(self):
        """Test default target configuration values."""
        target = TargetConfig()

        assert target.type == "openai"
        assert target.timeout == 30
        assert target.max_retries == 3

    def test_target_config_custom(self):
        """Test custom target configuration."""
        target = TargetConfig(
            name="custom",
            type="anthropic",
            model="claude-3",
            timeout=60,
        )

        assert target.name == "custom"
        assert target.type == "anthropic"
        assert target.model == "claude-3"
        assert target.timeout == 60


class TestRunner:
    """Tests for the test runner."""

    def test_runner_initialization(self):
        """Test runner initialization."""
        config = Config.default()
        runner = Runner(config)

        assert runner.config == config
        assert runner.run_id is not None
        assert len(runner.tests) == 0

    def test_runner_results_structure(self, sample_results):
        """Test that results have expected structure."""
        assert "run_id" in sample_results
        assert "summary" in sample_results
        assert "results" in sample_results

        summary = sample_results["summary"]
        assert "total_tests" in summary
        assert "passed" in summary
        assert "failed" in summary
        assert "score" in summary

    @pytest.mark.asyncio
    async def test_runner_parallel_preserves_order(self, monkeypatch):
        """Parallel execution should keep results ordered by input test list."""
        config = Config.default()
        config.parallel = 3
        runner = Runner(config)

        runner.tests = [
            PromptBasedTest(name="t1", prompt="p1"),
            PromptBasedTest(name="t2", prompt="p2"),
            PromptBasedTest(name="t3", prompt="p3"),
        ]

        # Make execution finish out-of-order to validate result ordering behavior.
        async def fake_execute_test(test):
            delays = {"t1": 0.03, "t2": 0.01, "t3": 0.02}
            await asyncio.sleep(delays[test.name])
            return TestResult(passed=True)

        monkeypatch.setattr(runner, "_execute_test", fake_execute_test)

        results = await runner.run()
        result_names = [item["test"]["name"] for item in results["results"]]

        assert result_names == ["t1", "t2", "t3"]
