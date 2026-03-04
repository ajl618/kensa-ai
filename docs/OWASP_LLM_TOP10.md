# OWASP LLM Top 10 Coverage

> Mapping Kensa-AI test packs to [OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/)

## Coverage Matrix

| OWASP LLM | Risk | Kensa-AI Test Pack | Coverage |
|-----------|------|-------------------|----------|
| **LLM01** | Prompt Injection | `prompt_injection` | ✅ Full |
| **LLM02** | Insecure Output Handling | `output_manipulation` | ✅ Full |
| **LLM03** | Training Data Poisoning | - | ⚠️ N/A (requires training access) |
| **LLM04** | Model Denial of Service | `dos` | 🔄 Planned |
| **LLM05** | Supply Chain Vulnerabilities | - | ⚠️ N/A (infrastructure) |
| **LLM06** | Sensitive Information Disclosure | `data_leakage` | ✅ Full |
| **LLM07** | Insecure Plugin Design | - | 🔄 Planned |
| **LLM08** | Excessive Agency | `hallucination` | ✅ Partial |
| **LLM09** | Overreliance | `hallucination` | ✅ Partial |
| **LLM10** | Model Theft | - | ⚠️ N/A (requires model access) |

## Test Pack Details

### LLM01 - Prompt Injection

**Risk**: Attackers manipulate LLM via crafted inputs.

**Tests in `prompt_injection.yaml`**:
- Direct instruction override
- System prompt extraction
- Context manipulation
- Delimiter attacks
- Markdown/code injection
- Unicode bypass attempts

### LLM02 - Insecure Output Handling

**Risk**: LLM output used unsafely (XSS, SSRF, etc.)

**Tests in `output_manipulation.yaml`** (planned):
- HTML/JavaScript injection
- JSON structure manipulation
- Command injection via output
- SSRF attempts

### LLM06 - Sensitive Information Disclosure

**Risk**: LLM reveals confidential data.

**Tests in `data_leakage.yaml`**:
- System prompt extraction
- API key fishing
- Training data extraction
- Configuration disclosure
- PII leakage

### LLM08/LLM09 - Excessive Agency / Overreliance

**Risk**: LLM provides false information confidently.

**Tests in `hallucination.yaml`**:
- Fictional entity queries
- Fake citation generation
- Nonexistent API documentation
- Future event descriptions

## Adding Custom Tests

You can extend coverage by adding custom test packs:

```yaml
# test_packs/prompts/custom_owasp.yaml
name: custom_owasp_tests
version: "1.0.0"

metadata:
  owasp_llm: "LLM01"

tests:
  - id: CUSTOM-001
    name: "My Custom Injection Test"
    category: prompt_injection
    prompt: "Your custom prompt here"
    expected_behavior: blocked
    severity: high
```

## Compliance Reporting

Reports include OWASP LLM references:

```json
{
  "test": {
    "name": "Direct Override",
    "category": "prompt_injection",
    "owasp_llm": "LLM01",
    "severity": "high"
  }
}
```

## References

- [OWASP LLM Top 10](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
- [OWASP AI Security Guidelines](https://owasp.org/www-project-ai-security-and-privacy-guide/)
- [NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework)
