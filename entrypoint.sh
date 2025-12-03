#!/bin/sh
set -e

echo "Starting Telethon FastAPI entrypoint..."

# Ensure we're in the app directory
cd /app

# Debug: Show current directory and contents
echo "Current directory: $(pwd)"
echo "Directory contents:"
ls -la

# Run Alembic migrations if available
if [ -f "alembic.ini" ] && command -v alembic >/dev/null 2>&1; then
    echo "Running Alembic migrations..."
    alembic upgrade head || {
        echo "Warning: Alembic migration failed (may not exist or DB unreachable); continuing..."
    }
else
    echo "Alembic config not found or alembic not installed; skipping migrations"
fi

echo "Starting Uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
