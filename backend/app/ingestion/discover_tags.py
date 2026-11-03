import sys
from app.db import SessionLocal
from app.models import Company
from app.ingestion.sec_client import fetch_company_facts

KEYWORDS = ["revenue", "costof", "operatingincome", "netincome",
            "propertyplant", "capitalexpend"]

def annual_rows(concept: dict):
    rows = []
    for unit_rows in concept.get("units", {}).values():
        for r in unit_rows:
            if r.get("form") == "10-K" and r.get("fp") == "FY" and "start" in r:
                rows.append(r)
    return rows

def main(ticker: str):
    with SessionLocal() as s:
        company = s.query(Company).filter_by(ticker=ticker).one()
    facts = fetch_company_facts(company.sec_cik)["facts"].get("us-gaap", {})
    print(f"\n=== {ticker}: us-gaap tags matching keywords (annual, ending 2023 or later) ===")
    for tag in sorted(facts):
        if not any(k in tag.lower() for k in KEYWORDS):
            continue
        rows = annual_rows(facts[tag])
        if not rows:
            continue
        ends = sorted({r["end"] for r in rows})
        if ends[-1] < "2023":
            continue
        print(f"{tag:70s} years={len(ends):2d}  {ends[0]} -> {ends[-1]}")

if __name__ == "__main__":
    main(sys.argv[1])