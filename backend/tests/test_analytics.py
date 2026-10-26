from datetime import date, datetime, timezone

from app.analytics import aggregate_actuals, calculate_metrics, decision_cutoff, select_forecasts


def test_cutoff_is_previous_day_and_timezone_aware():
    assert decision_cutoff(date(2026, 1, 15), "09:50") == datetime(2026, 1, 14, 9, 50, tzinfo=timezone.utc)


def test_latest_eligible_forecast_is_selected():
    rows = [
        {"startTime": "2026-01-15T12:00:00Z", "publishTime": "2026-01-14T08:30:00Z", "generation": 100},
        {"startTime": "2026-01-15T12:00:00Z", "publishTime": "2026-01-14T09:30:00Z", "generation": 110},
        {"startTime": "2026-01-15T12:00:00Z", "publishTime": "2026-01-14T10:30:00Z", "generation": 120},
    ]
    selected = select_forecasts(rows, datetime(2026, 1, 14, 9, 50, tzinfo=timezone.utc))
    assert next(iter(selected.values()))["generation"] == 110


def test_half_hours_are_averaged_as_power_not_summed():
    rows = [
        {"startTime": "2026-01-15T12:00:00Z", "generation": 800},
        {"startTime": "2026-01-15T12:30:00Z", "generation": 1000},
    ]
    assert next(iter(aggregate_actuals(rows).values())) == 900


def test_positive_error_is_procurement_shortfall():
    metrics = calculate_metrics([
        {"forecastMw": 1100, "actualMw": 900},
        {"forecastMw": 800, "actualMw": 900},
    ])
    assert metrics["biasMw"] == 50
    assert metrics["overforecastPct"] == 50
    assert metrics["maxShortfallMw"] == 200

