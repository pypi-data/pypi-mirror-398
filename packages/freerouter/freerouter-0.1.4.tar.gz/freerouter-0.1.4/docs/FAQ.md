# Frequently Asked Questions

## Architecture

### Q: Why use the Strategy Pattern?
**A**: Different providers fetch models in completely different ways (API, local, static), but all share the same goal: generating litellm configuration. The Strategy Pattern allows us to handle these differences uniformly through a common interface.

### Q: Why use the Factory Pattern?
**A**: It decouples configuration from code. Users declare which providers to use via YAML, and the factory creates instances automatically. Adding new providers doesn't require modifying the configuration loading logic.

### Q: Why have two configuration layers?
**A**: `providers.yaml` is human-friendly (what you want to use), while `config.yaml` is machine-friendly (what litellm needs). Separation of concerns - each file has a single purpose.

## Code Quality

### Q: How do we ensure code quality?
**A**:
1. **Testing**: Unit tests with >80% coverage
2. **Review**: Code review via PR process
3. **Automation**: black, flake8, mypy for consistency
4. **Documentation**: Write docs before/during implementation

## Development

### Q: How do I add a new provider?
**A**: See [Development Guide](development.md) for step-by-step instructions. In brief:
1. Create provider class in `freerouter/providers/`
2. Inherit from `BaseProvider`
3. Implement required methods
4. Register in factory
5. Write tests
6. Update example config

### Q: What's the testing policy?
**A**: Every feature/fix must include tests. Minimum 80% coverage. Tests must cover happy path, edge cases, and error handling.

### Q: When should I use which provider type?
**A**:
- **API Provider** (OpenRouter): Dynamic model discovery via API
- **Local Provider** (Ollama): Self-hosted models on your machine
- **Static Provider**: Predefined model list or single custom endpoint
- **OAI Provider**: Generic OpenAI-compatible APIs with auto-discovery

## Configuration

### Q: Where should configuration files go?
**A**: Two options:
- **User-level**: `~/.config/freerouter/` - Shared across projects
- **Project-level**: `./config/` - Specific to one project

Use `freerouter init` to set up interactively.

### Q: How do environment variables work?
**A**: Use `${VAR_NAME}` syntax in `providers.yaml`. Variables are resolved from:
1. `.env` file in project root
2. System environment variables

Example:
```yaml
providers:
  - type: openrouter
    api_key: ${OPENROUTER_API_KEY}  # Reads from environment
```

## Service Management

### Q: How does the daemon mode work?
**A**: When you run `freerouter start`:
1. Process starts in foreground
2. CLI monitors logs for "Uvicorn running" message
3. Once confirmed, process detaches (new session)
4. Terminal is released, service runs in background
5. PID stored for management (`freerouter stop`)

### Q: Where are the logs?
**A**: All service output goes to `{config_dir}/freerouter.log`. Use `freerouter logs` to tail in real-time.

## Troubleshooting

### Q: "Config not found" error when starting?
**A**: Run `freerouter fetch` first to generate `config.yaml` from your `providers.yaml`.

### Q: Service won't start?
**A**: Check:
1. `config.yaml` exists (`freerouter fetch`)
2. No other service on port 4000
3. Logs: `cat {config_dir}/freerouter.log`

### Q: How do I update models?
**A**: Run `freerouter fetch` again. It will regenerate `config.yaml` with latest models from enabled providers.
