"""
ModelScope Provider

ModelScope 是中国的模型社区平台，提供 API-Inference 服务
API 文档: https://help.aliyun.com/zh/model-studio/getting-started/
免费额度: 每天 2000 次调用，每个模型上限 500 次
"""

from .oai import OAIProvider


class ModelScopeProvider(OAIProvider):
    """ModelScope Provider - 魔搭社区免费推理服务"""

    def __init__(self, api_key: str = None, **kwargs):
        """
        初始化 ModelScope Provider

        Args:
            api_key: ModelScope API Key (从 https://modelscope.cn/ 获取)
        """
        super().__init__(
            name="modelscope",
            api_base="https://api-inference.modelscope.cn/v1",
            api_key=api_key,
            **kwargs
        )

    # 预留空间：未来如果需要特殊逻辑（如额度管理、免费/付费筛选），可以重写：
    # def filter_models(self, models: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    #     """筛选符合条件的模型"""
    #     # 添加特殊筛选逻辑（如过滤某些付费模型）
    #     return super().filter_models(models)
