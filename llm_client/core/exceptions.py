class LLMAppError(Exception):
    """应用的基础异常类"""
    pass

class ConfigError(LLMAppError):
    """配置相关的错误"""
    pass

class ModelNotFoundError(LLMAppError):
    """当请求的模型在配置中未找到时抛出"""
    pass

class APIConnectionError(LLMAppError):
    """API连接相关的错误"""
    pass

class StorageError(LLMAppError):
    """数据存储相关的错误"""
    pass