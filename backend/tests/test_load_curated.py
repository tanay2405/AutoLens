from datetime import date
from types import SimpleNamespace

import pytest
from app.ingestion.load_curated import parse_row

COMPANIES = {"TSLA": SimpleNamespace(id=1)}
METRICS = {
    "vehicles_produced": SimpleNamespace(id=7, category="manufacturing"),
    "revenue": SimpleNamespace(id=1, category="financial"),
}
GOOD = {
    "ticker": "TSLA", "metric": "vehicles_produced", "period_end": "2025-12-31",
    "period_type": "annual", "value": "1654667", "data_type": "reported",
    "source": "Tesla Q4 2025 release", "source_url": "https://example.com/x",
}


def test_valid_row_parses():
    comp, metric, end, ptype, value, dtype, source, url = parse_row(GOOD, COMPANIES, METRICS)
    assert comp.id == 1 and metric.id == 7
    assert end == date(2025, 12, 31)
    assert value == 1654667.0 and dtype == "reported"


@pytest.mark.parametrize("field, bad", [
    ("ticker", "XYZ"), ("metric", "revenue"), ("data_type", "forecast"),
    ("source_url", ""), ("source_url", "not-a-link"), ("value", "0"), ("value", "abc"),
])
def test_bad_rows_are_rejected(field, bad):
    with pytest.raises(ValueError):
        parse_row({**GOOD, field: bad}, COMPANIES, METRICS)