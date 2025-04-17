FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
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

# Install Python + Playwright dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Install Node.js and Playwright browser
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    npx playwright install --with-deps chromium

# Copy your app
COPY . .

# Expose port Railway uses
EXPOSE 8000

# Start the app
CMD gunicorn app:app --bind 0.0.0.0:$PORT
