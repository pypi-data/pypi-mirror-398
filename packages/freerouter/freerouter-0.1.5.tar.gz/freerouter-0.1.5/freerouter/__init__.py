"""
FreeRouter - Free LLM Router Service

A clean and elegant LLM routing service based on LiteLLM with support for
multiple providers (OpenRouter, Ollama, ModelScope, etc.)
"""

from freerouter.__version__ import __version__, __author__, __license__
from freerouter.core.fetcher import FreeRouterFetcher
from freerouter.core.factory import ProviderFactory
from freerouter.providers.base import BaseProvider

__all__ = [
    "__version__",
    "__author__",
    "__license__",
    "FreeRouterFetcher",
    "ProviderFactory",
    "BaseProvider",
]
