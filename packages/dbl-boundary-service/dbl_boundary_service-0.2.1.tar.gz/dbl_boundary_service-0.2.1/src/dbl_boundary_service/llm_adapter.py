from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from .security import ensure_api_key


# ---------------------------------------------------------------------------
# LlmPayload / LlmResult
# Minimal typed structures for the LLM call.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LlmPayload:
    """Input for an LLM call."""
    model: str
    prompt: str
    max_tokens: int = 1024
    temperature: float = 0.7


@dataclass(frozen=True)
class LlmResult:
    """Output from an LLM call."""
    content: str
    model: str
    usage: dict[str, int]
    raw_response: dict[str, Any]


# ---------------------------------------------------------------------------
# OpenAI Chat Completion Adapter
# This is the KL effector function for LLM operations.
# It lives in the boundary service, not in kl-kernel-logic.
# ---------------------------------------------------------------------------

OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"


async def call_openai_chat(payload: LlmPayload) -> LlmResult:
    """
    Calls OpenAI Chat Completion API.
    
    This is a pure effector: no governance, no policy logic.
    The governance decision has already been made by DBL.
    KL traces this operation as a deterministic step.
    """
    api_key = ensure_api_key()
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    body = {
        "model": payload.model,
        "messages": [{"role": "user", "content": payload.prompt}],
        "max_tokens": payload.max_tokens,
        "temperature": payload.temperature,
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(OPENAI_CHAT_URL, headers=headers, json=body)
        response.raise_for_status()
        data = response.json()
    
    content = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    
    return LlmResult(
        content=content,
        model=data.get("model", payload.model),
        usage={
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
        },
        raw_response=data,
    )


# ---------------------------------------------------------------------------
# Dry Run (no actual LLM call)
# For testing the boundary flow without spending tokens.
# ---------------------------------------------------------------------------

async def dry_run_llm(payload: LlmPayload) -> LlmResult:
    """
    Simulates an LLM call without hitting the API.
    Useful for testing the full DBL+KL flow.
    """
    return LlmResult(
        content=f"[DRY RUN] Would have called {payload.model} with prompt: {payload.prompt[:50]}...",
        model=payload.model,
        usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        raw_response={"dry_run": True},
    )

