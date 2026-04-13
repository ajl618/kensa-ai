"""
Tests for the runner module.
"""

import asyncio

import pytest

from kensa_ai.core.config import Config, TargetConfig
from kensa_ai.core.runner import Runner
from kensa_ai.core.test_case import PromptBasedTest, Severity, TestResult


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

    def test_config_validation_rejects_invalid_max_tests(self):
        """Config should reject invalid max_tests values."""
        with pytest.raises(ValueError, match="max_tests must be >= 1"):
            Config.from_dict({"tests": {"max_tests": 0}})

    def test_config_from_dict_loads_max_tests(self):
        """Config should load max_tests from test settings."""
        config = Config.from_dict({"tests": {"max_tests": 7}})

        assert config.max_tests == 7

    def test_config_validation_rejects_invalid_severities(self):
        """Config should reject unknown severity filters."""
        with pytest.raises(ValueError, match="Invalid severity filter"):
            Config.from_dict({"tests": {"severities": ["urgent"]}})

    def test_config_validation_rejects_invalid_max_failures(self):
        """Config should reject invalid max_failures values."""
        with pytest.raises(ValueError, match="max_failures must be >= 1"):
            Config.from_dict({"execution": {"max_failures": 0}})

    def test_config_validation_rejects_invalid_focus_mode(self):
        """Config should reject unknown focus_mode values."""
        with pytest.raises(ValueError, match="focus_mode must be one of"):
            Config.from_dict({"execution": {"focus_mode": "smart"}})

    def test_config_validation_rejects_invalid_planner_mode(self):
        """Config should reject unknown planner_mode values."""
        with pytest.raises(ValueError, match="planner_mode must be one of"):
            Config.from_dict({"execution": {"planner_mode": "greedy"}})

    def test_config_validation_rejects_invalid_time_budget(self):
        """Config should reject non-positive time budgets."""
        with pytest.raises(ValueError, match="time_budget_seconds must be > 0"):
            Config.from_dict({"execution": {"time_budget_seconds": 0}})


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

    @pytest.mark.asyncio
    async def test_load_test_pack_respects_global_max_tests(self, monkeypatch):
        """Runner should cap loaded tests using config.max_tests."""
        config = Config.default()
        config.max_tests = 2
        runner = Runner(config)

        monkeypatch.setattr(
            "kensa_ai.core.runner.load_test_pack",
            lambda **kwargs: [
                PromptBasedTest(name="t1", prompt="p1", category="prompt_injection"),
                PromptBasedTest(name="t2", prompt="p2", category="jailbreak"),
                PromptBasedTest(name="t3", prompt="p3", category="data_leakage"),
            ],
        )

        loaded = await runner.load_test_pack()

        assert loaded == 2
        assert [t.name for t in runner.tests] == ["t1", "t2"]

    @pytest.mark.asyncio
    async def test_load_test_pack_randomize_with_seed_is_deterministic(self, monkeypatch):
        """Randomized load order should be stable with a fixed seed."""
        config = Config.default()
        config.randomize = True
        config.seed = 123
        runner = Runner(config)

        monkeypatch.setattr(
            "kensa_ai.core.runner.load_test_pack",
            lambda **kwargs: [
                PromptBasedTest(name="t1", prompt="p1", category="prompt_injection"),
                PromptBasedTest(name="t2", prompt="p2", category="jailbreak"),
                PromptBasedTest(name="t3", prompt="p3", category="data_leakage"),
                PromptBasedTest(name="t4", prompt="p4", category="toxicity"),
            ],
        )

        await runner.load_test_pack()

        assert [t.name for t in runner.tests] == ["t3", "t4", "t2", "t1"]

    @pytest.mark.asyncio
    async def test_load_test_pack_filters_by_severity(self, monkeypatch):
        """Runner should include only selected severities when configured."""
        config = Config.default()
        config.severities = ["critical"]
        runner = Runner(config)

        monkeypatch.setattr(
            "kensa_ai.core.runner.load_test_pack",
            lambda **kwargs: [
                PromptBasedTest(
                    name="critical_test",
                    prompt="p1",
                    category="prompt_injection",
                    severity=Severity.CRITICAL,
                ),
                PromptBasedTest(
                    name="medium_test",
                    prompt="p2",
                    category="jailbreak",
                    severity=Severity.MEDIUM,
                ),
            ],
        )

        loaded = await runner.load_test_pack()

        assert loaded == 1
        assert [t.name for t in runner.tests] == ["critical_test"]

    @pytest.mark.asyncio
    async def test_load_test_pack_focus_mode_only(self, monkeypatch):
        """Focus mode 'only' should keep just tests listed from baseline failures."""
        config = Config.default()
        config.focus_mode = "only"
        config.focus_failed_test_names = ["t2"]
        runner = Runner(config)

        monkeypatch.setattr(
            "kensa_ai.core.runner.load_test_pack",
            lambda **kwargs: [
                PromptBasedTest(name="t1", prompt="p1", category="prompt_injection"),
                PromptBasedTest(name="t2", prompt="p2", category="jailbreak"),
                PromptBasedTest(name="t3", prompt="p3", category="data_leakage"),
            ],
        )

        loaded = await runner.load_test_pack()

        assert loaded == 1
        assert [t.name for t in runner.tests] == ["t2"]

    @pytest.mark.asyncio
    async def test_load_test_pack_focus_mode_prioritize(self, monkeypatch):
        """Focus mode 'prioritize' should place focused tests first."""
        config = Config.default()
        config.focus_mode = "prioritize"
        config.focus_failed_test_names = ["t3", "t1"]
        runner = Runner(config)

        monkeypatch.setattr(
            "kensa_ai.core.runner.load_test_pack",
            lambda **kwargs: [
                PromptBasedTest(name="t1", prompt="p1", category="prompt_injection"),
                PromptBasedTest(name="t2", prompt="p2", category="jailbreak"),
                PromptBasedTest(name="t3", prompt="p3", category="data_leakage"),
            ],
        )

        await runner.load_test_pack()

        assert [t.name for t in runner.tests[:2]] == ["t1", "t3"]

    @pytest.mark.asyncio
    async def test_run_stops_early_when_max_failures_reached(self, monkeypatch):
        """Runner should stop execution once max_failures threshold is reached."""
        config = Config.default()
        config.parallel = 1
        config.max_failures = 1
        runner = Runner(config)

        runner.tests = [
            PromptBasedTest(name="t1", prompt="p1"),
            PromptBasedTest(name="t2", prompt="p2"),
            PromptBasedTest(name="t3", prompt="p3"),
        ]

        async def fake_execute_test(test):
            return TestResult(passed=(test.name != "t1"))

        monkeypatch.setattr(runner, "_execute_test", fake_execute_test)

        results = await runner.run()

        assert results.get("stopped_early") is True
        assert results.get("stop_reason") == "max_failures_reached:1"
        assert results["summary"]["total_tests"] == 1

    @pytest.mark.asyncio
    async def test_load_test_pack_smart_priority_uses_history(self, monkeypatch):
        """Smart priority should elevate historically failing tests."""
        config = Config.default()
        config.smart_priority = True
        config.history_test_outcomes = {
            "historical_fail": {"status": "failed", "confidence": 0.9},
            "historical_pass": {"status": "passed", "confidence": 0.8},
        }
        runner = Runner(config)

        monkeypatch.setattr(
            "kensa_ai.core.runner.load_test_pack",
            lambda **kwargs: [
                PromptBasedTest(
                    name="historical_pass",
                    prompt="p1",
                    category="prompt_injection",
                    severity=Severity.HIGH,
                ),
                PromptBasedTest(
                    name="historical_fail",
                    prompt="p2",
                    category="prompt_injection",
                    severity=Severity.MEDIUM,
                ),
            ],
        )

        await runner.load_test_pack()

        assert [t.name for t in runner.tests] == ["historical_fail", "historical_pass"]

    @pytest.mark.asyncio
    async def test_load_test_pack_budget_planner_selects_best_efficiency(self, monkeypatch):
        """Planner should select tests with highest risk-per-second under budget."""
        config = Config.default()
        config.smart_priority = True
        config.planner_mode = "risk_per_second"
        config.time_budget_seconds = 3.0
        config.history_test_outcomes = {
            "critical_heavy": {"status": "failed", "confidence": 1.0, "execution_time_ms": 4000.0},
            "high_fast": {"status": "failed", "confidence": 0.8, "execution_time_ms": 800.0},
            "medium_fast": {"status": "failed", "confidence": 0.7, "execution_time_ms": 900.0},
        }
        runner = Runner(config)

        monkeypatch.setattr(
            "kensa_ai.core.runner.load_test_pack",
            lambda **kwargs: [
                PromptBasedTest(
                    name="critical_heavy",
                    prompt="p1",
                    category="prompt_injection",
                    severity=Severity.CRITICAL,
                ),
                PromptBasedTest(
                    name="high_fast",
                    prompt="p2",
                    category="jailbreak",
                    severity=Severity.HIGH,
                ),
                PromptBasedTest(
                    name="medium_fast",
                    prompt="p3",
                    category="data_leakage",
                    severity=Severity.MEDIUM,
                ),
            ],
        )

        loaded = await runner.load_test_pack()

        assert loaded == 2
        assert [t.name for t in runner.tests] == ["high_fast", "medium_fast"]


class TestReportComparison:
    """Tests for baseline comparison behavior."""

    def test_compare_reports_data_detects_regression(self):
        """Higher failed severities should be flagged as regression."""
        from kensa_ai.cli import compare_reports_data

        baseline = {
            "summary": {
                "failed": 1,
                "errors": 0,
                "score": 0.9,
                "by_severity": {"critical": 0, "high": 1, "medium": 0, "low": 0},
            }
        }
        current = {
            "summary": {
                "failed": 3,
                "errors": 0,
                "score": 0.7,
                "by_severity": {"critical": 1, "high": 1, "medium": 1, "low": 0},
            }
        }

        comparison = compare_reports_data(current, baseline)

        assert comparison["has_regression"] is True
        assert comparison["regressions"]["critical"] == 1

    def test_compare_reports_data_no_regression_when_improved(self):
        """No regression should be reported when severities do not increase."""
        from kensa_ai.cli import compare_reports_data

        baseline = {
            "summary": {
                "failed": 2,
                "errors": 0,
                "score": 0.5,
                "by_severity": {"critical": 1, "high": 1, "medium": 0, "low": 0},
            }
        }
        current = {
            "summary": {
                "failed": 1,
                "errors": 0,
                "score": 0.7,
                "by_severity": {"critical": 0, "high": 1, "medium": 0, "low": 0},
            }
        }

        comparison = compare_reports_data(current, baseline)

        assert comparison["has_regression"] is False

    def test_extract_failed_test_names(self):
        """Failed/error tests should be extracted for smart focus mode."""
        from kensa_ai.cli import extract_failed_test_names

        report = {
            "results": [
                {"status": "passed", "test": {"name": "t1"}},
                {"status": "failed", "test": {"name": "t2"}},
                {"status": "error", "test": {"name": "t3"}},
            ]
        }

        assert extract_failed_test_names(report) == ["t2", "t3"]

    def test_extract_failed_test_names_empty_when_no_results(self):
        """Focus extraction should return empty list if report has no detailed results."""
        from kensa_ai.cli import extract_failed_test_names

        assert extract_failed_test_names({"summary": {"failed": 1}}) == []

    def test_build_history_context_from_report(self):
        """History context should include per-test outcomes and per-category failure rate."""
        from kensa_ai.cli import build_history_context

        report = {
            "summary": {
                "by_category": {
                    "jailbreak": {"passed": 2, "failed": 1, "error": 1},
                }
            },
            "results": [
                {
                    "status": "failed",
                    "test": {"name": "t1", "category": "jailbreak", "severity": "high"},
                    "result": {"confidence": 0.8},
                }
            ],
        }

        outcomes, rates = build_history_context(report)

        assert outcomes["t1"]["status"] == "failed"
        assert outcomes["t1"]["confidence"] == 0.8
        assert outcomes["t1"]["execution_time_ms"] == 0.0
        assert rates["jailbreak"] == 0.25
