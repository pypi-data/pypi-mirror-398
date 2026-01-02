"""
OAI (OpenAI-Compatible) Provider

通用的 OpenAI 兼容 API Provider，支持任何遵循 OpenAI API 规范的服务
API 规范: https://platform.openai.com/docs/api-reference/models/list
"""

import requests
from typing import List, Dict, Any
from .base import BaseProvider


class OAIProvider(BaseProvider):
    """OAI Provider - OpenAI 兼容服务的通用 Provider"""

    def __init__(self, name: str, api_base: str, api_key: str = None, **kwargs):
        """
        初始化 OAI Provider

        Args:
            name: 供应商名称 (如 myservice, mycompany 等)
            api_base: API 基础地址 (如 https://api.example.com/v1)
            api_key: API Key
        """
        super().__init__(**kwargs)
        self.name = name
        self.api_base = api_base.rstrip('/')  # 去掉末尾的 /
        self.api_key = api_key or ""

    @property
    def provider_name(self) -> str:
        return self.name

    def fetch_models(self) -> List[Dict[str, Any]]:
        """
        从 OpenAI 兼容的 /v1/models 接口获取模型列表

        Returns:
            模型列表，每个模型包含 id 字段
        """
        url = f"{self.api_base}/models"
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        } if self.api_key else {}

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            if "data" in data:
                models = data["data"]
                self.logger.info(f"Fetched {len(models)} models from {self.name}")
                return models
            else:
                self.logger.warning(f"No 'data' field in {self.name} response")
                return []

        except Exception as e:
            self.logger.error(f"Failed to fetch models from {self.name}: {e}")
            return []

    def format_service(self, model: Dict[str, Any]) -> Dict[str, Any]:
        """
        将模型格式化为 LiteLLM 配置

        OpenAI 兼容服务使用 openai/ 前缀

        Args:
            model: 模型信息字典

        Returns:
            LiteLLM service 配置
        """
        model_id = model.get("id", "unknown")

        return {
            "model_name": model_id,
            "litellm_params": {
                "model": f"openai/{model_id}",
                "api_base": self.api_base,
                "api_key": self.api_key,
            }
        }
