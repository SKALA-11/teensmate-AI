# Build stage
FROM python:3.12-slim AS builder

WORKDIR /app

# Install uv via official installer (faster & recommended)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# .venv 경로를 /app/.venv 로 고정, 시스템 파이썬과 분리
ENV UV_PROJECT_ENVIRONMENT=/app/.venv

# Install dependencies (locked, no internet after this)
RUN uv sync --frozen --no-dev


# Runtime stage
FROM python:3.12-slim

WORKDIR /app

# curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Copy venv from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY config ./config
COPY prompts ./prompts
COPY agents ./agents
COPY tools ./tools
COPY rag ./rag
COPY stock ./stock
COPY backend ./backend
COPY frontend ./frontend

# Set environment
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"

# Expose ports
EXPOSE 8000 8501

# Health check (curl 사용 - requests 패키지 불필요)
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD curl -sf http://localhost:8000/api/v1/health || exit 1

# Default: backend
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
