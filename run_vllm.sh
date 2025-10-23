#!/bin/bash

# =========================================================
# vLLM服务启动脚本 (使用 vllm serve 命令)
# =========================================================

# 配置参数
MODEL_PATH="/models/Qwen3-4B-Instruct-2507" # 使用修改后的容器内部路径
MAX_MODEL_LEN=12800
PORT=4567
LOG_FILE="/app/vllm_service.log"
CHECK_INTERVAL=5
MAX_WAIT_TIME=180

# 显式激活 Conda 环境
source /opt/conda/etc/profile.d/conda.sh
conda activate vllm

# 0. 检查并终止现有vLLM服务
if pgrep -f "vllm serve" > /dev/null; then
    echo "发现现有vLLM服务,正在终止..."
    pkill -f "vllm serve"
    sleep 5
    echo "现有服务已终止。"
fi

# 1. 启动服务并重定向日志
echo "Starting vLLM service..."
# 使用 vllm serve 命令，并传入模型路径
nohup vllm serve "${MODEL_PATH}" \
    --served-model-name "Qwen3-4B-Instruct-2507" \
    --host 0.0.0.0 \
    --port "${PORT}" \
    --tensor-parallel-size 1 \
    --max-model-len "${MAX_MODEL_LEN}" \
    --gpu-memory-utilization 0.25 \
    > "$LOG_FILE" 2>&1 &

# 2. 检查服务是否成功启动
start_time=$(date +%s)
while true; do
    # 检查日志文件是否包含"Application startup complete."这样的成功信息
    if grep -q "Application startup complete." "$LOG_FILE"; then
        echo "vLLM service started successfully!"
        echo "You can check logs with: docker logs vllm-container"
        break
    fi

    # 检查是否超时
    current_time=$(date +%s)
    if (( current_time - start_time > MAX_WAIT_TIME )); then
        echo "Error: Service failed to start within the time limit." >&2
        cat "$LOG_FILE"
        exit 1
    fi

    echo "Waiting for service to start... (waited $(( current_time - start_time ))s)"
    sleep "$CHECK_INTERVAL"
done

# 3. 让脚本继续在后台运行，确保容器不退出
tail -f "$LOG_FILE"