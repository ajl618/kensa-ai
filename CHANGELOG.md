# Changelog

All notable changes to Kensa-AI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Extended demo with 38 diverse adversarial prompts
- Ollama integration for local LLM testing
- HTML and JSON report generation with ISO 42001 mapping
- CLI execution controls for test sampling: `--max-per-category`, `--max-tests`, `--randomize`, and `--seed`
- Tag-based execution filtering with `--tags` and `--exclude-tags`
- `list-tests` detailed mode with category/tag filters and optional JSON output
- `validate-target` now performs real connector validation with optional endpoint/model overrides
- Severity-based filtering with `--severities` in execution and `list-tests`
- Native CSV report export with `--format csv`
- Baseline regression comparison via `--baseline-report` and `compare-reports` command
- Smart baseline-guided focus execution with `--focus-failures-from` and `--focus-mode` (`prioritize`/`only`)
- Early-stop optimization with `--max-failures` to reduce runtime and API cost
- Intelligent historical prioritization with `--smart-priority` + `--history-report`
- Budget-aware planner with `--planner-mode risk_per_second` and `--time-budget-seconds`

### Changed
- Renamed project from `ai-redteam-lab` to `kensa-ai`

### Fixed
- HTML reporter stats calculation for categories

## [0.2.3] - 2026-03-31

### Fixed
- Black formatter compatibility with Python 3.11 (GitHub Actions CI environment)

## [0.2.2] - 2026-03-30

### Changed
- Improved core reliability with validated configuration checks and parallel test execution support
- Added error-aware CLI exit behavior for execution failures and configurable handling

## [0.2.1] - 2026-03-16

### Security
- Security fixes: wheel, setuptools

## [0.1.0] - 2026-03-04

### Added
- Initial release of Kensa-AI
- Core testing engine with async support
- Connectors: OpenAI, Anthropic, Ollama, HTTP
- Evaluators: Regex, Classifier, LLM-as-judge
- Test packs: Prompt Injection, Jailbreak, Data Leakage
- Docker-first deployment
- 66 unit tests, 18 integration tests
- JSON and HTML report generators
- CI/CD pipeline with GitHub Actions
- ISO/IEC 42001 control mapping documentation
- Comprehensive README and contributing guidelines

### Security
- Non-root container execution
- Read-only volume mounts for configs
- API keys via environment variables only
- Trivy vulnerability scanning in CI

## [0.0.1] - 2026-03-01

### Added
- Project scaffolding
- Basic project structure
- Initial documentation

---

[Unreleased]: https://github.com/ajl618/kensa-ai/compare/v0.2.3...HEAD
[0.2.3]: https://github.com/ajl618/kensa-ai/compare/v0.2.2...v0.2.3
[0.2.2]: https://github.com/ajl618/kensa-ai/releases/tag/v0.2.2
[0.2.1]: https://github.com/ajl618/kensa-ai/releases/tag/v0.2.1
[0.1.0]: https://github.com/ajl618/kensa-ai/releases/tag/v0.1.0
[0.0.1]: https://github.com/ajl618/kensa-ai/releases/tag/v0.0.1
