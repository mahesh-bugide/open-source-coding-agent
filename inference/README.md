# Inference Service (vLLM)

This directory contains the vLLM model server for:

- Model: `Qwen/Qwen2.5-Coder-1.5B-Instruct` (fits a single T4/g4dn-class GPU; swap `MODEL_NAME` for a larger model if you have more VRAM)
- API: OpenAI-compatible (`/v1/chat/completions`)
- Target context: 4K (raise `MAX_MODEL_LEN` if your GPU has more VRAM)
- Target GPU: any CUDA GPU with >=16GB VRAM (e.g. NVIDIA T4 / g4dn instance family)

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
  -e MODEL_NAME=Qwen/Qwen2.5-Coder-1.5B-Instruct \
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
  -d '{"model":"Qwen/Qwen2.5-Coder-1.5B-Instruct","messages":[{"role":"user","content":"hello"}]}'
```
