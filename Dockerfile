# FinSight backend (FastAPI) for Railway.
# Build context is the repository root; .dockerignore admits only backend/ and sample_statements/.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    FINSIGHT_ENV=production \
    FINSIGHT_DATA_DIR=/data

WORKDIR /app

# Dependencies first so code changes don't reinstall them
COPY backend/requirements.txt backend/requirements.txt
RUN pip install -r backend/requirements.txt

COPY backend/ backend/
COPY sample_statements/ sample_statements/

WORKDIR /app/backend
EXPOSE 8000

# One worker: the login rate limits and the hourly demo cleanup live in this single process.
# Runs as root because Railway volumes are mounted root-owned.
CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --no-server-header"]
