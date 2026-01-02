"""
iFlow Provider

iFlow 是一个提供免费 AI 模型的服务
API 文档: https://iflow.cn/
"""

from .oai import OAIProvider


class IFlowProvider(OAIProvider):
    """iFlow Provider - 免费模型服务"""

    def __init__(self, api_key: str = None, **kwargs):
        """
        初始化 iFlow Provider

        Args:
            api_key: iFlow API Key (从 https://iflow.cn/ 获取)
        """
        super().__init__(
            name="iflow",
            api_base="https://apis.iflow.cn/v1",
            api_key=api_key,
            **kwargs
        )

    # 预留空间：未来如果需要特殊逻辑（如免费/付费筛选），可以重写：
    # def filter_models(self, models: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    #     """筛选免费模型"""
    #     # 添加特殊筛选逻辑
    #     return super().filter_models(models)
