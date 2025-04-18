# Defines the container image used for local and Kubernetes deployment

FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    chromium \
    libnss3 \
    libgtk-3-0 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libasound2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libgbm1 \
    libxshmfence1 \
    libnss3-tools \
    ca-certificates \
    openssl \
    wget \
    curl \
    x11-apps \
    vim-common \
    && rm -rf /var/lib/apt/lists/*

# Install mkcert
RUN wget -O /usr/local/bin/mkcert https://github.com/FiloSottile/mkcert/releases/download/v1.4.4/mkcert-v1.4.4-linux-amd64 && \
    chmod +x /usr/local/bin/mkcert

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install pytest pytest-playwright
RUN playwright install chromium && \
    mkcert -install && \
    mkcert -cert-file localhost.pem -key-file localhost-key.pem localhost 127.0.0.1 ::1 172.17.0.2

# Copy all app files
COPY . /app/
