# Docker Deployment

## Quick Start

### Using Docker Compose

1. Create `config/providers.yaml`:
```yaml
providers:
  - type: openrouter
    api_key: ${OPENROUTER_API_KEY}
```

2. Start the service:
```bash
docker-compose -f docker/docker-compose.yml up -d
```

### Using Docker CLI

```bash
# Pull the image
docker pull ghcr.io/mmdsnb/freerouter:latest

# Run the container
docker run -d \
  -p 4000:4000 \
  -v ./config:/root/.config/freerouter \
  -e OPENROUTER_API_KEY=your_key \
  ghcr.io/mmdsnb/freerouter:latest
```

## Configuration

- Mount your config directory: `-v ./config:/root/.config/freerouter`
- Ensure `providers.yaml` exists in your config directory
- Set API keys via environment variables

## Files

- `Dockerfile` - Multi-platform image (amd64, arm64)
- `docker-compose.yml` - Compose configuration
- `docker-entrypoint.sh` - Container startup script
