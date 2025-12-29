from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Optional


_LOGGER_NAME = "dbl_boundary_service"
_DEFAULT_LOG_DIR = Path("logs")
_LOG_DIR_ENV = "DBL_LOG_DIR"


def get_log_dir() -> Path:
    value = os.getenv(_LOG_DIR_ENV)
    return Path(value) if value else _DEFAULT_LOG_DIR


def setup_logging() -> None:
    log_dir = get_log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app.log"

    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(logging.INFO)

    if any(isinstance(h, RotatingFileHandler) for h in logger.handlers):
        return

    handler = RotatingFileHandler(
        log_file,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    )
    logger.addHandler(handler)


@dataclass(frozen=True)
class RunLogEntry:
    request_id: str
    timestamp: str
    dry_run: bool
    pipeline_mode: str
    dbl_outcome: str
    blocked: bool
    block_reason: Optional[str]
    policy_eval_ms: float
    llm_call_ms: Optional[float]
    prompt_length: int
    model: str
    max_tokens: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "timestamp": self.timestamp,
            "dry_run": self.dry_run,
            "pipeline_mode": self.pipeline_mode,
            "dbl_outcome": self.dbl_outcome,
            "blocked": self.blocked,
            "block_reason": self.block_reason,
            "durations_ms": {
                "policy_eval": self.policy_eval_ms,
                "llm_call": self.llm_call_ms,
            },
            "prompt_length": self.prompt_length,
            "model": self.model,
            "max_tokens": self.max_tokens,
        }


def append_run_log(entry: RunLogEntry) -> None:
    log_dir = get_log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "runs.ndjson"
    line = json.dumps(entry.to_dict(), ensure_ascii=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def _event_payload(event: str, details: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    return {
        "event": event,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "details": details or {},
    }


class EventBus:
    def __init__(self) -> None:
        self._queues: dict[str, asyncio.Queue[Optional[dict[str, Any]]]] = {}
        self._cleanup_tasks: dict[str, asyncio.Task[None]] = {}

    def ensure_queue(self, request_id: str) -> asyncio.Queue[Optional[dict[str, Any]]]:
        if request_id not in self._queues:
            self._queues[request_id] = asyncio.Queue()
        return self._queues[request_id]

    def get_queue(self, request_id: str) -> Optional[asyncio.Queue[Optional[dict[str, Any]]]]:
        return self._queues.get(request_id)

    async def emit(self, request_id: str, event: str, details: Optional[dict[str, Any]] = None) -> None:
        queue = self.ensure_queue(request_id)
        await queue.put(_event_payload(event, details))

    async def finish(self, request_id: str) -> None:
        queue = self.ensure_queue(request_id)
        await queue.put(_event_payload("finished", {}))
        await queue.put(None)
        if request_id not in self._cleanup_tasks:
            self._cleanup_tasks[request_id] = asyncio.create_task(self._delayed_cleanup(request_id))

    def cleanup(self, request_id: str) -> None:
        self._queues.pop(request_id, None)
        task = self._cleanup_tasks.pop(request_id, None)
        if task:
            task.cancel()

    async def _delayed_cleanup(self, request_id: str) -> None:
        try:
            await asyncio.sleep(60)
            self.cleanup(request_id)
        except asyncio.CancelledError:
            return


event_bus = EventBus()
