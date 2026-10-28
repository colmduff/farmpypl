"""FarmManager.from_csv: the stale-price warning (Workbook E). Made-up farm, no fixture."""

import pytest

from farmpypl import FarmManager

HEADER = "farm_name,farm_type,uaa_ha,grassland_ha,tillage_ha,dairy_cows,yield_per_cow_l\n"
ROW = "Test Farm,dairy,50,50,0,40,6000\n"


@pytest.fixture
def csv_path(tmp_path):
    path = tmp_path / "farm.csv"
    path.write_text(HEADER + ROW)
    return path


def test_from_csv_warns_when_prices_are_stale(csv_path, monkeypatch):
    # the real answer depends on today's date, so patch it
    monkeypatch.setattr("farmpypl.core.stale_prices", lambda info: ["diesel"])
    with pytest.warns(UserWarning, match="diesel"):
        FarmManager.from_csv(csv_path)


def test_from_csv_is_quiet_when_prices_are_fresh(csv_path, monkeypatch, recwarn):
    monkeypatch.setattr("farmpypl.core.stale_prices", lambda info: [])
    FarmManager.from_csv(csv_path)
    assert not [w for w in recwarn if "prices fetched" in str(w.message)]
