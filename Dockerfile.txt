FROM python:3.11-slim

# Setup environment
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libnss3 \
    libxss1 \
    libasound2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libxcomposite1 \
    libxrandr2 \
    libxdamage1 \
    libgbm1 \
    libgtk-3-0 \
    libpango-1.0-0 \
    libx11-xcb1 \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Install Playwright and Chromium
RUN python -m playwright install --with-deps chromium

# Copy project files
COPY . .

# Expose port for Railway
EXPOSE 8000

# Start with Gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8000"]
