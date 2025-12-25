#!/usr/bin/env bash

# CI/CD SBOM Generation Script
# Optimized for automated pipelines

set -e

SBOM_DIR="${SBOM_DIR:-sbom_output}"
FORMAT="${FORMAT:-spdx-json}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "=== CI/CD SBOM Generation ==="
echo "Format: $FORMAT"
echo "Output: $SBOM_DIR"
echo ""

# Check if syft is installed
if ! command -v syft &> /dev/null; then
    echo "Installing Syft..."
    curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin
fi

# Create output directory
mkdir -p "$SBOM_DIR"

# Generate SBOMs based on what's available
if podman images -q localhost/msn-weather-wrapper_api:latest &> /dev/null; then
    echo "Generating API SBOM..."
    syft localhost/msn-weather-wrapper_api:latest -o "$FORMAT" > "$SBOM_DIR/api_sbom_${TIMESTAMP}.json"
    echo "✓ API SBOM generated"
fi

if podman images -q localhost/msn-weather-wrapper_frontend:latest &> /dev/null; then
    echo "Generating Frontend SBOM..."
    syft localhost/msn-weather-wrapper_frontend:latest -o "$FORMAT" > "$SBOM_DIR/frontend_sbom_${TIMESTAMP}.json"
    echo "✓ Frontend SBOM generated"
fi

# Always generate source SBOM
echo "Generating Source SBOM..."
syft dir:. -o "$FORMAT" > "$SBOM_DIR/source_sbom_${TIMESTAMP}.json"
echo "✓ Source SBOM generated"

echo ""
echo "SBOMs generated in: $SBOM_DIR"
ls -lh "$SBOM_DIR"/*${TIMESTAMP}*
