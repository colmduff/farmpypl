"""Read-only access to the bundled NFS benchmarks (nfs.db)."""

import sqlite3

from farmpypl.common.constants import NFS_BENCHMARK_ITEMS, NFS_SYSTEM, NFS_YEAR
from farmpypl.db.connect import sql


def nfs_value(con: sqlite3.Connection, category: str, section: str, line_item: str) -> float:
    """One NFS figure for one system, read by its label."""
    params = {"category": category, "year": NFS_YEAR, "section": section, "line_item": line_item}
    rows = con.execute(sql("nfs_line_item.sql"), params).fetchall()
    if len(rows) != 1:
        raise LookupError(f"expected 1 NFS row for {category}/{section}/{line_item}, got {len(rows)}")
    return rows[0]["value"]


def load_benchmark(con: sqlite3.Connection, farm_type: str) -> dict[str, float]:
    """The average NFS farm of this type: costs, livestock units, labour units."""
    category = NFS_SYSTEM[farm_type]
    return {
        name: sum(nfs_value(con, category, section, item) for section, item in items)
        for name, items in NFS_BENCHMARK_ITEMS.items()
    }
