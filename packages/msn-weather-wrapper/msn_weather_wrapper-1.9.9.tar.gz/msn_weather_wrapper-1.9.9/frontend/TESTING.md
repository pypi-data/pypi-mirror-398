# Frontend Testing Setup

## Overview
The frontend includes comprehensive E2E tests using Playwright, covering:
- **Accessibility Testing**: WCAG 2.1 Level AA compliance with @axe-core/playwright
- **Visual Regression Testing**: Screenshot comparison across viewports and states

## Test Files
- `tests/e2e/accessibility.spec.ts`: 13 accessibility tests covering ARIA, keyboard navigation, color contrast, semantic HTML, and screen reader support
- `tests/e2e/visual.spec.ts`: 15 visual regression tests with baseline screenshots across breakpoints
- `tests/e2e/weather.spec.ts`: Functional E2E tests for weather functionality

## Requirements
- **Node.js**: ≥ 20.19.0 or ≥ 22.12.0 (required by Vite 6.x and crypto.hash API)
- **Playwright**: ^1.49.1
- **@axe-core/playwright**: For automated accessibility scanning

## Running Tests

### Prerequisites
Ensure Node.js 20+ is installed:
```bash
node --version  # Should be >= 20.19.0
```

### Install Dependencies
```bash
cd frontend
npm install
```

### Run All Tests
```bash
npm run test:e2e
```

### Run Specific Test Suites
```bash
# Accessibility tests only
npx playwright test accessibility

# Visual regression tests only
npx playwright test visual

# Functional tests only
npx playwright test weather
```

### Update Visual Regression Baselines
```bash
npx playwright test --update-snapshots
```

### Run Tests in Specific Browsers
```bash
# Chromium only
npx playwright test --project=chromium

# All desktop browsers
npx playwright test --project="Desktop*"

# Mobile browsers
npx playwright test --project="Mobile*"
```

## Test Configuration

### Playwright Config (`playwright.config.ts`)
- **Test Directory**: `./tests/e2e`
- **Base URL**: `http://localhost:5173`
- **Browsers**: Chromium, Firefox, WebKit, Mobile Chrome, Mobile Safari
- **Reporters**: HTML reporter for detailed results
- **Screenshots**: Captured on failure
- **Trace**: Recorded on first retry

### Manual Server Setup (if auto-start fails)
If the webServer auto-start fails due to Node version issues:

1. Comment out `webServer` section in `playwright.config.ts`
2. Start dev server manually:
   ```bash
   npm run dev
   ```
3. Run tests in separate terminal:
   ```bash
   npx playwright test
   ```

## Using Docker/Podman

### Build Frontend Container
```bash
podman build -f Containerfile.dev -t msn-weather-frontend:dev .
```

### Run Frontend Container
```bash
podman run -d \
  --name frontend-dev \
  -p 5173:5173 \
  -v $(pwd):/app:Z \
  msn-weather-frontend:dev
```

### Run Tests in Container
```bash
podman exec frontend-dev npx playwright test
```

## Accessibility Test Coverage

### WCAG 2.1 Level AA Compliance
- ✅ Color contrast ratios
- ✅ ARIA labels and roles
- ✅ Keyboard navigation
- ✅ Focus management
- ✅ Heading hierarchy
- ✅ Form labels
- ✅ Alternative text for images
- ✅ Semantic HTML structure
- ✅ Screen reader support (aria-live regions)
- ✅ Error message accessibility

### Test Categories
1. **Homepage Accessibility**: Overall compliance check
2. **Interactive Elements**: ARIA labels on inputs/buttons
3. **Structure**: Heading hierarchy and landmarks
4. **Visual**: Color contrast compliance
5. **Keyboard**: Tab navigation and focus visibility
6. **Forms**: Proper labeling and associations
7. **Images**: Alt text validation
8. **WCAG Tags**: Comprehensive Level A and AA rules
9. **Dynamic Content**: Accessibility after data loads
10. **Semantic HTML**: Proper use of landmarks (main, nav, etc.)
11. **Error Handling**: Accessible error messages
12. **Focus Management**: Proper focus order
13. **Screen Readers**: ARIA announcements and live regions

## Visual Regression Test Coverage

### Viewports Tested
- **Mobile**: 320px, 375px, 414px
- **Tablet**: 768px, 1024px (portrait & landscape)
- **Desktop**: 1280px, 1920px

### States Captured
1. Homepage (all viewports)
2. Autocomplete dropdown
3. Weather results display
4. Loading state
5. Error state
6. Empty state
7. Focus states (input, button)
8. Hover states
9. Dark mode (if available)
10. Responsive breakpoints
11. Scrolled content
12. Animation end states

### Pixel Diff Tolerance
- Static content: 50-100px max diff
- Dynamic content: 150px max diff (weather data, animations)

## Continuous Integration

### GitHub Actions / GitLab CI
```yaml
- name: Install dependencies
  run: |
    cd frontend
    npm ci

- name: Install Playwright browsers
  run: npx playwright install --with-deps

- name: Run E2E tests
  run: npm run test:e2e

- name: Upload test results
  if: failure()
  uses: actions/upload-artifact@v3
  with:
    name: playwright-report
    path: frontend/playwright-report/
```

## Troubleshooting

### Issue: `crypto.hash is not a function`
**Cause**: Node.js < 22 (project standard) may not expose the crypto.hash API used by Vite 6.x

**Solution**:
- Upgrade Node.js: `nvm install 22` or use official installer
- Or use Docker/Podman container with Node 22 (see above)

### Issue: Playwright browsers not installed
**Solution**:
```bash
npx playwright install --with-deps
```

### Issue: Tests timing out
**Solution**:
- Increase timeout in test: `test.setTimeout(60000)`
- Check if dev server is running on port 5173
- Verify API backend is accessible

### Issue: Visual regression failures
**Solution**:
- Review diff images in `test-results/` directory
- Update baselines if changes are intentional: `--update-snapshots`
- Increase `maxDiffPixels` for dynamic content

### Issue: Accessibility violations detected
**Solution**:
- Review violation details in test output
- Fix issues in component code (add ARIA labels, fix contrast, etc.)
- Re-run tests to verify fixes

## Best Practices

1. **Run accessibility tests on every PR** - catch issues early
2. **Update visual baselines deliberately** - review diffs before accepting
3. **Test across all browsers** - WebKit may catch issues Chrome/Firefox miss
4. **Use semantic HTML** - reduces need for ARIA overrides
5. **Test keyboard navigation** - don't rely solely on mouse/touch
6. **Verify focus indicators** - ensure visible focus states
7. **Test with screen readers** - automated tools catch ~30-40% of issues

## Additional Resources
- [Playwright Documentation](https://playwright.dev/)
- [axe-core Rules](https://github.com/dequelabs/axe-core/blob/develop/doc/rule-descriptions.md)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
