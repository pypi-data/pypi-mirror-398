# FreeRouter v0.1.2 - Parallel Fetching Performance Update

## 🚀 Performance Improvements

### Parallel Provider Fetching ⚡
- **5x performance improvement** for `freerouter fetch` command
- Concurrent fetching from multiple providers using ThreadPoolExecutor
- Typical speedup: **2.5s → 0.5s** with 5 providers
- Robust error handling: one provider failure doesn't block others

## 📊 Benchmark Results

```
Setup:
  Providers: 5
  Delay per provider: 0.5s

Results:
  Sequential time: 2.50s
  Parallel time: 0.50s
  Speedup: 4.99x ✓
```

Run the benchmark yourself:
```bash
python tests/benchmark_parallel_fetch.py
```

## 🧪 Testing & Quality

- **97 tests** passing
- **83% code coverage**
- New tests for parallel execution and error handling
- Benchmark script included

## 📚 Documentation

- New `docs/PERFORMANCE.md` - Detailed performance optimization guide
- New `docs/features/parallel-fetching.md` - Feature documentation
- Updated `CHANGELOG.md` with complete release notes

## 📦 Installation

```bash
pip install --upgrade freerouter
```

## 🔧 Usage

No changes required! Just run:

```bash
freerouter fetch  # Now 5x faster!
```

The parallel fetching happens automatically when you have multiple providers enabled.

## 🎯 What's Included

All features from v0.1.1 plus:
- ✅ Parallel provider fetching (NEW)
- ✅ Interactive model selector (`freerouter select`)
- ✅ Enhanced service management (`status`, `reload`, `restore`)
- ✅ Multi-provider support (OpenRouter, iFlow, Ollama, ModelScope, OAI, Static)
- ✅ Beautiful CLI with colors (rich library)
- ✅ Daemon-style service management

## 🔄 Upgrade from v0.1.1

Simply upgrade the package:

```bash
pip install --upgrade freerouter
```

No configuration changes needed. Your existing setup will work with the new parallel fetching automatically.

## 📝 Full Changelog

See [CHANGELOG.md](https://github.com/mmdsnb/freerouter/blob/master/CHANGELOG.md) for complete details.

---

**What's Next?** Check out our [ROADMAP.md](https://github.com/mmdsnb/freerouter/blob/master/docs/ROADMAP.md) for upcoming features!
