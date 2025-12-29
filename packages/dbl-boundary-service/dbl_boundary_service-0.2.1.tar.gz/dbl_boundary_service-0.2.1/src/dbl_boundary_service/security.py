from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ApiKeyStore:
    """
    Simple in-memory storage for an API key.
    Deterministic, explicit, no side effects.
    In a real deployment, this would be a secure vault binding.
    """
    _api_key: Optional[str] = None

    def set(self, key: str) -> None:
        if not key or not key.strip():
            raise ValueError("API key cannot be empty")
        self._api_key = key.strip()

    def get(self) -> str:
        if self._api_key is None:
            raise RuntimeError("API key not set")
        return self._api_key

    def is_set(self) -> bool:
        return self._api_key is not None


# Singleton-like instance
api_key_store = ApiKeyStore()


# ---------------------------------------------------------------------
# Guard function: every LLM call must verify the API key existence.
# ---------------------------------------------------------------------

def ensure_api_key() -> str:
    """
    Deterministic guard: ensures the boundary has a usable key.
    No business logic, only structural validation.
    """
    if not api_key_store.is_set():
        raise RuntimeError("API key missing. Set it via /set-key first.")
    return api_key_store.get()
