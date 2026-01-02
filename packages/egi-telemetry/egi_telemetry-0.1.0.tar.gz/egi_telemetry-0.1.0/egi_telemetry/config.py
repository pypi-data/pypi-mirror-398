"""Configuration helpers for telemetry SDK."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class TelemetryConfig:
    engine_id: str
    sku: str
    service_version: str
    control_center_url: str
    api_token: Optional[str] = None
    modules: Optional[str] = None

    @classmethod
    def from_env(cls) -> "TelemetryConfig":
        missing = [
            key
            for key in ("ENGINE_ID", "ENGINE_SKU", "SERVICE_VERSION", "EGI_TELEMETRY_URL")
            if not os.getenv(key)
        ]
        if missing:
            raise RuntimeError(f"Missing telemetry env vars: {', '.join(missing)}")

        return cls(
            engine_id=os.environ["ENGINE_ID"],
            sku=os.environ["ENGINE_SKU"],
            service_version=os.environ["SERVICE_VERSION"],
            control_center_url=os.environ["EGI_TELEMETRY_URL"],
            api_token=os.getenv("EGI_TELEMETRY_TOKEN"),
            modules=os.getenv("EGI_MODULES"),
        )
