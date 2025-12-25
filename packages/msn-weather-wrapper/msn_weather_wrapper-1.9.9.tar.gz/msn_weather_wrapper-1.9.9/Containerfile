# Multi-stage Dockerfile - Unified Flask API + React Frontend
# Stage 1: Build React frontend
FROM node:lts-trixie-slim@sha256:9ad7e7db423b2ca7ddcc01568da872701ef6171505bd823978736247885c7eb4 AS frontend-builder

WORKDIR /frontend

# Copy frontend package files
COPY frontend/package.json ./

# Install frontend dependencies
RUN npm install

# Copy frontend source
COPY frontend/ .

# Build frontend
RUN npm run build

# Stage 2: Python + Nginx unified container
FROM python:3.12-slim-trixie

WORKDIR /app

# Install system dependencies (nginx, gcc for Python packages, supervisor)
RUN apt-get update && apt-get install -y \
    gcc \
    nginx \
    supervisor \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python project files
COPY pyproject.toml .
COPY README.md .
COPY src/ src/
COPY api.py .

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Copy built frontend from builder stage
COPY --from=frontend-builder /frontend/dist /usr/share/nginx/html

# Copy nginx configuration
COPY config/nginx.conf /etc/nginx/sites-available/default

# Create supervisor configuration
RUN mkdir -p /var/log/supervisor
COPY config/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Set production environment variables
# Note: Override FLASK_SECRET_KEY in production with a secure value
ENV FLASK_ENV=production \
    FLASK_DEBUG=0 \
    CORS_ORIGINS=* \
    RATE_LIMIT_PER_IP=30 \
    RATE_LIMIT_GLOBAL=200 \
    CACHE_DURATION=300 \
    REQUEST_TIMEOUT=15

# Generate a secret key at build time (should be overridden in production)
# Use docker run -e FLASK_SECRET_KEY=your-key to override
RUN python -c "import secrets; print(f'FLASK_SECRET_KEY={secrets.token_hex(32)}')" >> /app/.env.production

# Expose port 80 (nginx will handle both frontend and API proxying)
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:80/api/v1/health/ready || exit 1

# Run supervisor to manage nginx and gunicorn
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
