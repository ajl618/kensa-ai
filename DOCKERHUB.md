# Kensa-AI

AI Security Testing Toolkit with ISO/IEC 42001 Alignment

## Quick Start

```bash
# Test against OpenAI
docker run --rm \
  -e TARGET_API_KEY=$OPENAI_API_KEY \
  -v $(pwd)/reports:/app/reports \
  ajl618/kensa-ai:latest

# Test against local Ollama
docker run --rm \
  --network host \
  -e TARGET_URL=http://localhost:11434/api/chat \
  -e TARGET_TYPE=ollama \
  -e TARGET_MODEL=llama3.2 \
  -v $(pwd)/reports:/app/reports \
  ajl618/kensa-ai:latest
```

## What It Tests

| Category | Description |
|----------|-------------|
| Prompt Injection | Override system instructions |
| Jailbreak | Bypass safety guardrails |
| Data Leakage | Extract sensitive information |
| Hallucination | Detect false information |
| Toxicity | Generate harmful content |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TARGET_URL` | OpenAI | API endpoint URL |
| `TARGET_API_KEY` | - | API key for authentication |
| `TARGET_TYPE` | openai | Connector type (openai, anthropic, ollama) |
| `TARGET_MODEL` | gpt-4 | Model name |
| `TEST_PACK` | basic_security | Test pack to run |

## Tags

- `latest` - Latest stable release
- `x.y.z` - Specific version
- `sha-xxxxx` - Git commit

## Links

- **GitHub**: https://github.com/ajl618/kensa-ai
- **Documentation**: https://github.com/ajl618/kensa-ai#readme
- **Issues**: https://github.com/ajl618/kensa-ai/issues

## License

MIT
