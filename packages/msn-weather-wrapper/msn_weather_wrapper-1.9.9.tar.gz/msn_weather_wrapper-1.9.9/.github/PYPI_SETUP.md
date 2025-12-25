# PyPI Publishing Setup

This guide helps you configure automated PyPI publishing for the first release.

## Quick Setup (5 minutes)

### 1. Create PyPI Account

1. Go to [PyPI](https://pypi.org/account/register/)
2. Register a new account
3. Verify your email

### 2. First Manual Upload

The first release **must** be uploaded manually to claim the package name on PyPI.

```bash
# Install build tools
pip install build twine

# Build package
python -m build

# Upload to PyPI (you'll be prompted for username/password)
python -m twine upload dist/*
```

Enter your PyPI username and password when prompted.

### 3. Create API Token

After the first upload:

1. Go to [PyPI Account Settings](https://pypi.org/manage/account/)
2. Scroll to **API tokens** section
3. Click **Add API token**
4. Configure:
   - **Token name**: `msn-weather-wrapper-github-actions`
   - **Scope**: **Project: msn-weather-wrapper** (select the project)
5. Click **Add token**
6. **Copy the token** (starts with `pypi-`)
   - ⚠️ Save it now - you won't see it again!

### 4. Add Token to GitHub

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Configure:
   - **Name**: `PYPI_TOKEN`
   - **Secret**: Paste the PyPI token
5. Click **Add secret**

### 5. Configure PyPI Environment (Optional but Recommended)

For additional security:

1. Go to **Settings** → **Environments**
2. Click **New environment**
3. Name: `pypi`
4. Configure protection rules:
   - ✅ Required reviewers (optional)
   - ✅ Wait timer (optional)
5. Click **Save protection rules**

This environment is already configured in `.github/workflows/ci.yml`.

## Testing the Setup

### Test Locally

```bash
# Build the package
python -m build

# Check package
python -m twine check dist/*

# Upload to TestPyPI (test first!)
python -m twine upload --repository testpypi dist/*
```

### Test Automated Release

Create a test release:

```bash
# Update version in pyproject.toml to 1.0.0-beta.1
vim pyproject.toml

# Commit
git add pyproject.toml
git commit -m "chore: prepare beta release"
git push origin main

# Create tag
git tag -a v1.0.0-beta.1 -m "Beta release for testing"
git push origin v1.0.0-beta.1
```

Check the GitHub Actions workflow to see if it completes successfully.

## Troubleshooting

### Token Not Working

**Symptoms:**
- `403 Forbidden` errors
- `Invalid or expired token`

**Solutions:**
1. Verify token is copied correctly (starts with `pypi-`)
2. Check token scope is set to the project (not entire account)
3. Ensure token hasn't expired
4. Regenerate token if needed

### Version Already Exists

**Symptoms:**
- `File already exists` error from PyPI

**Solution:**
PyPI versions are immutable. Increment the version:

```bash
# Update version
vim pyproject.toml  # Change 1.0.0 to 1.0.1

# Commit and tag
git add pyproject.toml
git commit -m "chore: bump version to 1.0.1"
git push origin main
git tag -a v1.0.1 -m "Release version 1.0.1"
git push origin v1.0.1
```

### Package Name Taken

**Symptoms:**
- First manual upload fails with "package name already exists"

**Solutions:**
1. Choose a different package name
2. Update `pyproject.toml` → `name = "msn-weather-wrapper-yourname"`
3. Contact PyPI support if you believe you own the name

### Build Fails

**Symptoms:**
- `python -m build` fails
- Missing dependencies

**Solutions:**

```bash
# Install build dependencies
pip install --upgrade pip setuptools wheel build

# Clean old builds
rm -rf dist/ build/ *.egg-info

# Rebuild
python -m build
```

## Security Best Practices

1. **Never commit tokens** to git
2. **Use project-scoped tokens** (not account-wide)
3. **Rotate tokens periodically** (every 6-12 months)
4. **Use environment protection** rules in GitHub
5. **Monitor PyPI download statistics** for suspicious activity
6. **Enable 2FA** on your PyPI account

## What Happens on Release

When you push a version tag (e.g., `v1.0.0`), the CI/CD pipeline automatically:

1. **Validates version** - Ensures tag matches `pyproject.toml`
2. **Runs all tests** - Quality gates must pass
3. **Builds package** - Creates wheel and source distribution
4. **Verifies package** - Runs `twine check`
5. **Publishes to PyPI** - Uploads using your token
6. **Builds containers** - Multi-platform images
7. **Creates release** - GitHub release with artifacts

All automatically, no manual steps needed!

## First Release Checklist

Before pushing v1.0.0:

- [ ] Manual upload completed (package name claimed)
- [ ] PyPI token created and added to GitHub Secrets
- [ ] `pyproject.toml` version set to `1.0.0`
- [ ] `CHANGELOG.md` updated with release notes
- [ ] All tests passing locally
- [ ] Repository URLs updated in all files
- [ ] Author information correct
- [ ] License file complete

Then:

```bash
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

Watch the magic happen! 🚀

## Additional Resources

- [PyPI Publishing Guide](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)
- [Trusted Publisher Setup](https://docs.pypi.org/trusted-publishers/) (Advanced)
- [TestPyPI](https://test.pypi.org/) - Test your releases safely
- [Versioning Guide](../docs/VERSIONING.md) - Complete semantic versioning guide
