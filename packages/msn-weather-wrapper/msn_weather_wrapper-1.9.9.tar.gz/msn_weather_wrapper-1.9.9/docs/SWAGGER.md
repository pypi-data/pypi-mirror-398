# Interactive API Documentation (Swagger UI)

## Overview

MSN Weather Wrapper provides **interactive API documentation** powered by Swagger UI (Flasgger). This allows you to explore, test, and understand the API directly from your browser.

## Accessing Swagger UI

### Local Development
When running the API locally:
```
http://localhost:5000/apidocs/
```

### Container Deployment
When running via Docker/Podman:
```
http://localhost:8080/apidocs/
```

### Production
Replace `localhost` with your domain:
```
https://your-domain.com/apidocs/
```

## Features

### 📖 Complete Documentation
- All 11 endpoints documented with detailed descriptions
- Request parameter specifications (query, body, headers)
- Response schemas with examples
- Error response documentation

### 🧪 Interactive Testing
- **Try it out**: Execute API calls directly from the browser
- **Real-time responses**: See actual API responses
- **Parameter validation**: Test with different inputs
- **Authentication support**: Session-based auth for recent searches

### 🏷️ Organized by Category
- **Health**: Health checks, liveness, readiness probes
- **Weather**: Weather data retrieval endpoints
- **Searches**: Recent search history management

### 🔍 Schema Validation
- OpenAPI 2.0 compliant specification
- Type-safe request/response schemas
- Automatic validation feedback

## OpenAPI Specification

The raw OpenAPI specification is available at:
```
http://localhost:5000/apispec.json
```

This can be imported into:
- Postman
- Insomnia
- API testing tools
- Code generators

## Available Endpoints

### Health Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Basic health check |
| `/api/v1/health` | GET | Versioned health check |
| `/api/v1/health/live` | GET | Kubernetes liveness probe |
| `/api/v1/health/ready` | GET | Kubernetes readiness probe |

### Weather Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/weather` | GET | Get weather by city (query params) |
| `/api/v1/weather` | GET | Versioned weather by city |
| `/api/weather` | POST | Get weather by city (JSON body) |
| `/api/v1/weather` | POST | Versioned weather by city (POST) |
| `/api/v1/weather/coordinates` | GET | Get weather by latitude/longitude |

### Search History Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/recent-searches` | GET | Get recent search history |
| `/api/v1/recent-searches` | DELETE | Clear search history |

## Using Swagger UI

### 1. Explore Endpoints
Click on any endpoint to view:
- Description and purpose
- Required/optional parameters
- Request/response examples
- Authentication requirements

### 2. Test an Endpoint
1. Click **"Try it out"** button
2. Fill in required parameters
3. Click **"Execute"**
4. View the response below

### 3. Example: Test Weather API
```
1. Navigate to: http://localhost:5000/apidocs/
2. Find "GET /api/weather" under "weather" tag
3. Click "Try it out"
4. Enter:
   - city: Seattle
   - country: USA
5. Click "Execute"
6. See the live weather response!
```

## Authentication

For endpoints requiring session authentication (recent searches):
1. Make a weather request first to establish a session
2. The session cookie will be automatically included
3. Recent searches endpoints will now work

## Rate Limiting

Rate limits are enforced:
- **Weather endpoints**: 30 requests/minute per IP
- **Global**: 200 requests/hour

Exceeding limits returns HTTP 429 (Too Many Requests).

## Configuration

Swagger UI configuration in `api.py`:
```python
swagger_config = {
    "specs_route": "/apidocs/",
    "swagger_ui": True,
    # ... other settings
}
```

OpenAPI template includes:
- API metadata (title, description, version)
- Security definitions
- Tag descriptions
- License information

## Benefits

### For Developers
- ✅ No need to read lengthy documentation
- ✅ Test APIs without writing code
- ✅ Understand request/response structure instantly
- ✅ Export OpenAPI spec for code generation

### For Testing
- ✅ Manual integration testing
- ✅ Validate API behavior
- ✅ Debug request/response issues
- ✅ Share API capabilities with team

### For Documentation
- ✅ Always up-to-date with code
- ✅ Interactive examples
- ✅ Self-service API exploration
- ✅ Reduces support questions

## Troubleshooting

### Swagger UI Not Loading
```bash
# Check if Flask is running
curl http://localhost:5000/api/health

# Verify Swagger route
curl http://localhost:5000/apispec.json
```

### 404 Not Found
- Ensure Flasgger is installed: `pip install flasgger`
- Verify the API is running on the expected port
- Check for proxy configuration issues

### Missing Endpoints
- Endpoints must have OpenAPI docstrings to appear
- Verify YAML formatting in docstrings
- Check server logs for parsing errors

## Related Documentation

- [API Reference](API.md) - Complete REST API documentation
- [Development Guide](DEVELOPMENT.md) - Setup and development workflow
- [Security](SECURITY.md) - API security features

---

**Quick Start:**
```bash
# Start the API
python api.py

# Open your browser to:
http://localhost:5000/apidocs/
```

Enjoy exploring the API! 🚀
