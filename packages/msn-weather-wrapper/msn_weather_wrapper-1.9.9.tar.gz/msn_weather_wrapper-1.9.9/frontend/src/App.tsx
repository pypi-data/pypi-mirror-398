import { useState, useEffect } from 'react';
import CityAutocomplete from './components/CityAutocomplete';
import type { City, WeatherData, RecentSearch } from './types';
import './App.css';

type TempUnit = 'C' | 'F';

function App() {
  const [weather, setWeather] = useState<WeatherData | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [recentSearches, setRecentSearches] = useState<RecentSearch[]>([]);
  const [loadingLocation, setLoadingLocation] = useState<boolean>(false);
  const [unit, setUnit] = useState<TempUnit>(() => {
    const saved = localStorage.getItem('tempUnit');
    return (saved === 'C' || saved === 'F') ? saved : 'C';
  });

  // Load recent searches on mount
  useEffect(() => {
    fetchRecentSearches();
  }, []);

  const fetchRecentSearches = async (): Promise<void> => {
    try {
      const response = await fetch('/api/v1/recent-searches', {
        credentials: 'include',
      });
      if (response.ok) {
        const data = await response.json();
        setRecentSearches(data.recent_searches || []);
      }
    } catch (err) {
      console.error('Failed to fetch recent searches:', err);
    }
  };

  const convertTemp = (tempC: number, to: TempUnit): number => {
    return to === 'F' ? (tempC * 9 / 5) + 32 : tempC;
  };

  const fetchWeatherWithRetry = async (city: City, retries = 3): Promise<void> => {
    setLoading(true);
    setError(null);

    for (let attempt = 1; attempt <= retries; attempt++) {
      try {
        const response = await fetch(
          `/api/v1/weather?city=${encodeURIComponent(city.name)}&country=${encodeURIComponent(city.country)}`,
          { credentials: 'include' }
        );

        if (!response.ok) {
          const errorData = await response.json();

          // Don't retry on client errors (4xx)
          if (response.status >= 400 && response.status < 500) {
            throw new Error(errorData.message || 'Failed to fetch weather');
          }

          // Retry on server errors (5xx) or network issues
          if (attempt === retries) {
            throw new Error(errorData.message || 'Failed to fetch weather after multiple attempts');
          }

          // Wait before retrying (exponential backoff)
          await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
          continue;
        }

        const data: WeatherData = await response.json();
        setWeather(data);
        setError(null);
        await fetchRecentSearches(); // Refresh recent searches
        break;
      } catch (err) {
        if (attempt === retries) {
          const errorMessage = err instanceof Error ? err.message : 'An unknown error occurred';
          setError(errorMessage);
          setWeather(null);
        } else {
          // Wait before retrying
          await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
        }
      }
    }

    setLoading(false);
  };

  const fetchWeatherByLocation = async (): Promise<void> => {
    if (!navigator.geolocation) {
      setError('Geolocation is not supported by your browser');
      return;
    }

    setLoadingLocation(true);
    setError(null);

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords;

        try {
          const response = await fetch(
            `/api/v1/weather/coordinates?lat=${latitude}&lon=${longitude}`,
            { credentials: 'include' }
          );

          if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Failed to fetch weather');
          }

          const data: WeatherData = await response.json();
          setWeather(data);
          setError(null);
          await fetchRecentSearches(); // Refresh recent searches
        } catch (err) {
          const errorMessage = err instanceof Error ? err.message : 'An unknown error occurred';
          setError(errorMessage);
          setWeather(null);
        } finally {
          setLoadingLocation(false);
        }
      },
      (error) => {
        setError(`Failed to get your location: ${error.message}`);
        setLoadingLocation(false);
      }
    );
  };

  const handleRecentSearchClick = (search: RecentSearch): void => {
    fetchWeatherWithRetry({ name: search.city, country: search.country });
  };

  const clearRecentSearches = async (): Promise<void> => {
    try {
      const response = await fetch('/api/v1/recent-searches', {
        method: 'DELETE',
        credentials: 'include',
      });
      if (response.ok) {
        setRecentSearches([]);
      }
    } catch (err) {
      console.error('Failed to clear recent searches:', err);
    }
  };

  const toggleUnit = (): void => {
    const newUnit: TempUnit = unit === 'C' ? 'F' : 'C';
    setUnit(newUnit);
    localStorage.setItem('tempUnit', newUnit);
  };

  const getWeatherIcon = (condition: string): string => {
    const lowerCondition = condition.toLowerCase();
    if (lowerCondition.includes('sunny') || lowerCondition.includes('clear')) return '☀️';
    if (lowerCondition.includes('cloud')) return '☁️';
    if (lowerCondition.includes('rain')) return '🌧️';
    if (lowerCondition.includes('snow')) return '❄️';
    if (lowerCondition.includes('storm') || lowerCondition.includes('thunder')) return '⛈️';
    if (lowerCondition.includes('fog') || lowerCondition.includes('mist')) return '🌫️';
    return '🌤️';
  };

  return (
    <div className="app">
      <div className="container">
        <header className="header" role="banner">
          <h1 className="title">
            <span aria-hidden="true">🌤️</span>
            <span>MSN Weather</span>
          </h1>
          <p className="subtitle">Get real-time weather information for any city</p>
        </header>

        <div className="search-section" role="search" aria-label="Weather search">
          <CityAutocomplete onCitySelect={fetchWeatherWithRetry} />
          <button
            className="location-button"
            onClick={fetchWeatherByLocation}
            disabled={loadingLocation}
            aria-label="Get weather for my current location"
            aria-busy={loadingLocation}
          >
            <span aria-hidden="true">{loadingLocation ? '⏳' : '📍'}</span>
            <span>Use My Location</span>
          </button>
        </div>

        {recentSearches.length > 0 && (
          <section className="recent-searches" aria-label="Recent weather searches">
            <div className="recent-searches-header">
              <h3 id="recent-searches-heading">Recent Searches</h3>
              <button
                className="clear-button"
                onClick={clearRecentSearches}
                aria-label="Clear all recent searches"
              >
                Clear
              </button>
            </div>
            <div
              className="recent-searches-list"
              role="list"
              aria-labelledby="recent-searches-heading"
            >
              {recentSearches.map((search, index) => (
                <button
                  key={index}
                  className="recent-search-item"
                  onClick={() => handleRecentSearchClick(search)}
                  role="listitem"
                  aria-label={`View weather for ${search.city}, ${search.country}`}
                >
                  {search.city}, {search.country}
                </button>
              ))}
            </div>
          </section>
        )}

        {loading && (
          <div className="loading" role="status" aria-live="polite" aria-busy="true">
            <div className="spinner" aria-hidden="true"></div>
            <p>Fetching weather data...</p>
          </div>
        )}

        {error && (
          <div className="error-card" role="alert" aria-live="assertive">
            <span className="error-icon" aria-hidden="true">⚠️</span>
            <div className="error-content">
              <h3>Error</h3>
              <p>{error}</p>
            </div>
          </div>
        )}

        {weather && !loading && (
          <article
            className="weather-card"
            role="region"
            aria-label={`Weather information for ${weather.location.city}, ${weather.location.country}`}
          >
            <div className="weather-header">
              <div className="location-info">
                <h2 className="location-name" id="weather-location">{weather.location.city}</h2>
                <p className="location-country">{weather.location.country}</p>
              </div>
              <div className="weather-icon-large" aria-hidden="true">
                {getWeatherIcon(weather.condition)}
              </div>
            </div>

            <div className="temperature-section">
              <div className="temperature-main">
                <span aria-label={`Temperature: ${Math.round(convertTemp(weather.temperature, unit))} degrees ${unit === 'C' ? 'Celsius' : 'Fahrenheit'}`}>
                  {Math.round(convertTemp(weather.temperature, unit))}°{unit}
                </span>
                <button
                  className="unit-toggle"
                  onClick={toggleUnit}
                  aria-label={`Switch temperature unit to ${unit === 'C' ? 'Fahrenheit' : 'Celsius'}`}
                >
                  °{unit === 'C' ? 'F' : 'C'}
                </button>
              </div>
              <div className="condition" aria-label={`Condition: ${weather.condition}`}>
                {weather.condition}
              </div>
            </div>

            <div className="weather-details" role="list" aria-label="Weather details">
              <div className="detail-item" role="listitem">
                <span className="detail-icon" aria-hidden="true">💧</span>
                <div className="detail-content">
                  <span className="detail-label" id="humidity-label">Humidity</span>
                  <span className="detail-value" aria-labelledby="humidity-label">
                    {weather.humidity}%
                  </span>
                </div>
              </div>

              <div className="detail-item" role="listitem">
                <span className="detail-icon" aria-hidden="true">💨</span>
                <div className="detail-content">
                  <span className="detail-label" id="wind-label">Wind Speed</span>
                  <span className="detail-value" aria-labelledby="wind-label">
                    {weather.wind_speed.toFixed(1)} kilometers per hour
                  </span>
                </div>
              </div>
            </div>
          </article>
        )}

        {!weather && !loading && !error && (
          <div className="empty-state" role="status" aria-live="polite">
            <div className="empty-icon" aria-hidden="true">🔍</div>
            <h3>Search for a city</h3>
            <p>Start typing in the search box above to get weather information</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
