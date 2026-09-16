#!/usr/bin/env bash
set -euo pipefail

if [[ -f /app/config/vllm.env ]]; then
  source /app/config/vllm.env
fi

MODEL_NAME=${MODEL_NAME:-Qwen/Qwen2.5-Coder-7B-Instruct-AWQ}
MAX_MODEL_LEN=${MAX_MODEL_LEN:-8192}
GPU_MEMORY_UTILIZATION=${GPU_MEMORY_UTILIZATION:-0.85}
QUANTIZATION=${QUANTIZATION:-}
PORT=${PORT:-8001}
HOST=${HOST:-0.0.0.0}

QUANTIZATION_FLAG=()
if [[ -n "$QUANTIZATION" ]]; then
  QUANTIZATION_FLAG=(--quantization "$QUANTIZATION")
fi

python -m vllm.entrypoints.openai.api_server \
  --host "$HOST" \
  --port "$PORT" \
  --model "$MODEL_NAME" \
  --max-model-len "$MAX_MODEL_LEN" \
  --gpu-memory-utilization "$GPU_MEMORY_UTILIZATION" \
  "${QUANTIZATION_FLAG[@]}" \
  --enable-auto-tool-choice \
  --tool-call-parser hermes
