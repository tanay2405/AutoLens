from datetime import date
import numpy as np

from app.analytics.metrics import load_annual, add_derived
from app.analytics.forecast import (forecast_series, contiguous_series,
                                    HORIZON, MIN_TRAIN, MIN_POINTS)
from app.db import SessionLocal
from app.models import Company, MetricDefinition, Observation

N_SIM = 20_000
SIGMA_FLOOR = 0.01  # never claim less than one point of margin uncertainty
rng = np.random.default_rng(42)  # fixed seed: results are reproducible


# ---- Margin models: take margin levels m, return forecasts for h = 1..H -------
def mm_last(m, H):  return np.full(H, m[-1])
def mm_mean3(m, H): return np.full(H, m[-3:].mean())
def mm_mean5(m, H): return np.full(H, m[-5:].mean())

MARGIN_MODELS = {"last_value": mm_last, "mean_3y": mm_mean3, "mean_5y": mm_mean5}


def backtest_margin(m):
    errs = {n: [] for n in MARGIN_MODELS}
    for t in range(MIN_TRAIN, len(m)):
        for n, f in MARGIN_MODELS.items():
            errs[n].append(m[t] - f(m[:t], 1)[0])
    return {n: np.array(e) for n, e in errs.items()}


def main():
    d = add_derived(load_annual())
    with SessionLocal() as s:
        companies = {c.ticker: c for c in s.query(Company)}
        metric = s.query(MetricDefinition).filter_by(key="operating_income").one()

        for ticker, company in companies.items():
            rev = contiguous_series(d, ticker, "revenue")
            marg = contiguous_series(d, ticker, "operating_margin")
            if rev is None or marg is None or min(len(rev), len(marg)) < MIN_POINTS:
                print(f"\n=== {ticker}: skipped (not enough history) ===")
                continue
            assert rev.index[-1] == marg.index[-1], "revenue and margin end in different years"

            rev_res = forecast_series(rev)
            m = marg.values.astype(float)
            errs = backtest_margin(m)
            mae = {n: float(np.mean(np.abs(e))) for n, e in errs.items()}
            best = min(mae, key=mae.get)
            sigma_m = max(float(np.sqrt(np.mean(errs[best] ** 2))), SIGMA_FLOOR)
            mean_m = MARGIN_MODELS[best](m, HORIZON)

            print(f"\n=== {ticker} operating income ({len(marg)} margin years: "
                  f"{marg.index[0]}-{marg.index[-1]}) ===")
            print("margin backtest MAE: " + " | ".join(f"{k} {v * 100:.1f} pts" for k, v in mae.items())
                  + f"  -> chosen: {best}")

            s.query(Observation).filter_by(
                company_id=company.id, metric_id=metric.id, data_type="forecast").delete()

            for i, year in enumerate(rev_res["years"]):
                h = i + 1
                rev_sim = rev_res["point"][i] * np.exp(
                    rev_res["sigma"] * np.sqrt(h) * rng.standard_normal(N_SIM))
                m_sim = mean_m[i] + sigma_m * np.sqrt(h) * rng.standard_normal(N_SIM)
                lo, hi = np.percentile(rev_sim * m_sim, [10, 90])
                point = rev_res["point"][i] * mean_m[i]
                print(f"  {year}: revenue ${rev_res['point'][i] / 1e9:,.1f}B x margin {mean_m[i]:.1%}"
                      f" = ${point / 1e9:,.1f}B   (80%: ${lo / 1e9:,.1f}B to ${hi / 1e9:,.1f}B)")
                s.add(Observation(
                    company_id=company.id, metric_id=metric.id,
                    period_end=date(year, 12, 31), period_type="annual",
                    value=float(point), data_type="forecast",
                    source=(f"AutoLens simulated forecast: revenue {rev_res['model']} x "
                            f"margin {best}; 80% interval from 20,000 draws"),
                    lower_bound=float(lo), upper_bound=float(hi),
                    model_name=f"{rev_res['model']} x {best}"))
        s.commit()


if __name__ == "__main__":
    main()