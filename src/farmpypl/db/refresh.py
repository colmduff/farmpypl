"""Fetch the latest prices from their publishers into prices.db.

This is the only module in farmpypl that touches the network, and it only runs
when someone calls ``refresh_prices()``. Calculations never fetch: they read
whichever prices.db ``connect`` finds (decision 19).

Sources, each a function returning rows in the ``prices`` table's shape:

  CSO AJM08 / AJM09 / AJM10 / AHM05
      CSO PxStat API, monthly: feed, fertiliser, milk (EUR) and the
      agricultural price index. JSON-stat.
  Eurostat electricity
      nrg_pc_205, non-household band IA (< 20 MWh a year), Ireland,
      all taxes, half-yearly. JSON-stat.
  Oil Bulletin diesel
      European Commission Weekly Oil Bulletin history workbook, Ireland,
      prices with taxes: heating gas oil (~ green diesel) and road diesel.
      An .xlsx, so this one needs ``openpyxl`` (``pip install farmpypl[refresh]``).

The same code fills the project copy: ``etl/prices.py`` calls
``refresh_prices(path)`` with ``.data/db/prices.db``.
"""

import io
import json
import shutil
import sqlite3
import urllib.request
import warnings
from datetime import datetime, timezone
from functools import partial
from pathlib import Path

from farmpypl.db.connect import bundled_path, user_data_dir

SCHEMA = """
CREATE TABLE IF NOT EXISTS prices (
    series_id   TEXT NOT NULL,      -- 'AJM09', 'EUROSTAT_NRG_PC_205', 'EU_WOB'
    series_name TEXT NOT NULL,
    item        TEXT NOT NULL,      -- what is priced, as the publisher names it
    period      TEXT NOT NULL,      -- the publisher's label: '2026 July', '2026-S1', '2026-10-05'
    period_date TEXT NOT NULL,      -- ISO date of the period start, for ordering
    value       REAL,
    unit        TEXT NOT NULL,      -- 'EUR/tonne', 'EUR/kWh', 'EUR/litre', 'index_2020=100'
    kind        TEXT NOT NULL,      -- 'actual' | 'index'
    fetched_at  TEXT NOT NULL,      -- UTC timestamp of the refresh that wrote the row
    PRIMARY KEY (series_id, item, period)
);
CREATE INDEX IF NOT EXISTS ix_prices_item ON prices(item, period_date);

CREATE VIEW IF NOT EXISTS prices_latest AS
    SELECT p.* FROM prices p
    JOIN (SELECT series_id, item, MAX(period_date) AS d
          FROM prices GROUP BY series_id, item) m
      ON p.series_id = m.series_id AND p.item = m.item AND p.period_date = m.d;

CREATE TABLE IF NOT EXISTS refresh_log (
    attempted_at TEXT NOT NULL,     -- UTC timestamp
    ok           INTEGER NOT NULL,  -- 1 if this source was fetched
    n_rows       INTEGER NOT NULL,
    message      TEXT               -- 'CSO AJM09: ok' or the error
);
"""

USER_AGENT = {"User-Agent": "farmpypl"}


def _get(url: str, timeout: int = 120) -> bytes:
    req = urllib.request.Request(url, headers=USER_AGENT)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


# --- CSO ---------------------------------------------------------------------

CSO_API = ("https://ws.cso.ie/public/api.restful/"
           "PxStat.Data.Cube_API.ReadDataset/{code}/JSON-stat/2.0/en")

CSO_SERIES = {
    "AJM08": dict(name="Feed Stuff Price", kind="actual", unit="EUR/tonne"),
    "AJM09": dict(name="Fertiliser Price", kind="actual", unit="EUR/tonne"),
    "AJM10": dict(name="Manufacturing Milk Price", kind="actual", unit="EUR/litre"),
    "AHM05": dict(name="Agricultural Input/Output Price Index",
                  kind="index", unit="index_2020=100"),
}

MONTHS = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"], start=1)}


def cso_period_date(label: str) -> str:
    """'2026 July' -> '2026-07-01'. An annual label ('2025') becomes January."""
    year, *month = label.split()
    return f"{year}-{MONTHS[month[0]] if month else 1:02d}-01"


def fetch_cso(code: str) -> list[dict]:
    """One CSO PxStat table, flattened to one row per (item, month)."""
    d = json.loads(_get(CSO_API.format(code=code), timeout=60))
    d = d.get("result", d)
    ids, sizes, values, dim = d["id"], d["size"], d["value"], d["dimension"]
    tkey = next(k for k in ids if k.startswith("TLIST"))      # the time dimension
    ikey = next(k for k in ids if k not in ("STATISTIC", tkey))  # the item dimension
    periods = list(dim[tkey]["category"]["label"].values())
    items = list(dim[ikey]["category"]["label"].values())
    if "STATISTIC" in ids and sizes[ids.index("STATISTIC")] > 1:
        warnings.warn(f"CSO {code} has several statistics; reading the first")

    meta = CSO_SERIES[code]
    rows = []
    for ti, period in enumerate(periods):
        for ii, item in enumerate(items):
            pos = {tkey: ti, ikey: ii}
            idx = 0
            for key, size in zip(ids, sizes):  # row-major position in the flat value list
                idx = idx * size + pos.get(key, 0)
            value = values[idx] if idx < len(values) else None
            if value is None:
                continue
            rows.append(dict(
                series_id=code, series_name=meta["name"], item=item,
                period=period, period_date=cso_period_date(period),
                value=float(value), unit=meta["unit"], kind=meta["kind"]))
    return rows


# --- Eurostat electricity ----------------------------------------------------

EUROSTAT_URL = (
    "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/nrg_pc_205"
    "?geo=IE&nrg_cons=MWH_LT20&unit=KWH&currency=EUR&tax=I_TAX&lang=EN"
)
ELECTRICITY_ITEM = "Electricity, non-household band IA (<20 MWh), all taxes"
HALF_YEAR_START = {"S1": "01", "S2": "07"}


def fetch_electricity() -> list[dict]:
    """Eurostat JSON-stat: one value per half-year, EUR per kWh."""
    d = json.loads(_get(EUROSTAT_URL))
    if any(s != 1 for s in d["size"][:-1]):  # every dimension but time pinned to one value
        raise ValueError(f"unexpected Eurostat shape {dict(zip(d['id'], d['size']))}")
    label_at = {pos: label for label, pos in d["dimension"]["time"]["category"]["index"].items()}
    rows = []
    for pos, value in d["value"].items():
        label = label_at[int(pos)]                       # '2025-S1'
        year, half = label.split("-")
        rows.append(dict(
            series_id="EUROSTAT_NRG_PC_205", series_name="Eurostat electricity, non-household",
            item=ELECTRICITY_ITEM, period=label,
            period_date=f"{year}-{HALF_YEAR_START[half]}-01",
            value=float(value), unit="EUR/kWh", kind="actual"))
    return rows


# --- EU Weekly Oil Bulletin --------------------------------------------------

# The "price developments 2005 onwards" link on
# https://energy.ec.europa.eu/data-and-analysis/weekly-oil-bulletin_en
WOB_URL = (
    "https://energy.ec.europa.eu/document/download/906e60ca-8b6a-44e7-8589-652854d2fd3f_en"
    "?filename=Weekly_Oil_Bulletin_Prices_History_maticni_4web.xlsx"
)
WOB_ITEMS = {  # column header in sheet "Prices with taxes" -> our item name
    "IE_price_with_tax_heating_oil": "Heating gas oil (Ireland), with taxes",
    "IE_price_with_tax_diesel": "Automotive gas oil (Ireland), with taxes",
}


def fetch_diesel() -> list[dict]:
    """Oil Bulletin history workbook: Irish prices per 1000 L -> EUR per litre."""
    import openpyxl  # optional: only refreshing needs it, so it's imported here

    wb = openpyxl.load_workbook(io.BytesIO(_get(WOB_URL)), read_only=True, data_only=True)
    sheet = wb["Prices with taxes"].iter_rows(values_only=True)
    header = next(sheet)
    next(sheet), next(sheet)                             # long product names; units
    cols = {header.index(col): item for col, item in WOB_ITEMS.items()}
    rows = []
    for r in sheet:
        if not hasattr(r[0], "year"):                    # notes and blank lines
            continue
        day = r[0].date().isoformat()
        for col, item in cols.items():
            if r[col] is not None:
                rows.append(dict(
                    series_id="EU_WOB", series_name="EU Weekly Oil Bulletin",
                    item=item, period=day, period_date=day,
                    value=float(r[col]) / 1000, unit="EUR/litre", kind="actual"))
    return rows


SOURCES = {
    **{f"CSO {code}": partial(fetch_cso, code) for code in CSO_SERIES},
    "Eurostat electricity": fetch_electricity,
    "Oil Bulletin diesel": fetch_diesel,
}

# What a failed fetch can raise: network (URLError and timeouts are OSErrors),
# a changed format (KeyError, ValueError, IndexError, StopIteration), or openpyxl
# not installed (ImportError). Anything else is a bug and should be loud.
FETCH_ERRORS = (OSError, ValueError, KeyError, IndexError, StopIteration, ImportError)

INSERT = (
    "INSERT OR REPLACE INTO prices (series_id, series_name, item, period, period_date,"
    " value, unit, kind, fetched_at) VALUES (:series_id, :series_name, :item, :period,"
    " :period_date, :value, :unit, :kind, :fetched_at)"
)


def _seed(path: Path) -> None:
    """Start a new prices.db from the bundled snapshot, so a source that fails still has rows."""
    path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(bundled_path("prices.db"), path)


def refresh_prices(path: str | Path | None = None, sources: dict | None = None) -> list[dict]:
    """Fetch every source and write its rows into prices.db.

    Args:
        path: the file to write. Default: ``prices.db`` in the user data folder,
            which ``connect`` then prefers over the bundled snapshot.
        sources: name -> fetch function; default all of ``SOURCES``.

    Returns:
        One dict per source: ``source``, ``ok``, ``n_rows``, ``latest`` (newest
        period_date fetched) and ``error``. A failed source keeps the rows it
        already had, so a refresh can only add or update prices, never lose them.
    """
    path = Path(path) if path else user_data_dir() / "prices.db"
    if not path.exists():
        _seed(path)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    report = []
    con = sqlite3.connect(path)
    try:
        con.executescript(SCHEMA)
        for name, fetch in (sources or SOURCES).items():
            try:
                rows = fetch()
                if not rows:
                    raise ValueError("no rows returned")
            except FETCH_ERRORS as e:
                result = dict(source=name, ok=False, n_rows=0, latest=None,
                              error=f"{type(e).__name__}: {e}")
            else:
                with con:  # one transaction per source: all its rows, or none
                    con.executemany(INSERT, [{**r, "fetched_at": now} for r in rows])
                result = dict(source=name, ok=True, n_rows=len(rows),
                              latest=max(r["period_date"] for r in rows), error=None)
            with con:
                con.execute(
                    "INSERT INTO refresh_log (attempted_at, ok, n_rows, message) VALUES (?, ?, ?, ?)",
                    (now, int(result["ok"]), result["n_rows"],
                     f"{name}: {'ok' if result['ok'] else result['error']}"))
            report.append(result)
    finally:
        con.close()
    return report


def main() -> None:
    """``farmpypl-refresh``: refresh the user copy and print one line per source.

    The command prints; the library functions never do (decision 11).
    """
    report = refresh_prices()
    for r in report:
        if r["ok"]:
            print(f"ok    {r['source']:<22} {r['n_rows']:>5} rows, newest {r['latest']}")
        else:
            print(f"FAIL  {r['source']:<22} {r['error']} (kept its cached rows)")
    print(f"wrote {user_data_dir() / 'prices.db'}")
    raise SystemExit(0 if any(r["ok"] for r in report) else 1)
