# FreeRouter - Project Standards and Design Document

> **CRITICAL**: This document is the source of truth for all Claude Code instances. Any architectural decisions or code standards MUST be documented here to maintain consistency across all contributors.

## Meta: Document Maintenance

**Purpose**: Keep this document high-quality, concise, and conflict-free.

**Guidelines**:
- Only include information that affects code decisions
- Remove outdated content immediately
- Translate everything to English
- Move detailed tutorials to `docs/`
- **Ask user before resolving conflicts**

**Review triggers**: After major changes, when adding sections, if >500 lines

---

## Collaboration Workflow

### Git Policy
- **Auto-commit**: Create commits when completing meaningful work
  - Format: `<type>(<scope>): <subject>`
  - Types: feat, fix, docs, refactor, test, chore
- **Never auto-push**: Only push when user explicitly requests
- **Code quality**: Continuously refactor to prevent technical debt

### Pre-Commit Checklist
- [ ] KISS & Occam's Razor principles followed
- [ ] No code duplication (DRY)
- [ ] Single responsibility per function/class
- [ ] Clear naming (no unclear abbreviations)
- [ ] Error handling appropriate
- [ ] No hardcoded values
- [ ] English for user-facing text
- [ ] **Tests written** (80%+ coverage required)

### Testing Requirements
**MANDATORY**: Every feature/fix must include pytest tests.

**Coverage**: Minimum 80%, target 90%+

**Structure**:
```
tests/
├── test_cli.py       # CLI commands
├── test_config.py    # Configuration logic
├── test_providers.py # Provider implementations
├── test_fetcher.py   # Core fetcher
└── conftest.py       # Shared fixtures
```

**Run tests**: `pytest --cov=freerouter`

**Test types**: Happy path, edge cases, error handling, integration

---

## Architecture

### Design Patterns

**1. Strategy Pattern** - Provider System
- Each AI service = one Provider
- Unified interface (`BaseProvider`)
- Multiple implementations (API, local, static)

**2. Factory Pattern** - Provider Creation
- YAML configuration drives object creation
- Decouples config from implementation
- Environment variable injection (`${VAR}`)

**3. Single Responsibility**
- One class = one concern
- One function = one task

### Key Architectural Decisions

#### Service Management (2025-12-26)
**Problem**: Start command occupied terminal

**Solution**: Daemon-style detached process
- `subprocess.Popen` with `start_new_session=True`
- Monitor logs until "Uvicorn running"
- Release terminal once started
- PID file for management

**Commands**:
- `freerouter start` - Daemon start with monitoring
- `freerouter stop` - Graceful shutdown via PID
- `freerouter logs` - Tail real-time logs

**Files**: `freerouter/cli/main.py`, `{config_dir}/freerouter.{log,pid}`

---

## Code Standards

### Project Structure
```
freerouter/
├── freerouter/          # Core package
│   ├── cli/             # Command-line interface
│   ├── core/            # Business logic
│   └── providers/       # Provider implementations
├── tests/               # Test suite
├── docs/                # Documentation
├── examples/            # Example configs
└── config/              # User configs (gitignored)
```

### Naming Conventions
- **Classes**: `PascalCase` (`OpenRouterProvider`)
- **Functions**: `snake_case` (`fetch_models`)
- **Constants**: `UPPER_SNAKE_CASE` (`DEFAULT_PORT`)
- **Private**: Prefix `_` (`_internal_method`)

### Import Order
```python
# 1. Standard library
import os
from typing import List

# 2. Third-party
import yaml
import requests

# 3. Internal
from freerouter.providers.base import BaseProvider
```

### Configuration System
**Two-tier**:
1. `providers.yaml` - User intent (what to use)
2. `config.yaml` - Generated config (how to run)

**Locations** (priority order):
1. `./config/` - Project-level
2. `~/.config/freerouter/` - User-level

---

## Development Workflows

### Adding a Provider
1. Create `freerouter/providers/my_provider.py`
2. Inherit `BaseProvider`, implement `fetch_models()`
3. Register in `ProviderFactory.create_from_config()`
4. Add to `examples/providers.yaml.example`
5. Write tests in `tests/test_my_provider.py`
6. Update docs

### Git Commit Format
```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

**Example**:
```
feat(providers): add HuggingFace provider

- Implement HuggingFaceProvider with API integration
- Add model filtering by inference status
- Include tests with 85% coverage

Closes #42
```

### Publishing a New Release

**Use GitHub CLI** to create releases:

```bash
# Update version in code first
# 1. freerouter/__version__.py
# 2. pyproject.toml
# 3. CHANGELOG.md

# Commit and push
git add .
git commit -m "chore: bump version to X.Y.Z"
git push origin master

# Create GitHub Release (triggers automatic PyPI publish)
http_proxy=http://localhost:7890 https_proxy=http://localhost:7890 \
  gh release create vX.Y.Z \
  --title "Release vX.Y.Z" \
  --notes "Release notes here..."
```

**What happens**: GitHub Actions (`.github/workflows/publish.yml`) automatically builds and publishes to PyPI using OIDC trusted publishing.

---

## Security & Performance

### Security
- **Never** hardcode API keys
- Use environment variables (`.env` gitignored)
- Validate all config inputs
- Don't expose secrets in errors
- Timeout all network requests

### Performance
- Parallel provider fetching (where safe)
- Lazy loading providers
- Efficient file I/O
- Reasonable timeouts

---

## Dependencies

**Core**: litellm, pyyaml, requests, python-dotenv, click, typer

**Dev**: pytest, pytest-cov, black, flake8, mypy

**Python**: 3.10+

---

## Versioning

**Semantic Versioning** (MAJOR.MINOR.PATCH)
- MAJOR: Breaking API changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes (backward compatible)

**Current**: v0.1.1 (initial development)

---

## References

- [FAQ](docs/FAQ.md) - Common questions
- [Roadmap](docs/ROADMAP.md) - Future plans
- [Contributing](CONTRIBUTING.md) - How to contribute

---

**Last Updated**: 2025-12-26
**Maintainer**: @mmdsnb

*Remember: Simple, clear, maintainable > clever.*
