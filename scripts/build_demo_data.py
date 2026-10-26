#!/usr/bin/env python3
"""Build a browser fallback used by static previews when the API is unavailable."""

import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.analytics import build_day, build_month  # noqa: E402


def main() -> None:
    records = json.loads((ROOT / "backend/app/data/elexon_january_2026.json").read_text())
    days = {
        f"2026-01-{day:02d}": build_day(records, date(2026, 1, day), "09:50")
        for day in range(1, 32)
    }
    payload = {"cutoff": "09:50", "days": days, "month": build_month(records, "09:50")}
    output = ROOT / "frontend/public/demo-data.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, separators=(",", ":")))
    print(f"Wrote static fallback to {output}")


if __name__ == "__main__":
    main()

