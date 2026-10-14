"""IncomeCalculator on a made-up farm (Workbook F). No fixture: farm.csv is git-ignored."""

from contextlib import closing

import pytest

from farmpypl.calculators import IncomeCalculator
from farmpypl.common.constants import INCOME_LINES
from farmpypl.db import connect, load_benchmark
from farmpypl.farms import DairyFarm

PRICES = {"milk": 0.50}
LU = 120.0


@pytest.fixture(scope="module")
def benchmark():
    with closing(connect("nfs.db")) as con:
        return load_benchmark(con, "dairy")


def made_up_farm(**given) -> DairyFarm:
    """A 90-cow, 60 ha farm with every optional field blank unless given."""
    return DairyFarm(farm_name="Test", farm_type="dairy", uaa_ha=60, grassland_ha=60,
                     tillage_ha=0, dairy_cows=90, yield_per_cow_l=6000, **given)


def by_line(calc):
    return {line.line: line for line in calc.lines()}


def test_four_lines_in_order(benchmark):
    lines = IncomeCalculator(made_up_farm(), LU, benchmark, PRICES).lines()
    assert [line.line for line in lines] == list(INCOME_LINES)


def test_milk_is_litres_times_price(benchmark):
    milk = by_line(IncomeCalculator(made_up_farm(), LU, benchmark, PRICES))["milk"]
    assert milk.volume == 90 * 6000
    assert milk.eur == pytest.approx(90 * 6000 * 0.50)
    assert (milk.unit, milk.source) == ("L", "farmer")


def test_default_output_adds_up_to_nfs(benchmark):
    """Livestock + other = (total livestock & crops - milk) per LU x LU."""
    calc = IncomeCalculator(made_up_farm(), LU, benchmark, PRICES)
    lines = by_line(calc)
    rate = calc.rate_per_lu
    assert lines["livestock"].eur + lines["other"].eur == pytest.approx(
        (rate["output_total_eur"] - rate["milk_eur"]) * LU)
    assert all(lines[k].source == "default" for k in ("livestock", "subsidies", "other"))


def test_subsidies_default_is_per_hectare(benchmark):
    """Twice the land, twice the payments; the herd size doesn't matter."""
    small = by_line(IncomeCalculator(made_up_farm(), LU, benchmark, PRICES))["subsidies"]
    big = DairyFarm(farm_name="Big", farm_type="dairy", uaa_ha=120, grassland_ha=120,
                    tillage_ha=0, dairy_cows=90, yield_per_cow_l=6000)
    large = by_line(IncomeCalculator(big, LU, benchmark, PRICES))["subsidies"]
    assert large.eur == pytest.approx(2 * small.eur)
    assert small.eur == pytest.approx(benchmark["subsidies_eur"] / benchmark["uaa_ha"] * 60)


def test_farmer_euros_replace_the_default(benchmark):
    farm = made_up_farm(livestock_eur=40000, subsidies_eur=0, other_income_eur=500)
    lines = by_line(IncomeCalculator(farm, LU, benchmark, PRICES))
    assert (lines["livestock"].eur, lines["livestock"].source) == (40000, "farmer")
    assert (lines["subsidies"].eur, lines["subsidies"].source) == (0, "farmer")   # 0 is an answer
    assert (lines["other"].eur, lines["other"].source) == (500, "farmer")
