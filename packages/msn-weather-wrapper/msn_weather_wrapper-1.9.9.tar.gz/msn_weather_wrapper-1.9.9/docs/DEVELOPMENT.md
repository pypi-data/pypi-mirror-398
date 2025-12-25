# Development Guide

Complete guide for developing, testing, and contributing to MSN Weather Wrapper.

---

## Quick Start

### Containerized Development (Recommended)

Get a complete development environment in containers:

```bash
git clone https://github.com/jim-wyatt/msn-weather-wrapper.git
cd msn-weather-wrapper

# One-time setup
./dev.sh setup

# Start development
./dev.sh start

# Access services:
# - Frontend: http://localhost:5173 (Vite dev server with HMR)
# - Backend API: http://localhost:5000
# - Health Check: http://localhost:5000/api/v1/health
```

### Local Development

For direct local development without containers:

```bash
# Backend setup
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pre-commit install

# Start backend
python api.py

# Frontend setup (separate terminal)
cd frontend
npm install
npm run dev
```

---

## Development Workflow

### Container Development Commands

```bash
# Daily workflow
./dev.sh start    # Start all services
./dev.sh status   # Check service health
./dev.sh logs     # Watch logs
./dev.sh stop     # Stop all services
./dev.sh restart  # Restart services

# Testing
./dev.sh test     # Run all tests
./dev.sh shell-api      # Backend shell
./dev.sh shell-frontend # Frontend shell

# Maintenance
./dev.sh rebuild  # Rebuild from scratch
./dev.sh clean    # Remove containers & volumes
./dev.sh clean --gitignore  # Also clean git-ignored files (preview first)
./dev.sh docs     # Build & serve documentation
```

### Making Code Changes

#### Backend Changes
1. Edit files in `src/msn_weather_wrapper/` or `api.py`
2. Flask auto-reloads automatically
3. Test: `pytest tests/test_*.py`
4. Check types: `mypy src/`
5. Format: `ruff format .`

#### Frontend Changes
1. Edit files in `frontend/src/`
2. Vite HMR updates instantly
3. Test: `npm run test:e2e`
4. Type check: `npm run type-check`
5. Build: `npm run build`

---

## Code Quality Tools

### Python

```bash
# Format code
ruff format .

# Lint code
ruff check .
ruff check . --fix  # Auto-fix

# Type checking
mypy src/msn_weather_wrapper

# Run all checks
pre-commit run --all-files
```

### TypeScript

```bash
cd frontend

# Type checking
npm run type-check

# Build (includes type checking)
npm run build
```

---

## Testing

### Backend Testing

```bash
# All tests
pytest

# Specific test file
pytest tests/test_api.py -v

# With coverage
pytest --cov=src --cov-report=html

# Security tests
pytest tests/test_security.py -v
```

### Frontend Testing

```bash
cd frontend

# Install Playwright (first time)
npx playwright install

# Run E2E tests
npm run test:e2e

# Interactive mode
npm run test:e2e:ui

# Headed mode (see browser)
npm run test:e2e:headed
```

### Integration Testing

```bash
# Start API first
python api.py

# Run integration tests
pytest tests/test_integration.py -v
```

---

## Adding Features

### Backend Feature

1. **Write code** in `src/msn_weather_wrapper/`
2. **Add tests** in `tests/`
3. **Update types** in `models.py`
4. **Add API endpoint** in `api.py` (if needed)
5. **Update docs** in `docs/API.md`

### Frontend Feature

1. **Create component** in `frontend/src/components/`
2. **Add types** in `frontend/src/types.ts`
3. **Add E2E test** in `frontend/tests/e2e/`
4. **Update styles** as needed

---

## Dependency Management

### Python

```bash
# Edit pyproject.toml, then:
pip install -e ".[dev]"
```

### Node.js

```bash
cd frontend
npm install package-name          # Production
npm install --save-dev package   # Development
```

---

## Debugging

### Backend

```python
# Using logging
import structlog
logger = structlog.get_logger()
logger.info("debug message", variable=value)

# Using ipdb
import ipdb; ipdb.set_trace()

# In container
./dev.sh shell-api
ipython
```

### Frontend

- Open DevTools (F12)
- Console tab for logs
- Network tab for API calls
- React DevTools extension

---

## Common Tasks

### Generate Documentation

```bash
mkdocs serve       # Local preview
mkdocs build       # Build static site
mkdocs gh-deploy   # Deploy to GitHub Pages
```

### Generate SBOM

```bash
./tools/generate_sbom.sh
cat sbom_output/SBOM_SUMMARY_*.md
```

### Update Dependencies

```bash
# Python
pip install --upgrade -e ".[dev]"

# Node.js
cd frontend && npm update
```

---

## Containerized Development Details

### Architecture

- **API Container**: Python 3.12 slim (Trixie), port 5000, Flask with hot reload
- **Frontend Container**: Node 22 Trixie slim, port 5173, Vite with HMR
- **Volumes**: Source code mounted for hot reload

### Environment Variables

- **API**: `FLASK_ENV=development`, `FLASK_DEBUG=1`
- **Frontend**: `NODE_ENV=development`

---

## Troubleshooting

### Tests fail with import errors
```bash
pip install -e ".[dev]"
```

### Frontend won't start
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Container won't build
```bash
./dev.sh clean
./dev.sh setup
```

### Port already in use
```bash
# Find process
lsof -i :5000

# Kill process
kill -9 <PID>
```

---

## Contributing Guidelines

Before submitting PR:

1. ✅ All tests pass: `pytest`
2. ✅ Code formatted: `ruff format .`
3. ✅ No lint errors: `ruff check .`
4. ✅ Types valid: `mypy src/`
5. ✅ Coverage maintained: `pytest --cov=src`
6. ✅ Frontend tests pass: `npm run test:e2e`
7. ✅ Documentation updated
8. ✅ CHANGELOG.md updated

See the Contributing Guidelines section above for full guidelines.

---

## Project Structure

```
msn-weather-wrapper/
├── src/msn_weather_wrapper/    # Python package
│   ├── __init__.py             # Package exports
│   ├── client.py               # Weather client
│   ├── models.py               # Pydantic models
│   └── py.typed                # Type marker
├── tests/                      # Test suite
│   ├── test_api.py             # API tests
│   ├── test_client.py          # Client tests
│   ├── test_models.py          # Model tests
│   ├── test_security.py        # Security tests
│   └── test_integration.py     # Integration tests
├── frontend/                   # React application
│   ├── src/                    # TypeScript source
│   │   ├── components/         # React components
│   │   ├── data/               # City database
│   │   ├── App.tsx             # Main app
│   │   └── main.tsx            # Entry point
│   └── tests/e2e/              # Playwright tests
├── api.py                      # Flask REST API
├── docs/                       # Documentation
├── Containerfile               # Production container
├── Containerfile.dev           # Dev container
├── podman-compose.yml          # Production compose
└── pyproject.toml              # Python config
```

---

## Resources

- [Full Documentation](https://jim-wyatt.github.io/msn-weather-wrapper/)
- [API Reference](API.md)
- [Testing Guide](TESTING.md)
- [Security Guide](SECURITY.md)
- [Container Dev Setup](CONTAINER_DEV_SETUP.md)

---

**Need Help?**
- 🐛 [Report Issues](https://github.com/jim-wyatt/msn-weather-wrapper/issues)
- 💬 [Discussions](https://github.com/jim-wyatt/msn-weather-wrapper/discussions)
