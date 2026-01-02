"""HTTP client for sending telemetry payloads."""

from __future__ import annotations

import json
from typing import Any, Dict

import httpx

from .config import TelemetryConfig


class TelemetryClient:
    def __init__(self, config: TelemetryConfig) -> None:
        self.config = config
        self._client = httpx.AsyncClient(timeout=5)

    async def send_event(self, payload: Dict[str, Any]) -> None:
        data = {
            "engineId": self.config.engine_id,
            "sku": self.config.sku,
            "serviceVersion": self.config.service_version,
            **payload,
        }
        headers = {"Content-Type": "application/json"}
        if self.config.api_token:
            headers["Authorization"] = f"Bearer {self.config.api_token}"

        url = self.config.control_center_url.rstrip("/")
        await self._client.post(url, content=json.dumps(data), headers=headers)

    async def close(self) -> None:
        await self._client.aclose()
