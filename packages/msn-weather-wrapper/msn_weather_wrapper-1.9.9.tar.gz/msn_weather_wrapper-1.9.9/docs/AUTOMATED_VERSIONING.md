# Automated Semantic Versioning

This project uses **automated semantic versioning** - every merged pull request automatically increments the version number and publishes a new release to PyPI.

## How It Works

When a PR is merged to `main`, the Auto-Version and Release workflow:

1. **Determines the version bump type** based on PR labels, title, or branch prefix
2. **Increments the version** in `pyproject.toml` following semantic versioning
3. **Commits the version bump** back to the main branch
4. **Creates a git tag** for the new version
5. **Triggers the CI/CD pipeline** which builds and publishes to PyPI

## Version Bump Rules

The workflow follows [Semantic Versioning 2.0.0](https://semver.org/):

### Major Version (X.0.0) - Breaking Changes

Increments the major version and resets minor/patch to 0.

**Triggered by:**
- PR labels: `major`, `breaking`
- PR title: `feat!:` or `feature!:` (with exclamation mark)
- Branch prefix: `breaking/` or `major/`

**Example:** `1.2.3` → `2.0.0`

**Use when:**
- Breaking API changes
- Incompatible changes to public interfaces
- Removing deprecated features
- Major architectural changes

### Minor Version (0.X.0) - New Features

Increments the minor version and resets patch to 0.

**Triggered by:**
- PR labels: `minor`, `feature`, `enhancement`
- PR title: `feat:` or `feature:`
- Branch prefix: `feat/` or `feature/`

**Example:** `1.2.3` → `1.3.0`

**Use when:**
- Adding new features
- Adding new functionality (backwards compatible)
- Deprecating features (but not removing them)
- Substantial internal improvements

### Patch Version (0.0.X) - Bug Fixes & Maintenance

Increments only the patch version. **This is the default** if no specific indicators are found.

**Triggered by:**
- PR labels: `patch`, `fix`, `bugfix`
- PR title: `fix:`, `bugfix:`, `perf:`, `refactor:`
- Branch prefix: `fix/`, `bugfix/`, `hotfix/`
- **Default for all other PRs**

**Example:** `1.2.3` → `1.2.4`

**Use when:**
- Bug fixes
- Performance improvements
- Refactoring
- Documentation updates
- Test improvements
- Dependency updates
- CI/CD improvements

## Priority Order

The workflow checks for version bump indicators in this order:

1. **PR Labels** (highest priority)
2. **PR Title** (conventional commit format)
3. **Branch Prefix**
4. **Default to patch** (if nothing matches)

## Examples

### Using PR Labels

```bash
# Create PR with label
gh pr create --label "feature" --title "Add new weather endpoint"
# Result: Minor version bump (e.g., 1.2.3 → 1.3.0)

gh pr create --label "breaking" --title "Remove deprecated API"
# Result: Major version bump (e.g., 1.2.3 → 2.0.0)
```

### Using Conventional Commit Titles

```bash
# Feature (minor bump)
gh pr create --title "feat: add temperature forecast"
# Result: 1.2.3 → 1.3.0

# Breaking change (major bump)
gh pr create --title "feat!: redesign API response format"
# Result: 1.2.3 → 2.0.0

# Bug fix (patch bump)
gh pr create --title "fix: correct humidity calculation"
# Result: 1.2.3 → 1.2.4
```

### Using Branch Prefixes

```bash
# Feature branch (minor bump)
git checkout -b feat/add-wind-direction
# When PR merged: 1.2.3 → 1.3.0

# Fix branch (patch bump)
git checkout -b fix/temperature-conversion
# When PR merged: 1.2.3 → 1.2.4

# Breaking change branch (major bump)
git checkout -b breaking/remove-v1-api
# When PR merged: 1.2.3 → 2.0.0
```

## Workflow Integration

### Creating a PR with Proper Versioning

```bash
# For a bug fix (patch):
git checkout -b fix/issue-description
# ... make changes ...
git commit -m "fix: description of fix"
gh pr create --title "fix: description" --label "bugfix"

# For a new feature (minor):
git checkout -b feat/feature-name
# ... make changes ...
git commit -m "feat: description of feature"
gh pr create --title "feat: description" --label "feature"

# For a breaking change (major):
git checkout -b breaking/change-description
# ... make changes ...
git commit -m "feat!: description of breaking change"
gh pr create --title "feat!: description" --label "breaking"
```

### What Happens After Merge

1. **Auto-Version workflow runs** (takes ~10 seconds)
   - Determines bump type
   - Updates `pyproject.toml`
   - Commits to main
   - Creates version tag

2. **CI/CD Pipeline triggers** (takes ~5-10 minutes)
   - Runs all tests
   - Builds Python package
   - Publishes to PyPI
   - Creates GitHub Release
   - Generates SBOM and security reports

3. **Release is live!**
   - PyPI: `pip install msn-weather-wrapper==X.Y.Z`
   - GitHub: Release with artifacts
   - Containers: `ghcr.io/jim-wyatt/msn-weather-wrapper:X.Y.Z`

## Monitoring Releases

### Check Version Bump Status

```bash
# View workflow runs
gh run list --workflow=auto-tag-release.yml --limit 5

# View specific run
gh run view <run-id>
```

### Check Release Pipeline

```bash
# View CI/CD runs
gh run list --workflow=ci.yml --limit 5

# Check if tag triggered release
gh run list --json event,headBranch,conclusion | \
  jq '.[] | select(.event == "push" and (.headBranch | startswith("refs/tags/")))'
```

### Verify Publication

```bash
# Check PyPI
pip index versions msn-weather-wrapper

# Check GitHub releases
gh release list --limit 5

# Check containers
gh api /user/packages/container/msn-weather-wrapper/versions
```

## Best Practices

### 1. Use Descriptive PR Titles

Good:
```
feat: add weather alerts endpoint
fix: correct temperature unit conversion
refactor: improve caching logic
```

Bad:
```
Updated code
Fixed stuff
Changes
```

### 2. Apply Appropriate Labels

- Use GitHub labels to explicitly control version bumps
- Labels override title and branch detection
- Useful when branch names don't follow conventions

### 3. Group Related Changes

- Combine related fixes in one PR (single patch bump)
- Don't split one feature across multiple PRs (avoid unnecessary minor bumps)
- Use draft PRs for work-in-progress

### 4. Review Before Merging

- Every merge creates a new release
- Ensure all tests pass
- Review the version bump that will occur
- Consider if the change warrants immediate release

### 5. Handle Breaking Changes Carefully

- Document breaking changes thoroughly
- Update CHANGELOG.md
- Consider deprecation warnings before removal
- Coordinate with users for major versions

## Skipping Auto-Release

If you need to merge without creating a release (not recommended):

1. The workflow cannot be easily skipped (by design)
2. If needed, manually delete the created tag before CI/CD completes:
   ```bash
   git push origin :refs/tags/vX.Y.Z
   ```
3. Consider using draft PRs for work that shouldn't be released

## Troubleshooting

### Version Already Exists

If the workflow reports "Version Already Exists":
- The calculated version was already tagged
- Check if someone manually created the tag
- The workflow will skip and not create a duplicate

### Tag Created But No Release

If tag is created but PyPI release fails:
1. Check CI/CD pipeline status
2. Look for build or test failures
3. PyPI credentials might need updating

### Wrong Version Bump

If the version bumped incorrectly:
1. Check which indicator was used (label, title, or branch)
2. Remember labels have highest priority
3. Default is patch if nothing matches

To fix:
```bash
# Delete the tag
git push origin :refs/tags/vX.Y.Z

# Create a new PR with correct versioning indicators
```

## Related Documentation

- [Semantic Versioning Specification](https://semver.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

## Migrating from Manual Versioning

If you previously used manual version bumps:

1. **No action needed** - The workflow now handles all versioning
2. **Remove manual version bump PRs** - These are no longer necessary
3. **Update contribution docs** - Instruct contributors on labeling
4. **Communicate changes** - Inform team about new automated process

---

*Last updated: December 3, 2025*
