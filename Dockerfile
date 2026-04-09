FROM python:3.11-slim

WORKDIR /app

# Install system deps (curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    "openenv-core[core]>=0.2.2" \
    "openai>=1.0.0" \
    "uvicorn[standard]>=0.24.0" \
    "fastapi>=0.100.0" \
    "pydantic>=2.0.0"

# Copy all project files
COPY . /app

# Set Python path so all imports resolve correctly from /app
ENV PYTHONPATH="/app:$PYTHONPATH"

# Health check on the correct HF Space port (7860)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -sf -X POST http://localhost:7860/reset \
        -H "Content-Type: application/json" \
        -d '{}' || exit 1

EXPOSE 7860

CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]
