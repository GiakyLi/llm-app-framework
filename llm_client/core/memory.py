# llm_client/core/memory.py
from typing import List, Dict
import logging

logger = logging.getLogger("LLM_APP")

class ConversationMemory:
    def __init__(self, system_prompt: str, token_limit: int = 3000):
        self.system_prompt = {"role": "system", "content": system_prompt}
        self.token_limit = token_limit
        self.history: List[Dict[str, str]] = []
        logger.info(f"对话记忆已初始化，上下文Token限制: {self.token_limit}")

    def add_message(self, role: str, content: str):
        self.history.append({"role": role, "content": content})

    def get_messages(self) -> List[Dict[str, str]]:
        """
        获取符合上下文窗口大小的对话历史。
        始终包含系统提示词，并从最近的对话开始向前追溯。
        """
        messages_to_send = []
        current_token_count = 0
        
        # 简单的token计数器 (1 token ~= 4 chars in English)
        # 注意：这只是一个估算，精确计数需要使用模型的tokenizer
        system_prompt_tokens = len(self.system_prompt['content']) // 3 
        
        # 从后往前遍历历史记录
        for message in reversed(self.history):
            message_tokens = len(message['content']) // 3
            if current_token_count + message_tokens + system_prompt_tokens > self.token_limit:
                logger.warning(f"上下文窗口已满，对话历史将被截断。")
                break
            messages_to_send.insert(0, message)
            current_token_count += message_tokens
            
        # 始终将系统提示词放在最前面
        return [self.system_prompt] + messages_to_send

    def clear(self):
        self.history.clear()
        logger.info("对话记忆已清空。")