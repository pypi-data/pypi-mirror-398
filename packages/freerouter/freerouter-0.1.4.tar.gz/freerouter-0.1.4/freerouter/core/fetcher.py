"""
FreeRouter Fetcher - Main Business Logic

Manages providers and generates litellm configuration.
"""

import os
import yaml
import logging
import secrets
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from freerouter.providers.base import BaseProvider
from freerouter.core.factory import ProviderFactory

logger = logging.getLogger(__name__)


class FreeRouterFetcher:
    """
    Main fetcher class - manages providers and generates config

    Responsibilities:
    1. Load provider configurations from YAML
    2. Fetch models from all providers
    3. Generate litellm config.yaml
    """

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize FreeRouterFetcher

        Args:
            config_path: Path to output litellm config file
        """
        self.config_path = config_path
        self.providers: List[BaseProvider] = []

    def add_provider(self, provider: BaseProvider):
        """
        Add a provider to the fetcher

        Args:
            provider: BaseProvider instance
        """
        self.providers.append(provider)
        logger.info(f"Added provider: {provider.provider_name}")

    def load_providers_from_yaml(self, yaml_path: str = "config/providers.yaml"):
        """
        Load providers from YAML configuration file

        Args:
            yaml_path: Path to providers.yaml

        Example YAML:
            providers:
              - type: openrouter
                enabled: true
                api_key: ${OPENROUTER_API_KEY}
        """
        if not os.path.exists(yaml_path):
            logger.warning(f"Providers config not found: {yaml_path}")
            return

        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        for provider_config in data.get('providers', []):
            if not provider_config.get('enabled', True):
                logger.info(f"Skipping disabled provider: {provider_config.get('type')}")
                continue

            try:
                provider = ProviderFactory.create_from_config(provider_config)
                self.add_provider(provider)
            except Exception as e:
                logger.error(f"Failed to create provider from config: {e}")

    def fetch_all(self) -> List[Dict[str, Any]]:
        """
        Fetch services from all providers in parallel

        Returns:
            List of service configurations for litellm
        """
        all_services = []

        if not self.providers:
            return all_services

        # Use ThreadPoolExecutor for parallel fetching
        with ThreadPoolExecutor(max_workers=len(self.providers)) as executor:
            # Submit all provider fetch tasks
            future_to_provider = {
                executor.submit(provider.get_services): provider
                for provider in self.providers
            }

            # Collect results as they complete
            for future in as_completed(future_to_provider):
                provider = future_to_provider[future]
                try:
                    services = future.result()
                    all_services.extend(services)
                except Exception as e:
                    logger.error(f"Failed to fetch from {provider.provider_name}: {e}")

        return all_services

    def get_or_create_master_key(self) -> str:
        """
        Get master_key from environment or generate a new one.

        Priority:
        1. LITELLM_MASTER_KEY environment variable
        2. Generate new random key (ephemeral, not saved)

        Returns:
            str: The master key
        """
        # Check environment variable
        env_key = os.getenv("LITELLM_MASTER_KEY")
        if env_key:
            logger.info("Using LITELLM_MASTER_KEY from environment")
            return env_key

        # Generate new ephemeral key
        new_key = f"sk-{secrets.token_urlsafe(32)}"
        logger.info("Generated new ephemeral master_key (not saved to file)")
        logger.info("💡 Tip: Set LITELLM_MASTER_KEY env var to use a persistent key")
        return new_key

    def generate_config(self):
        """
        Generate litellm config.yaml

        Returns:
            bool: True if successful, False otherwise
        """
        services = self.fetch_all()

        if not services:
            logger.warning("No services configured. Config will be empty.")

        # Get or create master_key
        master_key = self.get_or_create_master_key()

        config = {
            "model_list": services,
            "litellm_settings": {
                "drop_params": True,
                "set_verbose": True,
                "request_timeout": 60,
                "telemetry": False,  # Disable LiteLLM telemetry
                "master_key": master_key,  # Add master_key for authentication
                # Log raw HTTP requests/responses (curl commands + raw responses)
                # Set to True to see actual requests sent to providers
                "log_raw_request_response": os.getenv("FREEROUTER_LOG_RAW", "false").lower() == "true"
            }
        }

        # Ensure config directory exists
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)

        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

        logger.info(f"Generated config at {self.config_path}")
        logger.info(f"Total services configured: {len(services)}")
        return True
