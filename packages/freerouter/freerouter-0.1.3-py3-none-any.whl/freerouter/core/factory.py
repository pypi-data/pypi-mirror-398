"""
Provider Factory - Factory Pattern Implementation

Creates Provider instances from configuration dictionaries.
"""

import os
from typing import Dict, Any

from freerouter.providers.base import BaseProvider
from freerouter.providers.openrouter import OpenRouterProvider
from freerouter.providers.ollama import OllamaProvider
from freerouter.providers.modelscope import ModelScopeProvider
from freerouter.providers.iflow import IFlowProvider
from freerouter.providers.oai import OAIProvider
from freerouter.providers.static import StaticProvider


class ProviderFactory:
    """Factory for creating providers based on config"""

    @staticmethod
    def create_from_config(config: Dict[str, Any]) -> BaseProvider:
        """
        Create provider from config dict

        Args:
            config: Configuration dictionary with 'type' field

        Returns:
            Provider instance

        Raises:
            ValueError: If provider type is unknown

        Example:
            >>> config = {"type": "openrouter", "api_key": "sk-xxx"}
            >>> provider = ProviderFactory.create_from_config(config)
        """
        provider_type = config.get("type")

        # Resolve environment variables
        resolved_config = ProviderFactory._resolve_env_vars(config)

        if provider_type == "openrouter":
            return OpenRouterProvider(
                api_key=resolved_config.get("api_key"),
                **resolved_config.get("options", {})
            )

        elif provider_type == "ollama":
            return OllamaProvider(
                api_base=resolved_config.get("api_base", "http://localhost:11434"),
                **resolved_config.get("options", {})
            )

        elif provider_type == "modelscope":
            return ModelScopeProvider(
                api_key=resolved_config.get("api_key"),
                **resolved_config.get("options", {})
            )

        elif provider_type == "iflow":
            return IFlowProvider(
                api_key=resolved_config.get("api_key"),
                **resolved_config.get("options", {})
            )

        elif provider_type == "oai":
            return OAIProvider(
                name=resolved_config.get("name", "oai"),
                api_base=resolved_config.get("api_base"),
                api_key=resolved_config.get("api_key"),
                **resolved_config.get("options", {})
            )

        elif provider_type == "static":
            return StaticProvider(
                model_name=resolved_config["model_name"],
                provider=resolved_config["provider"],
                api_base=resolved_config["api_base"],
                api_key=resolved_config.get("api_key", "dummy"),
                **resolved_config.get("options", {})
            )

        else:
            raise ValueError(f"Unknown provider type: {provider_type}")

    @staticmethod
    def _resolve_env_vars(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve ${ENV_VAR} in config values

        Args:
            config: Configuration dictionary

        Returns:
            Dictionary with environment variables resolved

        Example:
            >>> config = {"api_key": "${MY_KEY}"}
            >>> resolved = ProviderFactory._resolve_env_vars(config)
            >>> # resolved = {"api_key": "actual_value_from_env"}
        """
        resolved = {}
        for key, value in config.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                env_var = value[2:-1]
                resolved[key] = os.getenv(env_var)
            elif isinstance(value, dict):
                resolved[key] = ProviderFactory._resolve_env_vars(value)
            else:
                resolved[key] = value
        return resolved
