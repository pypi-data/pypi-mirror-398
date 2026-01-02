from egi_telemetry.config import TelemetryConfig


def test_config_from_env(monkeypatch):
    monkeypatch.setenv("ENGINE_ID", "acme-prod.hello")
    monkeypatch.setenv("ENGINE_SKU", "1.0.0.API.DK.20251104")
    monkeypatch.setenv("SERVICE_VERSION", "1.0.0")
    monkeypatch.setenv("EGI_TELEMETRY_URL", "https://example.com")
    config = TelemetryConfig.from_env()
    assert config.engine_id == "acme-prod.hello"
    assert config.sku.endswith("20251104")
