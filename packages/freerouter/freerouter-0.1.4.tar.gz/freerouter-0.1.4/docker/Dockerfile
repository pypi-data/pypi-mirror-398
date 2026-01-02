FROM python:3.11-slim

WORKDIR /app

# Copy package files
COPY pyproject.toml README.md ./

# Copy application code
COPY freerouter/ ./freerouter/

# Install the package
RUN pip install --no-cache-dir .

# Copy docker entrypoint
COPY docker/docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Expose litellm default port
EXPOSE 4000

# Use entrypoint script that runs litellm in foreground
ENTRYPOINT ["docker-entrypoint.sh"]
