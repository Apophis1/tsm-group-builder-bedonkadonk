FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

# Install system packages required for Chromium
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
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies and Playwright
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Install Playwright Chromium (this is the key step)
RUN python -m playwright install --with-deps chromium

# Copy your project files
COPY . .

# Expose Railway’s expected port
EXPOSE 8000

# Start your Flask app with Gunicorn
CMD gunicorn app:app --bind 0.0.0.0:$PORT
