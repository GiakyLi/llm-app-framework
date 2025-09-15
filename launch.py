# launch.py (Final Polished Version)
import subprocess
import time
import signal
import sys
import os
import argparse
import requests
import threading
from rich.console import Console
from llm_client.core.config_loader import ConfigLoader
from llm_client.core.exceptions import LLMAppError

def stream_output(pipe, prefix, log_file):
    """从子进程的管道中读取输出，写入日志文件，并有选择地打印到控制台"""
    try:
        for line in iter(pipe.readline, ''):
            # 1. 无论如何，都将原始日志行写入文件
            if log_file:
                log_file.write(line)

            # 2. [核心修改] 只有当日志行包含特定关键字时，才打印到控制台
            #    这可以过滤掉绝大多数VLLM的INFO级别的常规日志
            line_upper = line.upper()
            if 'ERROR' in line_upper or 'WARNING' in line_upper:
                print(f"[{prefix}] {line}", end="")
        pipe.close()
    except Exception as e:
        print(f"Error streaming output from {prefix}: {e}")


def start_vllm_server(model_path: str, host: str, port: int, log_file):
    """在后台启动VLLM服务器，并实时显示其日志"""
    command = [
        sys.executable,
        "-m", "vllm.entrypoints.openai.api_server",
        "--model", model_path,
        "--trust-remote-code",
        "--max-model-len", "8192",
        "--host", host,
        "--port", str(port)
    ]
    
    print(f"🚀 正在后台启动VLLM服务器...")
    print(f"   模型路径: {model_path}")
    print(f"   监听地址: http://{host}:{port}")
    print(f"   最大长度限制: 8192 tokens")
    print(f"   服务器日志将保存在: {log_file.name}") # 使用 log_file.name 获取路径
    print("-" * 50)

    preexec_fn = os.setsid if sys.platform != "win32" else None
    
    server_process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        preexec_fn=preexec_fn
    )

    # 创建并启动线程，将日志文件句柄传递进去
    stdout_thread = threading.Thread(
        target=stream_output, 
        args=(server_process.stdout, "VLLM-Server", log_file)
    )
    stderr_thread = threading.Thread(
        target=stream_output, 
        args=(server_process.stderr, "VLLM-Error", log_file)
    )
    stdout_thread.daemon = True
    stderr_thread.daemon = True
    stdout_thread.start()
    stderr_thread.start()

    return server_process

def wait_for_server_ready(server_process, server_url, console: Console, timeout: int = 60):
    """使用rich.status等待VLLM服务器准备就绪"""
    
    # 使用rich.status创建一个动态的加载动画
    with console.status("[bold yellow]⏳ 正在等待服务器响应...", spinner="dots12") as status:
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # 检查服务器进程是否已经意外退出
            if server_process.poll() is not None:
                return False # 如果进程退出，直接返回失败
                
            try:
                response = requests.get(server_url, timeout=2) # 使用较短的超时进行轮询
                if response.status_code == 200:
                    return True # 服务器就绪，返回成功
            except requests.exceptions.RequestException:
                pass # 忽略连接错误，继续等待
            
            time.sleep(2)
            
    return False # 如果循环结束仍未就绪，则为超时

def start_client(model_id: str, role_id: str):
    """在前台启动客户端应用"""
    command = [
        sys.executable,
        "main.py",
        "--model", model_id,
        "--role", role_id
    ]
    print("\n🚀 正在启动客户端...")
    print("-" * 50)
    subprocess.run(command)

def main():
    # [核心修改] 创建一个Console对象供后续使用
    console = Console()

    try:
        config_loader = ConfigLoader(
            app_config_path='configs/app_config.yaml',
            models_config_path='configs/models_config.yaml'
        )
        
        app_config = config_loader.app_config
        
        log_config = app_config.get("logging", {})
        log_dir = log_config.get("dir", "logs")
        os.makedirs(log_dir, exist_ok=True)
        vllm_log_path = os.path.join(log_dir, "vllm_server.log")

        server_config = app_config.get("vllm_server", {})
        server_host = server_config.get("host", "127.0.0.1")
        server_port = server_config.get("port", 8000)
        server_url = f"http://127.0.0.1:{server_port}/v1/models"
        
        model_choices = list(config_loader.models.keys())
        parser = argparse.ArgumentParser(description="一键启动VLLM服务器和客户端")
        parser.add_argument("-m", "--model", type=str, default=model_choices[0] if model_choices else None, choices=model_choices, help="要启动的本地模型ID")
        parser.add_argument("-r", "--role", type=str, default="default", help="客户端要使用的初始角色ID")
        args = parser.parse_args()

        if not args.model:
            console.print("[bold red]❌ 错误: 配置文件中未定义任何模型。")
            sys.exit(1)

        server_process = None
        
        with open(vllm_log_path, 'w', buffering=1, encoding='utf-8') as log_file:
            model_config = config_loader.get_model_config(args.model)
            
            should_start_server = "localhost" in getattr(model_config, 'api_base', '') or \
                                "127.0.0.1" in getattr(model_config, 'api_base', '')

            if not should_start_server:
                console.print(f"✅ 模型 '{args.model}' 是一个远程API模型，无需启动本地服务器。")
                start_client(args.model, args.role)
                return

            server_process = start_vllm_server(model_config.model_name, server_host, server_port, log_file)

            # [核心修改] 将console对象传递进去，并根据返回结果打印最终状态
            if wait_for_server_ready(server_process, server_url, console):
                console.print("[bold green]✅ 服务器已就绪！")
                start_client(args.model, args.role)
            else:
                console.print(f"\n[bold red]❌ 服务器启动超时或意外退出！请检查 'logs/vllm_server.log' 文件获取详细错误。")
                raise RuntimeError("无法启动VLLM服务器。")

    except (Exception, KeyboardInterrupt) as e:
        if isinstance(e, KeyboardInterrupt):
            console.print("\n👋 收到退出信号...")
        elif not isinstance(e, RuntimeError):
            console.print(f"\n[bold red]❌ 发生错误: {e}")
    finally:
        if server_process and server_process.poll() is None:
            console.print(f"🧹 正在关闭后台VLLM服务器 (PID: {server_process.pid})...")
            if sys.platform != "win32":
                os.killpg(os.getpgid(server_process.pid), signal.SIGTERM)
            else:
                server_process.terminate()
            console.print("✅ 清理完成。")

if __name__ == "__main__":
    main()