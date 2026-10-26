#!/usr/bin/env python3
from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
OUTPUT = Path(__file__).resolve().parents[1] / "backend" / "app" / "data" / "elexon_january_2026.json"


def iso(stamp: datetime) -> str:
    return stamp.isoformat(timespec="seconds").replace("+00:00", "Z")


def fetch_window(dataset: str, start: datetime, end: datetime) -> list[dict]:
    query = urllib.parse.urlencode({"publishDateTimeFrom": iso(start), "publishDateTimeTo": iso(end)})
    request = urllib.request.Request(
        f"{BASE_URL}/{dataset}/stream?{query}",
        headers={"User-Agent": "WindSight-pilot/1.0", "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def fetch_range(dataset: str, start: datetime, end: datetime, chunk_days: int = 2) -> list[dict]:
    records: list[dict] = []
    cursor = start
    while cursor < end:
        stop = min(cursor + timedelta(days=chunk_days), end)
        batch = fetch_window(dataset, cursor, stop)
        records.extend(batch)
        print(f"{dataset}: {iso(cursor)} to {iso(stop)} -> {len(batch):,}")
        cursor = stop
        time.sleep(0.05)
    return records


def deduplicate(records: list[dict], fields: tuple[str, ...]) -> list[dict]:
    unique = {}
    for row in records:
        unique[tuple(row.get(field) for field in fields)] = row
    return list(unique.values())


def main() -> None:
    utc = timezone.utc
    forecasts = fetch_range(
        "WINDFOR",
        datetime(2025, 12, 29, tzinfo=utc),
        datetime(2026, 2, 1, tzinfo=utc),
    )
    actuals = fetch_range(
        "FUELHH",
        datetime(2026, 1, 1, tzinfo=utc),
        datetime(2026, 2, 3, tzinfo=utc),
    )
    forecasts = deduplicate(forecasts, ("publishTime", "startTime"))
    actuals = [row for row in actuals if row.get("fuelType") == "WIND"]
    actuals = deduplicate(actuals, ("publishTime", "startTime", "fuelType"))
    payload = {
        "metadata": {
            "source": "Elexon Insights API: FUELHH and WINDFOR",
            "generatedAt": datetime.now(utc).isoformat().replace("+00:00", "Z"),
            "deliveryWindow": ["2026-01-01T00:00:00Z", "2026-02-01T00:00:00Z"],
        },
        "forecasts": forecasts,
        "actuals": actuals,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, separators=(",", ":")))
    print(f"Wrote {len(forecasts):,} forecasts and {len(actuals):,} wind actuals to {OUTPUT}")


if __name__ == "__main__":
    main()

