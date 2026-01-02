# egi-telemetry (Python)

Early scaffold for the EGIntegrations telemetry SDK. Goals:

- Minimal configuration via env vars (`ENGINE_ID`, `ENGINE_SKU`, `EGI_TELEMETRY_URL`).
- FastAPI middleware that records request duration + status codes.
- Background heartbeat task that publishes uptime and module toggles to Control Center.
- CLI helper (`egi-telemetry init`) that writes `.egi/telemetry.toml` and verifies connectivity.

## Quickstart

```bash
cd sdk/python
pip install -e .[fastapi]
egi-telemetry init --engine acme-prod.hello-engine --sku 1.0.0.API.DK.20251104 \
  --url https://control-center.egintegrations.com/api/ingest/telemetry
```

In your FastAPI app:

```python
from fastapi import FastAPI
from egi_telemetry.fastapi_middleware import TelemetryMiddleware, install_heartbeat

app = FastAPI()
app.add_middleware(TelemetryMiddleware)
install_heartbeat(app)
```

## Status

This is a scaffold—wire format and auth still subject to change once Control Center
ingest endpoints solidify.
