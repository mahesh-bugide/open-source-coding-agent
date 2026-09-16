# AWS Single-Instance Minimal Deployment

Fastest path to a working deployment: one EC2 instance, no ECR, no CodeBuild, no Terraform, no multi-instance networking.

## 1. Launch one instance

- AMI: `Deep Learning Base AMI with Single CUDA (Ubuntu 24.04)` (GPU driver + CUDA + Docker + NVIDIA Container Toolkit preinstalled).
- Instance type: `g4dn.xlarge` or `g4dn.2xlarge` (whatever has capacity). A non-GPU type (e.g. `t3.large`) also works if you only need mock-model validation first.
- IAM role: `AmazonSSMManagedInstanceCore` only.
- Security group: no public inbound rules needed; use Session Manager.

## 2. Connect and bootstrap

Connect via Session Manager, then:

```bash
export GIT_REPO_URL="https://github.com/your-org/your-repo"
curl -fsSL https://raw.githubusercontent.com/your-org/your-repo/main/scripts/aws/bootstrap_single_instance.sh | bash
```

Or, if the repo is already cloned on the instance:

```bash
cd ~/coding-agent
bash scripts/aws/bootstrap_single_instance.sh
```

This builds and starts `mock-model` + `api` only, and confirms `/health` and `/ready` respond — no GPU required for this step.

## 3. Switch to the real model (GPU instance only)

```bash
nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.3.2-base-ubuntu22.04 nvidia-smi

docker compose -f docker-compose.yml -f docker-compose.gpu.yml --profile gpu up -d --build vllm api
curl -sS http://127.0.0.1:8080/health
```

## 4. Run one end-to-end task

```bash
API_KEY=dev-local-key
WS=/home/ubuntu/coding-agent/examples/sample-repository

SESSION_ID=$(curl -sS -H "x-api-key: $API_KEY" -H "Content-Type: application/json" \
  -d "{\"workspace_path\":\"$WS\"}" http://127.0.0.1:8080/v1/sessions | jq -r .session_id)

curl -sS -H "x-api-key: $API_KEY" -H "Content-Type: application/json" \
  -d '{"message":"Read TASKS.md and suggest one safe small fix, then run tests."}' \
  http://127.0.0.1:8080/v1/sessions/$SESSION_ID/messages | jq
```

## Only add later, if actually needed

- **ECR + CI build pipeline** — once you need repeatable rebuilds without re-cloning on the box each time.
- **Second instance for API** — once GPU cost or scaling requires separating API from the model.
- **Load balancer / Terraform** — once you have more than one instance to manage consistently.
