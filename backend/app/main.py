from dataclasses import asdict
from typing import Optional

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.db import engine
from app.analytics.metrics import load_annual, add_derived
from app.analytics.anomalies import detect
from app.analytics.scenarios import Scenario, Assumptions, load_baseline, run

app = FastAPI(title="AutoLens API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"],
                   allow_methods=["*"], allow_headers=["*"])


def records(df: pd.DataFrame) -> list[dict]:
    """DataFrame -> JSON-safe list of dicts (NaN/inf become null)."""
    df = df.replace([np.inf, -np.inf], np.nan)
    return df.astype(object).where(df.notna(), None).to_dict(orient="records")


def require_company(ticker: str) -> str:
    ticker = ticker.upper()
    found = pd.read_sql(text("SELECT 1 FROM companies WHERE ticker = :t"), engine,
                        params={"t": ticker})
    if found.empty:
        raise HTTPException(404, f"Unknown ticker '{ticker}'")
    return ticker


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/companies")
def companies():
    return records(pd.read_sql("SELECT ticker, name FROM companies ORDER BY ticker", engine))


@app.get("/api/metrics")
def metrics():
    return records(pd.read_sql(
        "SELECT key, label, unit, category FROM metric_definitions ORDER BY category, key", engine))


@app.get("/api/companies/{ticker}/observations")
def observations(ticker: str, metric: Optional[str] = None, data_type: Optional[str] = None):
    ticker = require_company(ticker)
    if data_type not in (None, "reported", "estimated", "forecast"):
        raise HTTPException(422, "data_type must be reported, estimated, or forecast")
    df = pd.read_sql(text("""
        SELECT m.key AS metric, m.unit, o.period_end, o.period_type, o.value, o.data_type,
               o.lower_bound, o.upper_bound, o.model_name, o.source, o.source_url
        FROM observations o
        JOIN companies c ON c.id = o.company_id
        JOIN metric_definitions m ON m.id = o.metric_id
        WHERE c.ticker = :t
          AND (:metric IS NULL OR m.key = :metric)
          AND (:dt IS NULL OR o.data_type = :dt)
        ORDER BY m.key, o.period_end, o.data_type"""),
        engine, params={"t": ticker, "metric": metric, "dt": data_type})
    return records(df)


SUMMARY_COLS = ["year", "revenue", "operating_income", "net_income", "capex", "total_costs",
                "operating_margin", "net_margin", "capex_pct_revenue", "revenue_yoy",
                "volume", "volume_yoy", "revenue_minus_volume_growth"]


@app.get("/api/companies/{ticker}/summary")
def summary(ticker: str):
    ticker = require_company(ticker)
    d = add_derived(load_annual())
    if ticker not in d.index.get_level_values("ticker"):
        raise HTTPException(404, f"No data loaded for {ticker}")
    out = d.loc[ticker].reset_index()[SUMMARY_COLS]
    return {"data_type": "derived", "rows": records(out)}


@app.get("/api/anomalies")
def anomalies(ticker: Optional[str] = None):
    flags = [asdict(f) for f in detect()]
    if ticker:
        flags = [f for f in flags if f["ticker"] == ticker.upper()]
    return flags


class ScenarioRequest(BaseModel):
    ticker: str
    year: int = Field(2027, ge=2026, le=2028)
    volume_change: float = Field(0.0, ge=-0.5, le=0.5)
    material_cost_change: float = Field(0.0, ge=-0.5, le=1.0)
    capex_change: float = Field(0.0, ge=-0.5, le=1.0)
    variable_cost_share: float = Field(0.8, ge=0.0, le=1.0)
    material_share: float = Field(0.5, ge=0.0, le=1.0)
    price_passthrough: float = Field(0.0, ge=0.0, le=1.0)


@app.post("/api/scenarios")
def scenario(req: ScenarioRequest):
    ticker = require_company(req.ticker)
    if req.material_share > req.variable_cost_share:
        raise HTTPException(422, "material_share cannot exceed variable_cost_share")
    try:
        base = load_baseline(ticker, req.year)
    except ValueError as e:
        raise HTTPException(409, str(e))
    a = Assumptions(req.variable_cost_share, req.material_share, req.price_passthrough)
    sc = Scenario(req.volume_change, req.material_cost_change, req.capex_change)
    baseline, result = run(base, Scenario(), a), run(base, sc, a)
    return {
        "data_type": "scenario",
        "note": "Derived from model forecasts using illustrative, user-adjustable assumptions.",
        "ticker": ticker, "year": req.year,
        "assumptions": asdict(a), "scenario": asdict(sc),
        "baseline": baseline, "result": result,
        "delta": {k: result[k] - baseline[k] for k in baseline},
    }