#!/bin/bash
set -euo pipefail

exec > >(tee -a /var/log/user-data-agent.log) 2>&1

echo "[user-data] Starting bootstrap at $(date -Is)"

AWS_REGION="__AWS_REGION__"
AWS_ACCOUNT_ID="__AWS_ACCOUNT_ID__"
API_REPO="__API_REPO__"
VLLM_REPO="__VLLM_REPO__"
IMAGE_TAG="__IMAGE_TAG__"
MODEL_NAME="__MODEL_NAME__"
API_KEY="__API_KEY__"
HF_TOKEN="__HF_TOKEN__"
WORKSPACE_PATH="__WORKSPACE_PATH__"
GIT_REPO_URL="__GIT_REPO_URL__"
API_PORT="__API_PORT__"
VLLM_PORT="__VLLM_PORT__"

ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

apt-get update
apt-get install -y docker.io git curl jq awscli
systemctl enable --now docker

if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo "[user-data] ERROR: nvidia-smi not found. Use a GPU-ready AMI or preinstall NVIDIA driver." >&2
  exit 1
fi

if ! nvidia-smi >/dev/null 2>&1; then
  echo "[user-data] ERROR: nvidia-smi failed. Driver not ready." >&2
  exit 1
fi

if ! command -v nvidia-ctk >/dev/null 2>&1; then
  rm -f /etc/apt/sources.list.d/nvidia-container-toolkit.list
  curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
  curl -fsSL https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
    > /etc/apt/sources.list.d/nvidia-container-toolkit.list
  apt-get update
  apt-get install -y nvidia-container-toolkit
fi

nvidia-ctk runtime configure --runtime=docker || true
systemctl restart docker

aws ecr get-login-password --region "${AWS_REGION}" | \
  docker login --username AWS --password-stdin "${ECR_REGISTRY}"

mkdir -p "${WORKSPACE_PATH}" "${WORKSPACE_PATH}/.runtime"

if [[ -n "${GIT_REPO_URL}" && ! -d "${WORKSPACE_PATH}/.git" ]]; then
  git clone "${GIT_REPO_URL}" "${WORKSPACE_PATH}"
fi

docker network create agent-net || true
docker rm -f vllm enterprise-api || true

docker pull "${ECR_REGISTRY}/${VLLM_REPO}:${IMAGE_TAG}"
docker pull "${ECR_REGISTRY}/${API_REPO}:${IMAGE_TAG}"

docker run -d \
  --name vllm \
  --network agent-net \
  --gpus all \
  --ipc=host \
  --restart unless-stopped \
  -p "127.0.0.1:${VLLM_PORT}:8001" \
  -e MODEL_NAME="${MODEL_NAME}" \
  -e MAX_MODEL_LEN=2048 \
  -e GPU_MEMORY_UTILIZATION=0.80 \
  -e HUGGING_FACE_HUB_TOKEN="${HF_TOKEN}" \
  "${ECR_REGISTRY}/${VLLM_REPO}:${IMAGE_TAG}"

for i in $(seq 1 120); do
  if curl -sf "http://127.0.0.1:${VLLM_PORT}/health" >/dev/null; then
    break
  fi
  sleep 5
done

if ! curl -sf "http://127.0.0.1:${VLLM_PORT}/health" >/dev/null; then
  echo "[user-data] ERROR: vLLM did not become healthy in time" >&2
  docker logs --tail 200 vllm || true
  exit 1
fi

docker run -d \
  --name enterprise-api \
  --network agent-net \
  --restart unless-stopped \
  -p "${API_PORT}:8080" \
  -v "${WORKSPACE_PATH}:/workspace/coding-agent" \
  -e DEV_API_KEY="${API_KEY}" \
  -e REQUIRE_API_KEY=true \
  -e MODEL_MODE=openai \
  -e MODEL_BASE_URL="http://vllm:8001/v1" \
  -e MODEL_NAME="${MODEL_NAME}" \
  -e MODEL_API_KEY= \
  -e POSTGRES_DSN="sqlite+aiosqlite:////workspace/coding-agent/.runtime/agent.db" \
  -e REDIS_URL="redis://127.0.0.1:6399/0" \
  -e ALLOWED_WORKSPACE_ROOT="/workspace/coding-agent" \
  "${ECR_REGISTRY}/${API_REPO}:${IMAGE_TAG}"

echo "[user-data] Bootstrap complete at $(date -Is)"
echo "[user-data] API health:"
curl -sS "http://127.0.0.1:${API_PORT}/health" || true
