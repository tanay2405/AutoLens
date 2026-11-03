# AutoLens

**Financial and manufacturing intelligence for automakers.** AutoLens combines SEC-reported financials, curated vehicle volumes, baseline forecasts, and a scenario engine for Ford, GM, and Tesla. Every number is labeled **reported**, **derived**, **forecast**, or **scenario**, so a published figure is never confused with a model output.

A portfolio project built on real public data. Not investment advice.

## Features

- **Overview:** latest-year snapshot per company, plus automatically flagged anomalies
- **Company detail:** revenue and operating income charts (reported history, dashed forecast, shaded 80% interval) and an annual metrics table
- **Scenario lab:** sliders for volume, material cost, and capex shocks, with adjustable cost assumptions
- **Data sources and quality:** coverage matrix, known limitations, and every data point linked to its source

## Tech stack

Python, FastAPI, SQLAlchemy, SQLite, pandas · Next.js, TypeScript, Tailwind, Recharts · pytest · SEC EDGAR XBRL API

## Design decisions

- **Provenance on every row.** Each observation stores its data type, source description, and source URL. The UI badges come directly from that field.
- **Derived numbers are never stored as reported.** Margins, growth, and total costs are computed on the fly. Analytics read only reported rows, so forecasts can't feed back into later forecasts.
- **Flexible schema.** Metrics are rows, not columns. Adding wholesale volume mid-project took one line.
- **Honest about non-comparable data.** Ford and GM report wholesales, Tesla reports deliveries, and GM has no cost-of-sales line in SEC data. Each is stored as its own metric, growth rates are compared instead of levels, and gaps stay visibly empty.
- **Validated data loading.** The curated CSV loader checks every row and loads nothing if any row is bad.
- **Backtested forecasts.** Three simple baselines compete in backtests, and the lowest-error model wins per series. Interval width comes from that model's own past errors. Operating income combines revenue and margin forecasts through Monte Carlo simulation.
- **Rule-based anomaly detection.** Five documented rules with tunable thresholds. Flags say what is unusual, not why.
- **Explicit scenario assumptions.** Cost-structure splits aren't public, so they are visible, adjustable, and labeled illustrative.

## Key findings (FY2025)

| | Revenue growth | Volume growth | Operating margin |
|---|---|---|---|
| Ford | +1.2% | -1.7% | -4.9% |
| GM | -1.3% | -5.3% | 1.6% |
| Tesla | -2.9% | -8.6% | 4.6% |

- Revenue held up better than volume at all three companies, which is consistent with pricing and mix (or with definition differences).
- Operating margin fell at all three, most at Ford.
- Backtesting chose the naive last-value model for revenue at all three, since past shocks penalize growth-extrapolating models.
- In a -10% volume scenario, Ford is hit hardest relative to its profit, then Tesla, then GM. That ranking holds across all tested cost assumptions.

## Limitations

- Annual data only, with short histories, so forecast intervals are rough and probably too narrow.
- Forecasts are baselines, not predictions. They can't anticipate one-time charges, launches, tariffs, or recalls.
- Volume definitions differ by company, and Ford and GM don't publish global production.
- Ford and GM revenue includes their financing arms.
- Scenario results depend on illustrative assumptions. Read the shape of the response, not exact dollars.
- Some Tesla volume rows cite news coverage of Tesla's releases instead of Tesla's own pages.
- Tests cover the core logic (scenario math, derived metrics, data validation) but not the SEC network calls or the frontend.

## Getting started

Requires Python 3.10+ and Node 18+.

**1. Set up the backend**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

The SEC requires a contact email in the request header. Set it before loading data:
export SEC_USER_AGENT="AutoLens Portfolio Project you@example.com"

**2. Build the database** (from `backend/`; all steps are safe to re-run)

```bash
cd backend
python -m app.seed
python -m app.ingestion.load_sec
python -m app.ingestion.load_curated
python -m app.analytics.forecast
python -m app.analytics.forecast_profit
```

**3. Run the app**

```bash
# Terminal 1: backend/
uvicorn app.main:app --reload

# Terminal 2: frontend/
npm install
npm run dev
```

Open `http://localhost:3000` (use `localhost`, not `127.0.0.1`). API docs are at `http://127.0.0.1:8000/docs`.

**4. Run the tests**

```bash
cd backend
python -m pytest -v
```

## Adding another automaker

Add it to `seed.py` with its SEC CIK, map its XBRL tags in `load_sec.py`, add its volume metric to `metrics.py`, add curated rows to `data/curated/production.csv`, and re-run the pipeline. The API and frontend pick it up automatically.
