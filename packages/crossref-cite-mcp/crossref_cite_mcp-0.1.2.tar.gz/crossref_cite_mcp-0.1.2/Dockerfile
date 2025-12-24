# Multi-stage build for minimal image size
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir build && \
    pip install --no-cache-dir .

# Runtime stage
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy source code
COPY src/ src/

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser && \
    mkdir -p /home/appuser/.crossref-cite && \
    chown -R appuser:appuser /home/appuser /app

USER appuser

# Environment defaults
ENV PYTHONUNBUFFERED=1 \
    CROSSREF_CACHE_BACKEND=json \
    CROSSREF_CACHE_PATH=/home/appuser/.crossref-cite/cache.json \
    LOG_LEVEL=INFO

# Entry point
ENTRYPOINT ["python", "-m", "crossref_cite"]
