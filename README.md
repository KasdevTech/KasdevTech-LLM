# KasdevTech LLM

Deploy a real small LLM on Render using Docker and `llama-cpp-python`.

This repo now runs the model itself. On startup it:

- downloads a GGUF model file from `MODEL_URL`
- unzips it automatically if the file is a `.zip`
- starts an OpenAI-compatible API server

## Important reality check

This can work on Render, but there are two very different outcomes:

- `free test mode`: works with a tiny quantized model, but it will be slow and cold starts will hurt
- `useful mode`: use a paid Render instance and preferably a persistent disk, then run a 0.5B to 1.5B quantized instruct model

If you want something genuinely strong, Render is usually not the best place to host it. But for a small personal API, this setup is workable.

## What endpoint you get

The service exposes an OpenAI-compatible API:

- `GET /docs`
- `POST /v1/chat/completions`

If you set `API_KEY`, call it with:

```bash
-H "Authorization: Bearer YOUR_API_KEY"
```

## Default model

The default is a small GGUF build of Qwen 2.5 0.5B Instruct:

- good for testing
- much lighter than bigger models
- still limited for serious tasks

Default `MODEL_URL`:

```text
https://huggingface.co/bartowski/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/Qwen2.5-0.5B-Instruct-Q4_K_M.gguf
```

## Render deploy

### Option 1: Quick test on free Render

1. Open [Render Dashboard](https://dashboard.render.com/)
2. Click `New` -> `Blueprint`
3. Choose `KasdevTech/KasdevTech-LLM`
4. Render will read [`render.yaml`](/Users/kasisureshdevarajugattu/Coding/AI-Arch/Ollama/render.yaml)
5. Add env vars:
   - `API_KEY` = your secret key
   - `MODEL_URL` = keep default or replace it
   - `HF_TOKEN` = only if the model repo requires authentication
6. Deploy

This is okay for testing only.

### Option 2: Better and more useful

Use a paid Render web service with more RAM and add a persistent disk if available on your plan. Then use a somewhat better model, for example:

- Qwen 2.5 1.5B Instruct GGUF
- SmolLM2 1.7B Instruct GGUF

That will still be CPU inference, but it becomes more usable.

## Use your own zipped model

If you have a hosted zip file that contains a `.gguf` model:

1. Upload the zip somewhere reachable by HTTPS
2. Set:

```env
MODEL_URL=https://your-domain.com/your-model.zip
MODEL_FILE=model.gguf
```

At startup the app downloads the zip, extracts it, finds the `.gguf` file, and serves it.

## Good environment variables

```env
API_KEY=change-me
MODEL_URL=https://huggingface.co/bartowski/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/Qwen2.5-0.5B-Instruct-Q4_K_M.gguf
MODEL_FILE=model.gguf
MODEL_ALIAS=qwen2.5-0.5b
CHAT_FORMAT=chatml
N_CTX=4096
N_THREADS=4
N_BATCH=256
```

## Example request

```bash
curl https://your-service.onrender.com/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5-0.5b",
    "messages": [
      { "role": "system", "content": "You are helpful." },
      { "role": "user", "content": "Write a short intro about AI." }
    ]
  }'
```

## Recommended upgrades

If you want this to feel more useful next, the best improvements are:

1. Add a persistent disk so the model is not re-downloaded each deploy
2. Switch to a larger quantized instruct model
3. Add a small frontend playground
4. Add streaming responses
