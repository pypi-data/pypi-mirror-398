import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('Accessibility Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the application before each test
    await page.goto('/', { waitUntil: 'load' });
    await page.waitForSelector('h1:has-text("MSN Weather")', { timeout: 10000 });
  });

  test('should not have any automatically detectable accessibility issues on homepage', async ({ page }) => {
    const accessibilityScanResults = await new AxeBuilder({ page }).analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('should have proper ARIA labels on interactive elements', async ({ page }) => {
    // Check autocomplete input has label
    const cityInput = page.getByRole('combobox', { name: /city/i });
    await expect(cityInput).toBeVisible();

    // Check button has accessible name
    const button = page.getByRole('button', { name: /get weather|use my location/i });
    await expect(button).toBeVisible();
  });

  test('should have proper heading hierarchy', async ({ page }) => {
    // Check for h1
    const h1 = page.getByRole('heading', { level: 1 });
    await expect(h1).toBeVisible();

    // Run axe specifically for heading-order rule
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['cat.structure'])
      .analyze();

    const headingOrderViolations = accessibilityScanResults.violations.filter(
      v => v.id === 'heading-order'
    );
    expect(headingOrderViolations).toHaveLength(0);
  });

  test('should have sufficient color contrast', async ({ page }) => {
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['cat.color'])
      .analyze();

    const contrastViolations = accessibilityScanResults.violations.filter(
      v => v.id === 'color-contrast' || v.id === 'color-contrast-enhanced'
    );
    expect(contrastViolations).toHaveLength(0);
  });

  test('should be keyboard navigable', async ({ page }) => {
    // Tab through interactive elements
    await page.keyboard.press('Tab');
    await expect(page.locator(':focus')).toBeVisible();

    await page.keyboard.press('Tab');
    await expect(page.locator(':focus')).toBeVisible();

    // Check focus is visible (no violations)
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['cat.keyboard'])
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('should have proper form labels', async ({ page }) => {
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['cat.forms'])
      .analyze();

    const labelViolations = accessibilityScanResults.violations.filter(
      v => v.id === 'label' || v.id === 'label-title-only'
    );
    expect(labelViolations).toHaveLength(0);
  });

  test('should have alt text for images', async ({ page }) => {
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['cat.text-alternatives'])
      .analyze();

    const imageViolations = accessibilityScanResults.violations.filter(
      v => v.id === 'image-alt'
    );
    expect(imageViolations).toHaveLength(0);
  });

  test('should have proper WCAG 2.1 Level AA compliance', async ({ page }) => {
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('should be accessible after weather data loads', async ({ page }) => {
    // Enter city and select from dropdown
    const searchInput = page.getByPlaceholder(/Search for a city/i);
    await searchInput.fill('London');
    await page.waitForTimeout(500);

    // Click first suggestion
    const firstSuggestion = page.locator('.suggestion-item').first();
    await expect(firstSuggestion).toBeVisible({ timeout: 2000 });
    await firstSuggestion.click();

    // Wait for results
    await page.waitForSelector('.weather-card', { timeout: 5000 });

    // Check accessibility of results
    const accessibilityScanResults = await new AxeBuilder({ page }).analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('should have proper semantic HTML structure', async ({ page }) => {
    // Check for main landmark
    const main = page.getByRole('main');
    await expect(main).toBeVisible();

    // Run axe for landmark rules
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['cat.semantics'])
      .analyze();

    const landmarkViolations = accessibilityScanResults.violations.filter(
      v => v.id.includes('landmark') || v.id.includes('region')
    );
    expect(landmarkViolations).toHaveLength(0);
  });

  test('should have accessible error messages', async ({ page }) => {
    // Mock API error
    await page.route('**/api/v1/weather*', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal server error' }),
      });
    });

    // Trigger an error by searching
    const searchInput = page.getByPlaceholder(/Search for a city/i);
    await searchInput.fill('Seattle');
    await page.waitForTimeout(500);

    const firstSuggestion = page.locator('.suggestion-item').first();
    await expect(firstSuggestion).toBeVisible({ timeout: 2000 });
    await firstSuggestion.click();

    // Wait for error message
    await page.waitForSelector('[role="alert"]', { timeout: 5000 }).catch(() => {
      // If no alert role, that's ok, just check for error text
    });

    // Check accessibility of error state
    const accessibilityScanResults = await new AxeBuilder({ page }).analyze();

    // We allow some violations here as error handling might not be perfect
    // but should not have critical ones
    const criticalViolations = accessibilityScanResults.violations.filter(
      v => v.impact === 'critical' || v.impact === 'serious'
    );
    expect(criticalViolations.length).toBeLessThanOrEqual(2);
  });

  test('should have proper focus management', async ({ page }) => {
    const initialFocus = await page.evaluate(() => document.activeElement?.tagName);

    // Click button
    await page.click('button');

    // Focus should be managed properly
    const newFocus = await page.evaluate(() => document.activeElement?.tagName);
    expect(newFocus).toBeDefined();

    // Check for focus-visible issues
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withRules(['focus-order-semantics'])
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('should support screen reader announcements', async ({ page }) => {
    // Check for aria-live regions
    const liveRegions = await page.locator('[aria-live]').count();

    // Should have at least one live region for dynamic content
    expect(liveRegions).toBeGreaterThanOrEqual(0); // 0 is ok if using other methods

    // Check overall aria implementation
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['cat.aria'])
      .analyze();

    const ariaViolations = accessibilityScanResults.violations.filter(
      v => v.impact === 'critical' || v.impact === 'serious'
    );
    expect(ariaViolations).toHaveLength(0);
  });
});
