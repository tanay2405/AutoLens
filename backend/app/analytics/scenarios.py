from dataclasses import dataclass
import pandas as pd
from sqlalchemy import text
from app.analytics.fmt import billions as _b

from app.db import engine
from app.analytics.metrics import load_annual, add_derived


@dataclass(frozen=True)
class Assumptions:
    """ILLUSTRATIVE placeholders, not reported figures. Expose these as UI inputs."""
    variable_cost_share: float = 0.80   # share of total costs that scales with volume
    material_share: float = 0.50        # share of total costs that is materials (<= variable share)
    price_passthrough: float = 0.0      # share of a material-cost increase recovered through price

    def __post_init__(self):
        assert self.material_share <= self.variable_cost_share <= 1.0


@dataclass(frozen=True)
class Scenario:
    volume_change: float = 0.0          # -0.10 = 10% fewer vehicles
    material_cost_change: float = 0.0   # +0.10 = materials cost 10% more
    capex_change: float = 0.0           # +0.20 = 20% more capital spending


def load_baseline(ticker: str, year: int) -> dict:
    """Forecast revenue/operating income from the DB, plus a derived capex baseline."""
    q = text("""SELECT m.key AS metric, o.value
                FROM observations o
                JOIN companies c ON c.id = o.company_id
                JOIN metric_definitions m ON m.id = o.metric_id
                WHERE o.data_type = 'forecast' AND c.ticker = :t AND o.period_end = :d
                  AND m.key IN ('revenue', 'operating_income')""")
    df = pd.read_sql(q, engine, params={"t": ticker, "d": f"{year}-12-31"})
    vals = dict(zip(df["metric"], df["value"]))
    if set(vals) != {"revenue", "operating_income"}:
        raise ValueError(f"missing forecasts for {ticker} {year}; run the forecast scripts first")
    hist = add_derived(load_annual()).loc[ticker]
    vals["capex"] = vals["revenue"] * hist["capex_pct_revenue"].dropna().tail(3).mean()  # derived
    return vals


def run(base: dict, sc: Scenario, a: Assumptions = Assumptions()) -> dict:
    rev0, oi0, capex0 = base["revenue"], base["operating_income"], base["capex"]
    costs0 = rev0 - oi0
    v = sc.volume_change

    fixed = costs0 * (1 - a.variable_cost_share)
    variable = costs0 * a.variable_cost_share * (1 + v)
    materials = costs0 * a.material_share * (1 + v)       # materials follow volume
    material_delta = materials * sc.material_cost_change  # extra cost from price change

    revenue = rev0 * (1 + v) + material_delta * a.price_passthrough
    costs = fixed + variable + material_delta
    op_income = revenue - costs
    capex = capex0 * (1 + sc.capex_change)
    return {"revenue": revenue, "operating_income": op_income,
            "operating_margin": op_income / revenue, "capex": capex,
            "income_after_capex": op_income - capex}


STRESS = Scenario(volume_change=-0.10, material_cost_change=0.10, capex_change=0.20)
SINGLE = [("Volume -10%", Scenario(volume_change=-0.10)),
          ("Materials +10%", Scenario(material_cost_change=0.10)),
          ("Capex +10%", Scenario(capex_change=0.10))]


def main(year: int = 2027):
    a = Assumptions()
    print(f"Assumptions (illustrative): variable costs {a.variable_cost_share:.0%} of total, "
          f"materials {a.material_share:.0%}, price pass-through {a.price_passthrough:.0%}")
    for ticker in ("F", "GM", "TSLA"):
        b = load_baseline(ticker, year)
        base = run(b, Scenario(), a)
        print(f"\n=== {ticker} FY{year} baseline: revenue {_b(base['revenue'])}, "
              f"operating income {_b(base['operating_income'])} ({base['operating_margin']:.1%}), "
              f"capex {_b(base['capex'])} ===")
        s = run(b, STRESS, a)
        print(f"Combined stress (volume -10%, materials +10%, capex +20%):")
        print(f"  revenue {_b(s['revenue'])} | operating income {_b(s['operating_income'])} "
              f"({s['operating_margin']:.1%}) | income after capex {_b(s['income_after_capex'])}")
        print("Single-factor change in operating income / income after capex:")
        for label, sc in SINGLE:
            r = run(b, sc, a)
            d_oi = r["operating_income"] - base["operating_income"]
            d_ia = r["income_after_capex"] - base["income_after_capex"]
            print(f"  {label:15s} {_b(d_oi):>9s}  /  {_b(d_ia):>9s}")

def sweep(year: int = 2027):
    """How much do the conclusions depend on the assumed cost structure?"""
    for ticker in ("F", "GM", "TSLA"):
        b = load_baseline(ticker, year)
        base = run(b, Scenario())["operating_income"]
        print(f"\n=== {ticker} FY{year}: change in operating income (baseline {_b(base)}) ===")

        print("Volume -10%, by assumed variable-cost share:")
        for vcs in (0.6, 0.7, 0.8, 0.9):
            a = Assumptions(variable_cost_share=vcs, material_share=min(0.5, vcs))
            d = run(b, Scenario(volume_change=-0.10), a)["operating_income"] - base
            print(f"  {vcs:.0%}: {_b(d):>8s}  ({d / base:+.0%} of baseline)")

        print("Materials +10%, by assumed material share of costs (0% price pass-through):")
        for ms in (0.3, 0.4, 0.5, 0.6):
            a = Assumptions(variable_cost_share=max(0.8, ms), material_share=ms)
            d = run(b, Scenario(material_cost_change=0.10), a)["operating_income"] - base
            print(f"  {ms:.0%}: {_b(d):>8s}  ({d / base:+.0%} of baseline)")


if __name__ == "__main__":
    main()
    sweep()