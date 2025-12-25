import { test, expect } from '@playwright/test';

test.describe('MSN Weather App - Basic Functionality', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/', { waitUntil: 'load' });
    await page.waitForSelector('h1:has-text("MSN Weather")', { timeout: 10000 });
  });

  test('should display app header and title', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /MSN Weather/ })).toBeVisible();
    await expect(page.getByText('Get real-time weather information for any city')).toBeVisible();
  });

  test('should show empty state initially', async ({ page }) => {
    await expect(page.getByText('Search for a city')).toBeVisible();
    await expect(page.getByText('Start typing in the search box above')).toBeVisible();
  });

  test('should have search autocomplete input', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/Search for a city/i);
    await expect(searchInput).toBeVisible();
    await expect(searchInput).toBeEnabled();
  });

  test('should have "Use My Location" button', async ({ page }) => {
    const locationButton = page.getByRole('button', { name: /Use My Location/i });
    await expect(locationButton).toBeVisible();
    await expect(locationButton).toBeEnabled();
  });
});

test.describe('Weather Search', () => {
  test('should search for a city and display weather', async ({ page }) => {
    // Mock the API response
    await page.route('**/api/v1/weather*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          location: {
            city: 'Seattle',
            country: 'USA',
          },
          temperature: 15.5,
          condition: 'Partly Cloudy',
          humidity: 65,
          wind_speed: 12.5,
        }),
      });
    });

    // Mock recent searches endpoint
    await page.route('**/api/v1/recent-searches', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ recent_searches: [] }),
        });
      }
    });

    await page.goto('/');

    // Type in the search box
    const searchInput = page.getByPlaceholder(/Search for a city/i);
    await searchInput.fill('Seattle');

    // Wait for autocomplete dropdown to appear
    await page.waitForTimeout(500);

    // Click on the first suggestion
    const firstSuggestion = page.locator('.suggestion-item').first();
    await expect(firstSuggestion).toBeVisible({ timeout: 2000 });
    await firstSuggestion.click();

    // Wait for weather data to load
    await expect(page.getByText('Seattle')).toBeVisible({ timeout: 5000 });
    await expect(page.getByText('USA')).toBeVisible();
    await expect(page.getByText('Partly Cloudy')).toBeVisible();
  });

  test('should display error message on failed request', async ({ page }) => {
    // Mock failed API response
    await page.route('**/api/v1/weather*', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'Internal Server Error',
          message: 'Failed to fetch weather data',
        }),
      });
    });

    await page.route('**/api/v1/recent-searches', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ recent_searches: [] }),
      });
    });

    await page.goto('/');

    const searchInput = page.getByPlaceholder(/Search for a city/i);
    await searchInput.fill('Seattle');
    await page.waitForTimeout(500);

    // Click on the first suggestion to trigger the weather fetch
    const firstSuggestion = page.locator('.suggestion-item').first();
    await expect(firstSuggestion).toBeVisible({ timeout: 2000 });
    await firstSuggestion.click();

    // Wait for error message
    await expect(page.getByRole('alert')).toBeVisible({ timeout: 5000 });
    await expect(page.getByText(/Failed to fetch weather/i)).toBeVisible();
  });
});

test.describe('Temperature Unit Conversion', () => {
  test('should toggle between Celsius and Fahrenheit', async ({ page }) => {
    // Mock successful weather response
    await page.route('**/api/v1/weather*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          location: { city: 'Seattle', country: 'USA' },
          temperature: 20,
          condition: 'Sunny',
          humidity: 60,
          wind_speed: 10,
        }),
      });
    });

    await page.route('**/api/v1/recent-searches', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ recent_searches: [] }),
      });
    });

    await page.goto('/');

    // Search for a city
    const searchInput = page.getByPlaceholder(/Search for a city/i);
    await searchInput.fill('Seattle');
    await page.waitForTimeout(500);

    // Click on the first suggestion
    const firstSuggestion = page.locator('.suggestion-item').first();
    await expect(firstSuggestion).toBeVisible({ timeout: 2000 });
    await firstSuggestion.click();

    // Wait for weather to load
    await page.waitForSelector('.temperature-main', { timeout: 5000 });

    // Check initial temperature (should be in Celsius)
    const tempDisplay = page.locator('.temperature-main');
    await expect(tempDisplay).toContainText('°C');

    // Click unit toggle button
    const unitToggle = page.locator('.unit-toggle');
    await unitToggle.click();

    // Check temperature is now in Fahrenheit
    await expect(tempDisplay).toContainText('°F');

    // Toggle back to Celsius
    await unitToggle.click();
    await expect(tempDisplay).toContainText('°C');
  });

  test('should persist temperature unit preference', async ({ page, context }) => {
    // Mock API
    await page.route('**/api/v1/weather*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          location: { city: 'Seattle', country: 'USA' },
          temperature: 20,
          condition: 'Sunny',
          humidity: 60,
          wind_speed: 10,
        }),
      });
    });

    await page.route('**/api/v1/recent-searches', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ recent_searches: [] }),
      });
    });

    await page.goto('/');

    // Search and toggle to Fahrenheit
    const searchInput = page.getByPlaceholder(/Search for a city/i);
    await searchInput.fill('Seattle');
    await page.waitForTimeout(500);

    const firstSuggestion = page.locator('.suggestion-item').first();
    await expect(firstSuggestion).toBeVisible({ timeout: 2000 });
    await firstSuggestion.click();

    await page.waitForSelector('.unit-toggle', { timeout: 5000 });
    await page.locator('.unit-toggle').click();

    // Reload the page
    await page.reload();

    // Search again
    await searchInput.fill('Seattle');
    await page.waitForTimeout(500);

    const secondSuggestion = page.locator('.suggestion-item').first();
    await expect(secondSuggestion).toBeVisible({ timeout: 2000 });
    await secondSuggestion.click();

    await page.waitForSelector('.temperature-main', { timeout: 5000 });

    // Should still be in Fahrenheit
    await expect(page.locator('.temperature-main')).toContainText('°F');
  });
});

test.describe('Recent Searches', () => {
  test('should display recent searches after a successful search', async ({ page }) => {
    // Mock API responses
    await page.route('**/api/v1/weather*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          location: { city: 'Seattle', country: 'USA' },
          temperature: 20,
          condition: 'Sunny',
          humidity: 60,
          wind_speed: 10,
        }),
      });
    });

    let recentSearches: any[] = [];
    await page.route('**/api/v1/recent-searches', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ recent_searches: recentSearches }),
        });
      }
    });

    await page.goto('/');

    // Perform a search
    const searchInput = page.getByPlaceholder(/Search for a city/i);
    await searchInput.fill('Seattle');
    await page.waitForTimeout(500);

    const firstSuggestion = page.locator('.suggestion-item').first();
    await expect(firstSuggestion).toBeVisible({ timeout: 2000 });
    await firstSuggestion.click();

    // Wait for weather to load
    await page.waitForSelector('.weather-card', { timeout: 5000 });

    // Update mock to return recent searches
    recentSearches = [{ city: 'Seattle', country: 'USA' }];

    // Reload to fetch recent searches
    await page.reload();

    // Recent searches should be visible
    await expect(page.getByText('Recent Searches')).toBeVisible();
    await expect(page.getByText('Seattle, USA')).toBeVisible();
  });

  test('should allow clicking on recent search to fetch weather', async ({ page }) => {
    const recentSearches = [
      { city: 'Seattle', country: 'USA' },
      { city: 'New York', country: 'USA' },
    ];

    await page.route('**/api/v1/recent-searches', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ recent_searches: recentSearches }),
      });
    });

    await page.route('**/api/v1/weather*', async (route) => {
      const url = new URL(route.request().url());
      const city = url.searchParams.get('city');

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          location: { city: city || 'Unknown', country: 'USA' },
          temperature: 20,
          condition: 'Sunny',
          humidity: 60,
          wind_speed: 10,
        }),
      });
    });

    await page.goto('/');

    // Click on a recent search
    await page.getByText('New York, USA').click();

    // Wait for weather to load
    await expect(page.getByText('New York')).toBeVisible({ timeout: 5000 });
  });

  test('should clear recent searches', async ({ page }) => {
    const recentSearches = [
      { city: 'Seattle', country: 'USA' },
      { city: 'New York', country: 'USA' },
    ];

    await page.route('**/api/v1/recent-searches', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ recent_searches: recentSearches }),
        });
      } else if (route.request().method() === 'DELETE') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ message: 'Recent searches cleared' }),
        });
      }
    });

    await page.goto('/');

    // Recent searches should be visible
    await expect(page.getByText('Recent Searches')).toBeVisible();

    // Click clear button
    await page.getByRole('button', { name: 'Clear' }).click();

    // Update mock to return empty searches
    await page.route('**/api/v1/recent-searches', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ recent_searches: [] }),
      });
    });

    // Recent searches section should not be visible
    await expect(page.getByText('Recent Searches')).not.toBeVisible();
  });
});

test.describe('Responsive Design', () => {
  test('should display correctly on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });

    await page.route('**/api/v1/recent-searches', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ recent_searches: [] }),
      });
    });

    await page.goto('/');

    // Check that elements are visible on mobile
    await expect(page.getByRole('heading', { name: /MSN Weather/ })).toBeVisible();
    await expect(page.getByPlaceholder(/Search for a city/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /Use My Location/i })).toBeVisible();
  });
});
