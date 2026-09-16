FROM vllm/vllm-openai:v0.8.4

ENV MODEL_NAME=Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8 \
    MAX_MODEL_LEN=32768 \
    GPU_MEMORY_UTILIZATION=0.90

COPY start-vllm.sh /app/start-vllm.sh
COPY config/vllm.env /app/config/vllm.env
COPY healthcheck.sh /app/healthcheck.sh

RUN chmod +x /app/start-vllm.sh
RUN chmod +x /app/healthcheck.sh

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 CMD /app/healthcheck.sh

CMD ["/app/start-vllm.sh"]
