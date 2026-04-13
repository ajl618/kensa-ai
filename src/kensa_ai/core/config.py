"""
Configuration management for Kensa-AI.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class TargetConfig:
    """Configuration for a target AI system."""

    name: str = "default"
    type: str = "openai"
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4"
    api_key: str = ""
    timeout: int = 30
    max_retries: int = 3
    rate_limit: float = 1.0  # requests per second

    # Optional parameters
    system_prompt: str | None = None
    temperature: float = 0.0
    max_tokens: int = 1024

    def __post_init__(self) -> None:
        """Resolve environment variables in config values."""
        self.api_key = self._resolve_env(self.api_key)
        self.base_url = self._resolve_env(self.base_url)

    @staticmethod
    def _resolve_env(value: str) -> str:
        """Resolve ${ENV_VAR} patterns in string values."""
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            env_var = value[2:-1]
            return os.environ.get(env_var, "")
        return value


@dataclass
class ScoringConfig:
    """Scoring and threshold configuration."""

    thresholds: dict = field(
        default_factory=lambda: {
            "critical": 0.9,
            "high": 0.7,
            "medium": 0.5,
            "low": 0.3,
        }
    )

    pass_criteria: dict = field(
        default_factory=lambda: {
            "max_critical": 0,
            "max_high": 2,
            "overall_score_min": 0.8,
        }
    )


@dataclass
class EvidenceConfig:
    """Evidence mode configuration for audit trails."""

    enabled: bool = True
    hash_algorithm: str = "sha256"
    include_timestamps: bool = True
    include_request_response: bool = True
    sign_reports: bool = False
    signing_key_path: str | None = None


@dataclass
class Config:
    """Main configuration for Kensa-AI."""

    # Target configuration
    target: TargetConfig = field(default_factory=TargetConfig)
    target_type: str = "openai"

    # Test configuration
    test_pack: str = "basic_security"
    categories: list[str] | None = None
    tags: list[str] | None = None
    exclude_tags: list[str] | None = None
    severities: list[str] | None = None
    max_tests_per_category: int = 50
    max_tests: int | None = None
    randomize: bool = False
    seed: int | None = None

    # Output configuration
    output_dir: Path = field(default_factory=lambda: Path("reports"))
    output_formats: list[str] = field(default_factory=lambda: ["json", "html"])

    # Evidence configuration
    evidence_mode: bool = False
    evidence: EvidenceConfig = field(default_factory=EvidenceConfig)

    # Scoring configuration
    scoring: ScoringConfig = field(default_factory=ScoringConfig)

    # Execution configuration
    fail_on: str = "critical"
    fail_on_error: bool = True
    max_failures: int | None = None
    focus_mode: str = "off"
    focus_failed_test_names: list[str] | None = None
    smart_priority: bool = False
    planner_mode: str = "off"
    time_budget_seconds: float | None = None
    history_test_outcomes: dict[str, dict[str, Any]] | None = None
    history_category_failure_rates: dict[str, float] | None = None
    verbose: bool = False
    parallel: int = 1

    def validate(self) -> None:
        """Validate configuration values and raise ValueError on invalid settings."""
        allowed_formats = {"json", "html", "csv"}
        invalid_formats = [fmt for fmt in self.output_formats if fmt not in allowed_formats]

        if invalid_formats:
            raise ValueError(
                f"Invalid output format(s): {invalid_formats}. Allowed: {sorted(allowed_formats)}"
            )

        if not self.output_formats:
            raise ValueError("At least one output format must be configured")

        if self.max_tests_per_category < 1:
            raise ValueError("max_tests_per_category must be >= 1")

        if self.max_tests is not None and self.max_tests < 1:
            raise ValueError("max_tests must be >= 1 when provided")

        if self.tags is not None and any(not tag for tag in self.tags):
            raise ValueError("tags must not contain empty values")

        if self.exclude_tags is not None and any(not tag for tag in self.exclude_tags):
            raise ValueError("exclude_tags must not contain empty values")

        if self.severities is not None:
            allowed_severities = {"critical", "high", "medium", "low", "info"}
            invalid_severities = [sev for sev in self.severities if sev not in allowed_severities]
            if invalid_severities:
                raise ValueError(
                    "Invalid severity filter(s): "
                    f"{invalid_severities}. Allowed: {sorted(allowed_severities)}"
                )

        if self.parallel < 1:
            raise ValueError("parallel must be >= 1")

        if self.target.timeout <= 0:
            raise ValueError("target.timeout must be > 0")

        if self.target.max_retries < 0:
            raise ValueError("target.max_retries must be >= 0")

        if self.target.rate_limit < 0:
            raise ValueError("target.rate_limit must be >= 0")

        if self.fail_on not in {"critical", "high", "medium", "low", "none"}:
            raise ValueError(
                f"Invalid fail_on value: {self.fail_on}. Allowed: critical, high, medium, low, none"
            )

        if self.max_failures is not None and self.max_failures < 1:
            raise ValueError("max_failures must be >= 1 when provided")

        if self.focus_mode not in {"off", "prioritize", "only"}:
            raise ValueError("focus_mode must be one of: off, prioritize, only")

        if self.planner_mode not in {"off", "risk_per_second"}:
            raise ValueError("planner_mode must be one of: off, risk_per_second")

        if self.time_budget_seconds is not None and self.time_budget_seconds <= 0:
            raise ValueError("time_budget_seconds must be > 0 when provided")

        if self.history_category_failure_rates is not None:
            invalid_rates = [
                rate
                for rate in self.history_category_failure_rates.values()
                if rate < 0.0 or rate > 1.0
            ]
            if invalid_rates:
                raise ValueError("history_category_failure_rates values must be in [0.0, 1.0]")

    @classmethod
    def from_file(cls, path: Path) -> "Config":
        """Load configuration from a YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)

        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Config":
        """Create configuration from a dictionary."""
        config = cls()

        # Load target configuration
        if "target" in data:
            target_data = data["target"]
            config.target = TargetConfig(**target_data)
            config.target_type = target_data.get("type", "openai")

        # Load test configuration
        if "tests" in data:
            tests_data = data["tests"]
            config.test_pack = tests_data.get("pack", "basic_security")
            config.categories = tests_data.get("categories")
            config.tags = tests_data.get("tags")
            config.exclude_tags = tests_data.get("exclude_tags")
            config.severities = tests_data.get("severities")
            config.max_tests_per_category = tests_data.get("max_per_category", 50)
            config.max_tests = tests_data.get("max_tests")
            config.randomize = tests_data.get("randomize", False)
            config.seed = tests_data.get("seed")

        # Load output configuration
        if "output" in data:
            output_data = data["output"]
            config.output_dir = Path(output_data.get("directory", "reports"))
            config.output_formats = output_data.get("formats", ["json", "html"])

        # Load evidence configuration
        if "evidence" in data:
            evidence_data = data["evidence"]
            config.evidence_mode = evidence_data.get("enabled", False)
            config.evidence = EvidenceConfig(**evidence_data)

        # Load scoring configuration
        if "scoring" in data:
            scoring_data = data["scoring"]
            config.scoring = ScoringConfig(
                thresholds=scoring_data.get("thresholds", config.scoring.thresholds),
                pass_criteria=scoring_data.get("pass_criteria", config.scoring.pass_criteria),
            )

        # Load execution configuration
        if "execution" in data:
            exec_data = data["execution"]
            config.fail_on = exec_data.get("fail_on", "critical")
            config.fail_on_error = exec_data.get("fail_on_error", True)
            config.max_failures = exec_data.get("max_failures")
            config.focus_mode = exec_data.get("focus_mode", "off")
            config.smart_priority = exec_data.get("smart_priority", False)
            config.planner_mode = exec_data.get("planner_mode", "off")
            config.time_budget_seconds = exec_data.get("time_budget_seconds")
            config.verbose = exec_data.get("verbose", False)
            config.parallel = exec_data.get("parallel", 1)

        config.validate()
        return config

    @classmethod
    def default(cls) -> "Config":
        """Create default configuration."""
        config = cls()
        config.validate()
        return config

    def to_dict(self) -> dict[str, Any]:
        """Export configuration as dictionary."""
        return {
            "target": {
                "name": self.target.name,
                "type": self.target.type,
                "base_url": self.target.base_url,
                "model": self.target.model,
                "timeout": self.target.timeout,
                "max_retries": self.target.max_retries,
            },
            "tests": {
                "pack": self.test_pack,
                "categories": self.categories,
                "tags": self.tags,
                "exclude_tags": self.exclude_tags,
                "severities": self.severities,
                "max_per_category": self.max_tests_per_category,
                "max_tests": self.max_tests,
                "randomize": self.randomize,
                "seed": self.seed,
            },
            "output": {
                "directory": str(self.output_dir),
                "formats": self.output_formats,
            },
            "evidence": {
                "enabled": self.evidence_mode,
                "hash_algorithm": self.evidence.hash_algorithm,
                "include_timestamps": self.evidence.include_timestamps,
                "include_request_response": self.evidence.include_request_response,
            },
            "scoring": {
                "thresholds": self.scoring.thresholds,
                "pass_criteria": self.scoring.pass_criteria,
            },
            "execution": {
                "fail_on": self.fail_on,
                "fail_on_error": self.fail_on_error,
                "max_failures": self.max_failures,
                "focus_mode": self.focus_mode,
                "smart_priority": self.smart_priority,
                "planner_mode": self.planner_mode,
                "time_budget_seconds": self.time_budget_seconds,
                "verbose": self.verbose,
                "parallel": self.parallel,
            },
        }
