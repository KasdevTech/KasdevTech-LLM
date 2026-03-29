# KasdevTech LLM

Small, deployable LLM gateway for Render.

This project does **not** run a full model on Render's free tier. Instead, it gives you a single API endpoint you can use from anywhere and forwards requests to:

- a remote Ollama server you control, or
- any OpenAI-compatible provider

## Why this approach

Running Ollama directly on Render free tier is usually not practical because model files are large, cold starts are frequent, and free instances have tight resource limits. This gateway keeps the deployment simple and still gives you a stable API surface.

## Features

- OpenAI-style `POST /v1/chat/completions`
- API key protection for your own clients
- Switch upstream with environment variables
- Works on Render free tier

## Local run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export APP_API_KEY=change-me
export UPSTREAM_PROVIDER=ollama
export UPSTREAM_BASE_URL=http://localhost:11434
export DEFAULT_MODEL=llama3.2:3b
export ALLOWED_ORIGINS=*

uvicorn app.main:app --reload
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Chat request:

```bash
curl http://127.0.0.1:8000/v1/chat/completions \
  -H "Authorization: Bearer change-me" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2:3b",
    "messages": [
      { "role": "user", "content": "Write a one-line hello." }
    ]
  }'
```

## Render deploy

1. Push this repository to GitHub.
2. In Render, create a new Blueprint service from the repo.
3. Set the secret env vars:
   - `APP_API_KEY`
   - `UPSTREAM_BASE_URL`
   - `UPSTREAM_API_KEY` if using an OpenAI-compatible provider
   - `ALLOWED_ORIGINS` if you want to restrict browser access
4. Deploy.

## Upstream modes

### 1. Ollama

```env
UPSTREAM_PROVIDER=ollama
UPSTREAM_BASE_URL=https://your-ollama-host.example.com
DEFAULT_MODEL=llama3.2:3b
```

Your remote Ollama server should expose `/api/chat`.

### 2. OpenAI-compatible

```env
UPSTREAM_PROVIDER=openai
UPSTREAM_BASE_URL=https://your-provider.example.com
UPSTREAM_API_KEY=provider-secret
DEFAULT_MODEL=your-model-name
```

Your provider should expose `/v1/chat/completions`.

## Suggested usage

Use this gateway as your personal API endpoint from apps, scripts, websites, or automations. Keep the Render service lightweight and let the actual model run somewhere better suited for inference.
