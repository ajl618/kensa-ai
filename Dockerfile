# Kensa-AI Tester
# Production Docker image with full testing capabilities

FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

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

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash redteam

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /home/redteam/.local

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
