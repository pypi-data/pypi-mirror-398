# FreeRouter Roadmap

> **Last Updated**: 2025-12-26 (v0.1.1)
> Roadmap subject to change based on community feedback and priorities.

---

## Current State (v0.1.1) ✅

**Core Capabilities**:
- ✅ Multi-provider support (OpenRouter, iFlow, Ollama, ModelScope, OAI, Static)
- ✅ Automatic model discovery & configuration generation
- ✅ Service lifecycle management (start/stop/reload/status/logs)
- ✅ Configuration backup & restore
- ✅ Beautiful CLI with colors (rich library)
- ✅ 81% test coverage, 90 tests passing
- ✅ PyPI package published

**Recent Improvements** (v0.1.1):
- Interactive `freerouter init` with config location choice
- Daemon-style service management
- `freerouter status` command with detailed service info
- `freerouter reload` with `--refresh` flag
- `freerouter restore` for config rollback
- Colored output with rich library

---

## Prioritized Feature Roadmap

### 🔴 High Priority - Next Release (v0.2.0)

#### 1. Interactive Model Selector ✅ ⭐⭐⭐⭐⭐

**Command**: `freerouter select`

**Status**: ✅ Completed (2025-12-26)

**Problem**: Users get 50+ models after `fetch`, but typically only need 3-5 models.

**Solution**:
```bash
freerouter select
# Interactive multi-select list (using questionary)
# Filters config.yaml to include only selected models
# Reduces LiteLLM startup time and memory usage
```

**Value**:
- Solves real user pain point (too many models)
- Improves performance (smaller config → faster LiteLLM startup)
- Aligns with "simple by default" philosophy

**Effort**: 🟢 Low (1-2 days)

**Dependencies**: `questionary` library

---

#### 2. Health Check ⭐⭐⭐⭐

**Command**: `freerouter check`

**Problem**: Users configure providers but don't know if API keys are valid until runtime errors.

**Solution**:
```bash
freerouter check [--full]
# Tests each provider's connection
# Validates API keys
# Optional: Test-calls each model with --full flag
# Color-coded output (✓ green, ✗ red)
```

**Value**:
- Prevents runtime surprises
- Validates configuration before deployment
- Builds user confidence

**Effort**: 🟡 Medium (3-4 days)

**Implementation**:
- Add `test_connection()` method to BaseProvider
- Handle timeouts gracefully
- Display results in rich table

---

#### 3. Technical Improvements

- **Parallel Provider Fetching**: ✅ Completed (2025-12-26) - Use ThreadPoolExecutor for faster `fetch` (1 day)
- **Test Coverage**: 81% → 83% (cover ollama/openrouter providers) (2-3 days)
- **Error Messages**: Add context and suggestions to errors (ongoing)

**v0.2.0 Timeline**: ~2 weeks

---

### 🟡 Medium Priority - Future Release (v0.3.0)

#### 4. Enhanced Configuration Wizard ⭐⭐⭐⭐

**Command**: `freerouter init --wizard`

**Problem**: Current `init` requires manual YAML editing + separate `fetch` + `start`.

**Solution**: Interactive Q&A that completes full setup:
```bash
freerouter init --wizard
# 1. Which providers? (multi-select)
# 2. Enter API keys for selected providers
# 3. Fetch models now? (yes/no)
# 4. Start service? (yes/no)
# Result: Zero-to-running in one command
```

**Value**: Dramatically lowers onboarding friction (10+ min → 2 min)

**Effort**: 🟡 Medium (3-5 days)

---

#### 5. Model Search & Filtering ⭐⭐⭐

**Commands**:
```bash
freerouter list --search deepseek      # Fuzzy search
freerouter list --provider openrouter  # Filter by provider
freerouter list --free                 # Only free models
freerouter list --json                 # Machine-readable output
```

**Value**: Makes navigating 50+ models easier

**Effort**: 🟢 Low (1 day)

---

#### 6. Configuration Validation ⭐⭐⭐

**Command**: `freerouter validate [config-file]`

**Features**:
- YAML syntax check
- Schema validation (required fields)
- Warning for common mistakes
- Exit code 0/1 for CI/CD integration

**Effort**: 🟢 Low (1-2 days)

**Implementation**: Use `pydantic` or `jsonschema`

**v0.3.0 Timeline**: ~1.5 weeks

---

### 🟢 Low Priority - Later Versions (v0.4.0+)

#### 7. Performance Metrics ⭐⭐⭐

**Command**: `freerouter metrics [--live]`

**Features**:
- Total requests (per model, per provider)
- Error rates and average latency
- Token usage tracking
- Real-time updates with `--live`

**Effort**: 🟡 Medium-High (4-5 days)

**Dependencies**: LiteLLM log format knowledge

---

#### 8. Additional Providers

- [ ] HuggingFace Inference API
- [ ] Together AI
- [ ] Anthropic (native API)
- [ ] AWS Bedrock
- [ ] Azure OpenAI

**Effort**: 🟡 Medium (2-3 days per provider)

---

#### 9. Advanced Features

- **Configuration Diff**: `freerouter diff <backup-file>` (half day)
- **Shell Completion**: bash/zsh autocomplete (1 day)
- **Model Aliasing**: Custom names for models (2 days)
- **Migration Tools**: Upgrade configs between versions (2-3 days)

---

### 🔮 Future Vision (v1.0.0+)

#### Web Dashboard (Optional)

**Note**: Only if community strongly requests it. Adds significant complexity.

**Features**:
- Model list viewer
- Real-time logs
- Configuration editor
- Request analytics

**Effort**: 🔴 Very High (3+ weeks)

**Alternative**: TUI (Terminal UI) with `textual` library (1 week)

---

#### Provider Plugin System

Allow users to add custom providers without modifying core code.

**Value**: Extensibility for edge cases

**Effort**: 🔴 High (1-2 weeks)

**Implementation**:
- Design plugin API
- Discovery mechanism (Python entry points)
- Documentation and examples

---

#### Enterprise Features

**Not Planned for v1.0.0** - Only if there's enterprise demand:
- Multi-user support with API keys
- Rate limiting per user/model
- Distributed deployment (HA cluster mode)
- Advanced routing (fallback providers, cost optimization)
- Audit logging
- SSO integration

---

## Version Milestones

### v0.1.x - MVP ✅ (Complete)
- Core functionality working
- Basic provider support
- CLI interface
- Service management

### v0.2.0 - Quality & Selection 🚧 (Next, ~2 weeks)
**Release Goals**:
- Interactive model selector (`select`)
- Health check (`check`)
- Parallel fetching optimization
- 90%+ test coverage

**Target**: Late January 2026

---

### v0.3.0 - Onboarding & Discovery (~1.5 weeks)
**Release Goals**:
- Enhanced init wizard (`init --wizard`)
- Model search & filtering
- Configuration validation
- Better error messages

**Target**: Mid February 2026

---

### v0.4.0 - Monitoring & Extensions
**Release Goals**:
- Performance metrics
- Additional providers
- Plugin system (design phase)
- Advanced CLI features

**Target**: March 2026

---

### v1.0.0 - Production Ready
**Release Goals**:
- Stable API (no breaking changes)
- Complete documentation
- Production-tested at scale
- Performance benchmarks
- Optional: TUI or basic Web UI

**Target**: Q2 2026

---

## Technical Debt & Ongoing Work

### High Priority
- [ ] Increase test coverage to 90%+ (ollama/openrouter providers)
- [ ] Parallel provider fetching for faster `fetch` command
- [ ] Better error messages with context and suggestions

### Medium Priority
- [ ] CI/CD pipeline (GitHub Actions)
  - Automated testing on PR
  - Coverage reports
  - Automated PyPI publishing
- [ ] Documentation expansion
  - More examples in README
  - Troubleshooting guide
  - Provider-specific setup guides

### Low Priority
- [ ] Performance profiling and optimization
- [ ] Code refactoring for maintainability
- [ ] Internationalization (i18n) support

---

## Decision Criteria

When evaluating new features, we consider:

1. **User Impact**: Does it solve a real problem?
2. **Complexity**: Implementation + maintenance burden
3. **Alignment**: Fits project scope (config tool, not AI service)
4. **Dependencies**: Does it add new dependencies?
5. **Testing**: Can it be easily tested?
6. **Documentation**: Does it increase docs burden?

**Golden Rule**: KISS (Keep It Simple, Stupid) - FreeRouter should remain a focused, lightweight tool.

---

## Community Wishlist 💡

*Features requested by users - not committed to roadmap*

- Docker Compose deployment templates
- Kubernetes Helm charts
- Model fine-tuning integration
- Prompt caching layer
- Cost tracking and budgeting
- Multi-config support (dev/staging/prod)

**Want to request a feature?** [Open an issue](https://github.com/mmdsnb/freerouter/issues)

---

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for how to help with any of these features!

**Quick Start**:
- Good first issues: Search/filtering, validation
- Medium complexity: Model selector, health check
- Advanced: Plugin system, metrics

---

## Notes

- **Priorities may shift** based on user feedback and community contributions
- **Timeline estimates** are rough and subject to change
- **Breaking changes** will be avoided after v1.0.0
- **Backward compatibility** maintained within major versions

For detailed technical analysis of features, see code comments and architectural decisions in [CLAUDE.md](../CLAUDE.md).
