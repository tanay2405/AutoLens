import pytest
from app.analytics.scenarios import Assumptions, Scenario, run

# Costs = 95B. Defaults: 80% variable, 50% materials, 0% pass-through.
BASE = {"revenue": 100e9, "operating_income": 5e9, "capex": 4e9}


def test_no_shock_returns_baseline():
    r = run(BASE, Scenario())
    assert r["revenue"] == pytest.approx(100e9)
    assert r["operating_income"] == pytest.approx(5e9)


def test_volume_drop_exact_numbers_and_operating_leverage():
    # revenue 90; fixed 19 + variable 95*0.8*0.9 = 68.4 -> costs 87.4 -> income 2.6
    r = run(BASE, Scenario(volume_change=-0.10))
    assert r["operating_income"] == pytest.approx(2.6e9)
    assert (r["operating_income"] - 5e9) / 5e9 < -0.10  # profit falls faster than volume


@pytest.mark.parametrize("passthrough, expected", [(0.0, 0.25e9), (0.5, 2.625e9), (1.0, 5e9)])
def test_material_increase_and_price_passthrough(passthrough, expected):
    # materials = 47.5B, +10% = 4.75B extra cost; pass-through recovers that share via price
    r = run(BASE, Scenario(material_cost_change=0.10), Assumptions(price_passthrough=passthrough))
    assert r["operating_income"] == pytest.approx(expected)


def test_capex_changes_income_after_capex_not_operating_income():
    r = run(BASE, Scenario(capex_change=0.50))
    assert r["operating_income"] == pytest.approx(5e9)
    assert r["income_after_capex"] == pytest.approx(-1e9)