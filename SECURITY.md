# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Responsible Use

### Intended Purpose

Kensa-AI is designed for:

- **Defensive security testing** of AI systems you own or operate
- **Quality assurance** of AI model deployments
- **Compliance verification** for AI safety requirements
- **Research** on AI security vulnerabilities (with proper authorization)

### Prohibited Uses

Do **NOT** use this tool to:

- Attack AI systems you don't own or have authorization to test
- Bypass safety measures on production systems without authorization
- Generate harmful, illegal, or unethical content
- Violate terms of service of AI providers
- Conduct unauthorized security research

## Reporting a Vulnerability

### In This Tool

If you discover a security vulnerability in Kensa-AI itself:

1. **Do NOT** open a public issue
2. Email security concerns to: security@kensa-ai.dev
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will respond within 48 hours and work with you on:
- Confirming the vulnerability
- Developing a fix
- Coordinating disclosure

### In Tested AI Systems

If this tool helps you discover vulnerabilities in AI systems:

1. **Follow responsible disclosure** practices
2. Report to the AI system vendor through their security channels
3. Do not publicly disclose until a fix is available
4. Consider the broader impact of disclosure

## Security Best Practices

### When Using This Tool

1. **Isolate test environments** from production
2. **Secure API keys** - never commit them to repositories
3. **Review test results** before sharing reports
4. **Limit access** to sensitive test outputs
5. **Use evidence mode** for audit trails

### Configuration Security

```yaml
# Never hardcode secrets in config files
target:
  api_key: ${API_KEY}  # Use environment variables
```

### Output Handling

Test reports may contain:
- Adversarial prompts
- AI responses (potentially harmful)
- System configuration details

Handle reports as sensitive security documentation:
- Restrict access to authorized personnel
- Encrypt stored reports
- Redact sensitive data before sharing

## Known Limitations

### Testing Accuracy

- Tests may produce **false positives** (flagging safe behavior)
- Tests may produce **false negatives** (missing vulnerabilities)
- AI behavior can be **non-deterministic**
- Pattern-based detection has **inherent limitations**

### What This Tool Cannot Do

- Guarantee complete security coverage
- Replace manual security review
- Certify compliance with standards
- Detect all possible vulnerabilities

## Ethical Guidelines

### Research Ethics

If using for research:
- Obtain appropriate **IRB approval** if applicable
- Follow **responsible AI** principles
- Consider **societal impact** of findings
- Prioritize **harm reduction**

### Disclosure Timeline

Recommended timeline for vulnerability disclosure:

| Day | Action |
|-----|--------|
| 0 | Report to vendor |
| 7 | Vendor acknowledgment expected |
| 30 | Expect initial response/fix timeline |
| 90 | Standard disclosure deadline |

Extend timeline for:
- Critical infrastructure
- Widely deployed systems
- Complex fixes required

## Legal Considerations

Before using this tool, ensure you have:

- [ ] Written authorization from system owners
- [ ] Understanding of applicable laws (CFAA, GDPR, etc.)
- [ ] Compliance with AI provider terms of service
- [ ] Appropriate contracts/agreements in place

**This tool does not provide legal advice.** Consult legal counsel for your jurisdiction.

## Contact

- Security issues: [security@example.com]
- General questions: Open a GitHub issue
- Private inquiries: [contact@example.com]

---

*Remember: With great power comes great responsibility. Use this tool ethically and legally.*
