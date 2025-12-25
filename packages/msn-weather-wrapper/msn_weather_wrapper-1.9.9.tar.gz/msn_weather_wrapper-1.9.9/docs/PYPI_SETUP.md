# PyPI Publishing Setup Guide

Complete guide to setting up automated PyPI publishing for the MSN Weather Wrapper package.

---

## Overview

The project uses **GitHub's trusted publishing** (OIDC) for secure PyPI uploads with no stored secrets. The first release requires manual setup, but subsequent releases are fully automated.

---

## Quick Setup (First Release)

### Step 1: Create PyPI Account

1. Go to [PyPI.org](https://pypi.org/account/register/)
2. Register a new account
3. Verify your email address

### Step 2: Upload First Release Manually

The first release must be uploaded manually to claim the package name on PyPI.

```bash
# Install build tools
pip install build twine

# Build package
python -m build

# Upload to PyPI (interactive)
python -m twine upload dist/*
```

You'll be prompted for your PyPI username and password.

### Step 3: Configure Trusted Publishing (OIDC)

After the first manual upload:

1. Go to [PyPI Account Settings](https://pypi.org/manage/account/)
2. Scroll to **Publishing** section
3. Click **Add a new pending publisher**
4. Configure:
   - **PyPI Project Name**: `msn-weather-wrapper`
   - **Owner**: Your GitHub username
   - **Repository name**: `msn-weather-wrapper`
   - **Workflow name**: `publish-release.yml`
   - **Environment name**: Leave blank (or use `pypi`)
5. Click **Add**

**IMPORTANT:** The pending publisher must be confirmed from PyPI before the first automated release!

### Step 4: Verify in GitHub

Your repository is now configured for trusted publishing. No token storage needed!

---

## Automated Publishing Workflow

Once OIDC is configured, releases are fully automatic:

1. Developer creates PR with changes
2. PR merged to main
3. auto-version-release.yml triggers:
   - Determines version bump
   - Creates and merges version bump PR
   - Pushes version tag
4. publish-release.yml triggers on tag:
   - Uses OIDC to authenticate to PyPI
   - Builds Python package
   - Publishes to PyPI
   - Creates GitHub Release
5. Package available on PyPI ✅

---

## Version Management

### Conventional Commits

Use conventional commit prefixes in PR titles for automatic version bumping:

| Prefix | Type | Bump | Example |
|--------|------|------|---------|
| `feat:` | New Feature | Minor (0.X.0) | `feat: add weather alerts` |
| `fix:` | Bug Fix | Patch (0.0.X) | `fix: correct temp parsing` |
| `feat!:` | Breaking Feature | Major (X.0.0) | `feat!: redesign API` |
| `fix!:` | Breaking Fix | Major (X.0.0) | `fix!: change response format` |
| `docs:` | Documentation | Patch (0.0.X) | `docs: update README` |
| `chore:` | Maintenance | Patch (0.0.X) | `chore: update deps` |

Default: Patch version (0.0.X)

---

## Testing Before Release

### Test Locally

```bash
# Build the package
python -m build

# Verify package integrity
python -m twine check dist/*

# Optional: Test on TestPyPI first
python -m twine upload --repository testpypi dist/*
```

### Verify Package Metadata

```bash
# Check what will be published
tar -tzf dist/*.tar.gz | head -20

# Verify wheel contents
unzip -l dist/*.whl | head -20
```

---

## Troubleshooting

### OIDC Configuration Issues

**Problem:** Pending publisher not confirmed

**Solution:**

1. Go to [PyPI Account Settings](https://pypi.org/manage/account/)
2. Look for pending publishers
3. Click the pending publisher
4. Click **Confirm** to activate it

**Problem:** First automated release fails with auth error

**Solution:**

- Ensure OIDC pending publisher is confirmed (not just added)
- Wait a few minutes after confirming for caching to update
- Check `publish-release.yml` logs for specific error

### Package Upload Issues

**Problem:** Version already exists on PyPI

**Solution:**

- Versions are immutable on PyPI
- Create a new version bump (auto-version handles this)
- Cannot override or delete existing versions

**Problem:** Package name already taken

**Solution:**

- Update `project.name` in `pyproject.toml`
- Ensure uniqueness on PyPI
- Re-test with TestPyPI first

### Version Tag Issues

**Problem:** Tag not created automatically

**Solution:**

1. Check `auto-version-release.yml` logs
2. Verify version bump PR was merged
3. Manually create tag if needed:

```bash
git tag -a v1.2.3 -m "Release v1.2.3"
git push origin v1.2.3
```

---

## Manual Release Process

If automated release fails, you can manually publish:

```bash
# Build package
python -m build

# Get OIDC token (if using trusted publishing)
# This is handled automatically by the workflow
# For manual releases, use password/token auth

# Upload to PyPI
python -m twine upload dist/*

# Create GitHub release manually
gh release create v1.2.3 --title "Release v1.2.3" dist/*
```

---

## Security Best Practices

### ✅ Do

- Use **GitHub OIDC trusted publishing** (no tokens stored)
- Keep `pyproject.toml` version synchronized with git tags
- Review `publish-release.yml` logs for each release
- Test on TestPyPI before first production release
- Use conventional commits for clear version history

### ❌ Don't

- Never store PyPI tokens in GitHub secrets
- Never manually bump versions (let automation handle it)
- Never release without running full CI/CD pipeline
- Never use the same version twice

---

## Useful Commands

```bash
# Check current package version
grep '^version' pyproject.toml

# Build package locally
python -m build

# Check package contents
tar -tzf dist/*.tar.gz
unzip -l dist/*.whl

# Verify metadata
python -m twine check dist/*

# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# Upload to PyPI
python -m twine upload dist/*

# List releases
gh release list

# Check publish workflow runs
gh run list --workflow publish-release.yml
```

---

## Additional Resources

- [PyPI Documentation](https://pypi.org/help/)
- [Trusted Publishing Guide](https://docs.pypi.org/trusted-publishers/)
- [Python Packaging Guide](https://packaging.python.org/)
- [setuptools Documentation](https://setuptools.pypa.io/)
- [twine Documentation](https://twine.readthedocs.io/)

---

## Related Documentation

- [CI/CD Workflows](WORKFLOW_DIAGRAM.md) - Complete workflow documentation
- [Versioning Guide](VERSIONING.md) - Version management process
- [Development Guide](DEVELOPMENT.md) - Local development setup
