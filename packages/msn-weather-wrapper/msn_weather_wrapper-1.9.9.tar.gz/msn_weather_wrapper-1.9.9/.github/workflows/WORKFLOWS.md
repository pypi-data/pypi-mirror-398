# GitHub Actions Workflows

This directory contains the automated CI/CD workflows for the MSN Weather Wrapper project.

## 🚀 Auto-Versioning & Release Workflow

### How It Works

The project uses **automatic semantic versioning** that triggers on every merged PR:

1. **PR Merged to Main** → Triggers `auto-version-release.yml`
2. **Version Bump Determined** → Based on PR title, labels, or branch name
3. **Version Bump PR Created** → Automated PR updates version files
4. **Auto-Merge Enabled** → PR auto-merges when checks pass
5. **Tag Created** → Git tag `v X.Y.Z` is automatically created
6. **Release Published** → CI/CD builds and publishes to PyPI, Docker, and GitHub Releases

### Version Bump Rules

The bump type is determined by (in order of priority):

1. **PR Labels**:
   - `major` or `breaking` → Major version (X.0.0)
   - `minor`, `feature`, or `enhancement` → Minor version (0.X.0)
   - `patch`, `fix`, or `bugfix` → Patch version (0.0.X)

2. **PR Title** (Conventional Commits):
   - `feat!:` or `breaking:` → Major (X.0.0)
   - `feat:` or `feature:` → Minor (0.X.0)
   - `fix:`, `chore:`, `refactor:`, `perf:`, `docs:` → Patch (0.0.X - default)

3. **Branch Prefix**:
   - `breaking/` or `major/` → Major
   - `feat/` or `feature/` → Minor
   - `fix/` or `bugfix/` or `hotfix/` → Patch

**Default**: If no indicators are found, defaults to **patch** version bump.

### Example PR Titles

```text
feat: add weather alerts feature          → 0.X.0 (minor)
fix: correct temperature parsing          → 0.0.X (patch)
feat!: redesign API endpoints             → X.0.0 (major)
chore: update dependencies                → 0.0.X (patch)
docs: improve README                      → 0.0.X (patch)
refactor: simplify client logic           → 0.0.X (patch)
```

## 📋 Workflow Files

### Core Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| **`auto-version-release.yml`** | PR merged to main | Automatic version bumping and tagging |
| **`publish-release.yml`** | Tag push (v*.*.*) | Build package, publish to PyPI, create GitHub Release |
| **`ci.yml`** | Push, PR | Full CI/CD pipeline (test, build, docs) |

### Supplementary Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| **`security-scan.yml`** | Push/PR to main | Comprehensive security scanning (Bandit, Semgrep) |
| **`dependencies.yml`** | Weekly schedule | Dependency updates via Dependabot |
| **`performance.yml`** | PR to main | Performance benchmarking and load testing |

## 🔄 CI/CD Pipeline (`ci.yml`)

The main CI/CD pipeline runs on:

- **Push to `main` or `develop`**
- **Pull Requests to `main` or `develop`**

### Pipeline Stages

1. **Smoke Tests** - Fast syntax and import validation
2. **Code Quality** - Ruff formatting and linting, mypy type checking
3. **Security** - Bandit, pip-audit, license scanning
4. **Unit Tests** - Pytest across Python 3.10-3.12 (matrix on main, 3.12 only on PRs)
5. **Coverage** - Test coverage reporting with Codecov
6. **Docker Build** - Build and test container images
7. **Integration Tests** - End-to-end API testing
8. **Frontend Tests** - React/TypeScript testing
9. **E2E Tests** - Playwright browser testing
10. **SBOM Generation** - Software bill of materials (Syft, CycloneDX)
11. **Build Documentation** - Generate and publish docs to GitHub Pages (on main only)

**Note**: Release jobs (build package, publish to PyPI, create GitHub Release) have been moved to `publish-release.yml` which triggers on tag push. This keeps the CI pipeline focused on testing and building documentation.

## 📦 Release Publishing (`publish-release.yml`)

Automatically triggered when a version tag (`v*.*.*`) is created:

1. **Build Package** - Create wheel and source distribution
2. **Publish to PyPI** - Upload to PyPI with trusted publishing (OIDC)
3. **Create GitHub Release** - Create release with package artifacts attached

This workflow runs **independently** from CI to keep release operations separate from the main test/build pipeline.

## 🛡️ Security Workflows

### `security-scan.yml`

Runs on push to main and pull requests:

- **Bandit**: Python security linting
- **Semgrep**: Static application security testing (SAST)
- **Safety & pip-audit**: Dependency vulnerability scanning
- **Trivy**: Container vulnerability scanning
- **Grype**: SBOM-based vulnerability detection
- **License Compliance**: Automated license checking

## 📊 Performance Testing (`performance.yml`)

Runs on pull requests to main:

- API endpoint performance benchmarking
- Response time regression detection
- Load testing with Locust
- Results compared against baseline

## 🔄 Dependency Management (`dependencies.yml`)

Weekly automated updates:

- Frontend dependencies (npm)
- Python dependencies (pip)
- GitHub Actions versions
- Security patches prioritized

## 🎯 Best Practices

### For Contributors

1. **Use Conventional Commits**: Start PR titles with `feat:`, `fix:`, etc.
2. **Add Labels**: Label PRs with `feature`, `bugfix`, `breaking` for clarity
3. **Review Auto-Generated PRs**: Version bump PRs are automated but reviewable
4. **Monitor CI/CD**: Check workflow runs for any failures

### For Maintainers

1. **Branch Protection**: Keep `main` protected (require PR reviews, status checks)
2. **Secrets Management**:
   - No secrets needed! GitHub token is auto-provided
   - PyPI uses trusted publishing (OIDC), no token storage required
3. **Auto-Merge**: Version bump PRs use auto-merge for convenience
4. **Monitoring**: Watch workflow runs for any failures or issues

## ✨ Fully Automated Release Flow

The complete release process is now **fully automated** end-to-end:

```bash
1. Developer creates PR with code changes
   ↓
2. PR merged to main
   ↓
3. auto-version-release.yml triggers:
   - Determines version bump (major/minor/patch)
   - Creates version bump PR
   - Enables auto-merge
   ↓
4. Version bump PR auto-merges
   ↓
5. Git tag (v1.2.3) created automatically
   ↓
6. publish-release.yml triggers on tag:
   - Builds Python package
   - Publishes to PyPI
   - Creates GitHub Release with artifacts
   ↓
7. Release complete ✅
   - Package available on PyPI
   - Release notes on GitHub
   - No manual steps needed!
```

**Key Advantages:**

- ✅ No manual `gh workflow run` commands needed
- ✅ `[skip ci]` removed from commits - CI runs automatically on tag creation
- ✅ Separation of concerns: CI tests/builds, separate workflow handles releases
- ✅ Reduced complexity and fewer moving parts
- ✅ Consistent versioning across all releases

## 🐛 Troubleshooting

### Release not published automatically

**Check:**

1. Verify the tag exists: `git tag -l | grep v1.3.2`
2. Verify tag is on GitHub: `gh release list`
3. Check `publish-release.yml` workflow run: `gh run list --workflow publish-release.yml`

**If missing**: Tag may not have been created. Check `auto-version-release.yml` logs for version bump PR.

### Version bump PR not created

**Check:**

1. Was the PR merged? The workflow only triggers on `pull_request.merged == true`
2. Is the PR closing event being received? Check PR logs in GitHub
3. Are there any GITHUB_TOKEN permission issues?

**Solution**: Manually create a version bump PR or trigger `auto-version-release.yml` via workflow_dispatch

### PyPI publishing fails

**Check:**

1. Version already exists on PyPI → Versions are immutable
2. Token expired → Verify trusted publishing (OIDC) is configured
3. Package name conflicts → Ensure unique package name

**Solution**: The workflow logs will show the exact error## 📚 Additional Documentation

- [CI/CD Pipeline Details](./README.md)
- [Security Scanning Guide](../../docs/SECURITY.md)
- [Contributing Guidelines](../../CONTRIBUTING.md)
- [Versioning Guide](../../docs/VERSIONING.md)

## 🔗 Useful Links

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [Python Semantic Release](https://python-semantic-release.readthedocs.io/)
