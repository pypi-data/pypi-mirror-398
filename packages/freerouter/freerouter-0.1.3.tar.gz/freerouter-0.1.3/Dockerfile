FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY freellm/ ./freellm/
COPY scripts/ ./scripts/
COPY config/ ./config/
COPY examples/ ./examples/

# Expose litellm default port
EXPOSE 4000

# Default command
CMD ["python", "scripts/start.py"]
