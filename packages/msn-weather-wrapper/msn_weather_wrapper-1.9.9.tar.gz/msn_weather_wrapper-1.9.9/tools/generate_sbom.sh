#!/usr/bin/env bash

# SBOM Generation Script using Syft
# This script generates Software Bill of Materials for the MSN Weather Wrapper project

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Output directory for SBOMs
SBOM_DIR="sbom_output"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo -e "${BLUE}=== MSN Weather Wrapper SBOM Generator ===${NC}\n"

# Function to check if syft is installed
check_syft() {
    if ! command -v syft &> /dev/null; then
        echo -e "${RED}✗ Syft is not installed${NC}"
        echo -e "${YELLOW}Installing Syft...${NC}\n"

        # Install syft
        curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin

        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Syft installed successfully${NC}\n"
        else
            echo -e "${RED}✗ Failed to install Syft${NC}"
            echo -e "${YELLOW}Please install manually: https://github.com/anchore/syft#installation${NC}"
            exit 1
        fi
    else
        echo -e "${GREEN}✓ Syft is installed${NC}"
        syft version
        echo ""
    fi
}

# Function to create output directory
setup_output_dir() {
    mkdir -p "$SBOM_DIR"
    echo -e "${GREEN}✓ Output directory: $SBOM_DIR${NC}\n"
}

# Function to check if containers exist
check_containers() {
    echo -e "${BLUE}[1/7] Checking for containers...${NC}"

    API_EXISTS=$(podman images -q localhost/msn-weather-wrapper_api:latest 2>/dev/null)
    FRONTEND_EXISTS=$(podman images -q localhost/msn-weather-wrapper_frontend:latest 2>/dev/null)

    if [ -z "$API_EXISTS" ] || [ -z "$FRONTEND_EXISTS" ]; then
        echo -e "${YELLOW}⚠ Containers not found. Building...${NC}"
        podman-compose build
    else
        echo -e "${GREEN}✓ Containers found${NC}"
    fi
    echo ""
}

# Function to generate SBOM for API container
generate_api_sbom() {
    echo -e "${BLUE}[2/7] Generating SBOM for API container...${NC}"

    # SPDX JSON format
    syft localhost/msn-weather-wrapper_api:latest -o spdx-json > "$SBOM_DIR/api_sbom_spdx_${TIMESTAMP}.json"
    echo -e "${GREEN}✓ Generated: api_sbom_spdx_${TIMESTAMP}.json${NC}"

    # CycloneDX JSON format
    syft localhost/msn-weather-wrapper_api:latest -o cyclonedx-json > "$SBOM_DIR/api_sbom_cyclonedx_${TIMESTAMP}.json"
    echo -e "${GREEN}✓ Generated: api_sbom_cyclonedx_${TIMESTAMP}.json${NC}"

    # Human-readable table format
    syft localhost/msn-weather-wrapper_api:latest -o table > "$SBOM_DIR/api_sbom_table_${TIMESTAMP}.txt"
    echo -e "${GREEN}✓ Generated: api_sbom_table_${TIMESTAMP}.txt${NC}"
    echo ""
}

# Function to generate SBOM for Frontend container
generate_frontend_sbom() {
    echo -e "${BLUE}[3/7] Generating SBOM for Frontend container...${NC}"

    # SPDX JSON format
    syft localhost/msn-weather-wrapper_frontend:latest -o spdx-json > "$SBOM_DIR/frontend_sbom_spdx_${TIMESTAMP}.json"
    echo -e "${GREEN}✓ Generated: frontend_sbom_spdx_${TIMESTAMP}.json${NC}"

    # CycloneDX JSON format
    syft localhost/msn-weather-wrapper_frontend:latest -o cyclonedx-json > "$SBOM_DIR/frontend_sbom_cyclonedx_${TIMESTAMP}.json"
    echo -e "${GREEN}✓ Generated: frontend_sbom_cyclonedx_${TIMESTAMP}.json${NC}"

    # Human-readable table format
    syft localhost/msn-weather-wrapper_frontend:latest -o table > "$SBOM_DIR/frontend_sbom_table_${TIMESTAMP}.txt"
    echo -e "${GREEN}✓ Generated: frontend_sbom_table_${TIMESTAMP}.txt${NC}"
    echo ""
}

# Function to generate SBOM for source directory
generate_source_sbom() {
    echo -e "${BLUE}[4/7] Generating SBOM for source code...${NC}"

    # Scan the entire project directory
    syft dir:. -o spdx-json > "$SBOM_DIR/source_sbom_spdx_${TIMESTAMP}.json"
    echo -e "${GREEN}✓ Generated: source_sbom_spdx_${TIMESTAMP}.json${NC}"

    syft dir:. -o cyclonedx-json > "$SBOM_DIR/source_sbom_cyclonedx_${TIMESTAMP}.json"
    echo -e "${GREEN}✓ Generated: source_sbom_cyclonedx_${TIMESTAMP}.json${NC}"

    syft dir:. -o table > "$SBOM_DIR/source_sbom_table_${TIMESTAMP}.txt"
    echo -e "${GREEN}✓ Generated: source_sbom_table_${TIMESTAMP}.txt${NC}"
    echo ""
}

# Function to generate Python package SBOM
generate_python_sbom() {
    echo -e "${BLUE}[5/7] Generating SBOM for Python packages...${NC}"

    # Create virtual environment if it doesn't exist
    if [ ! -d ".venv" ]; then
        echo -e "${YELLOW}Creating virtual environment...${NC}"
        python3 -m venv .venv
        source .venv/bin/activate
        pip install -e ".[dev]"
    else
        source .venv/bin/activate
    fi

    # Generate SBOM from installed packages
    syft dir:.venv -o spdx-json > "$SBOM_DIR/python_packages_sbom_spdx_${TIMESTAMP}.json"
    echo -e "${GREEN}✓ Generated: python_packages_sbom_spdx_${TIMESTAMP}.json${NC}"

    syft dir:.venv -o table > "$SBOM_DIR/python_packages_sbom_table_${TIMESTAMP}.txt"
    echo -e "${GREEN}✓ Generated: python_packages_sbom_table_${TIMESTAMP}.txt${NC}"

    deactivate
    echo ""
}

# Function to generate summary report
generate_summary() {
    echo -e "${BLUE}[6/7] Generating summary report...${NC}"

    cat > "$SBOM_DIR/SBOM_SUMMARY_${TIMESTAMP}.md" << EOF
# SBOM Generation Summary

**Project:** MSN Weather Wrapper
**Generated:** $(date)
**Syft Version:** $(syft version | head -1)

## Generated Files

### API Container
- \`api_sbom_spdx_${TIMESTAMP}.json\` - SPDX JSON format
- \`api_sbom_cyclonedx_${TIMESTAMP}.json\` - CycloneDX JSON format
- \`api_sbom_table_${TIMESTAMP}.txt\` - Human-readable table

### Frontend Container
- \`frontend_sbom_spdx_${TIMESTAMP}.json\` - SPDX JSON format
- \`frontend_sbom_cyclonedx_${TIMESTAMP}.json\` - CycloneDX JSON format
- \`frontend_sbom_table_${TIMESTAMP}.txt\` - Human-readable table

### Source Code
- \`source_sbom_spdx_${TIMESTAMP}.json\` - SPDX JSON format
- \`source_sbom_cyclonedx_${TIMESTAMP}.json\` - CycloneDX JSON format
- \`source_sbom_table_${TIMESTAMP}.txt\` - Human-readable table

### Python Packages
- \`python_packages_sbom_spdx_${TIMESTAMP}.json\` - SPDX JSON format
- \`python_packages_sbom_table_${TIMESTAMP}.txt\` - Human-readable table

## Quick Stats

### API Container Packages
\`\`\`
$(grep -c '"name":' "$SBOM_DIR/api_sbom_spdx_${TIMESTAMP}.json" 2>/dev/null || echo "N/A") packages detected
\`\`\`

### Frontend Container Packages
\`\`\`
$(grep -c '"name":' "$SBOM_DIR/frontend_sbom_spdx_${TIMESTAMP}.json" 2>/dev/null || echo "N/A") packages detected
\`\`\`

## Usage

### Viewing SBOMs
- **JSON formats**: Use \`jq\` for parsing and analysis
- **Table formats**: View directly with \`cat\` or text editor

### Integration
- **Supply Chain Security**: Import JSON SBOMs into vulnerability scanners
- **Compliance**: Use for software composition analysis and license compliance
- **Dependency Tracking**: Monitor dependencies across releases

### Example Commands
\`\`\`bash
# View API packages in table format
cat $SBOM_DIR/api_sbom_table_${TIMESTAMP}.txt

# Parse with jq
jq '.packages[] | {name: .name, version: .versionInfo}' $SBOM_DIR/api_sbom_spdx_${TIMESTAMP}.json

# Find specific package
jq '.packages[] | select(.name=="flask")' $SBOM_DIR/api_sbom_spdx_${TIMESTAMP}.json
\`\`\`

## Next Steps

1. **Vulnerability Scanning**: Feed SBOMs into Grype or other vulnerability scanners
2. **License Compliance**: Analyze licenses with SBOM-aware tools
3. **Dependency Updates**: Track outdated packages
4. **CI/CD Integration**: Automate SBOM generation in your pipeline

## Resources

- [Syft Documentation](https://github.com/anchore/syft)
- [SPDX Specification](https://spdx.dev/)
- [CycloneDX Standard](https://cyclonedx.org/)
EOF

    echo -e "${GREEN}✓ Generated: SBOM_SUMMARY_${TIMESTAMP}.md${NC}"
    echo ""
}

# Function to display results
display_results() {
    echo -e "${BLUE}[7/7] SBOM Generation Complete!${NC}\n"

    echo -e "${GREEN}═══════════════════════════════════════${NC}"
    echo -e "${GREEN}           Generated Files             ${NC}"
    echo -e "${GREEN}═══════════════════════════════════════${NC}"
    ls -lh "$SBOM_DIR"/*${TIMESTAMP}* | awk '{print $9, "(" $5 ")"}'
    echo ""

    echo -e "${BLUE}Summary report: $SBOM_DIR/SBOM_SUMMARY_${TIMESTAMP}.md${NC}"
    echo ""

    echo -e "${YELLOW}Quick View Commands:${NC}"
    echo -e "  cat $SBOM_DIR/api_sbom_table_${TIMESTAMP}.txt"
    echo -e "  cat $SBOM_DIR/frontend_sbom_table_${TIMESTAMP}.txt"
    echo -e "  cat $SBOM_DIR/SBOM_SUMMARY_${TIMESTAMP}.md"
    echo ""
}

# Main execution
main() {
    check_syft
    setup_output_dir
    check_containers
    generate_api_sbom
    generate_frontend_sbom
    generate_source_sbom
    generate_python_sbom
    generate_summary
    display_results

    echo -e "${GREEN}✓ All SBOMs generated successfully!${NC}"
}

# Run main function
main "$@"
