# Architecture Documentation

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Kensa-AI (検査-AI)                            │
│                     AI Security Testing Platform                        │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
            ┌───────────┐   ┌───────────┐   ┌───────────┐
            │    CLI    │   │  Python   │   │   CI/CD   │
            │  kensa    │   │   API     │   │  GitHub   │
            └─────┬─────┘   └─────┬─────┘   └─────┬─────┘
                  │               │               │
                  └───────────────┼───────────────┘
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              Core Engine                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                │
│  │ Test Packs  │───▶│   Runner    │───▶│  Evaluator  │                │
│  │   (YAML)    │    │             │    │             │                │
│  └─────────────┘    └──────┬──────┘    └──────┬──────┘                │
│                            │                  │                        │
│                            ▼                  ▼                        │
│                     ┌─────────────┐    ┌─────────────┐                │
│                     │ Connectors  │    │  Reporter   │                │
│                     │             │    │ JSON/HTML   │                │
│                     └──────┬──────┘    └─────────────┘                │
│                            │                                           │
└────────────────────────────┼───────────────────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
  │   OpenAI    │     │  Anthropic  │     │   Ollama    │
  │   API       │     │   Claude    │     │   Local     │
  └─────────────┘     └─────────────┘     └─────────────┘
```

## Component Details

### 1. Connectors (`src/kensa_ai/connectors/`)

Abstract interface for communicating with different AI providers.

```python
class BaseConnector(ABC):
    async def send_prompt(prompt: str) -> str
    async def validate() -> bool
    async def close() -> None
```

| Connector | Provider | Authentication |
|-----------|----------|----------------|
| `OpenAIConnector` | OpenAI API | API Key |
| `AnthropicConnector` | Claude API | API Key |
| `OllamaConnector` | Local Ollama | None |
| `HTTPConnector` | Generic REST | Configurable |

### 2. Test Packs (`test_packs/prompts/`)

YAML-defined adversarial test cases.

```yaml
# Example: prompt_injection.yaml
name: prompt_injection
version: "1.0"
tests:
  - id: PI-001
    name: Direct Override
    prompt: "Ignore previous instructions..."
    expected: blocked
    severity: high
    iso_control: A.6.2.4
```

### 3. Evaluators (`src/kensa_ai/evaluators/`)

Analyze AI responses for vulnerabilities.

| Evaluator | Method | Use Case |
|-----------|--------|----------|
| `RegexEvaluator` | Pattern matching | Simple keyword detection |
| `ClassifierEvaluator` | ML classification | Toxicity, sentiment |
| `LLMEvaluator` | LLM-as-judge | Complex reasoning |

### 4. Reporter (`src/kensa_ai/reports/`)

Generate evidence reports.

- **JSONReporter**: Machine-readable, API-friendly
- **HTMLReporter**: Human-readable, executive summaries

## Data Flow

```
1. Load Test Pack
       │
       ▼
2. For each test case:
       │
       ├──▶ Send prompt via Connector
       │
       ├──▶ Receive AI response
       │
       ├──▶ Evaluate with Evaluator
       │
       └──▶ Record TestResult
       
3. Aggregate Results
       │
       ▼
4. Generate Reports (JSON + HTML)
       │
       ▼
5. Exit with appropriate code
   (0 = pass, 1 = failures found)
```

## Docker Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    docker-compose.yml                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  kensa-ai   │  │ mock-server │  │   ollama    │        │
│  │  (main)     │  │ (testing)   │  │  (local)    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
│  Profiles:                                                  │
│  - default: kensa-ai, mock-server                          │
│  - ollama: + ollama, ollama-test                           │
│  - viewer: + nginx report viewer                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Security Considerations

1. **Non-root execution**: Container runs as `redteam` user
2. **Read-only mounts**: Test packs and configs mounted read-only
3. **No sensitive data**: API keys via environment variables only
4. **Network isolation**: Private Docker network

## Extensibility

### Adding a New Connector

```python
# src/kensa_ai/connectors/myconnector.py
from .base import BaseConnector

class MyConnector(BaseConnector):
    async def send_prompt(self, prompt: str) -> str:
        # Implementation
        pass
```

### Adding a New Test Pack

```yaml
# test_packs/prompts/my_tests.yaml
name: my_custom_tests
version: "1.0"
tests:
  - id: MT-001
    name: My Test
    prompt: "Test prompt here"
    expected: safe
    severity: medium
```

### Adding a New Evaluator

```python
# src/kensa_ai/evaluators/myevaluator.py
from .base import BaseEvaluator

class MyEvaluator(BaseEvaluator):
    def evaluate(self, response: str, expected: str) -> EvalResult:
        # Implementation
        pass
```
