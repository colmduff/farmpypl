#!/usr/bin/env python3
"""Live input and output prices from the CSO PxStat API, cached into SQLite.

Why this exists: the NFS gives a complete, authoritative cost structure, but it
is an annual average published months in arrears. For inputs that move slowly
that is fine. For fertiliser and diesel it is not — measured over 2020-2026,
fertiliser has swung 3.0x and motor fuel 2.3x, and by July 2026 both sat far
above their 2025 annual averages.

So we use two mechanisms:

  ACTUAL    Where CSO publishes a real price (fertiliser and feed in EUR/tonne,
            milk in EUR/litre), use it directly. No escalation needed.

  ESCALATE  Where CSO publishes only an index (motor fuel, electricity,
            veterinary), take the absolute anchor from NFS and scale it by
            latest_index / nfs_year_average_index.

Every figure carries its period and source so nothing stale can masquerade as
current. If the API is unreachable the cache is used, and if the cache is empty
the caller is told to fall back to NFS rather than being handed a silent guess.

Prices live in their own file, .data/db/cso.db, separate from the NFS
benchmarks in nfs.db: the two are refreshed in different ways (API vs PDF).
Every refresh attempt is recorded in `refresh_log`, including failures, so a
caller can avoid re-hitting the API when nothing new has been published.

Usage:
    python etl/prices.py --refresh        # pull from CSO into the cache
    python etl/prices.py --show           # print current prices and escalators
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import statistics
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

# TODO(iteration 1, last step): copied verbatim from etl/prices.py. ROOT is
# wrong here (it resolves to src/), so refresh() would write into the package.
# Rewrite to write to the platformdirs user folder (architecture decision 4).
# Nothing imports this module until then.
ROOT = Path(__file__).resolve().parent.parent
CSO_DB = ROOT / ".data" / "db" / "cso.db"
NFS_DB = ROOT / ".data" / "db" / "nfs.db"

API = ("https://ws.cso.ie/public/api.restful/"
       "PxStat.Data.Cube_API.ReadDataset/{code}/JSON-stat/2.0/en")

# CSO tables we rely on. `kind` decides whether a value is a price or an index.
SERIES = {
    "AJM09": dict(name="Fertiliser Price", kind="actual", unit="EUR/tonne"),
    "AJM08": dict(name="Feed Stuff Price", kind="actual", unit="EUR/tonne"),
    "AJM10": dict(name="Manufacturing Milk Price", kind="actual", unit="EUR/litre"),
    "AHM05": dict(name="Agricultural Input/Output Price Index",
                  kind="index", unit="index_2020=100"),
}

# Inputs with no published absolute price: anchor on NFS, escalate by index.
ESCALATED = {
    "Motor fuel":          ("of which Fuel & Lub", "AHM05"),
    "Electricity":         ("Car, Electricity, Phone", "AHM05"),
    "Veterinary expenses": ("Livestock (A.I. Vet etc.)", "AHM05"),
}

MONTHS = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"], start=1)}

SCHEMA = """
CREATE TABLE IF NOT EXISTS prices (
    series_id   TEXT NOT NULL,
    series_name TEXT NOT NULL,
    item        TEXT NOT NULL,
    period      TEXT NOT NULL,      -- '2026 July' as CSO labels it
    period_date TEXT NOT NULL,      -- '2026-07-01', for ordering
    value       REAL,
    unit        TEXT NOT NULL,
    kind        TEXT NOT NULL,      -- 'actual' | 'index'
    fetched_at  TEXT NOT NULL,
    PRIMARY KEY (series_id, item, period)
);
CREATE INDEX IF NOT EXISTS ix_prices_item ON prices(item, period_date);

CREATE VIEW IF NOT EXISTS prices_latest AS
    SELECT p.* FROM prices p
    JOIN (SELECT series_id, item, MAX(period_date) AS d
          FROM prices GROUP BY series_id, item) m
      ON p.series_id = m.series_id AND p.item = m.item AND p.period_date = m.d;

CREATE TABLE IF NOT EXISTS refresh_log (
    attempted_at TEXT NOT NULL,     -- UTC ISO timestamp
    ok           INTEGER NOT NULL,  -- 1 if at least one series was fetched
    n_rows       INTEGER NOT NULL,
    message      TEXT
);
"""


def period_to_date(label: str) -> str:
    """'2026 July' -> '2026-07-01'. Annual labels fall back to January."""
    parts = label.split()
    year = parts[0]
    month = MONTHS.get(parts[1], 1) if len(parts) > 1 else 1
    return f"{year}-{month:02d}-01"


@dataclass(frozen=True)
class Reading:
    item: str
    value: float
    period: str
    unit: str
    source: str


def fetch(code: str, timeout: int = 40) -> list[dict]:
    """Pull one PxStat cube and flatten it to rows."""
    with urllib.request.urlopen(API.format(code=code), timeout=timeout) as r:
        raw = json.loads(r.read().decode("utf-8"))
    d = raw.get("result", raw)
    ids, sizes, values = d["id"], d["size"], d["value"]
    dim = d["dimension"]
    tkey = next(k for k in ids if k.startswith("TLIST"))
    ikey = next(k for k in ids if k not in ("STATISTIC", tkey))
    periods = list(dim[tkey]["category"]["label"].values())
    items = list(dim[ikey]["category"]["label"].values())
    n_stat = sizes[ids.index("STATISTIC")] if "STATISTIC" in ids else 1

    meta = SERIES[code]
    out = []
    for ti, period in enumerate(periods):
        for ii, item in enumerate(items):
            pos = {"STATISTIC": 0, tkey: ti, ikey: ii}
            idx = 0
            for key, size in zip(ids, sizes):
                idx = idx * size + pos.get(key, 0)
            val = values[idx] if idx < len(values) else None
            if val is None:
                continue
            out.append(dict(
                series_id=code, series_name=meta["name"], item=item,
                period=period, period_date=period_to_date(period),
                value=float(val), unit=meta["unit"], kind=meta["kind"],
            ))
    if n_stat > 1:  # defensive: we only read the first statistic
        print(f"  note: {code} has {n_stat} statistics; using the first",
              file=sys.stderr)
    return out


def refresh(db: Path = CSO_DB) -> int:
    db.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db)
    con.executescript(SCHEMA)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    total = 0
    failed = []
    for code in SERIES:
        try:
            rows = fetch(code)
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            print(f"  {code}: unreachable ({e}) — keeping cached rows")
            failed.append(code)
            continue
        for r in rows:
            r["fetched_at"] = now
        con.executemany(
            "INSERT OR REPLACE INTO prices (series_id,series_name,item,period,"
            "period_date,value,unit,kind,fetched_at) VALUES (:series_id,"
            ":series_name,:item,:period,:period_date,:value,:unit,:kind,"
            ":fetched_at)", rows)
        latest = max(r["period_date"] for r in rows)
        print(f"  {code}: {len(rows):>6} rows, latest {latest}")
        total += len(rows)
    con.execute(
        "INSERT INTO refresh_log (attempted_at, ok, n_rows, message) "
        "VALUES (?, ?, ?, ?)",
        (now, int(total > 0), total,
         f"unreachable: {', '.join(failed)}" if failed else None))
    con.commit()
    con.close()
    return total


def latest(con: sqlite3.Connection, item: str) -> Reading | None:
    row = con.execute(
        "SELECT item, value, period, unit, series_id FROM prices_latest "
        "WHERE item = ?", (item,)).fetchone()
    return Reading(*row) if row else None


def escalator(con: sqlite3.Connection, index_item: str, base_year: int) -> float | None:
    """latest index / mean index over base_year. None if either is missing."""
    base = [r[0] for r in con.execute(
        "SELECT value FROM prices WHERE item=? AND kind='index' "
        "AND period_date LIKE ?", (index_item, f"{base_year}-%"))]
    tip = latest(con, index_item)
    if not base or tip is None:
        return None
    return tip.value / statistics.mean(base)


def nfs_value(con: sqlite3.Connection, line_item: str,
              category: str = "Dairying") -> float | None:
    """Read an NFS anchor. Needs nfs.db attached to `con` as `nfs`."""
    row = con.execute(
        "SELECT value FROM nfs.observations WHERE line_item=? AND category=? "
        "AND breakdown='system' LIMIT 1", (line_item, category)).fetchone()
    return row[0] if row else None


def show(db: Path = CSO_DB, nfs_db: Path = NFS_DB,
         base_year: int = 2025) -> None:
    con = sqlite3.connect(db)
    con.execute("ATTACH DATABASE ? AS nfs", (str(nfs_db),))
    print("\nACTUAL PRICES — used directly, no escalation\n")
    for item in ["Calcium Ammonium Nitrate (27.5% N)", "Urea (46% N)",
                 "Ammonium Sulphate Nitrate (26%)",
                 "Milk (per litre), actual fat and protein",
                 "Milk (per litre), 3.6% fat and 3.3% protein"]:
        r = latest(con, item)
        if r:
            print(f"  {r.item:<46}{r.value:>9,.2f}  {r.unit:<12}{r.period}")

    print(f"\nESCALATED — NFS {base_year} anchor x live index\n")
    print(f"  {'input':<24}{'NFS €':>10}{'index':>9}{'x':>8}{'current €':>12}  period")
    for index_item, (nfs_item, _code) in ESCALATED.items():
        anchor = nfs_value(con, nfs_item)
        mult = escalator(con, index_item, base_year)
        tip = latest(con, index_item)
        if anchor is None or mult is None:
            print(f"  {index_item:<24}{'—':>10}{'—':>9}{'—':>8}"
                  f"{'fall back to NFS':>12}")
            continue
        print(f"  {index_item:<24}{anchor:>10,.0f}{tip.value:>9.1f}"
              f"{mult:>8.3f}{anchor*mult:>12,.0f}  {tip.period}")
    print("\n  (NFS anchors are whole-farm annual spend for the average dairy farm)")
    con.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--refresh", action="store_true", help="pull from CSO")
    ap.add_argument("--show", action="store_true", help="print current prices")
    a = ap.parse_args()
    if not (a.refresh or a.show):
        ap.error("pass --refresh and/or --show")
    if a.refresh:
        print("Refreshing CSO PxStat series")
        refresh()
    if a.show:
        show()
