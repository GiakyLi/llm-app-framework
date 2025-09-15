# 可扩展的大模型应用框架

这是一个高度模块化、配置驱动的Python框架，用于与本地（如VLLM部署）和云端（如OpenAI, Groq）的大语言模型进行交互。它不仅仅是一个客户端，更是一个坚实的基础，可以方便地扩展以支持RAG、Agents、数据库集成等高级功能。

## 核心特性

-   **配置即代码**:
    -   通过编辑 `configs/models_config.yaml` 即可轻松添加、删除或修改模型（本地/云端）。
    -   所有API密钥、模型参数、系统指令均在外部配置，无需修改代码。
-   **多模型支持**:
    -   内置支持所有兼容OpenAI API的接口（VLLM, OpenAI, Groq, ...）。
    -   架构上可轻松扩展以支持其他类型的模型（如直接加载Hugging Face模型）。
-   **对话历史存储**:
    -   所有交互式对话都会被自动保存到 `data/history/` 目录下。
    -   文件按 `年-月-日/时-分-秒.json` 的格式组织，方便追溯。
-   **强大的指令系统**:
    -   在 `models_config.yaml` 中预定义多种系统指令（System Prompt）。
    -   在聊天中通过 `/instruction <指令名>` 实时切换模型角色。
-   **健壮性**:
    -   完善的日志系统，同时输出到控制台和 `logs/app.log` 文件。
    -   自定义异常体系，错误信息清晰明了。
-   **高度可扩展**:
    -   清晰的模块划分（客户端、存储、配置），并预留了 `integrations` 目录。
    -   使用抽象基类定义核心接口，方便未来添加新的客户端、存储方式或RAG流程。

## 安装与设置

1.  **克隆项目**:
    ```bash
    git clone <your-repo-url>
    cd llm-app-framework
    ```

2.  **安装依赖**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **配置API密钥 (可选)**:
    -   对于需要API密钥的在线模型（如OpenAI, Groq），建议使用环境变量。打开 `configs/models_config.yaml`，可以看到 `api_key` 字段设置为 `ENV:YOUR_ENV_VARIABLE_NAME`。
    -   设置环境变量:
        ```bash
        # For Linux/macOS
        export OPENAI_API_KEY="your_openai_key"
        export GROQ_API_KEY="your_groq_key"

        # For Windows (Command Prompt)
        set OPENAI_API_KEY="your_openai_key"
        ```

4.  **配置模型**:
    -   打开 `configs/models_config.yaml`。
    -   **对于本地VLLM**: 修改 `llama3-8b-vllm` 条目，确保 `api_base` 地址正确，`model_name` 与你VLLM服务器启动时使用的 `--model` 参数完全一致。
    -   **对于在线API**: 检查模型名称是否正确。
    -   你可以根据需要添加或删除任何模型配置。

5.  **启动本地VLLM服务器 (如果需要)**:
    在一个**单独的终端**中，启动你的VLLM服务：
    ```bash
    python -m vllm.entrypoints.openai.api_server --model meta-llama/Meta-Llama-3-8B-Instruct
    ```

## 如何运行

直接运行 `main.py` 即可启动交互式聊天。

```bash
python main.py [OPTIONS]
```

**可选参数**:
-   `-m, --model <模型ID>`: 选择一个在 `models_config.yaml` 中定义的模型启动。默认为配置文件中的第一个模型。
    ```bash
    # 启动时使用 gpt-4o 模型
    python main.py --model gpt-4o
    ```
-   `-i, --instruction <指令ID>`: 选择一个初始指令。默认为 `default`。
    ```bash
    # 以代码专家模式启动
    python main.py --model llama3-8b-vllm --instruction code_expert
    ```

### 交互式命令

在聊天界面中，你可以使用以下命令：

-   `/help`: 显示所有可用命令。
-   `/exit` 或 `/quit`: 退出程序并保存对话。
-   `/clear`: 清空当前对话，但保留系统指令。
-   `/instruction <指令ID>`: 实时切换系统指令。
-   `/save`: 手动保存当前对话历史。