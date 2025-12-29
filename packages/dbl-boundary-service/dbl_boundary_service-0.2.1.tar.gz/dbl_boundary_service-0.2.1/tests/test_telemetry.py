from __future__ import annotations

import json
import os

from fastapi.testclient import TestClient

from dbl_boundary_service.main import create_app


def test_sse_emits_first_event() -> None:
    app = create_app()
    with TestClient(app) as client:
        payload = {"prompt": "hello", "dry_run": True}
        response = client.post("/run", json=payload)
        assert response.status_code == 200
        request_id = response.json()["snapshot"]["request_id"]

        with client.stream("GET", f"/events/{request_id}") as stream:
            for line in stream.iter_lines():
                if not line:
                    continue
                line_text = line.decode() if isinstance(line, (bytes, bytearray)) else line
                if line_text.startswith("event:"):
                    assert "request_received" in line_text
                    break


def test_ndjson_logging_appends_for_dry_run(tmp_path) -> None:
    os.environ["DBL_LOG_DIR"] = str(tmp_path)
    app = create_app()
    with TestClient(app) as client:
        payload = {"prompt": "hello", "dry_run": True}
        response = client.post("/run", json=payload)
        assert response.status_code == 200
        request_id = response.json()["snapshot"]["request_id"]
    os.environ.pop("DBL_LOG_DIR", None)

    log_path = tmp_path / "runs.ndjson"
    assert log_path.exists()
    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert lines
    last = json.loads(lines[-1])
    assert last["request_id"] == request_id
    assert last["dry_run"] is True
