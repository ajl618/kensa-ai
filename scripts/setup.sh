#!/bin/bash
# Setup script for AI Red Team Tester
# Creates necessary directories and sets permissions

set -e

echo "Setting up AI Red Team Tester..."

# Create required directories
mkdir -p reports
mkdir -p logs

# Set permissions for Docker volumes
chmod 777 reports logs 2>/dev/null || true

# Create example environment file if not exists
if [ ! -f .env ]; then
    cat > .env << 'EOF'
# AI Red Team Tester Environment Configuration
# Copy this file and modify as needed

# Target Configuration
TARGET_URL=http://mock-server:8080/v1/chat/completions
TARGET_API_KEY=mock-api-key
TARGET_MODEL=mock-gpt-4
TARGET_TYPE=http

# Test Configuration
TEST_PACK=basic_security
LOG_LEVEL=INFO
EVIDENCE_MODE=true

# Output Configuration
OUTPUT_FORMAT=json,html
FAIL_ON=critical

# Mock Server Mode: safe, vulnerable, mixed
MOCK_MODE=safe

# For real APIs (uncomment and set):
# OPENAI_API_KEY=sk-your-key
# ANTHROPIC_API_KEY=sk-ant-your-key
EOF
    echo "Created .env file with default configuration"
fi

echo ""
echo "Setup complete! Next steps:"
echo "  1. Build:    make build"
echo "  2. Test:     make test"
echo "  3. Demo:     make demo"
echo ""
