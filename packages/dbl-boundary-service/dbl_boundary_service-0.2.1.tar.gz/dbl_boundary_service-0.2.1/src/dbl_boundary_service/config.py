from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


# -------------------------------------------------------------------
# Dataclass: BoundaryConfig
# A small, deterministic config structure:
# - api_key: optional, set live from the UI
# - model: default LLM model
# - dbl_pipeline: name of the pipeline in dbl-main
# - host/port: service binding
# -------------------------------------------------------------------

@dataclass(frozen=True)
class BoundaryConfig:
    api_key: Optional[str]
    model: str
    dbl_pipeline: str
    boundary_id: str
    boundary_version: str
    host: str
    port: int

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "BoundaryConfig":
        return BoundaryConfig(
            api_key=d.get("api_key"),
            model=d.get("model", "gpt-4.1-mini"),
            dbl_pipeline=d.get("dbl_pipeline", "default"),
            boundary_id=d.get("boundary_id", "dbl-boundary-service"),
            boundary_version=d.get("boundary_version", "0.2.0"),
            host=d.get("host", "127.0.0.1"),
            port=int(d.get("port", 8787)),
        )


# -------------------------------------------------------------------
# load_config
# Loads a JSON file, validates basic structure, and creates BoundaryConfig.
# The loader fails deterministically with clear error messages.
# -------------------------------------------------------------------

def load_config(path: str | Path) -> BoundaryConfig:
    p = Path(path)

    if not p.exists():
        raise FileNotFoundError(f"Config file not found: {p}")

    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"Config file is not valid JSON: {p}") from e

    if not isinstance(raw, dict):
        raise ValueError(f"Config root must be an object: {p}")

    return BoundaryConfig.from_dict(raw)


# -------------------------------------------------------------------
# get_dev_config
# Convenience method: used for local development startup.
# -------------------------------------------------------------------

def get_dev_config() -> BoundaryConfig:
    """
    Loads configs/boundary.dev.json by convention.
    """
    default_path = Path("configs/boundary.dev.json")

    if default_path.exists():
        return load_config(default_path)

    # Fallback if no config file exists yet.
    return BoundaryConfig(
        api_key=None,
        model="gpt-4.1-mini",
        dbl_pipeline="default",
        boundary_id="dbl-boundary-service",
        boundary_version="0.2.0",
        host="127.0.0.1",
        port=8787,
    )
