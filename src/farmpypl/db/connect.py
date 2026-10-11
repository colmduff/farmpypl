"""Open the databases read-only, and read the bundled SQL.

Two copies of prices.db can exist:

- the **bundled snapshot** inside the package, which ships with every release,
  is never written to, and works offline on a fresh install;
- a **user copy** in the user data folder, which ``refresh_prices()`` writes.

``connect`` opens whichever of the two holds the more recently fetched prices.
Usually that's the user copy; after an upgrade that ships a newer snapshot, it's
the bundle, so an old refresh can never hide newer data. nfs.db is only ever
bundled: the NFS is a yearly PDF, rebuilt by ``etl/extract_nfs.py``, not refreshed.
"""

import os
import sqlite3
from importlib.resources import files
from pathlib import Path

DATA = files("farmpypl.db") / "data"
QUERIES = files("farmpypl.db") / "queries"

REFRESHABLE = {"prices.db"}


def user_data_dir() -> Path:
    """Where refreshed data lives: ``$XDG_DATA_HOME/farmpypl``, else ``~/.local/share/farmpypl``.

    A function, not a constant, so it reads the environment each time it's
    called (the tests point ``XDG_DATA_HOME`` at a temporary folder).
    """
    base = os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share"
    return Path(base) / "farmpypl"


def bundled_path(name: str) -> Path:
    """The snapshot shipped inside the package."""
    return Path(str(DATA / name))


def newest_fetch(path: Path) -> str:
    """The latest ``fetched_at`` in a prices.db ('' if it has no rows)."""
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        return con.execute("SELECT MAX(fetched_at) FROM prices").fetchone()[0] or ""
    finally:
        con.close()


def database_path(name: str) -> Path:
    """The file ``connect`` will open: the user copy if it is fresher, else the bundled one."""
    bundled = bundled_path(name)
    if name in REFRESHABLE:
        user = user_data_dir() / name
        if user.exists() and newest_fetch(user) > newest_fetch(bundled):
            return user
    return bundled


def connect(name: str) -> sqlite3.Connection:
    """Open ``"nfs.db"`` or ``"prices.db"`` read-only, rows readable by column name."""
    con = sqlite3.connect(f"file:{database_path(name)}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def sql(name: str) -> str:
    """The text of one bundled query, e.g. ``sql("nfs_line_item.sql")``."""
    return (QUERIES / name).read_text(encoding="utf-8")
