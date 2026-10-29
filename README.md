# catgov-audit-client-demo

Minimal Python demo client for the **data-catalog-governance-service** audit REST API.

## What it does

Submits an async BQ table audit, polls until done, and prints the score, grade, P0/P1/P2 counts, readiness, and report URLs.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
# Dev (Bearer token)
python demo.py \
    --host https://catalog-governance.prd-dev.data.unity3d.com \
    --table unity-data-prd.attribution.secondary_conversion_session_v1 \
    --partition 2026-10-28 \
    --token <your-token>

# Prd (mTLS via SPIFFE mesh — no token needed)
python demo.py \
    --host https://catalog-governance.prd.data.unity3d.com \
    --table unity-data-prd.attribution.secondary_conversion_session_v1 \
    --partition 2026-10-28
```

## API

### `POST /audit/table`
```json
{ "tableFqn": "project.dataset.table", "partitionDate": "YYYY-MM-DD" }
```
Returns `202 { "jobId": "<uuid>" }`.

### `GET /audit/{jobId}`
Poll until `"status": "DONE"`. See `example_response.json` for the full schema.

## Environments

| Env | URL |
|-----|-----|
| dev | `https://catalog-governance.prd-dev.data.unity3d.com` |
| prd | `https://catalog-governance.prd.data.unity3d.com` |

Production uses mTLS (SPIFFE) — no `--token` needed inside the prd VPC.
