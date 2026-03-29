import os
from typing import Any

import httpx
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


app = FastAPI(title="KasdevTech LLM Gateway", version="0.1.0")


def get_allowed_origins() -> list[str]:
    raw = os.getenv("ALLOWED_ORIGINS", "*")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None or value == "":
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def normalize_auth_header(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1]:
        raise HTTPException(status_code=401, detail="Invalid Authorization header")
    return parts[1]


class ChatMessage(BaseModel):
    role: str
    content: Any


class ChatCompletionsRequest(BaseModel):
    model: str | None = None
    messages: list[ChatMessage]
    temperature: float | None = None
    stream: bool = False
    max_tokens: int | None = Field(default=None, alias="max_tokens")

    model_config = {"populate_by_name": True, "extra": "allow"}


@app.get("/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "name": "KasdevTech LLM Gateway",
        "docs": "/docs",
        "health": "/health",
        "chat_completions": "/v1/chat/completions",
    }


@app.post("/v1/chat/completions")
async def chat_completions(
    payload: ChatCompletionsRequest,
    authorization: str | None = Header(default=None),
) -> JSONResponse:
    expected_api_key = get_env("APP_API_KEY")
    provided_api_key = normalize_auth_header(authorization)
    if provided_api_key != expected_api_key:
        raise HTTPException(status_code=403, detail="Invalid API key")

    provider = os.getenv("UPSTREAM_PROVIDER", "ollama").lower()
    if provider == "ollama":
        response = await forward_to_ollama(payload)
    elif provider == "openai":
        response = await forward_to_openai_compatible(payload)
    else:
        raise HTTPException(
            status_code=500,
            detail="Unsupported UPSTREAM_PROVIDER. Use 'ollama' or 'openai'.",
        )

    return JSONResponse(content=response)


async def forward_to_ollama(payload: ChatCompletionsRequest) -> dict[str, Any]:
    base_url = get_env("UPSTREAM_BASE_URL")
    model = payload.model or get_env("DEFAULT_MODEL")

    request_body = {
        "model": model,
        "messages": [message.model_dump() for message in payload.messages],
        "stream": False,
    }
    if payload.temperature is not None:
        request_body["options"] = {"temperature": payload.temperature}
    if payload.max_tokens is not None:
        request_body.setdefault("options", {})["num_predict"] = payload.max_tokens

    async with httpx.AsyncClient(timeout=120.0) as client:
        upstream = await client.post(f"{base_url.rstrip('/')}/api/chat", json=request_body)

    if upstream.status_code >= 400:
        raise HTTPException(status_code=upstream.status_code, detail=upstream.text)

    data = upstream.json()
    message = data.get("message", {})
    return {
        "id": data.get("id", "chatcmpl-ollama"),
        "object": "chat.completion",
        "created": data.get("created_at", 0),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": message.get("role", "assistant"),
                    "content": message.get("content", ""),
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": data.get("prompt_eval_count", 0),
            "completion_tokens": data.get("eval_count", 0),
            "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
        },
    }


async def forward_to_openai_compatible(payload: ChatCompletionsRequest) -> dict[str, Any]:
    base_url = get_env("UPSTREAM_BASE_URL")
    model = payload.model or get_env("DEFAULT_MODEL")

    headers = {"Content-Type": "application/json"}
    upstream_api_key = os.getenv("UPSTREAM_API_KEY")
    if upstream_api_key:
        headers["Authorization"] = f"Bearer {upstream_api_key}"

    request_body = payload.model_dump(by_alias=True, exclude_none=True)
    request_body["model"] = model
    request_body["stream"] = False

    async with httpx.AsyncClient(timeout=120.0) as client:
        upstream = await client.post(
            f"{base_url.rstrip('/')}/v1/chat/completions",
            headers=headers,
            json=request_body,
        )

    if upstream.status_code >= 400:
        raise HTTPException(status_code=upstream.status_code, detail=upstream.text)

    return upstream.json()
