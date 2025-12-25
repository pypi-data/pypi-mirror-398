import { test, expect } from '@playwright/test';

test.describe('Visual Regression Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/', { waitUntil: 'load' });
    await page.waitForSelector('h1:has-text("MSN Weather")', { timeout: 10000 });
  });

  test('should match homepage screenshot', async ({ page }) => {
    await expect(page).toHaveScreenshot('homepage.png', {
      fullPage: true,
      maxDiffPixels: 100,
    });
  });

  test('should match homepage on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(page).toHaveScreenshot('homepage-mobile.png', {
      fullPage: true,
      maxDiffPixels: 100,
    });
  });

  test('should match homepage on tablet viewport', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(page).toHaveScreenshot('homepage-tablet.png', {
      fullPage: true,
      maxDiffPixels: 100,
    });
  });

  test('should match homepage on desktop viewport', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await expect(page).toHaveScreenshot('homepage-desktop.png', {
      fullPage: true,
      maxDiffPixels: 100,
    });
  });

  test('should match autocomplete dropdown', async ({ page }) => {
    // Open autocomplete
    await page.fill('input[type="text"]', 'Lon');
    await page.waitForTimeout(500); // Wait for autocomplete to render

    await expect(page).toHaveScreenshot('autocomplete-dropdown.png', {
      maxDiffPixels: 100,
    });
  });

  test('should match weather results display', async ({ page }) => {
    // Enter city and get weather
    await page.fill('input[type="text"]', 'London');
    await page.click('button:has-text("Get Weather")');

    // Wait for results
    await page.waitForSelector('.weather-result', { timeout: 5000 });
    await page.waitForTimeout(500); // Wait for animations

    await expect(page).toHaveScreenshot('weather-results.png', {
      fullPage: true,
      maxDiffPixels: 150, // Allow slightly more diff for dynamic content
    });
  });

  test('should match loading state', async ({ page }) => {
    // Click get weather and quickly capture loading state
    await page.fill('input[type="text"]', 'Paris');

    // Start request and capture loading
    const responsePromise = page.waitForResponse(response =>
      response.url().includes('/api/weather') && response.status() === 200
    );

    await page.click('button:has-text("Get Weather")');

    // Capture loading state quickly
    await page.waitForTimeout(100);
    await expect(page).toHaveScreenshot('loading-state.png', {
      maxDiffPixels: 100,
    });

    await responsePromise;
  });

  test('should match error state', async ({ page }) => {
    // Trigger error
    await page.fill('input[type="text"]', '!!!invalid!!!');
    await page.click('button:has-text("Get Weather")');

    // Wait for error to display
    await page.waitForTimeout(2000);

    await expect(page).toHaveScreenshot('error-state.png', {
      fullPage: true,
      maxDiffPixels: 100,
    });
  });

  test('should match empty state', async ({ page }) => {
    // Just homepage without interaction
    await expect(page).toHaveScreenshot('empty-state.png', {
      fullPage: true,
      maxDiffPixels: 50,
    });
  });

  test('should match focus states', async ({ page }) => {
    // Tab to input
    await page.keyboard.press('Tab');
    await expect(page).toHaveScreenshot('input-focused.png', {
      maxDiffPixels: 100,
    });

    // Tab to button
    await page.keyboard.press('Tab');
    await expect(page).toHaveScreenshot('button-focused.png', {
      maxDiffPixels: 100,
    });
  });

  test('should match hover states', async ({ page }) => {
    // Hover over button
    await page.hover('button:has-text("Get Weather")');
    await page.waitForTimeout(100); // Wait for hover transition

    await expect(page).toHaveScreenshot('button-hover.png', {
      maxDiffPixels: 100,
    });
  });

  test('should match dark mode (if supported)', async ({ page }) => {
    // Check if dark mode toggle exists
    const darkModeToggle = page.locator('[aria-label*="dark mode"]');
    const exists = await darkModeToggle.count();

    if (exists > 0) {
      await darkModeToggle.click();
      await page.waitForTimeout(300); // Wait for theme transition

      await expect(page).toHaveScreenshot('homepage-dark-mode.png', {
        fullPage: true,
        maxDiffPixels: 100,
      });
    } else {
      // Skip if no dark mode
      test.skip();
    }
  });

  test('should match responsive breakpoint transitions', async ({ page }) => {
    const breakpoints = [
      { width: 320, height: 568, name: 'mobile-small' },
      { width: 375, height: 667, name: 'mobile-medium' },
      { width: 414, height: 896, name: 'mobile-large' },
      { width: 768, height: 1024, name: 'tablet' },
      { width: 1024, height: 768, name: 'tablet-landscape' },
      { width: 1280, height: 720, name: 'desktop-small' },
      { width: 1920, height: 1080, name: 'desktop-large' },
    ];

    for (const breakpoint of breakpoints) {
      await page.setViewportSize({
        width: breakpoint.width,
        height: breakpoint.height
      });
      await page.waitForTimeout(200); // Wait for reflow

      await expect(page).toHaveScreenshot(`breakpoint-${breakpoint.name}.png`, {
        fullPage: true,
        maxDiffPixels: 100,
      });
    }
  });

  test('should match scrolled state with long content', async ({ page }) => {
    // Get weather to populate content
    await page.fill('input[type="text"]', 'Tokyo');
    await page.click('button:has-text("Get Weather")');
    await page.waitForSelector('.weather-result', { timeout: 5000 });

    // Scroll down
    await page.evaluate(() => window.scrollTo(0, 300));
    await page.waitForTimeout(200);

    await expect(page).toHaveScreenshot('scrolled-content.png', {
      maxDiffPixels: 150,
    });
  });

  test('should match animation end states', async ({ page }) => {
    // Fill input to trigger animation
    await page.fill('input[type="text"]', 'Berlin');
    await page.click('button:has-text("Get Weather")');

    // Wait for results and animations to complete
    await page.waitForSelector('.weather-result', { timeout: 5000 });
    await page.waitForTimeout(1000); // Wait for all animations

    await expect(page).toHaveScreenshot('animations-complete.png', {
      fullPage: true,
      maxDiffPixels: 150,
    });
  });
});
