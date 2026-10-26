# WindSight

WindSight is a pilot decision-support portal for a UK energy utility buying power in the day-ahead market. It recreates the wind forecast that was genuinely available before a configurable gate closure, compares it with Elexon outturn, and translates forecast error into a clear wind-shortfall risk signal.

## Live application

Public pilot preview: **https://windsight-qx7m2k.krishnasen0006.chatgpt.site**

The preview is a static, reproducible January 2026 snapshot. The React + FastAPI application is configured for Vercel and Heroku below; deploying to either provider requires an authenticated account for that provider.

## What the product does

- Recreates a historical day-ahead decision for every delivery day in January 2026.
- Selects only WINDFOR records published at or before the chosen D-1 cutoff.
- Compares the selected forecast with FUELHH `WIND` actual generation.
- Reports MAE, RMSE, bias, WAPE, overforecast frequency, and P90 wind shortfall.
- Shows the exact publication timestamp used for every delivery interval.

The default cutoff is **09:50 Europe/London on D-1**, matching the published Nord Pool N2EX day-ahead auction gate closure. It is configurable because a client's trading process or venue may use a different deadline.

## Architecture

```text
Elexon Insights API
  FUELHH + WINDFOR
          │
          ▼
scripts/fetch_elexon.py ──► reproducible JSON snapshot
                                  │
                                  ▼
                           FastAPI analytics API
                                  │
                                  ▼
                            React dashboard
```

The production Docker image builds React in a Node stage and serves the compiled frontend and JSON API from one FastAPI container.

## Repository structure

```text
backend/app/analytics.py       Point-in-time selection, interval alignment, metrics
backend/app/main.py            FastAPI routes and static React hosting
backend/app/data/              Reproducible Elexon snapshot
backend/tests/                 Analytics unit tests
frontend/src/App.tsx           Dashboard experience
frontend/src/styles.css        Responsive visual system
frontend/src/types.ts          API response types
scripts/fetch_elexon.py        Elexon ingestion and deduplication
scripts/build_demo_data.py     Static-preview fallback generator
scripts/make_demo_video.py     Narrated demo video renderer
VIDEO_SCRIPT.md                Customer and technical-review talk track
Dockerfile                     Multi-stage production image
docker-compose.yml             One-command local container startup
Procfile                       Heroku process definition
```

## Run with Docker

```bash
docker compose up --build
```

Open <http://localhost:8000>.

## Run for development

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements-dev.txt
cd frontend && npm install && cd ..
python scripts/fetch_elexon.py
python scripts/build_demo_data.py
uvicorn backend.app.main:app --reload --port 8000
```

In another terminal:

```bash
cd frontend
npm run dev
```

Open <http://localhost:5173>.

The supplied video script can also render a narrated MP4 from the running application. It requires Chrome, FFmpeg, and macOS speech synthesis:

```bash
python scripts/make_demo_video.py
```

## Tests and build

```bash
PYTHONPATH=backend pytest backend/tests
cd frontend && npm run build
docker build -t windsight .
```

## Deployment

Two deployment paths are included:

- `vercel.json` and `api/index.py` package the React SPA with the FastAPI ASGI function for Vercel.
- `heroku.yml`, `Procfile`, and the production `Dockerfile` support a container deployment on Heroku.

For Vercel CLI deployment:

```bash
npx vercel --prod
```

For Heroku, create an app using the container stack and deploy the repository using `heroku.yml`.

## Analytical decisions

### Point-in-time forecast selection

For each hourly target interval, WindSight chooses the WINDFOR record with the greatest `publishTime` satisfying:

```text
publishTime <= configured gate closure on D-1
```

Forecasts published later are deliberately excluded to prevent hindsight leakage.

### Resolution alignment

WINDFOR values are hourly while FUELHH values are half-hourly. The two half-hourly MW outturns within each clock hour are averaged. They are not summed because `generation` is a power value, not interval energy.

### Error direction

```text
error = forecast - actual
wind shortfall = max(error, 0)
```

A positive error means wind was overforecast and represents potential additional procurement need. The P90 shortfall is an empirical historical statistic, not a guaranteed reserve recommendation or probabilistic forecast.

## Data provenance and limitations

- Data source: Elexon Insights API only, using `FUELHH` and `WINDFOR` as required.
- Scope: national wind generation for January 2026.
- The portal is a retrospective pilot and does not include demand, prices, plant constraints, portfolio positions, or trading execution.
- The included snapshot makes the demonstration reproducible. Run the ingestion script to rebuild it from Elexon.
- Production use would require monitoring, persistent storage, data-quality alerts, authentication, and agreement on the client's precise auction deadline.

## AI assistance disclosure

This project was developed with assistance from OpenAI Codex for code generation, research, debugging, test development, interface design, and documentation. The analytical assumptions and generated implementation were reviewed and validated during development.

