# Kensa-AI Tester
# Production Docker image with full testing capabilities

FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip, setuptools, wheel to fix CVEs (wheel >=0.46.0, setuptools >=80.0)
RUN pip install --no-cache-dir --upgrade pip setuptools>=82.0.0 wheel>=0.46.3

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Install dev dependencies for testing
COPY pyproject.toml .
RUN pip install --no-cache-dir --user pytest pytest-asyncio pytest-cov pytest-mock

# Production image
FROM python:3.11-slim

LABEL maintainer="Kensa-AI Lab"
LABEL description="Open-source red teaming toolkit for AI systems"
LABEL version="0.1.0"

# Install runtime dependencies + apply security patches (glibc CVE fixes)
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash redteam

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /home/redteam/.local

# Remove setuptools/wheel from runtime (not needed, fixes Trivy CVEs)
RUN pip install --no-cache-dir --upgrade pip setuptools>=82.0.0 wheel>=0.46.3 && \
    rm -rf /usr/local/lib/python3.11/site-packages/setuptools/_vendor/jaraco* && \
    rm -rf /usr/local/lib/python3.11/site-packages/setuptools/_vendor/wheel* && \
    rm -rf /usr/local/lib/python3.11/site-packages/wheel-0.45* && \
    find /home/redteam/.local -name 'wheel-0.45*' -delete && \
    pip uninstall -y virtualenv pre-commit 2>/dev/null || true

# Copy application code
COPY --chown=redteam:redteam . .

# Make entrypoint executable
RUN chmod +x /app/docker-entrypoint.sh

# Set environment
ENV PATH=/home/redteam/.local/bin:$PATH
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Create directories for configs and reports
RUN mkdir -p /app/configs /app/reports /app/logs && \
    chown -R redteam:redteam /app

# Switch to non-root user
USER redteam

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import kensa_ai; print('OK')" || exit 1

# Default entrypoint
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD [""]
