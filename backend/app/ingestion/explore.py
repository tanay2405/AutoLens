import sys
from datetime import date
from app.db import SessionLocal
from app.models import Company
from app.ingestion.sec_client import fetch_company_facts


def load(ticker: str) -> dict:
    with SessionLocal() as s:
        c = s.query(Company).filter_by(ticker=ticker).one()
    return fetch_company_facts(c.sec_cik)["facts"].get("us-gaap", {})


def annual_values(concept: dict) -> dict:
    """One value per fiscal year: full-year duration, 10-K only, latest filing wins."""
    best = {}
    for unit, rows in concept.get("units", {}).items():
        for r in rows:
            if r.get("form") != "10-K" or "start" not in r:
                continue
            days = (date.fromisoformat(r["end"]) - date.fromisoformat(r["start"])).days
            if not 350 <= days <= 380:
                continue
            if r["end"] not in best or r["filed"] > best[r["end"]]["filed"]:
                best[r["end"]] = {**r, "unit": unit}
    return dict(sorted(best.items()))


def search(ticker: str, keywords: list[str]):
    facts = load(ticker)
    print(f"\n=== {ticker}: tags containing {keywords}, with full-year data ending 2024+ ===")
    for tag, concept in sorted(facts.items()):
        if not any(k.lower() in tag.lower() for k in keywords):
            continue
        vals = annual_values(concept)
        if vals and max(vals) >= "2024":
            print(f"{tag:75s} last={max(vals)}  | {concept.get('label', '')}")


def values(ticker: str, tags: list[str]):
    facts = load(ticker)
    for tag in tags:
        print(f"\n--- {ticker} / {tag} ---")
        if tag not in facts:
            print("  (tag not found)")
            continue
        for end, r in list(annual_values(facts[tag]).items())[-6:]:
            print(f"  FY end {end}: {r['val'] / 1e9:>10,.3f} B {r['unit']}   (filed {r['filed']})")


if __name__ == "__main__":
    mode, ticker, args = sys.argv[1], sys.argv[2], sys.argv[3:]
    search(ticker, args) if mode == "search" else values(ticker, args)