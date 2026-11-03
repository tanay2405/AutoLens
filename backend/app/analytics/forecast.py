from datetime import date
import numpy as np
import pandas as pd

from app.analytics.metrics import load_annual, VOLUME_METRIC
from app.db import SessionLocal
from app.models import Company, MetricDefinition, Observation

HORIZON = 3          # forecast years ahead
MIN_TRAIN = 4        # smallest history used inside a backtest
MIN_POINTS = 7       # need at least 3 backtest errors
Z80 = 1.2816         # z-score for an 80% interval
SIGMA_FLOOR = 0.03   # never claim less than ~3% one-step uncertainty


# ---- Models: take log-values y, return log-forecasts for h = 1..H -------------
def m_last_value(y, H):
    return np.full(H, y[-1])

def m_avg_growth(y, H, window=5):
    g = np.diff(y[-(window + 1):]).mean()
    return y[-1] + g * np.arange(1, H + 1)

def m_linear_trend(y, H, window=6):
    w = y[-window:]
    x = np.arange(len(w))
    slope, intercept = np.polyfit(x, w, 1)
    return intercept + slope * np.arange(len(w), len(w) + H)

# Order matters: on a tie, the earlier (simpler) model wins.
MODELS = {"last_value": m_last_value,
          "avg_growth_5y": m_avg_growth,
          "linear_trend_6y": m_linear_trend}


def backtest(y):
    """Expanding-window, one-step-ahead errors in log space (~ percentage error)."""
    errors = {name: [] for name in MODELS}
    for t in range(MIN_TRAIN, len(y)):
        for name, model in MODELS.items():
            errors[name].append(y[t] - model(y[:t], 1)[0])
    return {name: np.array(e) for name, e in errors.items()}


def forecast_series(series: pd.Series) -> dict:
    y = np.log(series.values.astype(float))
    errs = backtest(y)
    mae = {n: float(np.mean(np.abs(e))) for n, e in errs.items()}
    best = min(mae, key=mae.get)
    sigma = max(float(np.sqrt(np.mean(errs[best] ** 2))), SIGMA_FLOOR)
    mean = MODELS[best](y, HORIZON)
    h = np.arange(1, HORIZON + 1)
    width = Z80 * sigma * np.sqrt(h)
    last_year = int(series.index[-1])
    return {"model": best, "mae": mae, "sigma": sigma,
            "years": [last_year + int(i) for i in h],
            "point": np.exp(mean), "lower": np.exp(mean - width), "upper": np.exp(mean + width)}


def contiguous_series(wide, ticker, key):
    """Latest run of consecutive years (a gap would break a growth model)."""
    if key not in wide.columns:
        return None
    s = wide.loc[ticker][key].dropna().sort_index()
    if s.empty:
        return None
    years = list(s.index)
    start = len(years) - 1
    while start > 0 and years[start] - years[start - 1] == 1:
        start -= 1
    return s.iloc[start:]


def store(session, company, metric, res):
    # Replace old forecasts for this series so a changed winning model leaves no stale rows.
    session.query(Observation).filter_by(
        company_id=company.id, metric_id=metric.id, data_type="forecast").delete()
    for yr, p, lo, hi in zip(res["years"], res["point"], res["lower"], res["upper"]):
        session.add(Observation(
            company_id=company.id, metric_id=metric.id,
            period_end=date(yr, 12, 31), period_type="annual",
            value=float(p), data_type="forecast",
            source=(f"AutoLens {res['model']} forecast; 80% interval; "
                    f"backtest MAE {res['mae'][res['model']]:.1%}"),
            lower_bound=float(lo), upper_bound=float(hi), model_name=res["model"]))


def fmt(v, money):
    return f"${v / 1e9:,.1f}B" if money else f"{v / 1e3:,.0f}K"


def main():
    wide = load_annual()
    with SessionLocal() as s:
        companies = {c.ticker: c for c in s.query(Company)}
        metrics = {m.key: m for m in s.query(MetricDefinition)}
        for ticker, company in companies.items():
            if ticker not in wide.index.get_level_values("ticker"):
                continue
            for key in ("revenue", VOLUME_METRIC.get(ticker)):
                series = contiguous_series(wide, ticker, key) if key else None
                n = 0 if series is None else len(series)
                if n < MIN_POINTS:
                    print(f"\n=== {ticker} {key}: skipped ({n} contiguous years, need {MIN_POINTS}) ===")
                    continue
                res = forecast_series(series)
                money = metrics[key].unit == "USD"
                print(f"\n=== {ticker} {key} ({n} years: {series.index[0]}-{series.index[-1]}) ===")
                print("backtest MAE: " + " | ".join(f"{k} {v:.1%}" for k, v in res["mae"].items())
                      + f"  -> chosen: {res['model']}")
                for yr, p, lo, hi in zip(res["years"], res["point"], res["lower"], res["upper"]):
                    print(f"  {yr}: {fmt(p, money)}   (80%: {fmt(lo, money)} to {fmt(hi, money)})")
                store(s, company, metrics[key], res)
        s.commit()


if __name__ == "__main__":
    main()