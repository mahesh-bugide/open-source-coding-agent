# Inference

Inference service lives under [inference](inference).

## Model server

- Runtime: vLLM OpenAI-compatible API
- Model: Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8
- Context window target: 32K
- Tool calling: enabled in startup flags

## Startup

```bash
docker build -t enterprise-vllm ./inference
docker run --gpus all --rm -p 8001:8001 \
  -e HUGGING_FACE_HUB_TOKEN=$HUGGING_FACE_HUB_TOKEN \
  enterprise-vllm
```

## Health

```bash
curl http://localhost:8001/health
```

## Security

- Keep vLLM on private network in AWS.
- Restrict SG ingress to agent service only.
