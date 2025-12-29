# DBL Boundary Service Demo

Reference UI and service for deterministic boundary evaluation. Each request produces explicit DECISION events in V (append-only). Observations are non-normative.

## Quick Start

```bash
pip install dbl-boundary-service
dbl-boundary
```

Open http://127.0.0.1:8787

## What it does

Flow:

Input -> Boundary policies -> DECISION -> LLM call -> Observations

DECISION is produced before any LLM call and is the only normative effect in V.

## Demo presets

| Preset | Purpose |
|--------|---------|
| minimal | no policies (testing only) |
| basic_safety | light content safety |
| standard | content safety and rate limiting |
| enterprise | strict content safety and rate limiting |

## Dry run (no LLM)

Use "Dry run" to exercise the full boundary flow without calling the LLM.

## Observable outputs

The UI exposes the following outputs for each run:

- Outcome and DECISION events
- Request context and Psi definition
- LLM payload and LLM result (when executed)
- Observations (request id, timestamps, trace id)

Observations and timing metrics are non-normative and MUST NOT affect decisions.

![DBL Boundary Service UI](screenshots/dbl-boundary-ui-example.png)

## API usage

```bash
curl -X POST http://127.0.0.1:8787/run \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Hello, how are you?",
    "pipeline_mode": "standard",
    "dry_run": true
  }'
```

## Learn more

Deterministic Boundary Layer: https://github.com/lukaspfisterch/deterministic-boundary-layer

This repo is the reference UI/service. The theory and ecosystem map live there.
