import csv
from datetime import date
from pathlib import Path

from app.db import SessionLocal
from app.models import Company, MetricDefinition, Observation

CSV_DIR = Path(__file__).resolve().parents[2] / "data" / "curated"
VALID_DATA_TYPES = {"reported", "estimated"}
VALID_PERIODS = {"annual", "quarterly"}
REQUIRED = ["ticker", "metric", "period_end", "period_type",
            "value", "data_type", "source", "source_url"]


def parse_row(row, companies, metrics):
    for col in REQUIRED:
        if not (row.get(col) or "").strip():
            raise ValueError(f"missing '{col}'")
    ticker, key = row["ticker"].strip(), row["metric"].strip()
    if ticker not in companies:
        raise ValueError(f"unknown ticker {ticker}")
    if key not in metrics or metrics[key].category != "manufacturing":
        raise ValueError(f"'{key}' is not a manufacturing metric")
    if row["data_type"].strip() not in VALID_DATA_TYPES:
        raise ValueError(f"data_type must be one of {sorted(VALID_DATA_TYPES)}")
    if row["period_type"].strip() not in VALID_PERIODS:
        raise ValueError(f"period_type must be one of {sorted(VALID_PERIODS)}")
    if not row["source_url"].strip().startswith("http"):
        raise ValueError("source_url must be an http(s) link")
    value = float(row["value"].replace(",", ""))
    if value <= 0:
        raise ValueError("value must be positive")
    return (companies[ticker], metrics[key], date.fromisoformat(row["period_end"].strip()),
            row["period_type"].strip(), value, row["data_type"].strip(),
            row["source"].strip(), row["source_url"].strip())


def main():
    errors, parsed = [], []
    with SessionLocal() as s:
        companies = {c.ticker: c for c in s.query(Company).all()}
        metrics = {m.key: m for m in s.query(MetricDefinition).all()}

        for path in sorted(CSV_DIR.glob("*.csv")):
            with path.open(newline="") as f:
                for line_no, row in enumerate(csv.DictReader(f), start=2):
                    try:
                        parsed.append(parse_row(row, companies, metrics))
                    except ValueError as e:
                        errors.append(f"{path.name} line {line_no}: {e}")

        if errors:  # all-or-nothing: bad data never reaches the database
            print("Nothing loaded. Fix these first:")
            for e in errors:
                print("  -", e)
            return

        for comp, metric, end, ptype, value, dtype, source, url in parsed:
            obs = (s.query(Observation)
                   .filter_by(company_id=comp.id, metric_id=metric.id, period_end=end,
                              period_type=ptype, data_type=dtype)
                   .one_or_none())
            if obs is None:
                obs = Observation(company_id=comp.id, metric_id=metric.id, period_end=end,
                                  period_type=ptype, data_type=dtype)
                s.add(obs)
            obs.value, obs.source, obs.source_url = value, source, url
        s.commit()
        print(f"Loaded {len(parsed)} rows from {CSV_DIR}")


if __name__ == "__main__":
    main()