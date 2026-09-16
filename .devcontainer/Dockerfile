FROM mcr.microsoft.com/devcontainers/base:ubuntu

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    nodejs \
    npm \
    git \
    ripgrep \
    docker.io \
    && rm -rf /var/lib/apt/lists/*
