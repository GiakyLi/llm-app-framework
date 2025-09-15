# main.py
from llm_client.app import CommandLineApp
from llm_client.core.config_loader import ConfigLoader
from llm_client.core.storage import ConversationHistory
from llm_client.core.logger import setup_logger
from llm_client.core.exceptions import LLMAppError
import logging

def main():
    try:
        # 1. 加载所有配置
        config_loader = ConfigLoader(
            app_config_path='configs/app_config.yaml',
            models_config_path='configs/models_config.yaml'
        )
        app_config = config_loader.app_config

        # 2. 设置日志
        logger = setup_logger(app_config.get('logging', {}))
        
        # 3. 初始化存储和记忆模块配置
        history_saver = ConversationHistory(
            storage_dir=app_config.get('storage', {}).get('history_dir', 'data/history')
        )
        memory_config = app_config.get('memory', {})

        # 4. 创建并运行应用
        app = CommandLineApp(config_loader, history_saver, memory_config)
        app.run()

    except LLMAppError as e:
        print(f"\n[应用启动失败]: {e}")
        logging.basicConfig()
        logging.critical(f"应用启动失败: {e}", exc_info=True)
    except Exception as e:
        print(f"\n[发生未知致命错误]: {e}")
        logging.basicConfig()
        logging.critical(f"发生未知致命错误: {e}", exc_info=True)

if __name__ == "__main__":
    main()