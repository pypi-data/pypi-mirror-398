"""
Base Provider Interface - Strategy Pattern
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class BaseProvider(ABC):
    """
    Abstract base class for LLM service providers

    Each provider implements:
    1. How to fetch available models (or use static list)
    2. How to filter models (optional)
    3. How to format model config for litellm
    """

    def __init__(self, api_key: Optional[str] = None, api_base: Optional[str] = None, **kwargs):
        self.api_key = api_key
        self.api_base = api_base
        self.config = kwargs
        self.logger = logger

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider identifier (e.g., 'openrouter', 'ollama')"""
        pass

    @abstractmethod
    def fetch_models(self) -> List[Dict[str, Any]]:
        """
        Fetch available models from the provider

        Returns:
            List of dicts with at least 'id' field:
            [{'id': 'model-name', 'pricing': {...}, ...}, ...]
        """
        pass

    def filter_models(self, models: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter models (e.g., only free models)
        Default: return all models

        Override this in subclass for custom filtering
        """
        return models

    def format_service(self, model: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format model data into litellm service config

        Default implementation, override if needed
        """
        model_id = model.get('id')
        return {
            "model_name": model_id,
            "litellm_params": {
                "model": f"{self.provider_name}/{model_id}",
                "api_base": self.api_base,
                "api_key": self.api_key or "dummy"
            }
        }

    def get_services(self) -> List[Dict[str, Any]]:
        """
        Main entry point: fetch, filter, and format models
        """
        try:
            self.logger.info(f"Fetching models from {self.provider_name}...")

            models = self.fetch_models()
            if not models:
                self.logger.warning(f"No models found from {self.provider_name}")
                return []

            filtered = self.filter_models(models)
            self.logger.info(f"Filtered {len(filtered)}/{len(models)} models from {self.provider_name}")

            services = [self.format_service(model) for model in filtered]
            self.logger.info(f"✓ Added {len(services)} services from {self.provider_name}")

            return services

        except Exception as e:
            self.logger.error(f"Error fetching from {self.provider_name}: {e}")
            return []
