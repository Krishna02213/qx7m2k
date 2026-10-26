from __future__ import annotations

import json
import os
from datetime import date
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .analytics import build_day, build_month

APP_DIR = Path(__file__).resolve().parent
DATA_FILE = APP_DIR / "data" / "elexon_january_2026.json"
FRONTEND_DIST = Path(os.environ.get("FRONTEND_DIST", APP_DIR.parent.parent / "frontend" / "dist"))

app = FastAPI(title="WindSight API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@lru_cache(maxsize=1)
def load_records() -> dict:
    if not DATA_FILE.exists():
        raise RuntimeError("Elexon snapshot is missing. Run scripts/fetch_elexon.py first.")
    return json.loads(DATA_FILE.read_text())


def validate_cutoff(value: str) -> str:
    try:
        hour, minute = (int(part) for part in value.split(":"))
        if not 0 <= hour <= 23 or not 0 <= minute <= 59:
            raise ValueError
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="cutoff must be HH:MM") from exc
    return value


@app.get("/api/health")
def health() -> dict:
    records = load_records()
    return {
        "status": "ok",
        "source": "Elexon Insights API",
        "actualRecords": len(records["actuals"]),
        "forecastRecords": len(records["forecasts"]),
        "generatedAt": records["metadata"]["generatedAt"],
    }


@app.get("/api/delivery-days")
def delivery_days() -> dict:
    return {"days": [f"2026-01-{day:02d}" for day in range(1, 32)]}


@app.get("/api/forecast")
def forecast(
    delivery_date: date = Query(alias="delivery_date"),
    cutoff: str = Query(default="09:50"),
) -> dict:
    if delivery_date.year != 2026 or delivery_date.month != 1:
        raise HTTPException(status_code=422, detail="delivery_date must be in January 2026")
    return build_day(load_records(), delivery_date, validate_cutoff(cutoff))


@app.get("/api/performance")
def performance(cutoff: str = Query(default="09:50")) -> dict:
    return build_month(load_records(), validate_cutoff(cutoff))


if FRONTEND_DIST.exists():
    assets = FRONTEND_DIST / "assets"
    if assets.exists():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        candidate = FRONTEND_DIST / path
        if path and candidate.exists() and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")

