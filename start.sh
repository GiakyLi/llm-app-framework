python -m vllm.entrypoints.openai.api_server \
    --model "/home/lee/.cache/modelscope/hub/models/Qwen/Qwen3-4B-Instruct-2507" \
    --host "0.0.0.0" \
    --port 8000 \
    --max-model-len 8192 \
    --trust-remote-code