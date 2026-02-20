# Build stage
FROM python:3.12-slim as builder

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml .
COPY uv.lock .

# Install dependencies
RUN uv sync --frozen


# Runtime stage
FROM python:3.12-slim

WORKDIR /app

# Copy dependencies from builder
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

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app:$PYTHONPATH"

# Expose ports
EXPOSE 8000 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/api/v1/health')"

# Default command (run backend)
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
