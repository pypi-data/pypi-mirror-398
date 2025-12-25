# Syft Integration for MSN Weather Wrapper

## Overview

This project includes comprehensive Software Bill of Materials (SBOM) generation using [Syft](https://github.com/anchore/syft) by Anchore. SBOMs provide detailed inventories of all software components, dependencies, and metadata.

## What is Syft?

Syft is a CLI tool and Go library for generating SBOMs from container images and filesystems. It supports multiple output formats including:
- **SPDX** (Software Package Data Exchange)
- **CycloneDX**
- **Syft JSON**
- **Table** (human-readable)

## Quick Start

### Generate All SBOMs

```bash
./tools/generate_sbom.sh
```

This will:
1. Check/install Syft automatically
2. Generate SBOMs for unified container (API + Frontend + Nginx)
3. Generate SBOMs for source code
4. Generate SBOMs for Python packages
5. Create a summary report

### View Results

```bash
# View summary
cat sbom_output/SBOM_SUMMARY_*.md

# View API packages (table format)
cat sbom_output/api_sbom_table_*.txt

# View frontend packages
cat sbom_output/frontend_sbom_table_*.txt
```

## Installation

### Automatic Installation

The `tools/generate_sbom.sh` script will automatically install Syft if not found.

### Manual Installation

**macOS:**
```bash
brew install syft
```

**Linux:**
```bash
curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin
```

**Windows (WSL):**
```bash
curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin
```

**Verify Installation:**
```bash
syft version
```

## Scripts

### 1. `generate_sbom.sh` - Full SBOM Generation

Complete SBOM generation with multiple formats and comprehensive analysis.

```bash
./tools/generate_sbom.sh
```

**Generates:**
- Unified container SBOMs (SPDX, CycloneDX, Table)
- Source code SBOMs (SPDX, CycloneDX, Table)
- Python packages SBOMs (SPDX, Table)
- Summary report in Markdown

**Output Directory:** `sbom_output/`

### 2. `generate_sbom_ci.sh` - CI/CD Optimized

Lightweight script for CI/CD pipelines.

```bash
./generate_sbom_ci.sh
```

**Environment Variables:**
```bash
# Customize output directory
SBOM_DIR=artifacts/sboms ./generate_sbom_ci.sh

# Change output format
FORMAT=cyclonedx-json ./generate_sbom_ci.sh
```

## Output Formats

### SPDX JSON (`*_spdx_*.json`)
Industry-standard SBOM format, widely supported for compliance and security scanning.

```bash
# Parse with jq
jq '.packages[] | {name: .name, version: .versionInfo}' sbom_output/api_sbom_spdx_*.json
```

### CycloneDX JSON (`*_cyclonedx_*.json`)
Modern SBOM standard optimized for security use cases.

```bash
# View components
jq '.components[] | {name: .name, version: .version}' sbom_output/api_sbom_cyclonedx_*.json
```

### Table Format (`*_table_*.txt`)
Human-readable format for quick review.

```bash
# View directly
cat sbom_output/api_sbom_table_*.txt
```

## Use Cases

### 1. Vulnerability Scanning

Feed SBOMs into vulnerability scanners like Grype:

```bash
# Generate SBOM
./tools/generate_sbom.sh

# Scan for vulnerabilities
grype sbom:sbom_output/api_sbom_spdx_*.json
```

### 2. License Compliance

Analyze software licenses:

```bash
# Extract license information
jq '.packages[] | {name: .name, license: .licenseDeclared}' sbom_output/api_sbom_spdx_*.json
```

### 3. Dependency Tracking

Monitor dependencies across releases:

```bash
# Compare SBOMs
diff <(jq -S '.packages[].name' sbom_v1.json) \
     <(jq -S '.packages[].name' sbom_v2.json)
```

### 4. Supply Chain Security

Track and verify all software components:

```bash
# List all Python packages
jq '.packages[] | select(.name | startswith("python")) | .name' sbom_output/api_sbom_spdx_*.json
```

## Manual SBOM Generation

### Scan Container Images

```bash
# SPDX format
syft localhost/msn-weather-wrapper:latest -o spdx-json > container_sbom.json

# CycloneDX format
syft localhost/msn-weather-wrapper:latest -o cyclonedx-json > container_sbom.json

# Table format (human-readable)
syft localhost/msn-weather-wrapper:latest -o table

# Syft JSON (most detailed)
syft localhost/msn-weather-wrapper:latest -o syft-json > container_sbom.json
```

### Scan Directories

```bash
# Scan entire project
syft dir:. -o spdx-json > project_sbom.json

# Scan specific directory
syft dir:./src -o table

# Scan Python virtual environment
syft dir:./.venv -o spdx-json > venv_sbom.json
```

### Scan Archives

```bash
# Scan tar archive
syft file:archive.tar.gz -o spdx-json

# Scan zip file
syft file:package.zip -o table
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Generate SBOM

on:
  push:
    branches: [main]
  release:
    types: [created]

jobs:
  sbom:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Syft
        run: |
          curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin

      - name: Build containers
        run: podman-compose build

      - name: Generate SBOMs
        run: ./generate_sbom_ci.sh

      - name: Upload SBOMs
        uses: actions/upload-artifact@v4
        with:
          name: sboms
          path: sbom_output/

      - name: Scan for vulnerabilities
        run: |
          curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin
          grype sbom:sbom_output/api_sbom_*.json
```

### GitLab CI

```yaml
generate-sbom:
  stage: build
  image: ubuntu:latest
  script:
    - apt-get update && apt-get install -y curl podman
    - curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin
    - podman-compose build
    - ./generate_sbom_ci.sh
  artifacts:
    paths:
      - sbom_output/
    expire_in: 30 days
```

### Jenkins

```groovy
pipeline {
    agent any
    stages {
        stage('Generate SBOM') {
            steps {
                sh '''
                    curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin
                    ./generate_sbom_ci.sh
                '''
                archiveArtifacts artifacts: 'sbom_output/**', fingerprint: true
            }
        }
    }
}
```

## Advanced Usage

### Custom Catalogers

```bash
# Only catalog Python packages
syft dir:. --catalogers python -o table

# Only catalog OS packages
syft localhost/msn-weather-wrapper_api:latest --catalogers dpkg,apk -o table
```

### Filtering Output

```bash
# Exclude specific paths
syft dir:. --exclude './node_modules/**' --exclude './.git/**' -o spdx-json

# Include only specific file types
syft dir:. --select-catalogers python,javascript -o table
```

### Output to Multiple Formats

```bash
# Generate multiple formats at once
syft localhost/msn-weather-wrapper:latest \
  -o spdx-json=container_spdx.json \
  -o cyclonedx-json=container_cyclonedx.json \
  -o table=container_table.txt
```

## Best Practices

### 1. Generate SBOMs on Every Build

Automate SBOM generation in your CI/CD pipeline to maintain up-to-date inventories.

### 2. Store SBOMs with Releases

Archive SBOMs alongside release artifacts for compliance and auditing.

### 3. Version Control SBOMs

Track changes to dependencies by committing representative SBOMs.

### 4. Regular Vulnerability Scanning

Combine Syft with Grype for continuous vulnerability monitoring:

```bash
# Generate and scan
./tools/generate_sbom.sh
grype sbom:sbom_output/container_sbom_spdx_*.json --fail-on high
```

### 5. License Auditing

Review licenses regularly:

```bash
jq '.packages[] | select(.licenseDeclared != null) | {name: .name, license: .licenseDeclared}' \
  sbom_output/api_sbom_spdx_*.json | sort -u
```

## Troubleshooting

### Syft Not Found

```bash
# Install manually
curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin

# Add to PATH
export PATH=$PATH:/usr/local/bin
```

### Container Not Found

```bash
# Build containers first
podman-compose build

# Verify images exist
podman images | grep msn-weather
```

### Permission Denied

```bash
# Make scripts executable
chmod +x tools/generate_sbom.sh tools/generate_sbom_ci.sh
```

### Large SBOM Files

```bash
# Compress SBOMs
gzip sbom_output/*.json

# View compressed SBOM
zcat sbom_output/api_sbom_spdx_*.json.gz | jq '.packages[].name'
```

## Output Structure

```
sbom_output/
├── container_sbom_spdx_YYYYMMDD_HHMMSS.json       # Container SPDX SBOM
├── container_sbom_cyclonedx_YYYYMMDD_HHMMSS.json  # Container CycloneDX SBOM
├── container_sbom_table_YYYYMMDD_HHMMSS.txt       # Container Table SBOM
├── source_sbom_spdx_YYYYMMDD_HHMMSS.json          # Source SPDX SBOM
├── source_sbom_cyclonedx_YYYYMMDD_HHMMSS.json     # Source CycloneDX SBOM
├── source_sbom_table_YYYYMMDD_HHMMSS.txt          # Source Table SBOM
├── python_packages_sbom_spdx_YYYYMMDD_HHMMSS.json # Python SPDX SBOM
├── python_packages_sbom_table_YYYYMMDD_HHMMSS.txt # Python Table SBOM
└── SBOM_SUMMARY_YYYYMMDD_HHMMSS.md                # Summary Report
```

## Resources

- [Syft GitHub Repository](https://github.com/anchore/syft)
- [Syft Documentation](https://github.com/anchore/syft#syft)
- [SPDX Specification](https://spdx.dev/)
- [CycloneDX Standard](https://cyclonedx.org/)
- [NTIA SBOM Minimum Elements](https://www.ntia.gov/report/2021/minimum-elements-software-bill-materials-sbom)
- [Grype Vulnerability Scanner](https://github.com/anchore/grype)

## Support

For issues or questions:
- Syft Issues: https://github.com/anchore/syft/issues
- Project Issues: https://github.com/yourusername/msn-weather-wrapper/issues
