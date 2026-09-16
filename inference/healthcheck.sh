#!/usr/bin/env bash
set -euo pipefail

curl -sf http://localhost:8001/health >/dev/null
if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader >/dev/null
fi
