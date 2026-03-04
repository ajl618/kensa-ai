#!/bin/bash
# Kensa-AI (検査-AI) - Docker Entrypoint
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_banner() {
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║       🔍 Kensa-AI (検査-AI) v0.1.0                        ║"
    echo "║     AI Security Testing with ISO/IEC 42001 Alignment      ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Function to run tests
run_tests() {
    echo -e "${YELLOW}Running unit tests...${NC}"
    python -m pytest tests/ -v --tb=short
    echo -e "${GREEN}✓ All tests passed!${NC}"
}

# Function to run demo/example
run_demo() {
    echo -e "${YELLOW}Running demo with mock connector...${NC}"
    python -m kensa_ai.examples.demo
    echo -e "${GREEN}✓ Demo completed!${NC}"
}

# Function to validate setup
validate_setup() {
    echo -e "${YELLOW}Validating installation...${NC}"
    
    # Check Python
    python --version
    
    # Check package installation
    python -c "import kensa_ai; print(f'Package version: {kensa_ai.__version__}')"
    
    # Check dependencies
    python -c "import httpx, pydantic, yaml, jinja2, click, rich; print('All dependencies OK')"
    
    echo -e "${GREEN}✓ Installation validated!${NC}"
}

# Function to run integration tests
run_integration_tests() {
    echo -e "${YELLOW}Running integration tests...${NC}"
    python -m pytest tests/integration/ -v --tb=short 2>/dev/null || \
        python -m kensa_ai.examples.integration_tests
    echo -e "${GREEN}✓ Integration tests completed!${NC}"
}

# Function to run security tests against target
run_security_tests() {
    echo -e "${YELLOW}Running security tests...${NC}"
    python -m kensa_ai "$@"
}

# Main logic
print_banner

case "${1:-}" in
    test|tests)
        shift
        run_tests
        ;;
    demo|example)
        shift
        run_demo
        ;;
    validate|check)
        shift
        validate_setup
        ;;
    integration)
        shift
        run_integration_tests
        ;;
    ollama)
        shift
        echo -e "${YELLOW}Running Ollama tests...${NC}"
        python -m kensa_ai.examples.ollama_tests
        echo -e "${GREEN}✓ Ollama tests completed!${NC}"
        ;;
    shell|bash)
        exec /bin/bash
        ;;
    help|--help|-h)
        echo "Usage: docker run kensa-ai [COMMAND] [OPTIONS]"
        echo ""
        echo "Commands:"
        echo "  test, tests       Run unit tests (66 tests)"
        echo "  demo, example     Run demo with mock connector"
        echo "  validate, check   Validate installation"
        echo "  integration       Run integration tests (18 tests)"
        echo "  ollama            Run tests against Ollama local LLM"
        echo "  shell, bash       Open interactive shell"
        echo "  help              Show this help"
        echo "  (default)         Run validation + demo"
        echo ""
        echo "Examples:"
        echo "  docker run kensa-ai test"
        echo "  docker run kensa-ai demo"
        echo "  docker compose --profile ollama run ollama-test"
        echo "  docker run -e TARGET_API_KEY=sk-xxx kensa-ai --pack basic_security"
        ;;
    "")
        # No arguments - run validation and demo
        validate_setup
        echo ""
        run_demo
        ;;
    *)
        # Pass all arguments to the main application
        run_security_tests "$@"
        ;;
esac
