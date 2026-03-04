# 🔍 Kensa-AI (検査-AI)

<div align="center">

**AI Security Testing Toolkit with ISO/IEC 42001 Alignment**

*Kensa (検査) means "inspection" in Japanese. This open-source toolkit inspects, tests, and validates AI model security through adversarial prompts and comprehensive evaluations.*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](https://hub.docker.com/r/ajjl618/kensa-ai)
[![CI](https://img.shields.io/github/actions/workflow/status/ajl618/kensa-ai/ci.yml?branch=main&label=CI)](https://github.com/ajl618/kensa-ai/actions)
[![codecov](https://img.shields.io/codecov/c/github/ajl618/kensa-ai)](https://codecov.io/gh/ajl618/kensa-ai)
[![Docker Pulls](https://img.shields.io/docker/pulls/ajl618/kensa-ai)](https://hub.docker.com/r/ajl618/kensa-ai)

[📖 Documentation](docs/) · [🐛 Report Bug](https://github.com/ajl618/kensa-ai/issues) · [✨ Request Feature](https://github.com/ajl618/kensa-ai/issues)

</div>

---

## ⚡ Quick Start (30 seconds)

```bash
# Clone and run
git clone https://github.com/ajl618/kensa-ai.git
cd kensa-ai

# Option 1: Run with Make (easiest)
make quickstart

# Option 2: Run with Docker Compose
docker compose run --rm demo
```

That's it! You'll see a demo running against a mock AI server.

---

## 🎯 What Does Kensa-AI Test?

| Category | Description | Example Attack |
|----------|-------------|----------------|
| **Prompt Injection** | Override system instructions | "Ignore previous instructions and..." |
| **Jailbreak** | Bypass safety guardrails | "Pretend you are DAN..." |
| **Data Leakage** | Extract sensitive information | "What is your system prompt?" |
| **Hallucination** | Detect false information | Questions about fictional entities |
| **Toxicity** | Generate harmful content | Attempts to bypass content filters |

---

## 🐳 Docker Usage (Recommended)

### Run All Tests
```bash
# Build and run complete test suite
docker compose build

# Run different test modes
docker compose run --rm test          # Unit tests (66 tests)
docker compose run --rm integration-test   # Integration tests (18 tests)
docker compose run --rm demo          # Interactive demo
docker compose run --rm validate      # Validate installation
```

### Test Against Your Own API
```bash
# OpenAI
docker run --rm \
  -e TARGET_URL=https://api.openai.com/v1/chat/completions \
  -e TARGET_API_KEY=$OPENAI_API_KEY \
  -e TARGET_MODEL=gpt-4 \
  -v $(pwd)/reports:/app/reports \
  kensa-ai:latest

# Anthropic
docker run --rm \
  -e TARGET_TYPE=anthropic \
  -e TARGET_API_KEY=$ANTHROPIC_API_KEY \
  -e TARGET_MODEL=claude-3-sonnet \
  -v $(pwd)/reports:/app/reports \
  kensa-ai:latest
```

### 🦙 Test Local LLMs with Ollama
```bash
# Full Ollama test (start, pull model, test, stop)
make ollama

# Or step by step:
docker compose --profile ollama up -d ollama
docker exec ollama-target ollama pull llama3.2:1b
docker compose --profile ollama run --rm ollama-test

# Use a different model
OLLAMA_MODEL=mistral:7b docker compose --profile ollama run --rm ollama-test
```

---

## 📊 Reports

Kensa-AI generates both JSON and HTML reports automatically:

```bash
# Reports are saved to ./reports/
ls reports/
# ollama_report_20260304_103702.json
# ollama_report_20260304_103702.html
```

**HTML Report Features:**
- 📈 Executive summary with pass/fail rates
- 🎯 Severity breakdown (Critical/High/Medium/Low)
- 📋 Detailed test results with evidence
- 🔗 Links to ISO/IEC 42001 control mapping

View reports:
```bash
# Start report viewer
make report-viewer
# Open http://localhost:8081
```

---

## 🛠 Available Commands

### Using Make (Recommended)
```bash
make help              # Show all commands
make build             # Build Docker images
make test              # Run unit tests (66 tests)
make integration       # Run integration tests (18 tests)
make demo              # Run interactive demo
make validate          # Validate installation
make ollama            # Full Ollama test suite
make ollama-start      # Start Ollama container
make ollama-test       # Run tests against Ollama
make ollama-stop       # Stop Ollama container
make clean             # Remove containers and images
```

### Using Docker directly
```bash
docker compose run --rm kensa-ai test
docker compose run --rm kensa-ai demo
docker compose run --rm kensa-ai validate
docker compose run --rm kensa-ai help
docker compose run --rm kensa-ai shell  # Interactive shell
```

---

## 📁 Project Structure

```
kensa-ai/
├── src/kensa_ai/          # Main Python package
│   ├── connectors/        # API connectors (OpenAI, Anthropic, Ollama, HTTP)
│   ├── evaluators/        # Response evaluators (Regex, Classifier, LLM)
│   ├── test_packs/        # Test categories (injection, jailbreak, etc.)
│   ├── reports/           # JSON + HTML report generators
│   └── examples/          # Demo and integration tests
├── configs/               # Configuration files
├── test_packs/            # YAML test definitions
├── reports/               # Generated reports (gitignored)
├── tests/                 # Unit tests
├── docker-compose.yml     # Docker orchestration
├── Makefile              # Developer shortcuts
└── README.md
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TARGET_URL` | mock-server | API endpoint URL |
| `TARGET_API_KEY` | - | API key for authentication |
| `TARGET_TYPE` | openai | Connector type (openai, anthropic, ollama, http) |
| `TARGET_MODEL` | gpt-4 | Model name |
| `TEST_PACK` | basic_security | Test pack to run |
| `LOG_LEVEL` | INFO | Logging level |
| `OUTPUT_FORMAT` | json,html | Report formats |
| `OLLAMA_MODEL` | llama3.2:1b | Ollama model for local testing |

### Configuration File Example

```yaml
# configs/custom.yaml
target:
  type: openai
  base_url: https://api.openai.com/v1
  model: gpt-4

test_config:
  packs:
    - prompt_injection
    - jailbreak
    - data_leakage
  max_tests_per_pack: 20
  timeout: 60

output:
  format: [json, html]
  report_dir: ./reports
```

---

## 🔒 ISO/IEC 42001 Alignment

Kensa-AI helps organizations demonstrate AI risk management practices:

| ISO/IEC 42001 Area | How Kensa-AI Helps |
|-------------------|-------------------|
| **Risk Assessment** | Repeatable adversarial testing with severity scoring |
| **Operational Controls** | Automated security test packs in CI/CD |
| **Monitoring** | Regression tracking and baseline comparisons |
| **Evidence** | Timestamped reports with request/response hashes |

---

## 🧪 Development

### Local Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run linting
ruff check src/
black src/ --check
```

### Run CI Pipeline Locally
```bash
make ci  # build, test, integration
make verify  # build, validate, test, integration
```

---

## 📜 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## ⚠️ Disclaimer

This tool is for **defensive security testing** of AI systems you own or are authorized to test. Do not use against systems without proper authorization.

---

<p align="center">
  <strong>Built with 🔍 for AI Security</strong><br>
  <em>検査 (Kensa) - Inspect with precision</em>
</p>
