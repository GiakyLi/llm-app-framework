# llm_client/core/prompts.py
import yaml
from typing import Dict, List
from pydantic import BaseModel
from .exceptions import ConfigError
import logging

logger = logging.getLogger("LLM_APP")

class PromptTemplate(BaseModel):
    display_name: str
    template: str

class PromptManager:
    def __init__(self, filepath: str):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            self.system_prompts: Dict[str, PromptTemplate] = {
                k: PromptTemplate(**v) for k, v in data.get('system_prompts', {}).items()
            }
            self.user_prompts: Dict[str, PromptTemplate] = {
                k: PromptTemplate(**v) for k, v in data.get('user_prompts', {}).items()
            }
            logger.info(f"成功加载 {len(self.system_prompts)} 个系统提示词和 {len(self.user_prompts)} 个用户提示词。")
        except FileNotFoundError:
            raise ConfigError(f"提示词配置文件未找到: {filepath}")
        except Exception as e:
            raise ConfigError(f"解析提示词配置文件 '{filepath}' 时出错: {e}")

    def get_system_prompt(self, name: str) -> PromptTemplate:
        if name not in self.system_prompts:
            logger.warning(f"系统提示词 '{name}' 未找到，将使用'default'。")
            return self.system_prompts.get('default')
        return self.system_prompts[name]
    
    def list_system_prompts(self) -> List[str]:
        return [f"{name} - {prompt.display_name}" for name, prompt in self.system_prompts.items()]