# **LLM 应用框架 (LLM App Framework)**

这是一个高度模块化、配置驱动的 Python 框架，旨在简化与大语言模型（LLM）的交互，无论是本地部署的模型（如 VLLM）还是云端 API（如 OpenAI, Groq）。它不仅是一个聊天客户端，更是一个坚实且可扩展的基础，让开发者可以轻松集成 RAG、Agents、数据库等高级功能。

## **核心设计理念**

* **配置即代码**: 无需修改核心代码，通过编辑 YAML 文件即可添加新模型、定义系统角色或调整应用参数。  
* **高内聚，低耦合**: 每个模块（客户端、存储、配置、UI）都专注于单一职责，并通过清晰的接口相互协作。  
* **面向接口编程**: 核心逻辑依赖于抽象基类（如 BaseLLMClient），使得添加对新 LLM API（如 Hugging Face, Anthropic）的支持变得简单。  
* **开发者友好**: 提供一键启动脚本、清晰的日志系统和结构化的代码，让二次开发和维护更加高效。

## **核心特性**

* **多模型无缝切换**: 内置对所有兼容 OpenAI API 的接口的支持（VLLM, Groq, ...），并可通过工厂模式轻松扩展。  
* **动态角色系统**: 在配置文件中预定义多种系统指令（System Prompt），并在聊天中通过 /role \<角色名\> 实时切换模型的人设和行为。  
* **自动化对话历史**: 所有交互式对话都会被自动保存到本地，并按日期和时间进行组织，方便回顾和分析。  
* **强大的启动器 (Launcher)**: launch.py 脚本能够一键启动本地 VLLM 服务器和客户端应用，极大简化了本地模型的部署和调试流程。  
* **稳健的错误处理与日志**: 拥有自定义的异常体系和详细的日志记录，关键操作和错误信息都会被清晰地记录下来。  
* **优雅的命令行界面**: 基于 rich 库构建，提供语法高亮、美观的表格和面板，提升了终端使用体验。

## **项目结构**

```
.  
├── configs/                   \# 所有的YAML配置文件  
│   ├── app\_config.yaml       \# 应用级配置 (日志, 路径等)  
│   └── models\_config.yaml    \# 模型和系统指令的配置  
├── data/  
│   └── history/               \# 对话历史存储目录 (自动创建)  
├── logs/                      \# 日志文件目录 (自动创建)  
├── llm\_client/               \# 核心应用代码  
│   ├── clients/               \# LLM API 客户端实现  
│   ├── core/                  \# 核心模块 (配置加载, 内存, 存储等)  
│   ├── ui/                    \# 用户界面实现  
│   └── app.py                 \# 命令行应用主逻辑  
├── .gitignore  
├── launch.py                  \# (推荐) 一键启动VLLM服务器和客户端的脚本  
├── main.py                    \# 仅启动客户端的入口  
├── README.md                  \# 您正在阅读的文件  
└── requirements.txt           \# 项目依赖
```

## **快速开始**

### **1\. 环境准备**

克隆项目并安装所需的依赖包。

```
git clone \<your-repo-url\>  
cd llm-app-framework  
pip install \-r requirements.txt
```

### **2\. 模型配置**

打开 `configs/models\_config.yaml` 文件，根据您的需求进行配置。

#### **使用本地VLLM模型 (推荐):**

 ```
   1. 找到 llama3-8b-vllm 或 qwen3-4b-local 配置项。  
   2. 确保 api\_base 地址与您的 VLLM 服务器地址一致 (默认为 http://localhost:8000/v1)。  
   3. 确保 model\_name 与您 VLLM 服务器启动时加载的模型标识符完全一致。
   ```

#### **使用在线API (如 OpenAI, Groq):**

 ```
   1. 取消注释或仿照示例添加一个新的模型配置。  
   2. 将 api\_key 设置为 ENV:YOUR\_ENV\_VARIABLE\_NAME 的形式。  
   3. 在您的终端中设置相应的环境变量：
   
   # For Linux/macOS  
   export OPENAI\_API\_KEY="your\_openai\_key"  
   export GROQ\_API\_KEY="your\_groq\_key"
   
   # For Windows (Command Prompt)  
   set OPENAI\_API\_KEY="your\_openai\_key"
   ```

### **3\. 运行应用**

我们强烈推荐使用 `launch.py` 脚本来启动应用，它会为您处理所有事情。

#### **启动本地模型:**

该脚本会自动为您启动一个本地 VLLM 服务器，并等待其就绪后启动客户端。

```
# 启动 models\_config.yaml 中配置的第一个本地模型  
python launch.py

# 启动指定的本地模型和角色  
python launch.py \--model llama3-8b-vllm \--role code\_expert
```

您将在 `logs/vllm\_server.log` 中看到 VLLM 服务器的完整日志。

#### **启动在线模型:**

如果指定的模型是一个远程 API，脚本会自动跳过启动本地服务器的步骤。

```
# 假设 gpt-4o 是一个远程模型  
python launch.py \--model gpt-4o
```

### **4\. 交互式命令**

在聊天界面中，输入以下命令以控制应用：

| 命令             | 描述                                              |
| :--------------- | :------------------------------------------------ |
| /help            | 显示所有可用命令和角色列表。                      |
| /exit, /quit     | 退出程序并保存当前对话。                          |
| /clear           | 清空当前对话历史，但保留系统角色。                |
| /save            | 手动将当前对话保存到历史记录中。                  |
| /role \<角色ID\> | 切换系统角色并开始一个新对话。                    |
| /roles           | 列出所有在 models\_config.yaml 中定义的可用角色。 |