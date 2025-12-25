#!/bin/bash
set -e

echo "=================================================="
echo "MSN Weather Wrapper - Deployment Test Script"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Cleanup function
cleanup() {
    EXIT_CODE=$?
    echo ""
    echo -e "${BLUE}Cleaning up...${NC}"

    # Stop and remove containers
    podman-compose down 2>/dev/null || true

    # Remove generated test artifacts
    rm -rf htmlcov/ .coverage .pytest_cache/__pycache__ 2>/dev/null || true

    if [ $EXIT_CODE -ne 0 ]; then
        echo -e "${RED}✗ Deployment test failed (exit code: $EXIT_CODE)${NC}"
    else
        echo -e "${GREEN}✓ Cleanup completed${NC}"
    fi

    exit $EXIT_CODE
}

# Set trap to cleanup on exit
trap cleanup EXIT INT TERM

# Check prerequisites
echo -e "${BLUE}[1/8] Checking prerequisites...${NC}"
if ! command -v podman &> /dev/null; then
    echo "ERROR: podman is not installed"
    exit 1
fi
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 is not installed"
    exit 1
fi
if ! command -v podman-compose &> /dev/null; then
    echo "ERROR: podman-compose is not installed"
    exit 1
fi
echo -e "${GREEN}✓ All prerequisites found${NC}"
echo ""

# Clean up existing containers
echo -e "${BLUE}[2/8] Cleaning up existing containers...${NC}"
podman-compose down 2>/dev/null || true
echo -e "${GREEN}✓ Containers cleaned${NC}"
echo ""

# Set up Python virtual environment
echo -e "${BLUE}[3/8] Setting up Python virtual environment...${NC}"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}⚠ Virtual environment already exists${NC}"
fi
echo ""

# Install Python dependencies
echo -e "${BLUE}[4/8] Installing Python dependencies...${NC}"
source .venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -e ".[dev]"
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Build containers
echo -e "${BLUE}[5/8] Building containers (this may take a few minutes)...${NC}"
podman-compose build --no-cache
echo -e "${GREEN}✓ Containers built${NC}"
echo ""

# Start containers
echo -e "${BLUE}[6/8] Starting containers...${NC}"
podman-compose up -d
echo -e "${GREEN}✓ Containers started${NC}"
echo ""

# Wait for API to be ready
echo -e "${BLUE}[7/8] Waiting for API to be ready...${NC}"
echo -n "Attempting to connect"
MAX_RETRIES=30
RETRY_COUNT=0
APP_READY=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8080/api/health > /dev/null 2>&1; then
        APP_READY=true
        echo ""
        echo -e "${GREEN}✓ Application is ready${NC}"
        break
    fi
    echo -n "."
    sleep 2
    RETRY_COUNT=$((RETRY_COUNT + 1))
done

if [ "$APP_READY" = false ]; then
    echo ""
    echo -e "${YELLOW}⚠ Application not responding, attempting restart...${NC}"
    podman restart msn-weather-app
    sleep 20
    if curl -s http://localhost:8080/api/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Application is ready after restart${NC}"
    else
        echo "ERROR: Application failed to start"
        exit 1
    fi
fi
echo ""

# Run integration tests
echo -e "${BLUE}[8/8] Running integration tests...${NC}"
python -m pytest tests/test_integration.py -v -m integration --tb=short
TEST_EXIT_CODE=$?
echo ""

# Display summary
echo "=================================================="
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
else
    echo -e "${RED}✗ Some tests failed${NC}"
fi
echo "=================================================="
echo ""
echo "Services running:"
echo "  - Application: http://localhost:8080"
echo "  - API:         http://localhost:8080/api/"
echo ""
echo "To view logs:"
echo "  podman-compose logs -f"
echo ""
echo "To stop services:"
echo "  podman-compose down"
echo ""

# Exit with test result code
exit $TEST_EXIT_CODE
