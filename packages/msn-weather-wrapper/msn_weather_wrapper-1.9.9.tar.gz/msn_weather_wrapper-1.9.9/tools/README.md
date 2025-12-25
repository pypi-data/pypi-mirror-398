# Tools Directory

Shell scripts for SBOM generation and deployment testing.

---

## Scripts

### 1. `generate_sbom.sh`

**Purpose:** Comprehensive SBOM (Software Bill of Materials) generation for containers, source code, and dependencies.

**Usage:**
```bash
./tools/generate_sbom.sh
```

**What it does:**
- ✅ Checks/installs Syft 1.38.0 automatically
- ✅ Generates unified container SBOM (SPDX, CycloneDX, Table formats)
- ✅ Generates source code SBOM (SPDX, CycloneDX, Table formats)
- ✅ Generates Python package SBOM
- ✅ Creates detailed summary with statistics
- ✅ Color-coded output for easy reading

**Output directory:** `sbom_output/`

**Requirements:**
- Podman
- curl (for Syft installation)
- Unified container must be built first: `podman-compose up -d`

**Output files:**
- `container_sbom_spdx_YYYYMMDD_HHMMSS.json` - Container SPDX JSON
- `container_sbom_cyclonedx_YYYYMMDD_HHMMSS.json` - Container CycloneDX JSON
- `container_sbom_table_YYYYMMDD_HHMMSS.txt` - Container human-readable table
- `source_sbom_spdx_YYYYMMDD_HHMMSS.json` - Source SPDX JSON
- `source_sbom_cyclonedx_YYYYMMDD_HHMMSS.json` - Source CycloneDX JSON
- `source_sbom_table_YYYYMMDD_HHMMSS.txt` - Source table
- `python_packages_YYYYMMDD_HHMMSS.txt` - Python packages list
- `SBOM_SUMMARY_YYYYMMDD_HHMMSS.md` - Comprehensive summary

**Example:**
```bash
# Start containers first
podman-compose up -d

# Generate all SBOMs
./tools/generate_sbom.sh

# View summary
cat sbom_output/SBOM_SUMMARY_*.md
```

**See also:** [SYFT_GUIDE.md](../docs/SYFT_GUIDE.md) for detailed documentation

---

### 2. `generate_sbom_ci.sh`

**Purpose:** Lightweight SBOM generation optimized for CI/CD pipelines.

**Usage:**
```bash
./tools/generate_sbom_ci.sh
```

**What it does:**
- ✅ Checks/installs Syft automatically
- ✅ Generates source code SBOM (SPDX-JSON only)
- ✅ Fast execution (~30 seconds)
- ✅ No container builds required

**Output:**
- `sbom_output/source_sbom.json` - Source SBOM in SPDX format

**Use cases:**
- CI/CD pipelines (GitHub Actions, GitLab CI)
- Pre-commit hooks
- Quick vulnerability checks
- Automated security scanning

**Example in GitHub Actions:**
```yaml
- name: Generate SBOM
  run: ./tools/generate_sbom_ci.sh

- name: Scan for vulnerabilities
  run: grype sbom:sbom_output/source_sbom.json
```

**Differences from `generate_sbom.sh`:**
- ❌ No container SBOMs (faster)
- ❌ No multiple formats (SPDX only)
- ❌ No detailed summary
- ✅ Much faster execution
- ✅ No container runtime required

---

### 3. `test_deployment.sh`

**Purpose:** Automated deployment testing with containers.

**Usage:**
```bash
./tools/test_deployment.sh
```

**What it does:**
1. ✅ Checks prerequisites (podman, python3, podman-compose)
2. ✅ Cleans up existing containers
3. ✅ Sets up Python virtual environment
4. ✅ Installs dependencies
5. ✅ Starts containers with podman-compose
6. ✅ Waits for services to be ready (30 retries)
7. ✅ Tests API health endpoint
8. ✅ Runs full test suite (77 tests)
9. ✅ Shows service logs
10. ✅ Stops containers after testing

**Requirements:**
- Podman
- podman-compose
- Python 3.9+
- Internet connection (for image pulls)

**Test suite includes:**
- Unit tests (35 tests) - `tests/test_client.py`, `test_models.py`, `test_api.py`
- Security tests (25 tests) - `tests/test_security.py`
- Integration tests (17 tests) - `tests/test_integration.py`

**Example output:**
```
=================================
MSN Weather Wrapper - Deployment Test
=================================

Step 1: Checking prerequisites...
✓ podman is installed
✓ python3 is installed
✓ podman-compose is installed

Step 2: Cleaning up existing containers...
✓ Cleanup complete

Step 3: Setting up virtual environment...
✓ Virtual environment ready

Step 4: Installing dependencies...
✓ Dependencies installed

Step 5: Starting services...
✓ Services started

Step 6: Waiting for services...
✓ API is responding

Step 7: Running tests...
========================= 77 passed in 45.23s ==========================
✓ All tests passed

=================================
✓ Deployment test completed successfully!
=================================
```

**Options:**
```bash
# Keep containers running after tests
KEEP_RUNNING=1 ./tools/test_deployment.sh

# Use specific Python version
PYTHON_CMD=python3.11 ./tools/test_deployment.sh
```

---

## Quick Reference

| Script | Purpose | Duration | Requires Containers | CI-Friendly |
|--------|---------|----------|---------------------|-------------|
| `generate_sbom.sh` | Full SBOM generation | 2-5 min | Yes | No |
| `generate_sbom_ci.sh` | Quick SBOM for CI | 30 sec | No | Yes |
| `test_deployment.sh` | Full deployment test | 5-10 min | Builds them | No |

---

## Making Scripts Executable

If you get "Permission denied" errors:

```bash
chmod +x tools/generate_sbom.sh tools/generate_sbom_ci.sh tools/test_deployment.sh
```

---

## Integration Examples

### Local Development

```bash
# Quick SBOM check before commit
./tools/generate_sbom_ci.sh
grype sbom:sbom_output/source_sbom.json

# Full deployment test
./tools/test_deployment.sh
```

### GitHub Actions

```yaml
- name: Generate SBOM
  run: ./tools/generate_sbom_ci.sh

- name: Test Deployment
  run: ./tools/test_deployment.sh
```

### Pre-commit Hook

Add to `.git/hooks/pre-commit`:
```bash
#!/bin/bash
./tools/generate_sbom_ci.sh || exit 1
```

---

## Troubleshooting

### "Command not found: syft"

**Solution:** The scripts auto-install Syft. If it fails:
```bash
curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin
```

### "Cannot connect to Podman daemon"

**Solution:** Start Podman service (if using Podman Desktop):
```bash
# Or check Podman Desktop is running
podman info
```

### "Container not found"

**Solution:** Build containers first:
```bash
podman-compose up -d
```

### "Tests fail"

**Solution:** Check service logs:
```bash
podman-compose logs
```

---

## Additional Resources

- **SBOM Guide:** [docs/SYFT_GUIDE.md](../docs/SYFT_GUIDE.md)
- **API Documentation:** [docs/API.md](../docs/API.md)
- **Testing Guide:** [README.md](../README.md#testing)
- **Security:** [docs/SECURITY.md](../docs/SECURITY.md)
- **Syft Documentation:** https://github.com/anchore/syft
- **Grype Scanning:** https://github.com/anchore/grype

---

## Maintenance

### Updating Syft

Scripts use Syft 1.38.0. To update:

1. Edit script and change version:
   ```bash
   SYFT_VERSION="1.40.0"  # Update this line
   ```

2. Test the new version:
   ```bash
   ./tools/generate_sbom_ci.sh
   ```

### Adding New Scripts

When adding new scripts to this directory:

1. Make executable: `chmod +x tools/your_script.sh`
2. Add shebang: `#!/bin/bash`
3. Add documentation to this README
4. Update main project README if relevant

---

**Last Updated:** December 2, 2025
