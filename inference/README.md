# Inference Service (vLLM)

This directory contains the vLLM model server for:

- Model: `Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8`
- API: OpenAI-compatible (`/v1/chat/completions`)
- Target context: 32K
- Target GPU: NVIDIA L40S (MVP g6e.2xlarge)

## Security

- Do not expose this service publicly.
- Deploy in private subnets only.
- Restrict inbound to agent service security group.

## Requirements

- NVIDIA GPU with sufficient VRAM (L40S recommended)
- Docker with NVIDIA runtime
- Hugging Face token if model download requires authentication

## Run

```bash
docker build -t enterprise-vllm ./inference
docker run --gpus all --rm -p 8001:8001 \
  -e HUGGING_FACE_HUB_TOKEN=$HUGGING_FACE_HUB_TOKEN \
  -e MODEL_NAME=Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8 \
  enterprise-vllm
```

## Health check

```bash
curl http://localhost:8001/health
```

## API test

```bash
curl http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8","messages":[{"role":"user","content":"hello"}]}'
```
