"""FastAPI middleware + heartbeat hooks."""

from __future__ import annotations

import asyncio
import time
from typing import Callable

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

from .client import TelemetryClient
from .config import TelemetryConfig


class TelemetryMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, config: TelemetryConfig | None = None) -> None:
        self.config = config or TelemetryConfig.from_env()
        self.client = TelemetryClient(self.config)
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable):  # type: ignore[override]
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        asyncio.create_task(
            self.client.send_event(
                {
                    "kind": "http_request",
                    "metrics": {
                        "duration_ms": duration_ms,
                        "status_code": response.status_code,
                        "method": request.method,
                        "path": request.url.path,
                    },
                }
            )
        )
        return response


def install_heartbeat(app: FastAPI, interval: int = 60) -> None:
    config = TelemetryConfig.from_env()
    client = TelemetryClient(config)

    async def heartbeat_task() -> None:
        while True:
            await client.send_event({"kind": "heartbeat", "metrics": {"uptime_seconds": time.time()}})
            await asyncio.sleep(interval)

    @app.on_event("startup")
    async def _startup() -> None:  # pragma: no cover
        app.state._egi_heartbeat = asyncio.create_task(heartbeat_task())

    @app.on_event("shutdown")
    async def _shutdown() -> None:  # pragma: no cover
        task = getattr(app.state, "_egi_heartbeat", None)
        if task:
            task.cancel()
        await client.close()
