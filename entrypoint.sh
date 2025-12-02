#!/bin/sh
set -e

echo "Starting Telethon FastAPI entrypoint..."

# Run Alembic migrations if available
if command -v alembic >/dev/null 2>&1; then
    echo "Running Alembic migrations..."
    alembic upgrade head || {
        echo "Warning: Alembic migration failed (may not exist or DB unreachable); continuing..."
    }
else
    echo "Alembic not found in PATH; skipping migrations"
fi

echo "Starting Uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
