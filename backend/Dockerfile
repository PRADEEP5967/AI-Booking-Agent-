# Use an official, minimal, and secure Python image
FROM python:3.11-slim

# Set environment variables for best practices
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

# Set working directory
WORKDIR /app

# Install system dependencies for modern Python and common packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Upgrade pip to latest version for modern dependency resolution
RUN pip install --upgrade pip

# Copy requirements first for better Docker layer caching
COPY backend/requirements.txt .

# Install Python dependencies robustly
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend application code
COPY backend/ .

# Expose the port (Railway will set PORT environment variable)
EXPOSE $PORT

# Use a non-root user for security (modern best practice)
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# Use exec form for CMD for signal handling and robustness
# Railway will override this with the startCommand from railway.json
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]