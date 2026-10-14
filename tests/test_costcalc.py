"""CostCalculator on a made-up farm (Workbook C). No fixture: farm.csv is git-ignored."""

from contextlib import closing

import pytest

from farmpypl.calculators import CostCalculator
from farmpypl.common.constants import COST_LINES
from farmpypl.db import connect, load_benchmark
from farmpypl.farms import DairyFarm

PRICES = {"concentrates": 400.0, "fertiliser": 450.0, "diesel": 1.0,
          "electricity": 0.30, "road_diesel": 1.6, "milk": 0.45}
LU = 120.0


@pytest.fixture(scope="module")
def benchmark():
    with closing(connect("nfs.db")) as con:
        return load_benchmark(con, "dairy")


def made_up_farm(**given) -> DairyFarm:
    """A 90-cow farm with every optional field blank unless given."""
    return DairyFarm(farm_name="Test", farm_type="dairy", uaa_ha=60, grassland_ha=60,
                     tillage_ha=0, dairy_cows=90, yield_per_cow_l=6000, **given)


def test_nine_lines_in_order(benchmark):
    lines = CostCalculator(made_up_farm(), LU, benchmark, PRICES).lines()
    assert [line.line for line in lines] == list(COST_LINES)
    assert all(line.source == "default" for line in lines)


def test_default_lines_sum_to_nfs_cash_costs(benchmark):
    """Every line blank: the 9 lines add up to (total - depreciation) per LU x LU."""
    calc = CostCalculator(made_up_farm(), LU, benchmark, PRICES)
    total = sum(line.eur for line in calc.lines())
    rate = calc.rate_per_lu
    assert total == pytest.approx((rate["total_costs_eur"] - rate["depreciation_eur"]) * LU)


def test_farmer_euros_replace_the_default(benchmark):
    calc = CostCalculator(made_up_farm(contractor_eur=0, maintenance_eur=5000), LU, benchmark, PRICES)
    by_line = {line.line: line for line in calc.lines()}
    assert (by_line["contractor"].eur, by_line["contractor"].source) == (0, "farmer")   # 0 is an answer
    assert (by_line["maintenance"].eur, by_line["maintenance"].source) == (5000, "farmer")
    assert by_line["animal_health"].source == "default"
