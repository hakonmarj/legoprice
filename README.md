# legoprice

Scrapes LEGO prices from Icelandic stores, aggregates value metrics, stores daily snapshots in PostgreSQL, and serves data via ASP.NET Core + React frontend.

## Project layout

- `run_all.py` - main pipeline runner
- `scrapers/` - store scrapers (`legoprice_*.py`)
- `utils/` - shared helpers (`price_utils.py`, `exchange_rate_utils.py`)
- `data/sets.csv` - Rebrickable set catalog (auto-updated by `run_all.py`)
- `data/store_products/` - per-store outputs
- `data/aggregated_products.json` - merged value dataset
- `data/aggregated_cheapest_prices.json` - merged cheapest-price dataset
- `backend-dotnet/src/Legoprice.Api/` - ASP.NET Core API with Entity Framework Core (Controllers/Services/Repositories)
- `frontend/` - React + Vite + TypeScript UI
- `terraform/` - Azure infrastructure (ACR, Log Analytics, Container Apps, PostgreSQL)

## Pipeline order in `run_all.py`

1. Ensure folders exist
2. Fetch latest `sets.csv` from `https://rebrickable.com/downloads/` (with CDN fallback)
3. Run selected store scrapers
4. Run `aggregate_prices.py`
5. Run `aggregate_cheapest_prices.py`
6. Run `enrich_bricklink_prices.py` (unless explicitly skipped)
7. Optional: ingest current aggregate into backend API (`push_prices_to_api.py`) if `BACKEND_API_URL` is set

## Run commands

Run full pipeline (all stores):

```bash
.venv/bin/python run_all.py
```

Run selected stores only:

```bash
.venv/bin/python run_all.py --stores coolshop boozt hagkaup
```

Skip BrickLink enrichment:

```bash
.venv/bin/python run_all.py --skip-bricklink
```

Skip scraping and rebuild aggregates only:

```bash
.venv/bin/python run_all.py --skip-scrape
```

Skip sets download (only if `data/sets.csv` already exists):

```bash
.venv/bin/python run_all.py --skip-sets-update
```

## BrickLink enrichment

Create `.env` in the project root:

```bash
BRICKLINK_CONSUMER_KEY=...
BRICKLINK_CONSUMER_SECRET=...
BRICKLINK_TOKEN=...
BRICKLINK_TOKEN_SECRET=...
```

Run via pipeline:

```bash
.venv/bin/python run_all.py --skip-scrape --bricklink-workers 6
```

Or run directly:

```bash
.venv/bin/python enrich_bricklink_prices.py data/aggregated_products.json --workers 6
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Open:

- `http://localhost:5173/`

## Backend API

```bash
dotnet run --project backend-dotnet/src/Legoprice.Api/Legoprice.Api.csproj
```

Set `DATABASE_URL` (or `ConnectionStrings:DefaultConnection`) for PostgreSQL, for example:

```bash
export DATABASE_URL="Host=localhost;Port=5432;Database=legoprice;Username=postgres;Password=postgres"
```

Endpoints:

- `GET /api/products`
- `GET /api/products/{set_number}/history?days=30`
- `POST /api/ingest/products`
- `POST /api/pipeline/trigger` (secured trigger endpoint used by GitHub Actions)

Ingest aggregated output into API/database:

```bash
export BACKEND_API_URL="http://localhost:8080"
.venv/bin/python push_prices_to_api.py data/aggregated_products.json
```

### Trigger architecture (recommended)

For complex scraping/data-transformation logic, keep orchestration in backend and use GitHub Actions only as a trigger:

- GitHub Action: `.github/workflows/trigger-backend-pipeline.yml`
- Action sends `POST` to backend `/api/pipeline/trigger`
- Backend validates `X-Trigger-Token` and starts configured pipeline command

Required backend environment variables:

```bash
PIPELINE_TRIGGER_TOKEN=your-strong-token
PIPELINE_RUN_COMMAND="python3 /app/run_all.py --delay-seconds 0"
```

Required GitHub repository secrets:

- `BACKEND_TRIGGER_URL` (for example `https://<backend-host>/api/pipeline/trigger`)
- `BACKEND_TRIGGER_TOKEN` (must match backend `PIPELINE_TRIGGER_TOKEN`)

## Docker + CI

- Frontend Dockerfile: `frontend/Dockerfile`
- Backend Dockerfile: `backend-dotnet/src/Legoprice.Api/Dockerfile`
- Frontend push workflow: `.github/workflows/docker-build-frontend.yml`
- Backend push workflow: `.github/workflows/docker-build-backend.yml`
- Scheduled trigger workflow: `.github/workflows/trigger-backend-pipeline.yml`

Required GitHub secrets for the docker workflow:

- `ACR_LOGIN_SERVER`
- `ACR_USERNAME`
- `ACR_PASSWORD`

## Terraform (Azure)

Terraform scripts in `terraform/` create:

- Azure Resource Group
- Azure Container Registry
- Azure Log Analytics Workspace
- Azure Database for PostgreSQL Flexible Server
- Azure Container Apps Environment
- Container App for backend
- Container App for frontend

Supports search, store filter, theme filter, preset filters, and sorting (including BrickLink ratio).