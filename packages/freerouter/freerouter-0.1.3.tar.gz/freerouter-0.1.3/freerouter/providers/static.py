"""
Static Provider - for manually configured services
"""

from typing import List, Dict, Any
from .base import BaseProvider


class StaticProvider(BaseProvider):
    """
    Provider for manually configured services
    Doesn't fetch anything, just formats the config
    """

    def __init__(self, model_name: str, provider: str, api_base: str,
                 api_key: str = "dummy", **kwargs):
        super().__init__(api_key=api_key, api_base=api_base, **kwargs)
        self.model_name = model_name
        self._provider = provider

    @property
    def provider_name(self) -> str:
        return self._provider

    def fetch_models(self) -> List[Dict[str, Any]]:
        """Return single static model"""
        return [{"id": self.model_name}]
