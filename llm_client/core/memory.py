# llm_client/core/memory.py

import tiktoken
from typing import List, Dict
import logging

logger = logging.getLogger("LLM_APP")

class ConversationMemory:
    def __init__(self, system_prompt: str, token_limit: int = 3000):
        self.system_prompt = {"role": "system", "content": system_prompt}
        self.token_limit = token_limit
        self.history: List[Dict[str, str]] = []
        # 使用 tiktoken 初始化编码器，"cl100k_base" 适用于 gpt-4, gpt-3.5 等新模型
        try:
            self.encoding = tiktoken.get_encoding("cl100k_base")
        except Exception:
            # 如果下载失败，回退到按字符估算，并给出警告
            logger.warning("无法加载 tiktoken 编码器，将回退到基于字符的Token估算。")
            self.encoding = None
        logger.info(f"对话记忆已初始化，上下文Token限制: {self.token_limit}")

    def _count_tokens(self, text: str) -> int:
        if self.encoding:
            return len(self.encoding.encode(text))
        # 回退逻辑
        return len(text) // 3

    def add_message(self, role: str, content: str):
        self.history.append({"role": role, "content": content})

    def get_messages(self) -> List[Dict[str, str]]:
        """
        获取符合上下文窗口大小的对话历史。
        始终包含系统提示词，并从最近的对话开始向前追溯。
        """
        messages_to_send = []
        current_token_count = 0
        
        system_prompt_tokens = self._count_tokens(self.system_prompt['content'])
        
        for message in reversed(self.history):
            message_tokens = self._count_tokens(message['content'])
            if current_token_count + message_tokens + system_prompt_tokens > self.token_limit:
                logger.warning(f"上下文窗口已满，对话历史将被截断。")
                break
            messages_to_send.insert(0, message)
            current_token_count += message_tokens
            
        return [self.system_prompt] + messages_to_send

    def clear(self):
        self.history.clear()
        logger.info("对话记忆已清空。")