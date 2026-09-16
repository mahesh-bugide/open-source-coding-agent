#!/usr/bin/env bash
# Minimal single-instance bootstrap: clone repo, validate with mock model, then switch to real GPU model.
# Run this directly on an EC2 instance (AWS Deep Learning Base AMI recommended for GPU-ready hosts).
set -euo pipefail

REPO_DIR="${REPO_DIR:-$HOME/coding-agent}"
GIT_REPO_URL="${GIT_REPO_URL:-}"

if ! command -v docker >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y docker.io git
  sudo systemctl enable --now docker
  sudo usermod -aG docker "$USER"
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "docker compose plugin not found. Install Docker Compose v2 and re-run." >&2
  exit 1
fi

if [[ -n "${GIT_REPO_URL}" && ! -d "${REPO_DIR}/.git" ]]; then
  git clone "${GIT_REPO_URL}" "${REPO_DIR}"
fi

cd "${REPO_DIR}"

echo "Step 1: validating with mock model (no GPU required)..."
docker compose up -d --build mock-model api
sleep 3
curl -sS http://127.0.0.1:8080/health
curl -sS http://127.0.0.1:8080/ready

echo
echo "Mock validation done. To switch to the real GPU model, run:"
echo "  docker compose -f docker-compose.yml -f docker-compose.gpu.yml --profile gpu up -d --build vllm api"
