# llm_client/core/config_loader.py

import os
import yaml
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from .exceptions import ConfigError
import logging

temp_logger = logging.getLogger(__name__)

# 新增Instruction模板类
class InstructionTemplate(BaseModel):
    display_name: str
    template: str

class ModelParameters(BaseModel):
    temperature: float = 0.7
    max_tokens: int = 4096

class BaseModelConfig(BaseModel):
    provider: str
    display_name: str
    model_name: str
    parameters: ModelParameters

class OpenAICompatibleConfig(BaseModelConfig):
    provider: str = "openai_compatible"
    api_base: str
    api_key: str

    @validator('api_key')
    def get_api_key_from_env(cls, v):
        if v.startswith("ENV:"):
            env_var = v.split("ENV:")[1]
            key = os.getenv(env_var)
            if not key:
                raise ConfigError(f"环境变量 '{env_var}' 未设置, 无法加载API密钥。")
            return key
        return v

class ConfigLoader:
    def __init__(self, app_config_path: str, models_config_path: str):
        try:
            with open(app_config_path, 'r', encoding='utf-8') as f:
                self.app_config = yaml.safe_load(f)
            with open(models_config_path, 'r', encoding='utf-8') as f:
                self.models_config_data = yaml.safe_load(f)
        except FileNotFoundError as e:
            raise ConfigError(f"配置文件未找到: {e.filename}")
        except yaml.YAMLError as e:
            raise ConfigError(f"YAML配置文件格式错误: {e}")

        self.models: Dict[str, BaseModelConfig] = self._parse_models()
        # 直接解析instructions
        self.instructions: Dict[str, InstructionTemplate] = self._parse_instructions()
        temp_logger.info(f"成功加载 {len(self.models)} 个模型配置和 {len(self.instructions)} 条指令。")

    def _parse_instructions(self) -> Dict[str, InstructionTemplate]:
        instructions = {}
        for name, data in self.models_config_data.get('instructions', {}).items():
            try:
                instructions[name] = InstructionTemplate(**data)
            except Exception as e:
                raise ConfigError(f"解析指令 '{name}' 时出错: {e}")
        return instructions

    def _parse_models(self) -> Dict[str, BaseModelConfig]:
        # ... (此方法保持不变) ...
        models = {}
        for name, config in self.models_config_data.get('models', {}).items():
            provider = config.get('provider')
            try:
                if provider == 'openai_compatible':
                    models[name] = OpenAICompatibleConfig(**config)
                else:
                    temp_logger.warning(f"不支持的模型提供商: '{provider}' for model '{name}'. 已跳过。")
            except Exception as e:
                raise ConfigError(f"解析模型 '{name}' 配置时出错: {e}")
        return models

    def get_model_config(self, name: str) -> BaseModelConfig:
        model_conf = self.models.get(name)
        if not model_conf:
            raise ConfigError(f"模型 '{name}' 在配置文件中未定义。")
        return model_conf

    def get_instruction(self, name: str) -> InstructionTemplate:
        instruction = self.instructions.get(name)
        if not instruction:
            raise ConfigError(f"指令 '{name}' 在配置文件中未定义。")
        return instruction