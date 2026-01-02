"""
Ollama Provider - fetches models via local API
"""

import requests
from typing import List, Dict, Any
from .base import BaseProvider


class OllamaProvider(BaseProvider):
    """Ollama local provider with API-based model discovery"""

    def __init__(self, api_base: str = "http://localhost:11434", **kwargs):
        super().__init__(
            api_key="dummy",
            api_base=api_base,
            **kwargs
        )
        self.tags_endpoint = f"{api_base}/api/tags"

    @property
    def provider_name(self) -> str:
        return "ollama"

    def fetch_models(self) -> List[Dict[str, Any]]:
        """Fetch models from Ollama API"""
        try:
            response = requests.get(self.tags_endpoint, timeout=10)
            response.raise_for_status()

            data = response.json()
            models = data.get("models", [])

            # Convert Ollama format to standard format
            return [
                {"id": model.get("name")}
                for model in models
            ]

        except requests.exceptions.ConnectionError:
            self.logger.warning(f"Cannot connect to Ollama at {self.api_base}")
            return []
        except Exception as e:
            self.logger.error(f"Error fetching Ollama models: {e}")
            return []
