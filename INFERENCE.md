# Inference

Inference service lives under [inference](inference).

## Model server

- Runtime: vLLM OpenAI-compatible API
- Model: Qwen/Qwen2.5-Coder-1.5B-Instruct (fits a single T4/g4dn-class GPU)
- Context window target: 4K by default (raise if you have more VRAM)
- Tool calling: enabled in startup flags

## Startup

```bash
docker build -t enterprise-vllm ./inference
docker run --gpus all --rm -p 8001:8001 \
  -e HUGGING_FACE_HUB_TOKEN=$HUGGING_FACE_HUB_TOKEN \
  -e MODEL_NAME=Qwen/Qwen2.5-Coder-1.5B-Instruct \
  enterprise-vllm
```

## Health

```bash
curl http://localhost:8001/health
```

## Security

- Keep vLLM bound to localhost/private network only.
- If split across instances, restrict SG ingress to the API instance's security group only.
