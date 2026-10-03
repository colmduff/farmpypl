"""The data that ships inside the package: two SQLite snapshots and the SQL.

These prove packaging, not calculation. If they fail, the package cannot work
out of the box, whatever the calculators do.
"""

import sqlite3
from importlib.resources import files

import pytest

DATA = files("farmpypl.db") / "data"
QUERIES = files("farmpypl.db") / "queries"

MILK = "Milk (per litre), actual fat and protein"


def open_ro(name):
    return sqlite3.connect(f"file:{DATA / name}?mode=ro", uri=True)


def tables(con):
    return {r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type IN ('table', 'view')")}


def sql(name):
    return (QUERIES / name).read_text()


# --- bundled databases -------------------------------------------------------

def test_nfs_snapshot_has_benchmarks_and_no_prices():
    with open_ro("nfs.db") as con:
        assert {"sources", "observations", "dairy"} <= tables(con)
        assert "prices" not in tables(con)


def test_cso_snapshot_has_prices_and_no_benchmarks():
    with open_ro("cso.db") as con:
        assert {"prices", "prices_latest", "refresh_log"} <= tables(con)
        assert "observations" not in tables(con)


@pytest.mark.parametrize("name", ["nfs.db", "cso.db"])
def test_snapshots_are_not_wal(name):
    # A WAL database cannot be opened from a read-only install directory.
    with open_ro(name) as con:
        assert con.execute("PRAGMA journal_mode").fetchone()[0] != "wal"


def test_read_only_really_is_read_only():
    with open_ro("cso.db") as con, pytest.raises(sqlite3.OperationalError):
        con.execute("DELETE FROM prices")


# --- queries, against a fixture we control -----------------------------------

@pytest.fixture
def prices_db():
    """13 months of milk, Jul 2025 .. Jul 2026, value = month number / 100.

    Labels are CSO-style ('2026 July'). Sorted as text, '2026 May' would be the
    newest, which is the bug the queries must not have.
    """
    con = sqlite3.connect(":memory:")
    con.executescript("""
        CREATE TABLE prices (series_id TEXT, item TEXT, period TEXT,
                             period_date TEXT, value REAL);
        CREATE TABLE refresh_log (attempted_at TEXT, ok INTEGER,
                                  n_rows INTEGER, message TEXT);
    """)
    months = ["January", "February", "March", "April", "May", "June", "July",
              "August", "September", "October", "November", "December"]
    rows = []
    for i in range(13):
        y, m = divmod(6 + i, 12)          # July 2025 is index 6 of 2025
        rows.append(("AJM10", MILK, f"{2025 + y} {months[m]}",
                     f"{2025 + y}-{m + 1:02d}-01", (m + 1) / 100))
    rows.append(("AJM08", "Feed", "2026 May", "2026-05-01", 300.0))
    con.executemany("INSERT INTO prices VALUES (?,?,?,?,?)", rows)
    yield con
    con.close()


def test_milk_12mo_window_ends_at_latest_period_date(prices_db):
    r = prices_db.execute(sql("cso_milk_price_12mo.sql"), {"item": MILK}).fetchone()
    mean, lo, hi, n, first, last, last_date = r
    assert n == 12
    assert (first, last, last_date) == ("2025 August", "2026 July", "2026-07-01")
    # Aug..Dec 2025 = 8..12, Jan..Jul 2026 = 1..7, all /100
    assert mean == pytest.approx((sum(range(8, 13)) + sum(range(1, 8))) / 1200)


def test_milk_12mo_unknown_item_reports_zero_months(prices_db):
    r = prices_db.execute(sql("cso_milk_price_12mo.sql"), {"item": "Nope"}).fetchone()
    assert r[3] == 0 and r[0] is None


def test_newest_month_puts_stalest_series_first(prices_db):
    rows = prices_db.execute(sql("cso_newest_month.sql")).fetchall()
    assert rows[0] == ("AJM08", "2026-05-01", "2026-05-31")
    assert rows[1] == ("AJM10", "2026-07-01", "2026-07-31")


def test_last_attempt_empty_then_newest(prices_db):
    assert prices_db.execute(sql("cso_last_attempt.sql")).fetchall() == []
    prices_db.executemany("INSERT INTO refresh_log VALUES (?,?,?,?)", [
        ("2026-09-01T09:00:00+00:00", 1, 7558, None),
        ("2026-09-20T09:00:00+00:00", 0, 0, "unreachable: AJM10"),
    ])
    assert prices_db.execute(sql("cso_last_attempt.sql")).fetchone()[0] == \
        "2026-09-20T09:00:00+00:00"
