import openai
from typing import List, Dict, AsyncGenerator
from .base_client import BaseLLMClient
from llm_client.core.config_loader import OpenAICompatibleConfig
from llm_client.core.exceptions import APIConnectionError
from llm_client.core.config_loader import BaseModelConfig
import logging

logger = logging.getLogger("LLM_APP")

class OpenAICompatibleClient(BaseLLMClient):
    def __init__(self, config: OpenAICompatibleConfig):
        super().__init__(config)
        self.config: OpenAICompatibleConfig = config # for type hinting
        try:
            self.async_client = openai.AsyncOpenAI(
                base_url=self.config.api_base,
                api_key=self.config.api_key
            )
            logger.info(f"OpenAI兼容客户端已为模型 '{self.config.display_name}' 初始化，目标: {self.config.api_base}")
        except Exception as e:
            raise APIConnectionError(f"初始化OpenAI客户端失败: {e}")
    
    async def check_availability(self) -> bool:
        """通过尝试列出模型来检查服务的可用性。"""
        logger.info(f"正在检查API服务 '{self.config.api_base}' 的可用性...")
        try:
            # 发送一个轻量级请求
            await self.async_client.models.list(timeout=5)
            logger.info(f"API服务 '{self.config.api_base}' 连接成功。")
            return True
        except Exception as e:
            logger.error(f"无法连接到API服务 '{self.config.api_base}': {e}")
            return False

    async def get_streaming_chat_completion(
        self, messages: List[Dict[str, str]]
    ) -> AsyncGenerator[str, None]:
        logger.info(f"向模型 '{self.config.model_name}' 发送流式请求...")
        try:
            stream = await self.async_client.chat.completions.create(
                model=self.config.model_name,
                messages=messages,
                max_tokens=self.config.parameters.max_tokens,
                temperature=self.config.parameters.temperature,
                stream=True
            )
            async for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
            logger.info("流式响应接收完毕。")
        except openai.APIConnectionError as e:
            logger.error(f"无法连接到API服务器: {e.__cause__}", exc_info=True)
            yield f"\n[错误: 无法连接到API服务器 {self.config.api_base}]"
        except openai.NotFoundError as e:
             logger.error(f"模型未找到: {e}", exc_info=True)
             yield f"\n[错误: 模型 '{self.config.model_name}' 在服务器上未找到]"
        except Exception as e:
            logger.error(f"流式请求过程中发生未知错误: {e}", exc_info=True)
            yield f"\n[错误: {e}]"

def client_factory(model_config: BaseModelConfig) -> BaseLLMClient:
    """根据配置创建并返回相应的客户端实例"""
    provider = model_config.provider
    if provider == 'openai_compatible':
        return OpenAICompatibleClient(model_config)
    # 在这里可以添加其他客户端的工厂逻辑
    # elif provider == 'huggingface_local':
    #     return HuggingFaceClient(model_config)
    else:
        raise NotImplementedError(f"提供商 '{provider}' 的客户端尚未实现。")