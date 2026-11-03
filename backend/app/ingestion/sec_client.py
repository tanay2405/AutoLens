import json
import time
from pathlib import Path
import requests
import os

BASE = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
CACHE_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "sec"

# The SEC requires a descriptive User-Agent with contact info.
# Set it in your shell: export SEC_USER_AGENT="AutoLens Portfolio Project you@example.com"
def _headers() -> dict:
    ua = os.environ.get("SEC_USER_AGENT")
    if not ua:
        raise RuntimeError(
            'Set SEC_USER_AGENT first, e.g. export SEC_USER_AGENT="AutoLens you@example.com"')
    return {"User-Agent": ua}

def fetch_company_facts(cik: str, refresh: bool = False) -> dict:
    cik = str(cik).zfill(10)
    path = CACHE_DIR / f"CIK{cik}.json"
    if path.exists() and not refresh:
        return json.loads(path.read_text())
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    resp = requests.get(BASE.format(cik=cik), headers=_headers(), timeout=30)
    resp.raise_for_status()
    path.write_text(resp.text)
    time.sleep(0.2)  # stay well under SEC's rate limit
    return resp.json()