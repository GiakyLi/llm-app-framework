# llm_client/app.py
import argparse
import asyncio
from rich.live import Live
from rich.markdown import Markdown

from .core.config_loader import ConfigLoader
from .core.storage import ConversationHistory
from .core.exceptions import LLMAppError
from .core.prompts import PromptManager
from .core.memory import ConversationMemory
from .clients.openai_client import client_factory
from .ui.cli import RichCLI_UI
import logging

logger = logging.getLogger("LLM_APP")

class CommandLineApp:
    def __init__(self, config_loader: ConfigLoader, prompt_manager: PromptManager, 
                 history_saver: ConversationHistory, memory_config: dict):
        self.config_loader = config_loader
        self.prompt_manager = prompt_manager
        self.history_saver = history_saver
        self.memory_config = memory_config
        self.ui = RichCLI_UI()
        self.client = None
        self.memory: ConversationMemory = None
        self.current_model_id = None

    async def start_session(self, model_id: str, role_id: str):
        try:
            model_config = self.config_loader.get_model_config(model_id)
            self.client = client_factory(model_config)
            self.current_model_id = model_id
            
            system_prompt = self.prompt_manager.get_system_prompt(role_id)
            self.memory = ConversationMemory(
                system_prompt=system_prompt.template,
                token_limit=self.memory_config.get('max_context_tokens', 3000)
            )
            
            self.ui.display_welcome(model_config.display_name, system_prompt.display_name)
            logger.info(f"新会话启动. 模型: {model_id}, 角色: {role_id}")
            
        except LLMAppError as e:
            logger.critical(f"应用启动失败: {e}")
            self.ui.display_system_message(f"启动失败: {e}", "Error")
            return
        
        await self.main_loop()

    async def main_loop(self):
        while True:
            try:
                user_input = await asyncio.to_thread(self.ui.get_user_input)
                if user_input.startswith('/'):
                    await self.handle_command(user_input)
                    continue
                
                self.memory.add_message("user", user_input)
                
                self.ui.display_assistant_header()
                
                full_response = ""
                # 因为INFO日志被屏蔽，我们可以安全地直接打印流式内容
                async for chunk in self.client.get_streaming_chat_completion(self.memory.get_messages()):
                    # 使用UI方法直接打印块，实现打字机效果
                    self.ui.console.print(chunk, end="")
                    full_response += chunk
                
                # 流式结束后打印一个换行符，保持格式整洁
                self.ui.console.print()

                self.memory.add_message("assistant", full_response)

            except (KeyboardInterrupt, EOFError):
                break
        
        self.save_history()

    def save_history(self):
        if len(self.memory.history) > 0:
            try:
                # 传递完整的对话历史（包括系统提示）进行保存
                full_conversation = [self.memory.system_prompt] + self.memory.history
                self.history_saver.save(full_conversation, self.current_model_id)
            except LLMAppError as e:
                logger.error(f"无法保存对话历史: {e}")
        self.ui.display_system_message("再见!", "Session Ended")

    async def handle_command(self, command: str):
        parts = command.lower().strip().split()
        cmd = parts[0]

        if cmd in ['/exit', '/quit']:
            raise KeyboardInterrupt
        elif cmd == '/help':
            self.ui.display_help(self.prompt_manager.list_system_prompts())
        elif cmd == '/clear':
            self.memory.clear()
            self.ui.display_system_message("当前对话历史已清空。")
        elif cmd == '/save':
            self.save_history()
            self.ui.display_system_message("对话已手动保存。")
        elif cmd == '/roles':
            self.ui.display_help([]) # 只显示角色列表部分
        elif cmd == '/role':
            if len(parts) > 1:
                role_id = parts[1]
                try:
                    # 切换角色意味着开始一个全新的会话
                    self.save_history()
                    self.ui.display_system_message(f"正在切换到角色 '{role_id}' 并开始新会话...")
                    await self.start_session(self.current_model_id, role_id)
                except Exception as e:
                    self.ui.display_system_message(f"切换角色失败: {e}", "Error")
            else:
                self.ui.display_system_message("用法: /role <角色ID>", "Info")
        else:
            self.ui.display_system_message(f"未知命令: '{cmd}'. 输入 /help 查看帮助。", "Warning")

    def run(self):
        parser = argparse.ArgumentParser(description="一个可扩展的本地与云端大模型交互框架")
        
        model_choices = list(self.config_loader.models.keys())
        parser.add_argument(
            "-m", "--model", type=str, default=model_choices[0] if model_choices else None,
            choices=model_choices, help="要使用的模型ID"
        )
        
        role_choices = list(self.prompt_manager.system_prompts.keys())
        parser.add_argument(
            "-r", "--role", type=str, default="default",
            choices=role_choices, help="要使用的系统角色ID"
        )

        args = parser.parse_args()
        
        if not args.model:
            self.ui.display_system_message("配置文件中未定义任何模型，程序无法启动。", "Critical Error")
            return

        asyncio.run(self.start_session(args.model, args.role))