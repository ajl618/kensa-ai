# Changelog

All notable changes to Kensa-AI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Extended demo with 38 diverse adversarial prompts
- Ollama integration for local LLM testing
- HTML and JSON report generation with ISO 42001 mapping

### Changed
- Renamed project from `ai-redteam-lab` to `kensa-ai`

### Fixed
- HTML reporter stats calculation for categories

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

[Unreleased]: https://github.com/ajl618/kensa-ai/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/ajl618/kensa-ai/releases/tag/v0.1.0
[0.0.1]: https://github.com/ajl618/kensa-ai/releases/tag/v0.0.1
