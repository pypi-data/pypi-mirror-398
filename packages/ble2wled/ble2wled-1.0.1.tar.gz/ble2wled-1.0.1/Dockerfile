# Use a small, stable Python base image
FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffer stdout
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies (if needed later, easy to extend)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Upgrade pip and install your package
RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir ble2wled

# Optional: run as non-root user (recommended)
RUN useradd --create-home appuser
USER appuser

# Default environment variables (can be overridden at runtime)
ENV \
    WLED_HOST=wled.local \
    LED_COUNT=60 \
    MQTT_BROKER=localhost \
    MQTT_LOCATION=balkon \
    MQTT_PORT=1883 \
    MQTT_USERNAME=espresense \
    MQTT_PASSWORD=your_secure_password \
    BEACON_TIMEOUT_SECONDS=6.0 \
    BEACON_FADE_OUT_SECONDS=4.0 \
    UPDATE_INTERVAL=0.2 \
    TRAIL_LENGTH=10 \
    FADE_FACTOR=0.75 \
    OUTPUT_MODE=udp \
    UDP_PORT=21324 \
    HTTP_TIMEOUT=1 \
    LOG_LEVEL=INFO

# ble2wled is installed as a console script
ENTRYPOINT ["ble2wled"]
