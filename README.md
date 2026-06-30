# legoprice

Scrapes LEGO prices from Icelandic stores, aggregates value metrics, and supports BrickLink enrichment + frontend browsing.

## Project layout

- `run_all.py` - main pipeline runner
- `scrapers/` - store scrapers (`legoprice_*.py`)
- `utils/` - shared helpers (`price_utils.py`, `exchange_rate_utils.py`)
- `data/sets.csv` - Rebrickable set catalog (auto-updated by `run_all.py`)
- `data/store_products/` - per-store outputs
- `data/aggregated_products.json` - merged value dataset
- `data/aggregated_cheapest_prices.json` - merged cheapest-price dataset
- `frontend/` - static browser UI

## Pipeline order in `run_all.py`

1. Ensure folders exist
2. Fetch latest `sets.csv` from `https://rebrickable.com/downloads/` (with CDN fallback)
3. Run selected store scrapers
4. Run `aggregate_prices.py`
5. Run `aggregate_cheapest_prices.py`
6. Optional: run `enrich_bricklink_prices.py`

## Run commands

Run full pipeline (all stores):

```bash
.venv/bin/python run_all.py
```

Run selected stores only:

```bash
.venv/bin/python run_all.py --stores coolshop boozt hagkaup
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
.venv/bin/python run_all.py --skip-scrape --with-bricklink --bricklink-workers 6
```

Or run directly:

```bash
.venv/bin/python enrich_bricklink_prices.py data/aggregated_products.json --workers 6
```

## Frontend

```bash
python3 -m http.server 8000
```

Open:

- `http://localhost:8000/frontend/`

Supports search, store filter, theme filter, preset filters, and sorting (including BrickLink ratio).