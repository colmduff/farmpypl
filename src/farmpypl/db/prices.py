"""Read-only access to the prices (prices.db: CSO, Eurostat, EU Oil Bulletin)."""

import sqlite3
from datetime import datetime, timezone

from farmpypl.common.constants import PRICE_ITEMS, STALE_AFTER_DAYS
from farmpypl.db.connect import sql


def price_12mo(con: sqlite3.Connection, item: str) -> float:
    """Mean of one price series over the 12 months up to its latest observation."""
    row = con.execute(sql("price_12mo.sql"), {"item": item}).fetchone() 
    if row["n_obs"] == 0:                                                      
        raise LookupError(f"no prices for {item!r}")
    return row["mean_value"] 


def load_prices(con: sqlite3.Connection) -> dict[str, float]:
    """Every price the cost calculator needs, keyed by our short name ("concentrates", ...).
    """
    return {name: price_12mo(con, item) for name, item in PRICE_ITEMS.items()}


def price_status(con: sqlite3.Connection) -> list[dict]:
    """Which prices load_prices uses, and how fresh they are.

    One dict per PRICE_ITEMS entry: the 12-month mean, its unit, the window it
    covers, when it was fetched, and which file it came from (the bundled
    snapshot or a refreshed user copy). Advisory only: nothing refreshes itself.
    """
    file = con.execute("PRAGMA database_list").fetchone()["file"]
    status = []
    for name, item in PRICE_ITEMS.items():
        window = con.execute(sql("price_12mo.sql"), {"item": item}).fetchone()
        unit, fetched_at = con.execute(
            "SELECT unit, MAX(fetched_at) FROM prices WHERE item = ?", (item,)).fetchone()
        status.append({
            "price": name,
            "mean_12mo": window["mean_value"],
            "unit": unit,
            "n_obs": window["n_obs"],
            "first_period": window["first_period"],
            "last_period": window["last_period"],
            "fetched_at": fetched_at,
            "file": file,
        })
    return status


def stale_prices(price_info: list[dict], now: datetime | None = None,
                 max_age_days: int = STALE_AFTER_DAYS) -> list[str]:
    """The prices in price_status() output that were fetched more than max_age_days ago.

    Advisory: the caller decides whether to warn. ``now`` is for tests; default is
    the current time. The age is from the fetch, not the period: CSO publishes
    about ten weeks late, so a fresh fetch can still end months back.
    """
    now = now or datetime.now(timezone.utc)
    return [p["price"] for p in price_info
            if (now - datetime.fromisoformat(p["fetched_at"])).days > max_age_days]
