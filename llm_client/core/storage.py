import os
import json
from datetime import datetime
from typing import List, Dict
from .exceptions import StorageError
import logging

logger = logging.getLogger("LLM_APP")

class ConversationHistory:
    def __init__(self, storage_dir: str):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)
        logger.info(f"对话历史存储已初始化，目录: {self.storage_dir}")

    def save(self, messages: List[Dict[str, str]], model_name: str):
        try:
            now = datetime.now()
            date_dir = now.strftime("%Y-%m-%d")
            time_filename = now.strftime("%H-%M-%S") + ".json"
            
            day_path = os.path.join(self.storage_dir, date_dir)
            os.makedirs(day_path, exist_ok=True)
            
            filepath = os.path.join(day_path, time_filename)

            data_to_save = {
                "model": model_name,
                "timestamp_utc": now.isoformat(),
                "conversation": messages
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=2)
            
            logger.info(f"对话历史已保存至: {filepath}")

        except Exception as e:
            logger.error(f"保存对话历史失败: {e}", exc_info=True)
            raise StorageError(f"无法保存对话历史: {e}")