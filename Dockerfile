FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

RUN pip install "llama-cpp-python[server]==0.3.9"

WORKDIR /app

COPY scripts/start.sh /app/scripts/start.sh
RUN chmod +x /app/scripts/start.sh

ENV MODEL_DIR=/opt/render/project/.render-models \
    MODEL_ALIAS=local-model \
    MODEL_FILE=model.gguf \
    MODEL_URL=https://huggingface.co/bartowski/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/Qwen2.5-0.5B-Instruct-Q4_K_M.gguf \
    HOST=0.0.0.0 \
    PORT=8000 \
    N_CTX=4096 \
    N_THREADS=4 \
    N_BATCH=256 \
    CHAT_FORMAT=chatml

CMD ["/app/scripts/start.sh"]
