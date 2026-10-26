from __future__ import annotations

import math
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from statistics import mean
from zoneinfo import ZoneInfo

LONDON = ZoneInfo("Europe/London")


def parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def decision_cutoff(delivery_day: date, cutoff: str) -> datetime:
    hour, minute = (int(part) for part in cutoff.split(":"))
    local = datetime.combine(delivery_day - timedelta(days=1), time(hour, minute), LONDON)
    return local.astimezone(timezone.utc)


def quantile(values: list[float], probability: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def aggregate_actuals(records: list[dict]) -> dict[datetime, float]:
    buckets: dict[datetime, list[float]] = defaultdict(list)
    for row in records:
        stamp = parse_utc(row["startTime"])
        hour = stamp.replace(minute=0, second=0, microsecond=0)
        buckets[hour].append(float(row["generation"]))
    return {stamp: mean(values) for stamp, values in buckets.items()}


def select_forecasts(records: list[dict], cutoff_at: datetime) -> dict[datetime, dict]:
    selected: dict[datetime, dict] = {}
    for row in records:
        published = parse_utc(row["publishTime"])
        if published > cutoff_at:
            continue
        target = parse_utc(row["startTime"])
        current = selected.get(target)
        if current is None or published > parse_utc(current["publishTime"]):
            selected[target] = row
    return selected


def calculate_metrics(intervals: list[dict]) -> dict:
    paired = [row for row in intervals if row.get("actualMw") is not None and row.get("forecastMw") is not None]
    if not paired:
        return {"count": 0}
    errors = [row["forecastMw"] - row["actualMw"] for row in paired]
    absolute = [abs(value) for value in errors]
    shortfalls = [max(value, 0) for value in errors]
    actual_total = sum(row["actualMw"] for row in paired)
    return {
        "count": len(paired),
        "maeMw": round(mean(absolute), 1),
        "rmseMw": round(math.sqrt(mean([value * value for value in errors])), 1),
        "biasMw": round(mean(errors), 1),
        "wapePct": round(sum(absolute) / actual_total * 100, 1) if actual_total else None,
        "overforecastPct": round(sum(value > 0 for value in errors) / len(errors) * 100, 1),
        "p90ShortfallMw": round(quantile(shortfalls, 0.9) or 0, 1),
        "maxShortfallMw": round(max(shortfalls), 1),
        "forecastEnergyGwh": round(sum(row["forecastMw"] for row in paired) / 1000, 2),
        "actualEnergyGwh": round(actual_total / 1000, 2),
    }


def build_day(records: dict, delivery_day: date, cutoff: str) -> dict:
    day_start = datetime.combine(delivery_day, time.min, timezone.utc)
    day_end = day_start + timedelta(days=1)
    cutoff_at = decision_cutoff(delivery_day, cutoff)
    forecasts = select_forecasts(records["forecasts"], cutoff_at)
    actuals = aggregate_actuals(records["actuals"])
    targets = sorted(stamp for stamp in forecasts if day_start <= stamp < day_end)
    intervals = []
    for target in targets:
        forecast = forecasts[target]
        actual = actuals.get(target)
        forecast_mw = float(forecast["generation"])
        error = forecast_mw - actual if actual is not None else None
        intervals.append({
            "startTime": target.isoformat().replace("+00:00", "Z"),
            "label": target.strftime("%H:%M"),
            "forecastMw": round(forecast_mw, 1),
            "actualMw": round(actual, 1) if actual is not None else None,
            "errorMw": round(error, 1) if error is not None else None,
            "shortfallMw": round(max(error, 0), 1) if error is not None else None,
            "publishTime": forecast["publishTime"],
        })
    publications = sorted({row["publishTime"] for row in intervals})
    return {
        "deliveryDate": delivery_day.isoformat(),
        "cutoff": cutoff,
        "cutoffAt": cutoff_at.isoformat().replace("+00:00", "Z"),
        "latestPublishTime": publications[-1] if publications else None,
        "publicationCount": len(publications),
        "intervals": intervals,
        "metrics": calculate_metrics(intervals),
    }


def build_month(records: dict, cutoff: str) -> dict:
    days = []
    all_intervals = []
    current = date(2026, 1, 1)
    while current <= date(2026, 1, 31):
        day = build_day(records, current, cutoff)
        days.append({"date": current.isoformat(), **day["metrics"]})
        all_intervals.extend(day["intervals"])
        current += timedelta(days=1)
    metrics = calculate_metrics(all_intervals)
    worst = sorted(
        (row for row in all_intervals if row.get("shortfallMw") is not None),
        key=lambda row: row["shortfallMw"],
        reverse=True,
    )[:5]
    return {"cutoff": cutoff, "metrics": metrics, "days": days, "worstIntervals": worst}

