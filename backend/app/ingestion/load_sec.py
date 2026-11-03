from datetime import date
import pandas as pd

from app.db import SessionLocal, engine
from app.models import Company, MetricDefinition, Observation
from app.ingestion.sec_client import fetch_company_facts
from app.ingestion.explore import annual_values  # TODO: move to a shared module later

MIN_YEAR = 2015

# Ordered fallbacks: earlier tags win; later tags only fill years the earlier ones lack.
TAG_MAP = {
    "F": {
        "revenue": ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax"],
        "cost_of_revenue": ["CostOfGoodsAndServicesSold"],
        "operating_income": ["OperatingIncomeLoss"],
        "net_income": ["NetIncomeLoss", "NetIncomeLossAvailableToCommonStockholdersBasic"],
        "capex": ["PaymentsToAcquireProductiveAssets"],
    },
    "GM": {
        "revenue": ["Revenues"],
        "operating_income": ["OperatingIncomeLoss"],
        "net_income": ["NetIncomeLoss"],
        "capex": ["PaymentsToAcquirePropertyPlantAndEquipment"],
    },
    "TSLA": {
        "revenue": ["Revenues"],
        "cost_of_revenue": ["CostOfRevenue"],
        "operating_income": ["OperatingIncomeLoss"],
        "net_income": ["NetIncomeLoss"],
        "capex": ["PaymentsToAcquirePropertyPlantAndEquipment"],
    },
}


def load_company(session, company, metric_ids) -> dict:
    facts = fetch_company_facts(company.sec_cik)["facts"].get("us-gaap", {})
    counts = {}
    for metric_key, tags in TAG_MAP[company.ticker].items():
        chosen = {}  # period_end -> (tag, row)
        for tag in tags:
            if tag not in facts:
                print(f"  warning: {company.ticker} missing tag {tag}")
                continue
            for end, row in annual_values(facts[tag]).items():
                if int(end[:4]) >= MIN_YEAR and row["unit"] == "USD":
                    chosen.setdefault(end, (tag, row))

        for end, (tag, row) in chosen.items():
            period_end = date.fromisoformat(end)
            # Manual upsert: the table's unique constraint can't dedupe rows where
            # model_name is NULL (SQL treats NULLs as distinct).
            obs = (session.query(Observation)
                   .filter_by(company_id=company.id, metric_id=metric_ids[metric_key],
                              period_end=period_end, period_type="annual",
                              data_type="reported")
                   .one_or_none())
            if obs is None:
                obs = Observation(company_id=company.id, metric_id=metric_ids[metric_key],
                                  period_end=period_end, period_type="annual",
                                  data_type="reported")
                session.add(obs)
            accn = row["accn"].replace("-", "")
            obs.value = row["val"]
            obs.source = f"SEC 10-K filed {row['filed']}, us-gaap:{tag}"
            obs.source_url = (f"https://www.sec.gov/Archives/edgar/data/"
                              f"{int(company.sec_cik)}/{accn}/")
        counts[metric_key] = len(chosen)
    return counts


def report():
    df = pd.read_sql(
        """SELECT c.ticker, m.key AS metric, o.period_end, o.value
           FROM observations o
           JOIN companies c ON c.id = o.company_id
           JOIN metric_definitions m ON m.id = o.metric_id
           WHERE o.data_type = 'reported'""", engine)
    df["year"] = pd.to_datetime(df["period_end"]).dt.year
    df = df[df["year"] >= 2019]
    df["billions"] = (df["value"] / 1e9).round(2)
    for ticker, g in df.groupby("ticker"):
        print(f"\n=== {ticker} ($B) ===")
        print(g.pivot(index="metric", columns="year", values="billions").to_string())


def main():
    with SessionLocal() as s:
        metric_ids = {m.key: m.id for m in s.query(MetricDefinition).all()}
        for company in s.query(Company).all():
            counts = load_company(s, company, metric_ids)
            print(f"{company.ticker}: {counts}")
        s.commit()
    report()


if __name__ == "__main__":
    main()