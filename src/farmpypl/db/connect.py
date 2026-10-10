"""Open the bundled databases read-only, and read the bundled SQL."""

import sqlite3
from importlib.resources import files

DATA = files("farmpypl.db") / "data"
QUERIES = files("farmpypl.db") / "queries"


def connect(name: str) -> sqlite3.Connection:
    """Open a bundled database (``"nfs.db"`` or ``"cso.db"``) read-only."""
    con = sqlite3.connect(f"file:{DATA / name}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def sql(name: str) -> str:
    """The text of one bundled query, e.g. ``sql("nfs_line_item.sql")``."""
    return (QUERIES / name).read_text(encoding="utf-8")
