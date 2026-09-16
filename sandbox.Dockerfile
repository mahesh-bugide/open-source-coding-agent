FROM python:3.11-slim

WORKDIR /workspace

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ripgrep \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

CMD ["sh", "-lc", "sleep infinity"]
