"""
Tests for the runner module.
"""


from kensa_ai.core.config import Config, TargetConfig
from kensa_ai.core.runner import Runner


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
