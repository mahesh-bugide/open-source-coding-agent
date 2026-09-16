#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_FILE="${SCRIPT_DIR}/user-data/bootstrap_gpu_agent.tpl.sh"
ENV_FILE="${1:-${SCRIPT_DIR}/one_click.env}"
OUTPUT_FILE="${2:-${SCRIPT_DIR}/user-data/bootstrap_gpu_agent.sh}"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Missing env file: ${ENV_FILE}" >&2
  echo "Copy ${SCRIPT_DIR}/one_click.env.example to ${SCRIPT_DIR}/one_click.env and edit values." >&2
  exit 1
fi

# shellcheck disable=SC1090
source "${ENV_FILE}"

required_vars=(
  AWS_REGION
  AWS_ACCOUNT_ID
  API_REPO
  VLLM_REPO
  IMAGE_TAG
  MODEL_NAME
  API_KEY
  WORKSPACE_PATH
  API_PORT
  VLLM_PORT
)

for var_name in "${required_vars[@]}"; do
  if [[ -z "${!var_name:-}" ]]; then
    echo "Missing required variable in env file: ${var_name}" >&2
    exit 1
  fi
done

if [[ "${AWS_ACCOUNT_ID}" == "REPLACE_ME" || ! "${AWS_ACCOUNT_ID}" =~ ^[0-9]{12}$ ]]; then
  echo "AWS_ACCOUNT_ID must be set to a 12-digit account id in ${ENV_FILE}." >&2
  exit 1
fi

escape_sed() {
  printf '%s' "$1" | sed -e 's/[\/&|]/\\&/g'
}

mkdir -p "$(dirname "${OUTPUT_FILE}")"
cp "${TEMPLATE_FILE}" "${OUTPUT_FILE}"

sed -i "s|__AWS_REGION__|$(escape_sed "${AWS_REGION}")|g" "${OUTPUT_FILE}"
sed -i "s|__AWS_ACCOUNT_ID__|$(escape_sed "${AWS_ACCOUNT_ID}")|g" "${OUTPUT_FILE}"
sed -i "s|__API_REPO__|$(escape_sed "${API_REPO}")|g" "${OUTPUT_FILE}"
sed -i "s|__VLLM_REPO__|$(escape_sed "${VLLM_REPO}")|g" "${OUTPUT_FILE}"
sed -i "s|__IMAGE_TAG__|$(escape_sed "${IMAGE_TAG}")|g" "${OUTPUT_FILE}"
sed -i "s|__MODEL_NAME__|$(escape_sed "${MODEL_NAME}")|g" "${OUTPUT_FILE}"
sed -i "s|__API_KEY__|$(escape_sed "${API_KEY}")|g" "${OUTPUT_FILE}"
sed -i "s|__HF_TOKEN__|$(escape_sed "${HF_TOKEN:-}")|g" "${OUTPUT_FILE}"
sed -i "s|__WORKSPACE_PATH__|$(escape_sed "${WORKSPACE_PATH}")|g" "${OUTPUT_FILE}"
sed -i "s|__GIT_REPO_URL__|$(escape_sed "${GIT_REPO_URL:-}")|g" "${OUTPUT_FILE}"
sed -i "s|__API_PORT__|$(escape_sed "${API_PORT}")|g" "${OUTPUT_FILE}"
sed -i "s|__VLLM_PORT__|$(escape_sed "${VLLM_PORT}")|g" "${OUTPUT_FILE}"

chmod +x "${OUTPUT_FILE}"

echo "Rendered user-data script: ${OUTPUT_FILE}"
