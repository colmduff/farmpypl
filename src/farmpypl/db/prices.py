"""Read-only access to the bundled prices (cso.db: CSO, Eurostat, EU Oil Bulletin)."""

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
