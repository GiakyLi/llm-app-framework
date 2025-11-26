# launch.py (Restored to original format with added max_token control)
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
            # 原始日志行写入文件
            if log_file:
                log_file.write(line)

            # 过滤INFO级别日志
            line_upper = line.upper()
            if 'ERROR' in line_upper or 'WARNING' in line_upper:
                print(f"[{prefix}] {line}", end="")
        pipe.close()
    except Exception as e:
        print(f"Error streaming output from {prefix}: {e}")


def start_vllm_server(model_path: str, host: str, port: int, log_file, 
                        max_model_len: int = None, gpu_memory_utilization: float = 0.90):
    """在后台启动VLLM服务器，并实时显示其日志"""
    command = [
        sys.executable,
        "-m", "vllm.entrypoints.openai.api_server",
        "--model", model_path,
        "--trust-remote-code",
        "--host", host,
        "--port", str(port),
        "--gpu-memory-utilization", str(gpu_memory_utilization)
    ]
    
    if max_model_len:
        command.extend(["--max-model-len", str(max_model_len)])
    
    print(f"🚀 正在后台启动VLLM服务器...")
    print(f"   模型路径: {model_path}")
    print(f"   监听地址: http://{host}:{port}")
    if max_model_len:
        print(f"   最大模型长度: {max_model_len} tokens")
    print(f"   服务器日志将保存在: {log_file.name}") 
    print("-" * 50)

    preexec_fn = os.setsid if sys.platform != "win32" else None
    
    server_process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,  # 捕获标准输出
        stderr=subprocess.PIPE,  # 捕获标准错误
        text=True,  # 以文本模式读写 (str)
        bufsize=1,  # 开启行缓冲，确保日志能被逐行读取
        preexec_fn=preexec_fn,
        encoding='utf-8',
        errors='replace'
    )

    # 创建并启动线程
    stdout_thread = threading.Thread(target=stream_output, args=(server_process.stdout, "VLLM-Server", log_file), daemon=True)
    stderr_thread = threading.Thread(target=stream_output, args=(server_process.stderr, "VLLM-Error", log_file), daemon=True)
    stdout_thread.start()
    stderr_thread.start()

    return server_process

def wait_for_server_ready(server_process, server_url, console: Console, timeout: int = 120):
    """使用rich.status等待VLLM服务器准备就绪"""
    with console.status("[bold yellow]⏳ 正在等待服务器响应...", spinner="dots12") as status:
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if server_process.poll() is not None:
                return False 
                
            try:
                response = requests.get(server_url, timeout=2)
                if response.status_code == 200:
                    return True
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(2)
            
    return False

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
    # 替换进程，更好地信号处理(如Ctrl+C)
    os.execv(sys.executable, command)

def main():
    console = Console()
    server_process = None
    try:
        # 1. 加载配置
        config_loader = ConfigLoader(
            app_config_path='configs/app_config.yaml',
            models_config_path='configs/models_config.yaml'
        )
        
        app_config = config_loader.app_config
        defaults = app_config.get('launcher_defaults', {})
        default_model = defaults.get('default_model', None)
        default_role = defaults.get('default_role', 'default')
        default_gpu_util = defaults.get('default_gpu_utilization', 0.70)
        default_max_len = defaults.get('default_max_model_len', None)
        
        # 2. 设置日志目录
        log_dir = app_config.get("logging", {}).get("dir", "logs")
        os.makedirs(log_dir, exist_ok=True)  # 创建日志目录（如果不存在）
        vllm_log_path = os.path.join(log_dir, "vllm_server.log")

        # 3. 获取服务器配置
        server_config = app_config.get("vllm_server", {})
        server_host = server_config.get("host", "127.0.0.1")
        server_port = server_config.get("port", 8000)
        
        # 4. 智能处理健康检查的URL
        health_check_host = "127.0.0.1" if server_host == "0.0.0.0" else server_host
        server_url = f"http://{health_check_host}:{server_port}/health" # 使用 /health 接口
        
        # 5. 设置命令行参数解析
        parser = argparse.ArgumentParser(description="一键启动VLLM服务器和客户端")
        model_choices = list(config_loader.models.keys())

        if default_model and default_model in model_choices:
            final_default_model = default_model
        else:
            final_default_model = model_choices[0] if model_choices else None

        parser.add_argument("-m", "--model", type=str, default=final_default_model, choices=model_choices, help="要启动的本地模型ID")
        parser.add_argument("-r", "--role", type=str, default=default_role, help="客户端要使用的初始角色ID")
        parser.add_argument("--max-model-len", type=int, default=default_max_len, help="手动设置模型的最大序列长度以适应显存 (例如 8192)")
        parser.add_argument("--gpu-memory-utilization", type=float, default=default_gpu_util, help="设置vLLM可以使用的GPU显存比例 (0.0 到 1.0)")
        
        args = parser.parse_args()

        if not args.model:
            console.print("[bold red]❌ 错误: 配置文件中未定义任何模型。")
            sys.exit(1)

        # 6. 启动流程
        with open(vllm_log_path, 'w', buffering=1, encoding='utf-8') as log_file:
            model_config = config_loader.get_model_config(args.model)
            
            is_local = "localhost" in getattr(model_config, 'api_base', '') or "127.0.0.1" in getattr(model_config, 'api_base', '')

            if not is_local:
                console.print(f"✅ 模型 '{args.model}' 是一个远程API模型，无需启动本地服务器。")
                start_client(args.model, args.role)
                return

            server_process = start_vllm_server(
                model_config.model_name, server_host, server_port, log_file,
                args.max_model_len, args.gpu_memory_utilization
            )

            # 等待服务器准备就绪
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
                try:
                    os.killpg(os.getpgid(server_process.pid), signal.SIGTERM)
                except ProcessLookupError:
                    pass
            else:
                server_process.terminate()
            console.print("✅ 清理完成。")

if __name__ == "__main__":
    main()