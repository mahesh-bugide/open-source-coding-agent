#!/usr/bin/env bash
set -euo pipefail

if [[ -f /app/config/vllm.env ]]; then
  source /app/config/vllm.env
fi

MODEL_NAME=${MODEL_NAME:-Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8}
MAX_MODEL_LEN=${MAX_MODEL_LEN:-32768}
GPU_MEMORY_UTILIZATION=${GPU_MEMORY_UTILIZATION:-0.90}
PORT=${PORT:-8001}
HOST=${HOST:-0.0.0.0}

python -m vllm.entrypoints.openai.api_server \
  --host "$HOST" \
  --port "$PORT" \
  --model "$MODEL_NAME" \
  --max-model-len "$MAX_MODEL_LEN" \
  --gpu-memory-utilization "$GPU_MEMORY_UTILIZATION" \
  --enable-auto-tool-choice \
  --tool-call-parser hermes
