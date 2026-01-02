"""Command line helper for telemetry bootstrap."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize EGI telemetry settings",
    prog="EGITelemetry")
    parser.add_argument("--engine", required=True)
    parser.add_argument("--sku", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--token")
    parser.add_argument("--modules", help="Comma-delimited module list")
    parser.add_argument("--output", default=".egi/telemetry.toml")
    args = parser.parse_args()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "engine": args.engine,
        "sku": args.sku,
        "url": args.url,
        "token": args.token,
        "modules": args.modules,
    }
    output.write_text(json.dumps(payload, indent=2))
    print(f"Wrote telemetry config to {output}")


if __name__ == "__main__":  # pragma: no cover
    main()
