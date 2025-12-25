# MSN Weather Frontend

A modern React + Vite frontend for the MSN Weather Wrapper API.

## Features

- 🔍 **Smart City Autocomplete** - Instant search through 130+ cities worldwide
- 🎨 **Beautiful UI** - Modern gradient design with smooth animations
- 📱 **Fully Responsive** - Perfect on desktop, tablet, and mobile
- ⚡ **Lightning Fast** - Powered by Vite for instant hot module replacement
- 🌐 **API Proxy** - Seamless integration with Flask backend
- ♿ **Accessible** - Keyboard navigation support for autocomplete

## Quick Start

### Prerequisites

- Node.js 16+ and npm
- Flask API server running on `http://localhost:5000`

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

Open `http://localhost:3000` in your browser.

### Production Build

```bash
npm run build
npm run preview
```

## How It Works

1. **City Search** - Type in the search box to see matching cities
2. **Autocomplete** - Navigate suggestions with arrow keys or mouse
3. **Weather Display** - Select a city to fetch and display weather data
4. **Real-time Updates** - Data is fetched fresh from MSN Weather via the API

## API Integration

The frontend uses Vite's proxy feature to forward API requests to the Flask backend:

```javascript
// In vite.config.js
proxy: {
  '/api': {
    target: 'http://localhost:5000',
    changeOrigin: true,
  }
}
```

This means frontend code can make requests to `/api/weather` and they'll be automatically routed to `http://localhost:5000/api/weather`.

## Components

### CityAutocomplete

A smart autocomplete input component with:
- Fuzzy search through city names
- Keyboard navigation (arrow keys, Enter, Escape)
- Click-outside to close
- Visual selection indicator

### App

Main weather application with:
- Weather data fetching and display
- Loading states
- Error handling
- Weather icons based on conditions
- Temperature, humidity, and wind speed display

## Customization

### Adding More Cities

Edit `src/data/cities.js` to add more cities:

```javascript
export const cities = [
  { name: "Your City", country: "Your Country" },
  // ... more cities
];
```

### Styling

- Global styles: `src/App.css`
- Autocomplete styles: `src/components/CityAutocomplete.css`

## Tech Stack

- **React 18** - UI library
- **Vite 5** - Build tool and dev server
- **Vanilla CSS** - No CSS framework needed, custom styles included

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## License

MIT
