FROM python:3.11-slim

# Define browser path explicitly
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
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Force install Chromium to a known-good persistent location
RUN mkdir -p /ms-playwright && \
    python -m playwright install chromium

# Copy your app
COPY . .

EXPOSE 8000

CMD gunicorn app:app --bind 0.0.0.0:$PORT
