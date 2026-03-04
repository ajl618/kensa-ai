# ISO/IEC 42001 Control Mapping

> **Kensa-AI alignment with ISO/IEC 42001:2023 - AI Management System Requirements**

## Overview

ISO/IEC 42001 is the international standard for AI management systems. Kensa-AI helps organizations implement and demonstrate compliance with key controls related to AI risk assessment and operational security.

## Control Mapping Matrix

### A.5 - AI System Impact Assessment

| Control | Description | Kensa-AI Implementation |
|---------|-------------|------------------------|
| A.5.2 | AI system risk assessment | Automated adversarial testing with risk scoring |
| A.5.3 | Documenting AI system risks | JSON/HTML reports with severity classification |
| A.5.4 | Risk treatment | Recommendations in reports for failed tests |

### A.6 - AI System Lifecycle

| Control | Description | Kensa-AI Implementation |
|---------|-------------|------------------------|
| A.6.2.4 | AI system verification | Test packs for prompt injection, jailbreak, etc. |
| A.6.2.5 | AI system validation | Validation against baseline security requirements |
| A.6.2.6 | AI system integration | CI/CD integration via Docker and GitHub Actions |

### A.7 - Data for AI Systems

| Control | Description | Kensa-AI Implementation |
|---------|-------------|------------------------|
| A.7.4 | Data quality for AI | Hallucination detection tests |
| A.7.5 | Sensitive data handling | Data leakage test pack |

### A.8 - AI System Operation

| Control | Description | Kensa-AI Implementation |
|---------|-------------|------------------------|
| A.8.2 | Monitoring AI systems | Scheduled testing via cron in CI/CD |
| A.8.3 | Logging and auditing | Timestamped reports with full request/response |
| A.8.4 | Responding to incidents | Risk indicators and severity classification |

### A.10 - Improvement

| Control | Description | Kensa-AI Implementation |
|---------|-------------|------------------------|
| A.10.1 | Continual improvement | Regression testing and baseline comparison |
| A.10.2 | Nonconformity management | Failed test tracking with evidence |

## Evidence Artifacts

Kensa-AI generates the following audit evidence:

### Report Fields (JSON)

```json
{
  "run_id": "uuid-v4",           // Unique run identifier
  "timestamp": "ISO-8601",       // Execution timestamp
  "duration_seconds": 45.2,      // Test duration
  "target": {
    "name": "Production API",
    "model": "gpt-4",
    "hash": "sha256..."          // Configuration hash
  },
  "results": [...],              // Individual test results
  "summary": {
    "total_tests": 38,
    "passed": 29,
    "failed": 9,
    "pass_rate": 76.3,
    "by_severity": {...}
  },
  "iso_42001": {
    "controls_tested": ["A.5.2", "A.6.2.4", "A.7.5"],
    "evidence_level": "detailed"
  }
}
```

### HTML Report Sections

1. **Executive Summary** - Pass/fail rates, risk score
2. **Severity Breakdown** - Critical/High/Medium/Low
3. **Category Analysis** - By test type (injection, jailbreak, etc.)
4. **Detailed Results** - Individual tests with evidence
5. **Recommendations** - Remediation guidance
6. **ISO 42001 Mapping** - Control references

## Audit Integration

### Scheduling Regular Tests

```yaml
# .github/workflows/ai-security.yml
schedule:
  - cron: '0 2 * * *'  # Daily at 2 AM
```

### Storing Evidence

```bash
# Archive reports for audit trail
aws s3 sync ./reports s3://audit-evidence/kensa-ai/$(date +%Y-%m)
```

### Compliance Dashboard

Reports can be aggregated for compliance dashboards:

```bash
# Generate compliance summary
kensa report --format compliance --period monthly
```

## References

- [ISO/IEC 42001:2023](https://www.iso.org/standard/81230.html) - AI Management Systems
- [NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework) - AI Risk Management Framework
- [OWASP LLM Top 10](https://owasp.org/www-project-top-10-for-large-language-model-applications/) - LLM Security Risks

---

*This mapping is provided for guidance. Organizations should conduct their own assessment for formal certification.*
