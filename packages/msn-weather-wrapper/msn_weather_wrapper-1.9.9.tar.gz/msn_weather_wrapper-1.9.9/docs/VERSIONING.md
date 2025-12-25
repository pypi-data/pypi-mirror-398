# Semantic Versioning Guide

This project follows [Semantic Versioning 2.0.0](https://semver.org/).

## Automated Versioning (Primary Method)

**The project uses automated PR-based versioning** where every merged pull request automatically increments the version and publishes to PyPI. See [AUTOMATED_VERSIONING.md](AUTOMATED_VERSIONING.md) for the complete guide.

**Quick summary:**
- PR labels, title, or branch prefix determine version bump type
- Major (breaking changes): `major`, `breaking` labels or `feat!:` title
- Minor (new features): `minor`, `feature` labels or `feat:` title
- Patch (bug fixes): `patch`, `fix` labels or `fix:` title (default)

## Manual Release Process (Alternative)

If you need to release manually without the automated system:

## Version Format

```
MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]
```

- **MAJOR**: Breaking API changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)
- **PRERELEASE**: alpha, beta, rc (optional)
- **BUILD**: Build metadata (optional)

## Release Process

### Automated Release (Primary Method)

The project uses automated PR-based versioning. When a PR is merged to main:

1. **Auto-Version Workflow Triggers**
   - `auto-version-release.yml` automatically runs
   - Determines version bump from PR labels, title, or branch prefix

2. **Version Bump PR Created**
   - The workflow creates a PR with version updates
   - Updates `pyproject.toml` and `CHANGELOG.md`
   - Auto-merge is enabled

3. **Automatic Tag Creation**
   - When the version bump PR merges, a git tag is created (e.g., `v1.2.3`)

4. **CI/CD Pipeline Runs Automatically**
   - Build Python package
   - Publish to PyPI
   - Build container images
   - Generate SBOM
   - Create GitHub Release with artifacts

See [AUTOMATED_VERSIONING.md](AUTOMATED_VERSIONING.md) for complete details.

### Manual Release Process

If you need to release manually:

### 1. Update Version

Edit `pyproject.toml`:

```toml
[project]
version = "1.2.3"  # Update this line
```

### 2. Update Changelog

Edit `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com/):

```markdown
## [1.2.3] - 2024-01-15

### Added
- New feature descriptions

### Changed
- Modified behavior descriptions

### Fixed
- Bug fix descriptions

### Security
- Security fix descriptions
```

### 3. Commit Changes

```bash
git add pyproject.toml CHANGELOG.md
git commit -m "chore: bump version to 1.2.3"
git push origin main
```

### 4. Create Release Tag (Manual Process Only)

**Note**: This step is automated when using the Automated Release workflow.

```bash
# Create annotated tag
git tag -a v1.2.3 -m "Release version 1.2.3"

# Push tag to trigger release
git push origin v1.2.3
```

### 5. Automated CI/CD Pipeline

The CI/CD pipeline will automatically:

1. **Validate version** - Verifies tag matches `pyproject.toml`
2. **Run tests** - Ensures all tests pass
3. **Build package** - Creates wheel and source distribution
4. **Publish to PyPI** - Uploads package automatically
5. **Build containers** - Creates multi-platform images with semantic version tags:
   - `ghcr.io/owner/repo:1.2.3` (exact version)
   - `ghcr.io/owner/repo:1.2` (minor version)
   - `ghcr.io/owner/repo:1` (major version)
   - `ghcr.io/owner/repo:latest` (if not a prerelease)
6. **Create GitHub Release** - Publishes release with artifacts

## Version Increment Guidelines

### MAJOR Version (X.0.0)

Increment when making **breaking changes**:

- Removing endpoints or parameters
- Changing response formats
- Renaming models or fields
- Changing error codes
- Removing deprecated features
- Changing authentication methods

**Example:**

```python
# Before (v1.x.x)
@app.route('/weather/<city>')
def get_weather(city):
    return {"city": city, "temp": 20}

# After (v2.0.0) - Breaking change: response format changed
@app.route('/weather/<city>')
def get_weather(city):
    return {"location": {"name": city}, "current": {"temperature": 20}}
```

### MINOR Version (0.X.0)

Increment when adding **new features** (backward compatible):

- Adding new endpoints
- Adding optional parameters
- Adding new response fields (without removing old ones)
- Adding new models
- Deprecating features (but not removing)
- Performance improvements

**Example:**

```python
# v1.1.0 - Added new optional parameter
@app.route('/weather/<city>')
def get_weather(city, units='metric'):  # New optional parameter
    return {"city": city, "temp": 20, "units": units}
```

### PATCH Version (0.0.X)

Increment when fixing **bugs** (backward compatible):

- Bug fixes
- Documentation fixes
- Internal refactoring
- Security patches
- Dependency updates (patch level)

**Example:**

```python
# v1.0.1 - Bug fix
@app.route('/weather/<city>')
def get_weather(city):
    city = city.strip()  # Fix: handle whitespace in city names
    return {"city": city, "temp": 20}
```

## Prerelease Versions

Use prerelease identifiers for testing:

### Alpha (Early Testing)

```bash
# First alpha of v1.2.0
git tag -a v1.2.0-alpha.1 -m "Alpha release 1 for v1.2.0"
```

- Unstable, may have missing features
- For internal testing only
- Not recommended for production

### Beta (Feature Complete)

```bash
# First beta of v1.2.0
git tag -a v1.2.0-beta.1 -m "Beta release 1 for v1.2.0"
```

- Feature complete but may have bugs
- For wider testing
- Not recommended for production

### Release Candidate (Final Testing)

```bash
# First release candidate for v1.2.0
git tag -a v1.2.0-rc.1 -m "Release candidate 1 for v1.2.0"
```

- Nearly production-ready
- Only critical bug fixes
- Ready for production testing

## Container Image Tags

The Docker workflow automatically creates multiple tags:

| Tag Pattern | Example | Purpose |
|-------------|---------|---------|
| `X.Y.Z` | `1.2.3` | Exact version (immutable) |
| `X.Y` | `1.2` | Latest patch in minor version |
| `X` | `1` | Latest minor in major version |
| `latest` | `latest` | Latest stable release |
| `X.Y.Z-alpha.N` | `1.2.0-alpha.1` | Alpha prerelease |
| `X.Y.Z-beta.N` | `1.2.0-beta.1` | Beta prerelease |
| `X.Y.Z-rc.N` | `1.2.0-rc.1` | Release candidate |

### Usage Examples

```bash
# Pin to exact version (recommended for production)
docker pull ghcr.io/owner/msn-weather-wrapper:1.2.3

# Use latest patch version (auto-updates with patches)
docker pull ghcr.io/owner/msn-weather-wrapper:1.2

# Use latest minor version (auto-updates with new features)
docker pull ghcr.io/owner/msn-weather-wrapper:1

# Use latest stable (not recommended for production)
docker pull ghcr.io/owner/msn-weather-wrapper:latest

# Test prerelease
docker pull ghcr.io/owner/msn-weather-wrapper:1.2.0-rc.1
```

## PyPI Publishing

Packages are automatically published to PyPI on tagged releases.

### Required Secret

Configure the `PYPI_TOKEN` secret in your repository:

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Name: `PYPI_TOKEN`
4. Value: Your PyPI API token
5. Click **Add secret**

### Getting a PyPI Token

1. Go to [PyPI Account Settings](https://pypi.org/manage/account/)
2. Scroll to **API tokens**
3. Click **Add API token**
4. Name: `msn-weather-wrapper-github-actions`
5. Scope: **Project: msn-weather-wrapper** (after first manual upload) or **Entire account**
6. Click **Add token**
7. Copy the token (starts with `pypi-`)

### First Release Setup

For the first release, you need to manually upload a package to claim the project name:

```bash
# Build package
python -m build

# Upload to PyPI (you'll be prompted for credentials)
python -m twine upload dist/*
```

After the first manual upload, all subsequent releases will be automated.

## Version Validation

The CI/CD pipeline validates:

1. **Tag format** - Must match `vX.Y.Z` or `vX.Y.Z-prerelease.N`
2. **Version consistency** - Tag must match `pyproject.toml` version
3. **Semantic versioning** - Follows semver rules
4. **Unique version** - Version doesn't exist on PyPI

If validation fails, the release is aborted with a clear error message.

## Troubleshooting

### Version Mismatch Error

```
Error: Version mismatch!
Git tag: v1.2.3
pyproject.toml: 1.2.2
Please update pyproject.toml version to match the tag
```

**Solution:** Update `pyproject.toml` to match the tag:

```bash
# Fix the version
vim pyproject.toml  # Change version to 1.2.3

# Amend the commit
git add pyproject.toml
git commit --amend --no-edit
git push origin main --force

# Delete and recreate the tag
git tag -d v1.2.3
git push origin :refs/tags/v1.2.3
git tag -a v1.2.3 -m "Release version 1.2.3"
git push origin v1.2.3
```

### PyPI Upload Fails

**Check:**

1. Is `PYPI_TOKEN` configured correctly?
2. Does the version already exist on PyPI?
3. Is the package name available?

**Test locally:**

```bash
# Build package
python -m build

# Check package validity
python -m twine check dist/*

# Upload to TestPyPI first
python -m twine upload --repository testpypi dist/*
```

### Container Build Fails

**Check:**

1. Does the Containerfile exist?
2. Are there syntax errors in the Containerfile?
3. Check the Docker workflow logs for details

## Best Practices

1. **Never reuse versions** - Once published, a version is immutable
2. **Test prereleases** - Use alpha/beta/rc for testing
3. **Update changelog** - Document all changes before releasing
4. **Pin dependencies** - Use exact versions in production
5. **Automate everything** - Let CI/CD handle releases
6. **Validate locally** - Test builds before pushing tags
7. **Communicate changes** - Write clear release notes

## Examples

### Patch Release (Bug Fix)

```bash
# 1. Fix the bug
vim src/msn_weather_wrapper/client.py

# 2. Update version
vim pyproject.toml  # 1.0.0 → 1.0.1

# 3. Update changelog
vim CHANGELOG.md
# Add:
# ## [1.0.1] - 2024-01-15
# ### Fixed
# - Fixed city name whitespace handling

# 4. Commit and tag
git add .
git commit -m "fix: handle whitespace in city names"
git push origin main
git tag -a v1.0.1 -m "Release version 1.0.1"
git push origin v1.0.1
```

### Minor Release (New Feature)

```bash
# 1. Implement feature
vim src/msn_weather_wrapper/client.py

# 2. Update version
vim pyproject.toml  # 1.0.1 → 1.1.0

# 3. Update changelog
vim CHANGELOG.md
# Add:
# ## [1.1.0] - 2024-01-20
# ### Added
# - Added forecast endpoint with 7-day predictions

# 4. Commit and tag
git add .
git commit -m "feat: add 7-day weather forecast endpoint"
git push origin main
git tag -a v1.1.0 -m "Release version 1.1.0"
git push origin v1.1.0
```

### Major Release (Breaking Change)

```bash
# 1. Implement breaking changes
vim src/msn_weather_wrapper/client.py

# 2. Update version
vim pyproject.toml  # 1.1.0 → 2.0.0

# 3. Update changelog
vim CHANGELOG.md
# Add:
# ## [2.0.0] - 2024-02-01
# ### Changed
# - **BREAKING**: Changed response format for weather endpoints
# - **BREAKING**: Renamed `temp` field to `temperature`
# - See MIGRATION.md for upgrade guide

# 4. Create migration guide
vim docs/MIGRATION.md

# 5. Commit and tag
git add .
git commit -m "feat!: redesign API response format"
git push origin main
git tag -a v2.0.0 -m "Release version 2.0.0"
git push origin v2.0.0
```

## References

- [Semantic Versioning 2.0.0](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [PyPI Publishing Guide](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
