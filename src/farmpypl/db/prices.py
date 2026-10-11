"""Read-only access to the prices (prices.db: CSO, Eurostat, EU Oil Bulletin)."""

import sqlite3

from farmpypl.common.constants import PRICE_ITEMS
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
