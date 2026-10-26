# WindSight — 10-minute demonstration script

## Part 1: customer presentation (0:00–5:00)

### 0:00–0:35 — The decision

“Every morning, the trading desk must decide how much conventional power to procure before tomorrow's wind is known. WindSight recreates exactly what the desk knew at gate closure and turns the historical forecast error into a procurement-risk signal.”

### 0:35–1:20 — Point-in-time integrity

Show the delivery-day and cutoff controls. Explain that the portal selects only forecasts published before the displayed cutoff. Point to the eligible publication timestamp. Stress that later forecast revisions are excluded.

### 1:20–2:45 — Delivery profile

Walk through forecast versus actual. Change the delivery date once. Explain forecast energy, observed energy, mean bias, and the P90 shortfall buffer. Describe positive bias as wind overforecast, which can leave power still to procure.

### 2:45–4:05 — Quantified accuracy

Show MAE as the typical miss, RMSE as sensitivity to large misses, WAPE as the volume-relative error, and overforecast rate as the frequency of downside exposure. Emphasise that the P90 buffer is descriptive pilot evidence, not an automatic trading instruction.

### 4:05–5:00 — Business value

“The pilot gives the trader one auditable view: what forecast was available, how wrong forecasts like it have been, and where the downside sits. The next phase would combine this risk signal with portfolio demand, market prices, and the client's risk appetite.”

## Part 2: technical review (5:00–10:00)

### 5:00–5:40 — Architecture

Show the README architecture. Elexon FUELHH and WINDFOR feed a reproducible snapshot. FastAPI owns business logic and serves a React frontend. A multi-stage Dockerfile produces one deployable container.

### 5:40–6:45 — Data pipeline

Open `scripts/fetch_elexon.py`. Explain chunked API requests, WIND filtering, deduplication, and the extended extraction window: forecasts from December cover 1 January, while later actual publications cover the end of the month.

### 6:45–7:50 — Core algorithm

Open `backend/app/analytics.py`. Show the D-1 timezone-aware cutoff and the latest-eligible-publication selection. Then show that two FUELHH half-hours are averaged to match an hourly WINDFOR value.

### 7:50–8:35 — API and frontend

Show the `/api/forecast`, `/api/performance`, and `/api/health` routes. Briefly show the React request flow and responsive dashboard. Point out that analytical rules are centralized in Python, not duplicated in the browser.

### 8:35–9:20 — Quality practices

Run the unit tests and frontend build. Explain the tests for cutoff leakage, latest eligible forecast selection, resolution alignment, and error direction. Show the health endpoint and Docker configuration.

### 9:20–10:00 — Limitations and handover

Cover the documented scope limits: national wind only, historical pilot, no demand or price data. Describe production additions: scheduled ingestion, persistent database, authentication, observability, data-quality alerts, and client-agreed auction configuration.
