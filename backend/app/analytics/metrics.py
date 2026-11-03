import pandas as pd
from app.db import engine

# Volume metric used for growth comparisons, per company.
# Definitions differ (see data/curated notes), so we compare growth rates, not levels.
VOLUME_METRIC = {"TSLA": "vehicles_delivered", "F": "vehicles_wholesale", "GM": "vehicles_wholesale"}


def load_annual() -> pd.DataFrame:
    """Reported annual observations as a wide table: one row per (ticker, year)."""
    df = pd.read_sql(
        """SELECT c.ticker, m.key AS metric, o.period_end, o.value
           FROM observations o
           JOIN companies c ON c.id = o.company_id
           JOIN metric_definitions m ON m.id = o.metric_id
           WHERE o.data_type = 'reported' AND o.period_type = 'annual'""", engine)
    df["year"] = pd.to_datetime(df["period_end"]).dt.year
    wide = df.pivot_table(index=["ticker", "year"], columns="metric", values="value")
    return wide.sort_index()


def add_derived(wide: pd.DataFrame) -> pd.DataFrame:
    d = wide.copy()
    # Ratios (all derived)
    d["operating_margin"] = d["operating_income"] / d["revenue"]
    d["net_margin"] = d["net_income"] / d["revenue"]
    d["capex_pct_revenue"] = d["capex"] / d["revenue"]
    d["total_costs"] = d["revenue"] - d["operating_income"]          # comparable across all three
    d["total_costs_pct_revenue"] = d["total_costs"] / d["revenue"]

    # Growth (per company, so years never bleed across tickers)
    for col in ["revenue", "operating_income", "net_income", "capex", "total_costs"]:
        d[f"{col}_yoy"] = d.groupby(level="ticker")[col].pct_change(fill_method=None)

    # Pick each company's volume series and compute its growth
    vol = pd.Series(index=d.index, dtype="float64")
    for ticker, metric in VOLUME_METRIC.items():
        if metric in d.columns and ticker in d.index.get_level_values("ticker"):
            vol.loc[ticker] = d.loc[ticker, metric].values
    d["volume"] = vol
    d["volume_yoy"] = d.groupby(level="ticker")["volume"].pct_change(fill_method=None)

    # Revenue growth above volume growth = pricing/mix/other (positive) or the reverse
    d["revenue_minus_volume_growth"] = d["revenue_yoy"] - d["volume_yoy"]
    return d


def summary(year: int = 2025) -> pd.DataFrame:
    d = add_derived(load_annual())
    cols = ["revenue_yoy", "volume_yoy", "revenue_minus_volume_growth",
            "operating_margin", "net_margin", "capex_pct_revenue"]
    return d.xs(year, level="year")[cols]


if __name__ == "__main__":
    pd.options.display.float_format = "{:.1%}".format
    for y in (2024, 2025):
        print(f"\n=== {y} ===")
        print(summary(y).to_string())