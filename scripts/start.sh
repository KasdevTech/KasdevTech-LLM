#!/usr/bin/env bash
set -euo pipefail

mkdir -p "${MODEL_DIR}"

DOWNLOAD_PATH="${MODEL_DIR}/download.bin"
ARCHIVE_PATH="${MODEL_DIR}/model.zip"
MODEL_PATH="${MODEL_DIR}/${MODEL_FILE}"

download_model() {
  if [[ -z "${MODEL_URL:-}" ]]; then
    echo "MODEL_URL is required"
    exit 1
  fi

  echo "Downloading model from ${MODEL_URL}"

  if [[ -n "${HF_TOKEN:-}" ]]; then
    curl -L --fail \
      -H "Authorization: Bearer ${HF_TOKEN}" \
      -o "${DOWNLOAD_PATH}" \
      "${MODEL_URL}"
  else
    curl -L --fail -o "${DOWNLOAD_PATH}" "${MODEL_URL}"
  fi

  case "${MODEL_URL}" in
    *.zip)
      mv "${DOWNLOAD_PATH}" "${ARCHIVE_PATH}"
      unzip -o "${ARCHIVE_PATH}" -d "${MODEL_DIR}"
      ;;
    *)
      mv "${DOWNLOAD_PATH}" "${MODEL_PATH}"
      ;;
  esac
}

if [[ ! -f "${MODEL_PATH}" ]]; then
  download_model
fi

if [[ ! -f "${MODEL_PATH}" ]]; then
  FOUND_GGUF="$(find "${MODEL_DIR}" -maxdepth 2 -type f -name '*.gguf' | head -n 1 || true)"
  if [[ -n "${FOUND_GGUF}" ]]; then
    MODEL_PATH="${FOUND_GGUF}"
  else
    echo "No GGUF model file found in ${MODEL_DIR}"
    exit 1
  fi
fi

echo "Starting model server with ${MODEL_PATH}"

ARGS=(
  -m llama_cpp.server
  --host "${HOST}"
  --port "${PORT}"
  --model "${MODEL_PATH}"
  --model-alias "${MODEL_ALIAS}"
  --chat_format "${CHAT_FORMAT}"
  --n_ctx "${N_CTX}"
  --n_threads "${N_THREADS}"
  --n_batch "${N_BATCH}"
)

if [[ -n "${API_KEY:-}" ]]; then
  ARGS+=(--api_key "${API_KEY}")
fi

exec python "${ARGS[@]}"
