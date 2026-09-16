#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"

if [[ -f "${SCRIPT_DIR}/one_click.env" ]]; then
  # shellcheck disable=SC1091
  source "${SCRIPT_DIR}/one_click.env"
fi

AWS_REGION="${AWS_REGION:-eu-west-1}"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:-$(aws sts get-caller-identity --query Account --output text)}"
API_REPO="${API_REPO:-enterprise-api}"
VLLM_REPO="${VLLM_REPO:-enterprise-vllm}"
IMAGE_TAG="${IMAGE_TAG:-v1}"

if [[ "${AWS_ACCOUNT_ID}" == "REPLACE_ME" ]]; then
  AWS_ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
fi

if [[ ! "${AWS_ACCOUNT_ID}" =~ ^[0-9]{12}$ ]]; then
  echo "AWS_ACCOUNT_ID must be a 12-digit account id. Current value: ${AWS_ACCOUNT_ID}" >&2
  exit 1
fi

for cmd in aws docker; do
  if ! command -v "${cmd}" >/dev/null 2>&1; then
    echo "Missing required command: ${cmd}" >&2
    exit 1
  fi
done

ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

cd "${REPO_ROOT}"

echo "Ensuring ECR repositories exist..."
aws ecr describe-repositories --region "${AWS_REGION}" --repository-names "${API_REPO}" >/dev/null 2>&1 || \
  aws ecr create-repository --region "${AWS_REGION}" --repository-name "${API_REPO}" >/dev/null

aws ecr describe-repositories --region "${AWS_REGION}" --repository-names "${VLLM_REPO}" >/dev/null 2>&1 || \
  aws ecr create-repository --region "${AWS_REGION}" --repository-name "${VLLM_REPO}" >/dev/null

echo "Logging into ECR ${ECR_REGISTRY}..."
aws ecr get-login-password --region "${AWS_REGION}" | \
  docker login --username AWS --password-stdin "${ECR_REGISTRY}"

echo "Building API image..."
docker build -t "${API_REPO}:${IMAGE_TAG}" "${REPO_ROOT}/services/api"
docker tag "${API_REPO}:${IMAGE_TAG}" "${ECR_REGISTRY}/${API_REPO}:${IMAGE_TAG}"
docker push "${ECR_REGISTRY}/${API_REPO}:${IMAGE_TAG}"

echo "Building vLLM image..."
docker build -t "${VLLM_REPO}:${IMAGE_TAG}" "${REPO_ROOT}/inference"
docker tag "${VLLM_REPO}:${IMAGE_TAG}" "${ECR_REGISTRY}/${VLLM_REPO}:${IMAGE_TAG}"
docker push "${ECR_REGISTRY}/${VLLM_REPO}:${IMAGE_TAG}"

echo "Done. Pushed images:"
echo "  ${ECR_REGISTRY}/${API_REPO}:${IMAGE_TAG}"
echo "  ${ECR_REGISTRY}/${VLLM_REPO}:${IMAGE_TAG}"
