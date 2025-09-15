from abc import ABC, abstractmethod
from typing import List, Dict, AsyncGenerator
from llm_client.core.config_loader import BaseModelConfig

class BaseLLMClient(ABC):
    def __init__(self, config: BaseModelConfig):
        self.config = config

    @abstractmethod
    async def get_streaming_chat_completion(
        self, messages: List[Dict[str, str]]
    ) -> AsyncGenerator[str, None]:
        """以异步生成器的方式获取流式的聊天补全。"""
        pass

    @abstractmethod
    def check_availability(self) -> bool:
        """检查模型服务的可用性"""
        pass