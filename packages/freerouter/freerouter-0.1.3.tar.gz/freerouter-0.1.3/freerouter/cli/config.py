"""
Configuration file discovery and management
"""

import os
import yaml
from pathlib import Path
from typing import Optional


class ConfigManager:
    """
    Manages configuration file locations with priority order:
    1. Current directory: ./config/providers.yaml
    2. User home: ~/.config/freerouter/providers.yaml
    3. System default: Use example
    """

    DEFAULT_PROVIDER_CONFIG = "providers.yaml"
    DEFAULT_OUTPUT_CONFIG = "config.yaml"

    def __init__(self):
        self.config_locations = [
            Path.cwd() / "config",
            Path.home() / ".config" / "freerouter",
        ]

    def find_provider_config(self) -> Optional[Path]:
        """
        Find providers.yaml with priority order

        Returns:
            Path to providers.yaml or None if not found
        """
        for location in self.config_locations:
            config_file = location / self.DEFAULT_PROVIDER_CONFIG
            if config_file.exists():
                return config_file
        return None

    def get_output_config_path(self) -> Path:
        """
        Get path for output config.yaml

        Returns:
            Path where config.yaml should be written
        """
        # Try current directory first
        local_config = Path.cwd() / "config"
        if local_config.exists():
            return local_config / self.DEFAULT_OUTPUT_CONFIG

        # Use user home
        user_config = Path.home() / ".config" / "freerouter"
        user_config.mkdir(parents=True, exist_ok=True)
        return user_config / self.DEFAULT_OUTPUT_CONFIG

    def ensure_user_config_dir(self) -> Path:
        """
        Ensure user config directory exists

        Returns:
            Path to user config directory
        """
        user_config = Path.home() / ".config" / "freerouter"
        user_config.mkdir(parents=True, exist_ok=True)
        return user_config

    def _disable_all_providers(self, config_dict: dict) -> dict:
        """
        将配置中所有 provider 的 enabled 设置为 false

        Args:
            config_dict: 从 YAML 读取的配置字典

        Returns:
            修改后的配置字典
        """
        if "providers" in config_dict:
            for provider in config_dict["providers"]:
                provider["enabled"] = False
        return config_dict

    def init_config(self, interactive: bool = False, use_user_config: bool = True) -> Path:
        """
        Initialize config directory with example

        Args:
            interactive: 是否为交互式模式
            use_user_config: True 使用 ~/.config/freerouter, False 使用 ./config

        Returns:
            Path to created config directory
        """
        # 确定目标目录
        if use_user_config:
            target_dir = Path.home() / ".config" / "freerouter"
        else:
            target_dir = Path.cwd() / "config"

        # 创建目录
        target_dir.mkdir(parents=True, exist_ok=True)

        # 目标配置文件
        target_file = target_dir / "providers.yaml"

        # Ask if overwrite when file exists
        if target_file.exists() and interactive:
            overwrite = input(f"\nConfiguration file already exists: {target_file}\nOverwrite? [y/N]: ").strip().lower()
            if overwrite != "y":
                print("Keeping existing configuration")
                return target_dir

        # 读取示例文件
        example_file = Path(__file__).parent.parent.parent / "examples" / "providers.yaml.example"

        if example_file.exists():
            # 读取示例文件内容
            with open(example_file, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)

            # 将所有 provider 的 enabled 设置为 false
            config_data = self._disable_all_providers(config_data)

            # 写入目标文件
            with open(target_file, "w", encoding="utf-8") as f:
                # 保留注释的方式：直接读取原始文本并替换
                with open(example_file, "r", encoding="utf-8") as ef:
                    content = ef.read()
                    # 将所有 "enabled: true" 替换为 "enabled: false"
                    content = content.replace("enabled: true", "enabled: false")
                f.write(content)
        else:
            # 如果示例文件不存在，创建一个空配置
            empty_config = {"providers": []}
            with open(target_file, "w", encoding="utf-8") as f:
                yaml.dump(empty_config, f)

        return target_dir
