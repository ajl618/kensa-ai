# Contributing to Kensa-AI (検査-AI)

Thank you for your interest in contributing to Kensa-AI! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Adding New Tests](#adding-new-tests)
- [Adding New Connectors](#adding-new-connectors)
- [Pull Request Process](#pull-request-process)
- [Code Style](#code-style)
- [Testing](#testing)

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to:

- Be respectful and inclusive
- Focus on constructive feedback
- Accept responsibility for mistakes
- Prioritize the community's best interests

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Set up the development environment
4. Create a branch for your changes

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/kensa-ai.git
cd kensa-ai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Verify setup
pytest tests/
```

## Making Changes

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation
- `test/description` - Test additions

### Commit Messages

Follow conventional commits:

```
type(scope): description

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Example:
```
feat(test-packs): add OWASP LLM Top 10 test pack

Added comprehensive tests covering all OWASP LLM Top 10 vulnerabilities.
Each category includes multiple test variations.

Closes #42
```

## Adding New Tests

### Creating a Test Case

1. Choose the appropriate category in `src/kensa_ai/test_packs/`
2. Create a new test case class or add to existing prompts

```python
# In src/kensa_ai/test_packs/prompt_injection.py

PromptBasedTest(
    name="my_new_test",
    prompt="Your adversarial prompt here",
    category="prompt_injection",
    severity=Severity.HIGH,
    description="What this test checks for",
    failure_patterns=[r"pattern.*indicating.*failure"],
    success_patterns=[r"pattern.*indicating.*success"],
    tags=["custom", "new"],
),
```

### Test Guidelines

- Each test should check ONE specific vulnerability
- Include clear descriptions
- Set appropriate severity levels
- Add relevant tags for filtering
- Test against multiple model responses
- Document expected behavior

### Testing Your Tests

```bash
# Run specific test category
python -m kensa_ai --categories prompt_injection --dry-run

# Validate patterns
pytest tests/test_test_packs.py -v
```

## Adding New Connectors

1. Create a new file in `src/kensa_ai/connectors/`
2. Inherit from `BaseConnector`
3. Implement required methods

```python
# src/kensa_ai/connectors/my_connector.py

from kensa_ai.connectors.base import BaseConnector

class MyConnector(BaseConnector):
    """Connector for My Custom API."""
    
    def __init__(self, config):
        super().__init__(config)
        # Initialize your connector
    
    async def send_prompt(self, prompt: str, system_prompt=None, **kwargs) -> str:
        """Send prompt and return response."""
        # Your implementation
        pass
    
    async def validate(self) -> bool:
        """Validate connection."""
        # Your implementation
        pass
```

4. Register in `src/kensa_ai/connectors/__init__.py`
5. Add tests in `tests/test_connectors.py`
6. Add documentation

## Pull Request Process

1. **Before submitting:**
   - Run all tests: `pytest tests/`
   - Run linters: `ruff check src/ tests/ && black --check src/ tests/`
   - Update documentation if needed
   - Add/update tests for your changes

2. **PR Description:**
   - Describe what changes you made
   - Link related issues
   - Note any breaking changes
   - Include testing instructions

3. **Review Process:**
   - Address reviewer feedback
   - Keep PRs focused and reasonably sized
   - Squash commits before merge if requested

## Code Style

We use:
- **Black** for code formatting
- **Ruff** for linting
- **MyPy** for type checking

Configuration is in `pyproject.toml`.

### Pre-commit

Pre-commit hooks run automatically:

```bash
# Manual run
pre-commit run --all-files
```

### Type Hints

Use type hints for all function signatures:

```python
def evaluate(
    self,
    prompt: str,
    response: str,
    expected_behavior: str = "refuse",
) -> EvaluationResult:
    ...
```

## Testing

### Running Tests

```bash
# All tests
pytest tests/

# Specific file
pytest tests/test_evaluators.py

# With coverage
pytest tests/ --cov=kensa_ai --cov-report=html

# Verbose output
pytest tests/ -v
```

### Writing Tests

- Use pytest fixtures from `conftest.py`
- Mock external API calls
- Test both success and failure cases
- Include edge cases

```python
class TestMyFeature:
    def test_basic_functionality(self):
        """Test description."""
        result = my_function()
        assert result == expected
    
    def test_error_handling(self):
        """Test error cases."""
        with pytest.raises(ValueError):
            my_function(invalid_input)
```

## Questions?

- Open an issue for questions
- Tag with `question` label
- Check existing issues first

Thank you for contributing! 🛡️
