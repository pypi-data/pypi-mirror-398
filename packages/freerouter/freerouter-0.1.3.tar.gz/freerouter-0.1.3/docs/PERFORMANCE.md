# Performance Optimizations

This document describes performance optimizations implemented in FreeRouter.

## Parallel Provider Fetching

**Status**: ✅ Implemented (v0.2.0)

### Problem

When running `freerouter fetch`, the tool needs to query multiple providers (OpenRouter, Ollama, ModelScope, etc.) to discover available models. Previously, these queries were executed sequentially:

```
Provider 1 (0.5s) → Provider 2 (0.5s) → Provider 3 (0.5s) = 1.5s total
```

With 5+ providers, this could take several seconds, creating a poor user experience.

### Solution

We implemented parallel fetching using Python's `concurrent.futures.ThreadPoolExecutor`. Now all providers are queried simultaneously:

```
Provider 1 (0.5s) ┐
Provider 2 (0.5s) ├─→ All complete in ~0.5s
Provider 3 (0.5s) ┘
```

### Implementation

The change was made in `freerouter/core/fetcher.py`:

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_all(self) -> List[Dict[str, Any]]:
    """Fetch services from all providers in parallel"""
    all_services = []
    
    with ThreadPoolExecutor(max_workers=len(self.providers)) as executor:
        future_to_provider = {
            executor.submit(provider.get_services): provider
            for provider in self.providers
        }
        
        for future in as_completed(future_to_provider):
            provider = future_to_provider[future]
            try:
                services = future.result()
                all_services.extend(services)
            except Exception as e:
                logger.error(f"Failed to fetch from {provider.provider_name}: {e}")
    
    return all_services
```

### Performance Results

Benchmark results with 5 providers (0.5s delay each):

| Metric | Sequential | Parallel | Improvement |
|--------|-----------|----------|-------------|
| Time | 2.50s | 0.50s | **5.0x faster** |
| User Experience | Slow | Fast | ✓ |

Real-world results will vary based on:
- Number of providers enabled
- Network latency to each provider's API
- Provider API response times

### Error Handling

The parallel implementation includes robust error handling:

- If one provider fails, others continue fetching
- Errors are logged but don't block the entire fetch
- Users still get models from successful providers

### Testing

We added comprehensive tests in `tests/test_fetcher.py`:

1. **test_parallel_fetch**: Verifies parallel execution is faster than sequential
2. **test_parallel_fetch_with_error**: Ensures one provider error doesn't block others

Run the benchmark:

```bash
python tests/benchmark_parallel_fetch.py
```

### Future Improvements

Potential future optimizations:

1. **Caching**: Cache provider responses for a short time (5-10 minutes)
2. **Incremental Updates**: Only fetch from providers that have changed
3. **Background Refresh**: Periodically refresh model list in background
4. **Rate Limiting**: Respect provider rate limits with backoff

### Technical Details

**Why ThreadPoolExecutor instead of asyncio?**

- Most provider APIs use `requests` library (blocking I/O)
- ThreadPoolExecutor is simpler and works well for I/O-bound tasks
- No need to refactor all providers to async/await
- Performance gain is similar for this use case

**Thread Safety**

- Each provider operates independently
- Results are collected in a thread-safe manner using `as_completed()`
- No shared state between providers

### Monitoring

To see the performance improvement in action:

```bash
# Enable verbose logging
export FREEROUTER_LOG_LEVEL=DEBUG

# Run fetch and observe parallel execution
freerouter fetch
```

You'll see log messages from multiple providers appearing simultaneously.

---

**Related Issues**: None (proactive optimization)  
**Pull Request**: TBD  
**Version**: 0.2.0
