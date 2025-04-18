FROM python:3.11-slim

# Tell Playwright where to install browsers
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    gnupg \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libasound2 \
    libxss1 \
    libgtk-3-0 \
    libx11-xcb1 \
    libgbm1 \
    libpango-1.0-0 \
    fonts-liberation \
    libdbus-1-3 \
    libcups2 \
    json5 \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# ✅ Explicitly install Chromium to known location
RUN python -m playwright install chromium

# Copy your app code
COPY . .

# Open the backend port
EXPOSE 8000

# Start Gunicorn
CMD gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120

