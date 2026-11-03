import numpy as np
import pandas as pd
import pytest
from app.analytics.metrics import add_derived


def make_wide():
    idx = pd.MultiIndex.from_tuples(
        [("F", 2024), ("F", 2025), ("TSLA", 2024), ("TSLA", 2025)], names=["ticker", "year"])
    return pd.DataFrame({
        "revenue": [100.0, 110.0, 50.0, 45.0],
        "operating_income": [10.0, 11.0, 5.0, 2.25],
        "net_income": [8.0, 9.0, 4.0, 2.0],
        "capex": [5.0, 6.0, 5.0, 4.5],
        "vehicles_wholesale": [1000.0, 900.0, np.nan, np.nan],
        "vehicles_delivered": [np.nan, np.nan, 200.0, 190.0],
    }, index=idx)


def test_margins_and_derived_total_costs():
    d = add_derived(make_wide())
    assert d.loc[("F", 2025), "operating_margin"] == pytest.approx(0.10)
    assert d.loc[("F", 2025), "total_costs"] == pytest.approx(99.0)


def test_growth_does_not_cross_companies():
    d = add_derived(make_wide())
    assert d.loc[("F", 2025), "revenue_yoy"] == pytest.approx(0.10)
    assert pd.isna(d.loc[("TSLA", 2024), "revenue_yoy"])  # must not compare against Ford 2025


def test_each_company_uses_its_own_volume_metric():
    d = add_derived(make_wide())
    assert d.loc[("F", 2025), "volume_yoy"] == pytest.approx(-0.10)      # wholesale
    assert d.loc[("TSLA", 2025), "volume_yoy"] == pytest.approx(-0.05)   # deliveries