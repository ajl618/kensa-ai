#!/bin/bash
# Quick verification script for AI Red Team Tester
# Run: ./scripts/verify.sh

set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║        AI Red Team Tester - Quick Verification                ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    exit 1
fi
echo "✓ Docker is available"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed"
    exit 1
fi
echo "✓ Docker Compose is available"

echo ""
echo "Building images..."
docker-compose build --quiet

echo ""
echo "Running validation..."
docker-compose run --rm validate

echo ""
echo "Running unit tests..."
docker-compose run --rm test

echo ""
echo "Starting mock server..."
docker-compose up -d mock-server
sleep 3

echo ""
echo "Running integration tests..."
docker-compose run --rm integration-test
result=$?

echo ""
echo "Stopping mock server..."
docker-compose stop mock-server

echo ""
if [ $result -eq 0 ]; then
    echo "═══════════════════════════════════════════════════════════════"
    echo "✓ All verification steps completed successfully!"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
    echo "Next steps:"
    echo "  1. Run demo:      make demo"
    echo "  2. View reports:  make report-viewer"
    echo "  3. Run tests:     make run-basic"
    echo ""
else
    echo "═══════════════════════════════════════════════════════════════"
    echo "✗ Some verification steps failed"
    echo "═══════════════════════════════════════════════════════════════"
    exit 1
fi
