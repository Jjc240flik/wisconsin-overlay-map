# Wisconsin Overlay Map - Production Docker Image
FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    gdal-bin \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium

# Copy application
COPY . .

# Environment
ENV PYTHONUNBUFFERED=1
ENV POSTGRES_HOST=db

# Default command
CMD ["python", "main.py", "--county", "Brown"]