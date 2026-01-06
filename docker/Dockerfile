FROM python:3.12-slim

# Accept UID and GID as build arguments
ARG PUID=1000
ARG PGID=1000

# No need for cron - we use Python scheduler
# We run as non-root user for security

WORKDIR /app

# Install dependencies
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy scripts
COPY app/TSSK.py ./tssk.py
COPY app/scheduler.py .
COPY docker/entrypoint.sh /app/entrypoint.sh

# Create group and user with specified UID/GID (non-root)
RUN groupadd -g ${PGID} appuser 2>/dev/null || true && \
    useradd -u ${PUID} -g ${PGID} -m -s /bin/bash appuser 2>/dev/null || true

# Create directories (will be overridden by volume mounts, but good for non-volume usage)
RUN mkdir -p /app/data /app/logs /app/tssk && \
    chown -R ${PUID}:${PGID} /app

# Set default environment variables (can be overridden)
ENV APP_TIMES="02:00"
ENV RUN_AT_START="true"
ENV PUID=${PUID}
ENV PGID=${PGID}

# Make scripts executable
RUN chmod +x tssk.py scheduler.py entrypoint.sh

# Note: Config and output files will be created by the application at runtime in mounted volumes
# With read_only: true and volume mounts, the app will create files in mounted volumes

# Entrypoint runs as the user specified in docker-compose (non-root)
# Container runs with security hardening: cap_drop: ALL, read_only: true
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python3", "-u", "/app/scheduler.py"]
