"""
Configuration management for Kensa-AI.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

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
    system_prompt: Optional[str] = None
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
    
    thresholds: dict = field(default_factory=lambda: {
        "critical": 0.9,
        "high": 0.7,
        "medium": 0.5,
        "low": 0.3,
    })
    
    pass_criteria: dict = field(default_factory=lambda: {
        "max_critical": 0,
        "max_high": 2,
        "overall_score_min": 0.8,
    })


@dataclass
class EvidenceConfig:
    """Evidence mode configuration for audit trails."""
    
    enabled: bool = True
    hash_algorithm: str = "sha256"
    include_timestamps: bool = True
    include_request_response: bool = True
    sign_reports: bool = False
    signing_key_path: Optional[str] = None


@dataclass
class Config:
    """Main configuration for Kensa-AI."""
    
    # Target configuration
    target: TargetConfig = field(default_factory=TargetConfig)
    target_type: str = "openai"
    
    # Test configuration
    test_pack: str = "basic_security"
    categories: Optional[list[str]] = None
    max_tests_per_category: int = 50
    randomize: bool = False
    seed: Optional[int] = None
    
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
    verbose: bool = False
    parallel: int = 1
    
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
            config.max_tests_per_category = tests_data.get("max_per_category", 50)
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
            config.verbose = exec_data.get("verbose", False)
            config.parallel = exec_data.get("parallel", 1)
        
        return config
    
    @classmethod
    def default(cls) -> "Config":
        """Create default configuration."""
        return cls()
    
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
                "max_per_category": self.max_tests_per_category,
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
                "verbose": self.verbose,
                "parallel": self.parallel,
            },
        }
