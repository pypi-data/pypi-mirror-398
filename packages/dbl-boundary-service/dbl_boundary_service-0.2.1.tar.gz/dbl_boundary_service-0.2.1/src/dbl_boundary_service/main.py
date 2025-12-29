from __future__ import annotations

import json
import logging
import webbrowser
from contextlib import asynccontextmanager
from typing import Any, Optional
from uuid import uuid4

import uvicorn
from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel

from .config import get_dev_config, BoundaryConfig
from .security import api_key_store
from .web.ui import render_index
from .boundary_flow import BoundaryRequest, run_boundary_flow
from .pipeline_factory import PIPELINE_MODES, KNOWN_POLICY_NAMES
from .telemetry import event_bus, setup_logging, RunLogEntry, append_run_log

logger = logging.getLogger("dbl_boundary_service")

# Global config, loaded on startup
_config: Optional[BoundaryConfig] = None


class RunRequest(BaseModel):
    """Request body for /run endpoint."""
    prompt: str
    tenant_id: Optional[str] = None
    channel: Optional[str] = None
    max_tokens: int = 1024
    temperature: float = 0.7
    dry_run: bool = False
    pipeline_mode: str = "basic_safety"  # minimal, basic_safety, standard, enterprise
    enabled_policies: Optional[list[str]] = None  # Explicit policy override


def _admission_check(request: RunRequest) -> tuple[bool, str, str]:
    if not request.prompt.strip():
        return False, "admission.invalid_prompt", "prompt must be non-empty"
    if request.max_tokens < 1 or request.max_tokens > 8192:
        return False, "admission.invalid_max_tokens", "max_tokens must be between 1 and 8192"
    if request.temperature < 0.0 or request.temperature > 2.0:
        return False, "admission.invalid_temperature", "temperature must be between 0.0 and 2.0"
    if request.pipeline_mode not in PIPELINE_MODES:
        return False, "admission.invalid_pipeline_mode", "pipeline_mode is not recognized"
    if request.enabled_policies:
        unknown = [p for p in request.enabled_policies if p not in KNOWN_POLICY_NAMES]
        if unknown:
            return False, "admission.invalid_policy_override", f"unknown policies: {', '.join(unknown)}"
    return True, "", ""


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan hook for startup and shutdown.
    Loads config and prepares DBL/KL wiring.
    """
    global _config
    setup_logging()
    logger.info("Starting dbl-boundary-service")
    _config = get_dev_config()
    logger.info(f"Loaded config: model={_config.model}, pipeline={_config.dbl_pipeline}")
    try:
        yield
    finally:
        logger.info("Stopping dbl-boundary-service")


def create_app() -> FastAPI:
    """
    Create the FastAPI application instance.

    For now this is a minimal skeleton:
    - GET /health for probes
    - PATCH /set-key to register the API key
    - GET / for the initial UI shell
    The LLM and DBL integration will be added on top of this.
    """
    app = FastAPI(
        title="DBL Boundary Service",
        description=(
            "Small reference service that exposes a governed LLM boundary. "
            "Requests will be routed through DBL policies and traced via KL."
        ),
        version="0.2.0",
        lifespan=lifespan,
    )

    @app.get("/health", response_class=JSONResponse)
    async def health() -> dict[str, Any]:
        return {"status": "ok"}

    @app.patch("/set-key")
    async def set_key(api_key: str = Body(..., embed=True)) -> dict[str, str]:
        """
        Receives an API key from the UI and stores it in-memory.
        This is a structural guard, not a full security solution.
        """
        api_key_store.set(api_key)
        return {"status": "ok", "message": "API key stored"}

    @app.get("/", response_class=HTMLResponse)
    async def index() -> str:
        return render_index()

    @app.get("/events/{request_id}")
    async def events(request_id: str) -> StreamingResponse:
        queue = event_bus.get_queue(request_id)
        if queue is None:
            raise HTTPException(status_code=404, detail="Unknown request_id")

        async def event_stream():
            try:
                while True:
                    item = await queue.get()
                    if item is None:
                        break
                    payload = json.dumps(item, ensure_ascii=True)
                    yield f"event: {item['event']}\ndata: {payload}\n\n"
            finally:
                event_bus.cleanup(request_id)

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    @app.post("/run", response_class=JSONResponse)
    async def run(request: RunRequest) -> dict[str, Any]:
        """
        Main boundary endpoint.
        
        Flow:
        1. Build PsiDefinition + BoundaryContext
        2. Run DBL pipeline (policies)
        3. If allowed: run KL execution with LLM effector
        4. Return response + snapshot for insights panel
        """
        if _config is None:
            raise HTTPException(status_code=500, detail="Service not initialized")
        
        request_id = str(uuid4())
        event_bus.ensure_queue(request_id)
        await event_bus.emit(request_id, "request_received", {"dry_run": request.dry_run})

        if not api_key_store.is_set() and not request.dry_run:
            await event_bus.emit(request_id, "blocked", {"reason": "admission.missing_api_key"})
            await event_bus.finish(request_id)
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "admission.missing_api_key",
                    "message": "API key not set. Use /set-key first or enable dry_run.",
                },
            )

        ok, reason_code, reason_message = _admission_check(request)
        if not ok:
            await event_bus.emit(request_id, "blocked", {"reason": reason_code})
            await event_bus.finish(request_id)
            raise HTTPException(status_code=400, detail={"error_code": reason_code, "message": reason_message})

        boundary_request = BoundaryRequest(
            prompt=request.prompt,
            tenant_id=request.tenant_id,
            channel=request.channel,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            pipeline_mode=request.pipeline_mode,
            enabled_policies=request.enabled_policies,
        )
        
        try:
            response = await run_boundary_flow(
                request=boundary_request,
                config=_config,
                dry_run=request.dry_run,
                request_id=request_id,
                event_emitter=event_bus.emit,
            )
        except Exception as e:
            await event_bus.emit(request_id, "error", {"message": str(e)})
            await event_bus.finish(request_id)
            logger.exception("Boundary flow failed")
            raise HTTPException(status_code=500, detail=str(e))

        await event_bus.finish(request_id)
        append_run_log(
            RunLogEntry(
                request_id=request_id,
                timestamp=response.snapshot.timestamp,
                dry_run=request.dry_run,
                pipeline_mode=request.pipeline_mode,
                dbl_outcome=response.dbl_outcome,
                blocked=response.blocked,
                block_reason=response.block_reason,
                policy_eval_ms=response.policy_eval_ms,
                llm_call_ms=response.llm_call_ms,
                prompt_length=response.prompt_length,
                model=response.model,
                max_tokens=response.max_tokens,
            )
        )
        
        return {
            "content": response.content,
            "blocked": response.blocked,
            "snapshot": {
                "request_id": response.snapshot.request_id,
                "timestamp": response.snapshot.timestamp,
                "boundary_context": response.snapshot.boundary_context,
                "policy_decisions": response.snapshot.policy_decisions,
                "dbl_outcome": response.snapshot.dbl_outcome,
                "psi_definition": response.snapshot.psi_definition,
                "execution_trace_id": response.snapshot.execution_trace_id,
                "llm_payload": response.snapshot.llm_payload,
                "llm_result": response.snapshot.llm_result,
                "was_blocked": response.snapshot.was_blocked,
                "block_reason": response.snapshot.block_reason,
                "dry_run": response.snapshot.dry_run,
            },
            "v_events": response.v_events,
            "observations": response.observations,
        }

    return app


def run(
    host: str | None = None,
    port: int | None = None,
    open_browser: bool = True,
) -> None:
    """
    Run the boundary service with uvicorn.

    In dev mode this will automatically open the browser on the configured port.
    Host and port can be overridden via arguments; otherwise config is used.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    cfg = get_dev_config()
    effective_host = host or cfg.host
    effective_port = port or cfg.port

    app = create_app()
    url = f"http://{effective_host}:{effective_port}"

    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            logger.warning("Could not open browser automatically", exc_info=True)

    uvicorn.run(app, host=effective_host, port=effective_port, log_level="info")


if __name__ == "__main__":
    run()
