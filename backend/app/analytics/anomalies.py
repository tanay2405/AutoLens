from dataclasses import dataclass
import pandas as pd
from app.analytics.metrics import load_annual, add_derived
from app.analytics.fmt import billions as _b

# Tunable thresholds. Document these in the README.
THRESHOLDS = {
    "nonoperating_gap": 0.05,     # |net income - operating income| as share of revenue
    "margin_swing": 0.05,         # YoY change in operating margin (5 points)
    "margin_swing_high": 0.075,   # severity escalates above this
    "revenue_volume_gap": 0.05,   # revenue growth minus volume growth
    "capex_change": 0.30,         # YoY capex change
}


@dataclass
class Flag:
    ticker: str
    year: int
    rule: str
    severity: str  # "high" | "medium" | "low"
    message: str


def detect(min_year: int = 2019) -> list[Flag]:
    d = add_derived(load_annual())
    d["operating_margin_change"] = d.groupby(level="ticker")["operating_margin"].diff()
    t = THRESHOLDS
    flags: list[Flag] = []

    for (ticker, year), r in d.iterrows():
        if year < min_year:
            continue

        def add(rule, severity, msg):
            flags.append(Flag(ticker, int(year), rule, severity, msg))

        # 1. Operating loss
        if pd.notna(r["operating_income"]) and r["operating_income"] < 0:
            add("operating_loss", "high",
                f"Operating loss of {_b(r['operating_income'])} ({r['operating_margin']:.1%} margin).")

        # 2. Net income far from operating income -> non-operating or one-time items
        if pd.notna(r["net_income"]) and pd.notna(r["operating_income"]):
            gap = (r["net_income"] - r["operating_income"]) / r["revenue"]
            if abs(gap) > t["nonoperating_gap"]:
                add("nonoperating_gap", "medium",
                    f"Net income {_b(r['net_income'])} vs operating income "
                    f"{_b(r['operating_income'])}: gap of {gap:+.1%} of revenue. "
                    f"Suggests large non-operating or one-time items; worth investigating.")

        # 3. Operating margin swing
        chg = r["operating_margin_change"]
        if pd.notna(chg) and abs(chg) > t["margin_swing"]:
            sev = "high" if abs(chg) > t["margin_swing_high"] else "medium"
            add("margin_swing", sev,
                f"Operating margin moved {chg * 100:+.1f} points year over year "
                f"(now {r['operating_margin']:.1%}).")

        # 4. Revenue growth diverging from volume growth
        gap = r["revenue_minus_volume_growth"]
        if pd.notna(gap) and abs(gap) > t["revenue_volume_gap"]:
            add("revenue_vs_volume", "low",
                f"Revenue {r['revenue_yoy']:+.1%} vs volume {r['volume_yoy']:+.1%}. "
                f"Points to pricing/mix, definition differences, or non-vehicle revenue.")

        # 5. Large capex change
        if pd.notna(r["capex_yoy"]) and abs(r["capex_yoy"]) > t["capex_change"]:
            add("capex_change", "low",
                f"Capex changed {r['capex_yoy']:+.0%} to {_b(r['capex'])}.")

    order = {"high": 0, "medium": 1, "low": 2}
    return sorted(flags, key=lambda f: (-f.year, order[f.severity], f.ticker))


if __name__ == "__main__":
    for f in detect():
        print(f"{f.year} {f.ticker:5s} [{f.severity:6s}] {f.rule}: {f.message}")