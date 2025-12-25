# DevSecOps Monitoring Dashboard

Comprehensive real-time monitoring dashboard for local development environment and GitHub CI/CD workflows with Red-Amber-Green (RAG) status indicators.

---

## Quick Start

```bash
# Generate local reports first
./dev.sh test      # Run tests with coverage
./dev.sh docs      # Generate all reports

# Launch the monitor
./dev.sh monitor
```

The dashboard auto-refreshes every 60 seconds and shows at-a-glance status using RAG indicators.

---

## RAG Status Indicators

### Legend

| Symbol | Color | Status | Meaning |
|--------|-------|--------|---------|
| ✅ | Green | Healthy/Passing | Everything is good |
| ⚠️ | Amber | Warning | Needs attention soon |
| ❌ | Red | Critical | Immediate action required |
| ○ | Grey | Unknown | Data not available |

### Status Thresholds

**Green (✅)** - Healthy/Passing
- Code coverage: 80%+
- All tests passing
- No critical security issues
- Services running and healthy

**Amber (⚠️)** - Warning/Needs Attention

- Code coverage: 60-79%
- Minor issues detected
- Partial services running
- Dependent vulnerabilities detected

**Red (❌)** - Critical/Failing

- Code coverage: <60%
- Failed tests
- Critical security vulnerabilities
- Services down or unhealthy

**Grey (○)** - Unknown/Not Available

- No data available
- Feature disabled
- Not yet scanned

---

## Monitored Items

### 1. Local Development Environment

#### Container Services

**Status**: Running/Stopped/Healthy/Unhealthy

**Checks**:
- API container status and health endpoint
- Frontend container status
- Podman availability

**RAG Thresholds**:
- 🟢 Green: Both services healthy
- 🟡 Amber: Services running but unhealthy, or partial
- 🔴 Red: Services stopped
- ⚪ Grey: Podman not available

#### Python Virtual Environment

**Status**: Active/Inactive/Not Configured

**Checks**:
- Virtual environment directory exists (`venv/`)
- Environment is currently activated

**RAG Thresholds**:
- 🟢 Green: Environment active
- 🟡 Amber: Environment exists but not activated
- 🔴 Red: Environment not configured

#### Git Working Directory

**Status**: Clean/Dirty

**Checks**:
- Staged changes
- Unstaged modifications
- Untracked files

**RAG Thresholds**:
- 🟢 Green: No uncommitted changes
- 🟡 Amber: Uncommitted changes present

### 2. Code Quality & Testing

#### Test Execution

**Status**: Pass/Fail/No Report

**Checks**:
- JUnit XML test results (`junit.xml`)
- Test pass/fail counts

**RAG Thresholds**:
- 🟢 Green: All tests passing
- 🔴 Red: Any test failures
- ⚪ Grey: No test report available

#### Code Coverage

**Status**: Percentage (0-100%)

**Checks**:
- HTML coverage report (`htmlcov/index.html`)
- Overall coverage percentage

**RAG Thresholds**:
- 🟢 Green: ≥ 80% coverage (Excellent)
- 🟡 Amber: 60-79% coverage (Good)
- 🔴 Red: < 60% coverage (Needs improvement)
- ⚪ Grey: No coverage report

### 3. Security & Compliance

#### SAST Security Scan

**Status**: Clean/Issues/No Report

**Checks**:
- Bandit security scan results
- Critical/High severity issues

**RAG Thresholds**:
- 🟢 Green: No critical vulnerabilities
- 🔴 Red: Critical issues found
- ⚪ Grey: No security report

#### Dependency Scan

**Status**: Clean/Vulnerabilities/Unchecked

**Checks**:
- pip-audit vulnerability scanning
- Known vulnerable packages

**RAG Thresholds**:
- 🟢 Green: No known vulnerabilities
- 🟡 Amber: Vulnerable packages detected
- ⚪ Grey: Not scanned (pip-audit not installed)

#### License Compliance

**Status**: Tracked/Not Available

**Checks**:
- License report (`artifacts/security-reports/licenses.json`)
- Number of dependencies tracked

**RAG Thresholds**:
- 🟢 Green: Dependencies tracked
- ⚪ Grey: No license report

### 4. GitHub CI/CD Workflows

The dashboard fetches the latest workflow run status from GitHub's public API (no authentication required).

#### CI Pipeline

**Workflow**: `.github/workflows/ci.yml`

**Status**: Success/Failure/Cancelled/No Recent Runs

**RAG Thresholds**:
- 🟢 Green: Latest run succeeded
- 🔴 Red: Latest run failed
- ⚪ Grey: Cancelled or no recent runs

#### Security Scans

**Workflow**: `.github/workflows/security.yml`

**Status**: Success/Failure/Cancelled/No Recent Runs

**RAG Thresholds**:
- 🟢 Green: Latest run succeeded
- 🔴 Red: Latest run failed
- ⚪ Grey: Cancelled or no recent runs

#### Build & Push

**Workflow**: `.github/workflows/build.yml`

**Status**: Success/Failure/Cancelled/No Recent Runs

**RAG Thresholds**:
- 🟢 Green: Latest run succeeded
- 🔴 Red: Latest run failed
- ⚪ Grey: Cancelled or no recent runs

#### Deploy to Production

**Workflow**: `.github/workflows/deploy.yml`

**Status**: Success/Failure/Cancelled/No Recent Runs

**RAG Thresholds**:
- 🟢 Green: Latest run succeeded
- 🔴 Red: Latest run failed
- ⚪ Grey: Cancelled or no recent runs

---

## Usage

### Starting the Monitor

```bash
./dev.sh monitor
```

The dashboard will:
1. Display immediately with current status
2. Auto-refresh every 60 seconds
3. Cache GitHub API responses for 30 seconds to reduce API calls
4. Continue until you press `Ctrl+C`

### Keyboard Controls

- **Ctrl+C** - Exit the monitor

### Update Frequency

- **Local Checks**: Real-time on each refresh (60s)
- **GitHub API**: Cached for 30 seconds, refreshed as needed
- **Display Refresh**: Every 60 seconds

---

## GitHub API Details

The monitor uses GitHub's public REST API to fetch workflow status:

- **Endpoint**: `https://api.github.com/repos/{owner}/{repo}/actions/runs`
- **Authentication**: None required (public API)
- **Rate Limit**: 60 requests/hour for unauthenticated requests
- **Caching**: Responses cached for 30 seconds to minimize API usage
- **Data Fetched**: Latest 5 completed workflow runs

### API Response Handling

- Fetches only completed runs (`status=completed`)
- Matches workflows by name
- Extracts conclusion (success/failure/cancelled)
- Falls back to "unknown" if workflow not found

---

## Prerequisites

### Required

- `bash` shell
- `curl` - For GitHub API calls
- `jq` - For JSON parsing
- `git` - For repository status

### Optional (for full functionality)

- `podman` - For container status
- `pip-audit` - For dependency vulnerability scanning
- Generated reports:
  - `htmlcov/index.html` - Coverage report
  - `junit.xml` - Test results
  - `artifacts/security-reports/bandit-report.json` - Security scan
  - `artifacts/security-reports/licenses.json` - License report

---

## Generating Reports

To generate local reports for monitoring:

```bash
# Run tests with coverage
./dev.sh test

# Generate all reports and documentation
./dev.sh docs
```

---

## Example Output

```
╔═══════════════════════════════════════════════════════════════════════════╗
║ DevSecOps Dashboard                                                       ║
║ jim-wyatt/msn-weather-wrapper @ main                                      ║
║ 2025-12-04 14:30:45                                                       ║
╚═══════════════════════════════════════════════════════════════════════════╝

┌─ Local Development Environment ────────────────────────────────────────────┐
│ Container Services:      ✅  Both services healthy                          │
│ Python Virtual Env:      ✅  Active (venv/)                                 │
│ Git Working Directory:   ✅  No uncommitted changes                         │
└─────────────────────────────────────────────────────────────────────────────┘

┌─ Code Quality & Testing ────────────────────────────────────────────────────┐
│ Test Execution:          ✅  168 tests passed                               │
│ Code Coverage:           ✅  97% (Excellent)                                │
└─────────────────────────────────────────────────────────────────────────────┘

┌─ Security & Compliance ─────────────────────────────────────────────────────┐
│ SAST Security Scan:      ✅  No critical vulnerabilities                    │
│ Dependency Scan:         ✅  No known vulnerabilities                       │
│ License Compliance:      ✅  142 dependencies tracked                       │
└─────────────────────────────────────────────────────────────────────────────┘

┌─ GitHub CI/CD Workflows (Latest Runs) ──────────────────────────────────────┐
│ CI Pipeline:             ✅  Passed                                         │
│ Security Scans:          ✅  Passed                                         │
│ Build & Push:            ✅  Passed                                         │
│ Deploy to Production:    ✅  Passed                                         │
└─────────────────────────────────────────────────────────────────────────────┘

 ● Press Ctrl+C to exit  •  Updates every 60s  •  GitHub API via public endpoint
```

---

## Troubleshooting

### No data available for local checks

Generate reports first:

```bash
./dev.sh test      # Generates junit.xml and htmlcov/
./dev.sh docs      # Generates all reports
```

### GitHub API rate limit

The public API allows 60 requests/hour. With 30-second caching, you can run the monitor continuously for hours without hitting the limit.

### jq not found

Install jq for JSON parsing:

```bash
# Ubuntu/Debian
sudo apt-get install jq

# macOS
brew install jq

# Fedora
sudo dnf install jq
```

### Container status shows "disabled"

Ensure Podman is installed:

```bash
# Ubuntu/Debian
sudo apt-get install podman

# macOS
brew install podman

# Fedora
sudo dnf install podman
```

### No GitHub data

Check internet connectivity and verify API endpoint:

```bash
curl -s https://api.github.com/repos/jim-wyatt/msn-weather-wrapper/actions/runs | jq '.workflow_runs[0]'
```

---

## Integration with CI/CD

The monitor dashboard is designed for local development but aligns with CI/CD workflows:

1. **Local Testing** - Run tests and generate reports locally
2. **Monitor Status** - Use dashboard to verify everything is green
3. **Push Changes** - Commit and push to GitHub
4. **Watch Workflows** - Monitor dashboard shows GitHub workflow status
5. **Iterate** - Fix any red/amber items and repeat

---

## Development Workflow

### Pre-Push Checklist

```bash
# 1. Generate latest reports
./dev.sh test
./dev.sh docs

# 2. Launch monitor
./dev.sh monitor

# 3. Check for green indicators
# - All local environment items green?
# - Code coverage above 80%?
# - No critical security issues?

# 4. If all green, push changes
git push

# 5. Monitor continues showing GitHub workflow status
```

### Continuous Development

Leave the monitor running in a dedicated terminal window during development for continuous visibility into:
- Container health
- Test results after each run
- Security scan results
- GitHub workflow status after push

---

## Performance Considerations

### API Rate Limiting

- GitHub public API: 60 requests/hour
- Caching: 30-second cache reduces API calls to ~2 per minute
- With caching: Can run continuously for many hours without hitting limit

### Local Performance

- Minimal CPU usage (mostly sleep)
- Quick status checks (<1 second per refresh)
- File-based caching for GitHub data

---

## Future Enhancements

Potential improvements for future versions:

- Docker support (in addition to Podman)
- Configurable refresh intervals
- Historical trend visualization
- Alert notifications for status changes
- GitHub Actions running status (not just completed)
- Support for GitHub authentication to increase API rate limits
- Export status to JSON/HTML report
- Custom threshold configuration
- Integration with other CI/CD platforms (GitLab, CircleCI, etc.)

---

## See Also

- [Development Guide](DEVELOPMENT.md) - Local development setup
- [Testing Documentation](TESTING.md) - Test suite and coverage
- [Security Documentation](SECURITY.md) - Security features and scanning
- [Container Development Setup](CONTAINER_DEV_SETUP.md) - Podman/Docker deployment
- [CI/CD Workflows](WORKFLOW_DIAGRAM.md) - GitHub Actions automation
