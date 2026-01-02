# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.3] - 2025-12-28

### Added
- **Request Filtering**: New `--requests` / `-r` flag for `freerouter logs` command to filter and show only API requests/responses
- **Request Log Parser**: New `request_log_parser.py` module with `LogStreamFilter` class for parsing LiteLLM debug logs
- **Pretty Request Formatting**: Colored output with structured display of requests (headers, body) and responses (model, content, tokens)
- **Debug Mode**: New `--debug` flag for `start` and `reload` commands to enable detailed HTTP request/response logging
- **Documentation**: Added logging guide, debug requests documentation, and view API requests guide
- **Log Rotation**: Added example log rotation scripts and logrotate configuration

### Fixed
- `/v1/models` endpoint returning empty list when `LITELLM_MASTER_KEY` is set
- Incomplete URL in logs (now properly appends `/chat/completions` to `/v1/` URLs)
- Environment variable interference in debug mode
- Missing `os` module import in CLI

### Changed
- Removed hardcoded master key checking logic
- Removed `router_settings` and `general_settings` from generated config (causes `/v1/models` issues)
- Enhanced `list` command to use API endpoint instead of config file
- Improved environment variable handling for cleaner debug mode

### Testing
- Added 32 unit tests for request log parser (100% coverage on new module)
- Added comprehensive tests for `/v1/models` endpoint bug fix
- Total: 134 tests passing
- Coverage: 80% (+3% from v0.1.2)

## [0.1.2] - 2025-12-26

### Added
- Parallel provider fetching using ThreadPoolExecutor for 3-5x faster `fetch` command
- Benchmark script to demonstrate parallel fetching performance (`tests/benchmark_parallel_fetch.py`)
- Comprehensive performance documentation (`docs/PERFORMANCE.md`)
- Feature documentation (`docs/features/parallel-fetching.md`)

### Performance
- `freerouter fetch` now fetches from multiple providers concurrently
- Typical speedup: 3-5x when using multiple providers (e.g., 2.5s → 0.5s with 5 providers)
- Robust error handling: one provider failure doesn't block others

### Testing
- Added 2 new tests for parallel execution and error handling
- All 97 tests passing with 83% coverage

## [0.1.1] - 2025-12-26

### Added
- Interactive `freerouter init` command with config location choice
- Daemon-style service management (start/stop/logs commands)
- Makefile for standardized development commands
- Comprehensive test suite with 79% coverage (74 tests)

### Fixed
- CONFIG_FILE_PATH environment variable conflict with LiteLLM
- All providers now disabled by default in generated config
- Test suite performance and reliability issues

### Changed
- All user-facing messages translated to English
- Documentation restructured (FAQ, ROADMAP moved to docs/)
- CLAUDE.md refactored for clarity and maintainability

### Removed
- Obsolete scripts directory (replaced by CLI commands)
- Temporary development documentation files
- Chinese README (internationalization - English only)

## [0.1.0] - 2025-12-25

### Added
- Initial release
- Strategy Pattern based Provider architecture
- Factory Pattern for provider creation
- OpenRouter Provider with API-based model discovery
- Ollama Provider for local models
- ModelScope Provider with static model list
- Static Provider for manual configuration
- YAML-based configuration
- Environment variable support
- Docker and Docker Compose support
- Basic unit tests
- Documentation and examples

### Design
- KISS principle implementation
- Occam's Razor approach
- Clean project structure (freerouter/, tests/)
- Comprehensive documentation in CLAUDE.md
