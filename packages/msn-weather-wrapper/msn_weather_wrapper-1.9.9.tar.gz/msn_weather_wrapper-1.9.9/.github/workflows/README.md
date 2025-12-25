# GitHub Actions CI/CD Pipeline

This directory contains the GitHub Actions workflows for automated testing, building, and deployment of the MSN Weather Wrapper project.

## Workflows

### 1. `ci.yml` - Main CI/CD Pipeline

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Manual workflow dispatch

**Jobs:**

1. **code-quality** - Runs Ruff formatting/linting and mypy type checking
2. **security** - Runs Bandit security scanning and Safety dependency checks
3. **unit-tests** - Runs unit and security tests on Python 3.10-3.12 (matrix)
4. **coverage** - Generates test coverage reports and uploads to Codecov
5. **container-build** - Builds and tests unified Podman container image
6. **integration-tests** - Runs full integration tests with podman-compose
7. **sbom** - Generates SBOM with Syft and scans vulnerabilities with Grype
8. **docs** - Builds MkDocs documentation
9. **deploy-docs** - Deploys documentation to GitHub Pages (main branch only)
10. **release** - Creates GitHub releases with SBOM attachments (on version tags)

**Artifacts:**
- `bandit-report` - Security scan results
- `coverage-report` - HTML coverage report
- `sbom-reports` - SBOM files in multiple formats
- `documentation` - Built MkDocs site

### 2. `podman.yml` - Podman Build & Push

**Triggers:**
- Push to `main` branch
- Version tags (`v*`)
- Pull requests to `main`
- Manual workflow dispatch

**Jobs:**

1. **build-and-push** - Builds multi-platform unified Podman image (amd64/arm64)
   - Unified image: Built from root Containerfile (includes API + Frontend + Nginx)
   - Pushes to GitHub Container Registry (ghcr.io)
   - Generates SBOM for image
   - Tags: `latest`, `sha-{sha}`, version tags

2. **scan-images** - Scans Podman images for vulnerabilities
   - Grype scanning (fails on critical vulnerabilities)
   - Trivy scanning with SARIF output
   - Uploads results to GitHub Security

**Container Registry:**
- `ghcr.io/{owner}/{repo}:latest` (unified container with API + Frontend + Nginx)

### 3. `dependencies.yml` - Dependency Updates

**Triggers:**
- Scheduled: Every Monday at 9:00 AM UTC
- Manual workflow dispatch

**Jobs:**

1. **update-dependencies** - Updates Python dependencies
   - Runs `pip install --upgrade` for all packages
   - Runs full test suite
   - Creates pull request with update summary

2. **update-frontend** - Updates frontend dependencies
   - Runs `npm update`
   - Builds frontend to verify changes
   - Creates pull request with outdated packages list

3. **security-audit** - Runs security audits
   - Python: Safety and pip-audit
   - Frontend: npm audit
   - Uploads audit reports as artifacts

**Pull Request Labels:**
- `dependencies` - All dependency updates
- `frontend` - Frontend-specific updates
- `automated` - Automated PRs

### 4. `performance.yml` - Performance Testing

**Triggers:**
- Pull requests to `main`
- Manual workflow dispatch

**Jobs:**

1. **load-test** - Load testing with Locust
   - Simulates 50 concurrent users
   - 2-minute test duration
   - Tests weather endpoint and health check
   - Generates HTML report and CSV results

2. **benchmark** - Benchmark tests with pytest-benchmark
   - Runs performance benchmarks
   - Compares against previous results
   - Alerts on 150%+ performance regression
   - Stores results for trending

**Artifacts:**
- `load-test-results` - Locust HTML report and CSV files
- `benchmark-results` - JSON benchmark data

## Setup Instructions

### Prerequisites

1. **Enable GitHub Actions** in repository settings
2. **Enable GitHub Pages** (Settings → Pages → Source: Deploy from branch `gh-pages`)
3. **Enable Container Registry** (automatic with GitHub Actions)

### Optional: Codecov Integration

1. Sign up at [codecov.io](https://codecov.io)
2. Add repository to Codecov
3. Copy upload token
4. Add as repository secret: `CODECOV_TOKEN`

### Secrets Required

**Auto-configured (no action needed):**
- `GITHUB_TOKEN` - Automatically provided by GitHub Actions

**Optional:**
- `CODECOV_TOKEN` - For Codecov coverage reporting (optional, fails gracefully)

### Branch Protection Rules

Recommended settings for `main` branch:

- ✅ Require pull request reviews (1 approver)
- ✅ Require status checks to pass:
  - `code-quality`
  - `unit-tests (3.10, 3.11, 3.12)`
  - `coverage`
  - `container-build`
  - `integration-tests`
- ✅ Require branches to be up to date
- ✅ Require linear history
- ✅ Include administrators

## Usage

### Running Workflows Manually

1. Go to **Actions** tab in GitHub
2. Select workflow from left sidebar
3. Click **Run workflow** button
4. Choose branch and click **Run workflow**

### Creating Releases

To trigger a release with SBOM:

```bash
# Tag the commit
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

This will:
- Run all CI/CD tests
- Build and push Podman images
- Generate SBOMs
- Deploy documentation
- Create GitHub release with SBOM attachments

### Viewing Results

- **Test Results**: Actions → CI/CD Pipeline → Summary
- **Coverage**: Download `coverage-report` artifact
- **Podman Images**: Packages tab in repository
- **Documentation**: https://{username}.github.io/{repo}/
- **SBOMs**: Release attachments or artifact downloads

## Workflow Dependencies

```
code-quality ──┐
security ──────┤
               ├──> container-build ──┐
unit-tests ────┤                      │
               │                      ├──> integration-tests ──┐
coverage ──────┘                      │                        │
                                      │                        ├──> release
sbom ─────────────────────────────────┘                        │
                                                               │
docs ──────────────────────────────────────────────────────────┴──> deploy-docs
```

## Maintenance

### Updating Workflow Versions

Check for updates to GitHub Actions periodically:

```bash
# Check for action updates
gh extensions install mheap/gh-action-update
gh action-update --dry-run
```

### Monitoring Workflow Performance

- Monitor workflow run times in Actions tab
- Optimize slow jobs with caching or parallelization
- Use matrix strategies for multiple configurations

### Troubleshooting

**Podman container build failures:**
- Check Containerfile syntax
- Verify base image availability (python:3.12-slim-trixie, node:22-trixie-slim)
- Review multi-stage build logs in Actions
- Ensure frontend build completes successfully

**Test failures:**
- Check test logs in job output
- Download coverage report artifact
- Run tests locally: `pytest -v`

**Documentation deployment issues:**
- Verify GitHub Pages is enabled
- Check `gh-pages` branch exists
- Review MkDocs build logs

**Dependency update failures:**
- Check compatibility between packages
- Review test failures in PR
- Manually test updates locally

## Best Practices

1. **Keep workflows fast**: Use caching, parallelize jobs
2. **Fail fast**: Run quick checks (linting) before slow tests
3. **Use matrix builds**: Test multiple Python/Node versions
4. **Monitor costs**: Review Actions usage in billing
5. **Secure workflows**: Never commit secrets, use `GITHUB_TOKEN`
6. **Document changes**: Update this README when modifying workflows

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Actions Marketplace](https://github.com/marketplace?type=actions)
- [Workflow Syntax Reference](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
