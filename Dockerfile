FROM python:3.11-slim

# Install Chrome and dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg2 \
    ca-certificates \
    curl \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy backend requirements and install
COPY backend/requirements.txt backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Install Playwright browsers
RUN playwright install --with-deps chromium

# Copy backend application code
COPY backend/ backend/

# Create directories for runtime data
RUN mkdir -p backend/data backend/logs backend/screenshots backend/input

# Copy environment files (optional — credentials can be set per-user in browser Settings)
COPY .env* ./

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 5000

# Run from backend directory
WORKDIR /app/backend
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]
