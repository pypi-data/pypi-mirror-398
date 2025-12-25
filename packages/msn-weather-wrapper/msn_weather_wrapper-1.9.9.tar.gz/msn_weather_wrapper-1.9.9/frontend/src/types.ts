export interface City {
  name: string;
  country: string;
}

export interface RecentSearch {
  city: string;
  country: string;
}

export interface WeatherData {
  location: {
    city: string;
    country: string;
  };
  temperature: number;
  condition: string;
  humidity: number;
  wind_speed: number;
}

export interface WeatherError {
  error: string;
  message: string;
}
