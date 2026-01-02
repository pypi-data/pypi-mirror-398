"""
OpenRouter Provider - fetches models via API
"""

import requests
from typing import List, Dict, Any
from .base import BaseProvider


class OpenRouterProvider(BaseProvider):
    """OpenRouter provider with API-based model discovery"""

    def __init__(self, api_key: str, **kwargs):
        super().__init__(
            api_key=api_key,
            api_base="https://openrouter.ai/api/v1",
            **kwargs
        )
        self.models_endpoint = "https://openrouter.ai/api/v1/models"

    @property
    def provider_name(self) -> str:
        return "openrouter"

    def fetch_models(self) -> List[Dict[str, Any]]:
        """Fetch models from OpenRouter API"""
        if not self.api_key:
            self.logger.warning("OpenRouter API key not provided")
            return []

        response = requests.get(
            self.models_endpoint,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            timeout=30
        )
        response.raise_for_status()

        data = response.json()
        return data.get("data", [])

    def filter_models(self, models: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter for free models (pricing.prompt == 0)"""
        # Option 1: Only free models
        free_models = [
            model for model in models
            if model.get("pricing", {}).get("prompt", "1") == "0" or
               "free" in model.get("id", "").lower()
        ]

        # If no free models, return all (user has API key anyway)
        if not free_models:
            self.logger.info("No free models found, using all available models")
            return models

        return free_models
