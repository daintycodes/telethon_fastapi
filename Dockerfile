FROM python:3.12-slim

# Version: 2024-12-03-v3 (fix entrypoint path)
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application
COPY . .

# Copy entrypoint to root and make executable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Verify app directory exists
RUN ls -la /app && ls -la /app/app || echo "Warning: app directory structure issue"

# Default command: run entrypoint (migrations + uvicorn)
ENTRYPOINT ["/entrypoint.sh"]
