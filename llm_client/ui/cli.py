# llm_client/ui/cli.py
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

class RichCLI_UI:
    def __init__(self):
        self.console = Console()

    def display_full_assistant_response(self, full_response: str):
        self.console.print("\n")
        md = Markdown(full_response)
        self.console.print(md)
        self.console.print()

    def display_system_message(self, message: str, title: str = "System"):
        self.console.print(Panel(message, title=f"[bold yellow]{title}[/bold yellow]", border_style="yellow"))

    def display_welcome(self, model_display_name: str, prompt_display_name: str):
        welcome_message = (
            f"你好！你正在与 [bold green]{model_display_name}[/bold green] 对话。\n"
            f"当前系统角色: [bold cyan]{prompt_display_name}[/bold cyan]。\n"
            "输入 `/help` 查看所有可用命令。"
        )
        self.console.print(Panel(welcome_message, title="[bold magenta]LLM 交互框架[/bold magenta]", expand=False))

    def display_assistant_header(self):
        """打印助手的回复头部，并确保换行"""
        self.console.print("\n[bold magenta]Assistant:[/bold magenta]")

    def get_user_input(self) -> str:
        # 在用户输入前也加一个换行，让布局更宽松
        return self.console.input("\n[bold green]You: [/bold green]")

    def display_help(self, system_prompts: list):
        table = Table(title="[bold]可用命令[/bold]")
        table.add_column("命令", style="cyan")
        table.add_column("描述")
        
        table.add_row("/exit, /quit", "退出程序并保存当前对话。")
        table.add_row("/clear", "清空当前对话历史。")
        table.add_row("/save", "手动保存当前对话。")
        table.add_row("/role <角色ID>", "切换一个新的系统角色并开始新对话。")
        table.add_row("/roles", "列出所有可用的系统角色。")
        table.add_row("/help", "显示此帮助信息。")
        
        self.console.print(table)
        
        self.console.print("\n[bold]可用角色 ( /role <角色ID> ):[/bold]")
        for prompt_info in system_prompts:
            self.console.print(f"  - {prompt_info}")