"""refresh_prices() and the user-copy switch in connect(), without the network.

The fetchers are replaced by tiny fakes, and XDG_DATA_HOME points at a
temporary folder, so these tests never touch the internet or your real
~/.local/share/farmpypl.
"""

import sqlite3
import urllib.error

import pytest

from farmpypl.common.constants import PRICE_ITEMS
from farmpypl.db import connect, database_path, price_status, refresh_prices, user_data_dir
from farmpypl.db.connect import bundled_path


@pytest.fixture(autouse=True)
def user_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    return tmp_path / "farmpypl"


def fake_rows(item="Test item", day="2099-01-01", value=1.0):
    return [dict(series_id="TEST", series_name="Test", item=item, period=day,
                 period_date=day, value=value, unit="EUR/test", kind="actual")]


def unreachable():
    raise urllib.error.URLError("no network in tests")


def count(path, item):
    with sqlite3.connect(path) as con:
        return con.execute("SELECT COUNT(*) FROM prices WHERE item = ?", (item,)).fetchone()[0]


def test_connect_uses_bundle_until_refreshed(user_dir):
    assert database_path("prices.db") == bundled_path("prices.db")
    refresh_prices(sources={"fake": fake_rows})
    assert database_path("prices.db") == user_dir / "prices.db"


def test_failed_refresh_does_not_shadow_the_bundle(user_dir):
    # Every source down: the seeded user copy holds nothing newer, so stay on the bundle.
    refresh_prices(sources={"fake": unreachable})
    assert (user_dir / "prices.db").exists()
    assert database_path("prices.db") == bundled_path("prices.db")


def test_newer_bundle_wins_over_an_old_refresh(user_dir):
    # As after upgrading farmpypl: the user copy was fetched before the shipped snapshot.
    refresh_prices(sources={"fake": fake_rows})
    with sqlite3.connect(user_dir / "prices.db") as con:
        con.execute("UPDATE prices SET fetched_at = '2000-01-01T00:00:00+00:00'")
    assert database_path("prices.db") == bundled_path("prices.db")


def test_nfs_is_always_bundled(user_dir):
    user_dir.mkdir(parents=True)
    (user_dir / "nfs.db").write_bytes(b"")
    assert database_path("nfs.db") == bundled_path("nfs.db")


def test_first_refresh_seeds_from_bundle_then_adds(user_dir):
    report = refresh_prices(sources={"fake": fake_rows})
    path = user_dir / "prices.db"
    assert report == [dict(source="fake", ok=True, n_rows=1, latest="2099-01-01", error=None)]
    assert count(path, "Test item") == 1
    for item in PRICE_ITEMS.values():          # the bundled rows came along
        assert count(path, item) > 0


def test_failed_source_keeps_its_rows_and_is_logged(user_dir):
    refresh_prices(sources={"fake": fake_rows})
    report = refresh_prices(sources={"fake": unreachable})
    assert report[0]["ok"] is False and "URLError" in report[0]["error"]
    path = user_dir / "prices.db"
    assert count(path, "Test item") == 1       # still there
    with sqlite3.connect(path) as con:
        log = con.execute("SELECT ok, message FROM refresh_log ORDER BY rowid").fetchall()
    assert log[-2:] == [(1, "fake: ok"), (0, "fake: URLError: <urlopen error no network in tests>")]


def test_one_failure_does_not_stop_the_others(user_dir):
    report = refresh_prices(sources={"down": unreachable, "up": fake_rows})
    assert [r["ok"] for r in report] == [False, True]


def test_refresh_updates_a_value_in_place(user_dir):
    refresh_prices(sources={"fake": fake_rows})
    refresh_prices(sources={"fake": lambda: fake_rows(value=2.0)})
    with sqlite3.connect(user_dir / "prices.db") as con:
        values = con.execute("SELECT value FROM prices WHERE item = 'Test item'").fetchall()
    assert values == [(2.0,)]                   # replaced, not duplicated


def test_explicit_path_leaves_user_folder_alone(tmp_path, user_dir):
    target = tmp_path / "project" / "prices.db"
    refresh_prices(target, sources={"fake": fake_rows})
    assert count(target, "Test item") == 1
    assert not (user_dir / "prices.db").exists()


def test_price_status_names_every_price_and_its_file():
    with connect("prices.db") as con:
        status = price_status(con)
    assert [s["price"] for s in status] == list(PRICE_ITEMS)
    assert all(s["n_obs"] > 0 and s["file"].endswith("prices.db") for s in status)


def test_user_data_dir_follows_xdg(user_dir):
    assert user_data_dir() == user_dir


@pytest.mark.network
def test_live_refresh(user_dir):
    """Real fetch from all six sources. Run with: pytest -m network"""
    pytest.importorskip("openpyxl")
    report = refresh_prices()
    assert all(r["ok"] for r in report), report
