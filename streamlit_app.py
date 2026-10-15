"""Streamlit front end for farmpypl.

Run from the repository root:
    pip install streamlit openpyxl
    streamlit run streamlit_app.py
"""

import io
import sys
import tempfile
import zipfile
from contextlib import closing
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

# Use the package from ./src without needing `pip install -e .`
SRC = Path(__file__).resolve().parent / "src"
if SRC.exists() and str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import farmpypl as fpl  # noqa: E402
from farmpypl.common.constants import (  # noqa: E402
    FARM_TYPES, LU_COEFF, PRICE_ITEMS, SR_BANDS, STALE_AFTER_DAYS,
)
from farmpypl.db import connect, database_path, stale_prices, user_data_dir  # noqa: E402
from farmpypl.db.connect import bundled_path  # noqa: E402
from farmpypl.loaders.csv_loader import CSVLoadingError  # noqa: E402

st.set_page_config(page_title="farmpypl", page_icon="🐄", layout="wide")

# --------------------------------------------------------------------------- #
# Input schema (mirrors FarmProfileInput)
# --------------------------------------------------------------------------- #
# Read the accepted columns from the installed farmpypl, so the app sends only
# fields this version of FarmProfileInput knows about (it forbids extra columns).
from farmpypl.data_validation import FarmProfileInput  # noqa: E402

_FIELDS = FarmProfileInput.model_fields
REQUIRED = [n for n, f in _FIELDS.items() if f.is_required()]
OPTIONAL = [n for n, f in _FIELDS.items() if not f.is_required()]
COLUMNS = REQUIRED + OPTIONAL

HELP = {
    "farm_name": "Name of the farm",
    "farm_type": "NFS farm system",
    "uaa_ha": "Utilised agricultural area, ha",
    "grassland_ha": "Grassland, ha (grassland + tillage ≤ UAA)",
    "tillage_ha": "Tillage, ha",
    "dairy_cows": "Adult dairy cows, head",
    "yield_per_cow_l": "Milk yield, litres per cow per year",
    "concentrate_per_cow_kg": "Concentrate fed, kg per cow per year (blank = NFS average)",
    "fertilizer_per_hectare_kg": "Fertiliser, kg N per ha of grassland (blank = NFS average)",
    "diesel_liters": "Diesel, litres per year (blank = NFS average)",
    "electricity_kwh": "Electricity, kWh per year (blank = NFS average)",
    "contractor_eur": "Contractor, € per year (blank = NFS average)",
    "animal_health_eur": "Vet, medicines, A.I., € per year (blank = NFS average)",
    "repairs_eur": "Buildings and land upkeep, € per year (blank = NFS average)",
    "organic_feed_eur": "Organic feed, € per year (blank = NFS average)",
}

EXAMPLE = pd.DataFrame([{
    "farm_name": "Example farm", "farm_type": "dairy", "uaa_ha": 100.0,
    "grassland_ha": 95.0, "tillage_ha": 5.0, "dairy_cows": 100,
    "yield_per_cow_l": 5500.0, "diesel_liters": 6000.0,
}]).reindex(columns=COLUMNS)


def blank_template() -> str:
    return EXAMPLE.to_csv(index=False)


# --------------------------------------------------------------------------- #
# Running the model
# --------------------------------------------------------------------------- #
def df_to_csv_text(df: pd.DataFrame) -> str:
    """Turn the editor table into the CSV text farmpypl expects (blank = NFS average)."""
    df = df.copy()
    df = df.dropna(how="all")
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = None
    df = df[COLUMNS]
    if "dairy_cows" in df:
        df["dairy_cows"] = df["dairy_cows"].map(
            lambda v: "" if pd.isna(v) else str(int(float(v))))
    return df.to_csv(index=False, na_rep="")


@st.cache_data(show_spinner="Running farmpypl…")
def run_model(csv_text: str, prices_file: str, prices_mtime: float):
    """Load farms through the real FarmManager.from_csv route and return every output.

    prices_file / prices_mtime are only cache keys, so a price refresh re-runs the model.
    """
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "farms.csv"
        path.write_text(csv_text, encoding="utf-8")
        manager = fpl.FarmManager.from_csv(path)
    return {
        "farm": manager.farm_summary(),
        "herd": manager.herd_summary(),
        "cohorts": manager.herd_cohorts(),
        "costs": manager.costs(),
        "prices": manager.price_summary(),
        "price_info": manager.price_info,
        "benchmarks": manager.benchmarks,
    }


def prices_key() -> tuple[str, float]:
    p = database_path("prices.db")
    return str(p), p.stat().st_mtime


def eur(x: float) -> str:
    return f"€{x:,.0f}"


# --------------------------------------------------------------------------- #
# Sidebar: farm input
# --------------------------------------------------------------------------- #
st.sidebar.title("🐄 farmpypl")
st.sidebar.caption("Irish dairy farm cost calculator"
                   + (f" · v{fpl.__version__}" if fpl.__version__ != "unknown" else ""))

with st.sidebar.form("farm_form"):
    st.markdown("**Required**")
    name = st.text_input("Farm name", "My farm", help=HELP["farm_name"])
    ftype = st.selectbox("Farm type", FARM_TYPES, index=FARM_TYPES.index("dairy"),
                         help=HELP["farm_type"])
    uaa = st.number_input("UAA (ha)", 0.1, 1000.0, 100.0, help=HELP["uaa_ha"])
    grass = st.number_input("Grassland (ha)", 0.1, 1000.0, 95.0, help=HELP["grassland_ha"])
    till = st.number_input("Tillage (ha)", 0.0, 1000.0, 5.0, help=HELP["tillage_ha"])
    cows = st.number_input("Dairy cows", 0, 5000, 100, help=HELP["dairy_cows"])
    yld = st.number_input("Yield per cow (L/yr)", 1.0, 15000.0, 5500.0,
                          help=HELP["yield_per_cow_l"])
    st.markdown("**Optional** — tick to enter your own figure, "
                "otherwise the NFS average is used")
    opt_vals = {}
    defaults = {"concentrate_per_cow_kg": 1000.0, "fertilizer_per_hectare_kg": 170.0,
                "diesel_liters": 6000.0, "electricity_kwh": 40000.0,
                "contractor_eur": 20000.0, "animal_health_eur": 15000.0,
                "repairs_eur": 8000.0, "organic_feed_eur": 0.0}
    maxes = {"concentrate_per_cow_kg": 5000.0, "fertilizer_per_hectare_kg": 400.0}
    for col in OPTIONAL:
        c1, c2 = st.columns([1, 2])
        use = c1.checkbox("use", key=f"use_{col}", value=(col == "diesel_liters"))
        val = c2.number_input(col, 0.0, maxes.get(col, 1e9), defaults.get(col, 0.0),
                              help=HELP.get(col), key=f"val_{col}")
        opt_vals[col] = val if use else None
    submitted = st.form_submit_button("Calculate", width="stretch")
row = {"farm_name": name, "farm_type": ftype, "uaa_ha": uaa, "grassland_ha": grass,
       "tillage_ha": till, "dairy_cows": cows, "yield_per_cow_l": yld, **opt_vals}
csv_text = df_to_csv_text(pd.DataFrame([row]))

# --------------------------------------------------------------------------- #
# Main page
# --------------------------------------------------------------------------- #
st.title("Farm income & cost calculator")
st.caption("Describe a farm; farmpypl derives the herd, prices each input and fills "
           "blanks with Teagasc NFS averages. Prices: CSO, Eurostat, EU Weekly Oil Bulletin.")

if not csv_text:
    st.stop()

try:
    res = run_model(csv_text, *prices_key())
except CSVLoadingError as e:
    st.error(f"**Input problem:** {e}")
    st.stop()
except Exception as e:  # any other farmpypl error (e.g. missing benchmark)
    st.error(f"**farmpypl could not run:** {type(e).__name__}: {e}")
    st.stop()

farm, herd, cohorts, costs = res["farm"], res["herd"], res["cohorts"], res["costs"]
names = farm["farm_name"].tolist()

stale = stale_prices(res["price_info"])
if stale:
    st.warning(f"Prices older than {STALE_AFTER_DAYS} days: {', '.join(stale)}. "
               "Refresh them on the **Prices** tab.")

tabs = st.tabs(["Overview", "Farm", "Herd", "Costs", "Prices", "NFS benchmark", "Export"])

# ---------------- Overview ----------------
with tabs[0]:
    totals = costs.groupby("farm_name", sort=False)["eur"].sum()
    for _, f in farm.iterrows():
        n = f["farm_name"]
        h = herd.set_index("farm_name").loc[n]
        total = totals.get(n, 0.0)
        st.subheader(n)
        k = st.columns(6)
        k[0].metric("Annual milk", f"{f['annual_yield_l']:,.0f} L")
        k[1].metric("Livestock units", f"{h['livestock_units']:,.1f}")
        lo, hi = SR_BANDS[f["farm_type"]]
        k[2].metric("Stocking rate", f"{h['stocking_rate']:.2f} LU/ha",
                    "in NFS band" if h["in_sr_band"] else f"outside {lo}–{hi}",
                    delta_color="normal" if h["in_sr_band"] else "inverse")
        k[3].metric("Total costs", eur(total))
        k[4].metric("Cost per litre",
                    f"€{total / f['annual_yield_l']:.3f}" if f["annual_yield_l"] else "–")
        k[5].metric("Cost per cow", eur(total / f["dairy_cows"]) if f["dairy_cows"] else "–")
    if len(names) > 1:
        st.divider()
        st.markdown("**Comparison**")
        comp = herd.merge(farm[["farm_name", "uaa_ha", "annual_yield_l"]], on="farm_name")
        comp["total_costs_eur"] = comp["farm_name"].map(totals)
        comp["eur_per_litre"] = (comp["total_costs_eur"] / comp["annual_yield_l"]).round(3)
        comp["eur_per_ha"] = (comp["total_costs_eur"] / comp["uaa_ha"]).round(0)
        st.dataframe(comp, hide_index=True, width="stretch")

# ---------------- Farm ----------------
with tabs[1]:
    st.markdown("The farm as entered (after validation), plus annual milk yield. "
                "Blank optional values (`None`) are filled from NFS averages.")
    st.dataframe(farm, hide_index=True, width="stretch")
    land = farm.melt(id_vars="farm_name", value_vars=["grassland_ha", "tillage_ha"],
                     var_name="land", value_name="ha")
    other = farm.assign(other_ha=farm["uaa_ha"] - farm["grassland_ha"] - farm["tillage_ha"])
    land = pd.concat([land, other.melt(id_vars="farm_name", value_vars=["other_ha"],
                                       var_name="land", value_name="ha")])
    st.altair_chart(alt.Chart(land).mark_bar().encode(
        x=alt.X("ha:Q", title="Hectares", stack="zero"),
        y=alt.Y("farm_name:N", title=None),
        color=alt.Color("land:N", title="Land use"),
        tooltip=["farm_name", "land", "ha"]).properties(height=60 + 40 * len(names)),
        width="stretch")

# ---------------- Herd ----------------
with tabs[2]:
    st.markdown("Followers are derived from adult cows using national (2020) herd ratios.")
    st.dataframe(herd, hide_index=True, width="stretch",
                 column_config={"in_sr_band": st.column_config.CheckboxColumn("in SR band")})
    st.caption("Stocking-rate bands (LU/ha grassland): " +
               ", ".join(f"{k} {lo}–{hi}" for k, (lo, hi) in SR_BANDS.items()))
    sel = st.selectbox("Farm", names, key="herd_farm") if len(names) > 1 else names[0]
    hide_zero = st.toggle("Hide empty cohorts", True)
    c = cohorts[cohorts["farm_name"] == sel]
    if hide_zero:
        c = c[c["head"] > 0]
    c = c.assign(lu_per_head=c["cohort"].map(LU_COEFF))
    left, right = st.columns([3, 2])
    with left:
        metric = st.radio("Show", ["head", "lu"], horizontal=True,
                          format_func={"head": "Head", "lu": "Livestock units"}.get)
        st.altair_chart(alt.Chart(c).mark_bar().encode(
            x=alt.X(f"{metric}:Q", title=metric),
            y=alt.Y("cohort:N", sort="-x", title=None),
            tooltip=["cohort", "head", "lu", "lu_per_head"]), width="stretch")
    with right:
        st.dataframe(c.drop(columns="farm_name"), hide_index=True, width="stretch")

# ---------------- Costs ----------------
with tabs[3]:
    st.markdown("Each line is volume × price. **farmer** = your figure; "
                "**default** = NFS average scaled by livestock units.")
    sel_c = st.selectbox("Farm", names, key="cost_farm") if len(names) > 1 else names[0]
    cf = costs[costs["farm_name"] == sel_c]
    f = farm.set_index("farm_name").loc[sel_c]
    total = cf["eur"].sum()
    m = st.columns(4)
    m[0].metric("Total", eur(total))
    m[1].metric("From your figures", eur(cf.loc[cf["source"] == "farmer", "eur"].sum()))
    m[2].metric("Per ha UAA", eur(total / f["uaa_ha"]))
    m[3].metric("Per litre", f"€{total / f['annual_yield_l']:.3f}" if f["annual_yield_l"] else "–")
    left, right = st.columns([3, 2])
    with left:
        st.altair_chart(alt.Chart(cf).mark_bar().encode(
            x=alt.X("eur:Q", title="€ per year"),
            y=alt.Y("line:N", sort="-x", title=None),
            color=alt.Color("source:N", scale=alt.Scale(domain=["farmer", "default"],
                                                        range=["#2e7d32", "#9e9e9e"])),
            tooltip=["line", "volume", "unit", alt.Tooltip("eur:Q", format=",.0f"), "source"]),
            width="stretch")
    with right:
        show = cf.drop(columns="farm_name").assign(
            share=lambda d: (d["eur"] / total * 100).round(1))
        st.dataframe(show, hide_index=True, width="stretch",
                     column_config={"eur": st.column_config.NumberColumn("€", format="%,.0f"),
                                    "share": st.column_config.NumberColumn("% of total",
                                                                           format="%.1f")})
    if len(names) > 1:
        st.markdown("**All farms**")
        st.altair_chart(alt.Chart(costs).mark_bar().encode(
            x=alt.X("eur:Q", title="€ per year"), y=alt.Y("farm_name:N", title=None),
            color="line:N", tooltip=["farm_name", "line", "eur", "source"]),
            width="stretch")

# ---------------- Prices ----------------
with tabs[4]:
    pinfo = res["prices"]
    used = Path(database_path("prices.db"))
    src = "refreshed user copy" if used != bundled_path("prices.db") else "bundled snapshot"
    st.markdown(f"Prices are 12-month means.")
    st.dataframe(pinfo.drop(columns="file"), hide_index=True, width="stretch")

    st.markdown("**Price history**")
    item_name = st.selectbox("Series", list(PRICE_ITEMS))
    with closing(connect("prices.db")) as con:
        hist = pd.read_sql_query(
            "SELECT period_date, value, unit FROM prices WHERE item = ? ORDER BY period_date",
            con, params=(PRICE_ITEMS[item_name],))
    if not hist.empty:
        hist["period_date"] = pd.to_datetime(hist["period_date"])
        years = st.slider("Years shown", 1, 20, 5)
        hist = hist[hist["period_date"] >= hist["period_date"].max() - pd.DateOffset(years=years)]
        st.altair_chart(alt.Chart(hist).mark_line(point=len(hist) < 60).encode(
            x=alt.X("period_date:T", title=None),
            y=alt.Y("value:Q", title=hist["unit"].iloc[0], scale=alt.Scale(zero=False)),
            tooltip=["period_date:T", "value"]), width="stretch")

    st.divider()
    st.markdown("**Refresh prices from CSO, Eurostat and the EU Oil Bulletin**")
    st.caption(f"Writes to `{user_data_dir() / 'prices.db'}`. Calculations then use whichever "
               "copy is fresher. Needs internet access and `openpyxl` for diesel.")
    if st.button("Refresh prices now", type="primary"):
        with st.spinner("Fetching prices… this can take a minute"):
            report = fpl.refresh_prices()
        rep = pd.DataFrame(report)
        ok = rep["ok"].sum()
        (st.success if ok == len(rep) else st.warning)(
            f"{ok} of {len(rep)} sources refreshed. Failed sources keep their cached rows.")
        st.dataframe(rep, hide_index=True, width="stretch")
        run_model.clear()
        st.button("Recalculate with new prices")

    with st.expander("Refresh log"):
        try:
            with closing(connect("prices.db")) as con:
                log = pd.read_sql_query(
                    "SELECT * FROM refresh_log ORDER BY attempted_at DESC LIMIT 50", con)
            st.dataframe(log, hide_index=True, width="stretch")
        except Exception:
            st.caption("No refresh log in this database yet.")

# ---------------- NFS benchmark ----------------
with tabs[5]:
    st.markdown("The average NFS farm for each system used — what blank inputs are "
                "scaled from (by the ratio of your livestock units to these).")
    bm = pd.DataFrame(res["benchmarks"]).rename_axis("item").reset_index()
    st.dataframe(bm, hide_index=True, width="stretch")
    if len(names):
        sel_b = st.selectbox("Compare a farm with the NFS average", names, key="bm_farm")
        f = farm.set_index("farm_name").loc[sel_b]
        b = res["benchmarks"][f["farm_type"]]
        mine = costs[costs["farm_name"] == sel_b].set_index("line")["eur"]
        lu = herd.set_index("farm_name").loc[sel_b, "livestock_units"]
        nfs = {
            "feed": b["concentrates_eur"] + b["bulky_feed_eur"],
            "fertiliser": b["fertiliser_eur"], "diesel": b["diesel_eur"],
            "electricity": b["electricity_eur"], "labour": b["labour_eur"],
            "other": b["total_costs_eur"] - sum(b[k] for k in (
                "concentrates_eur", "bulky_feed_eur", "fertiliser_eur", "diesel_eur",
                "electricity_eur", "labour_eur", "depreciation_eur")),
        }
        cmp = pd.DataFrame({
            "line": list(nfs),
            "your € per LU": [mine.get(k, 0) / lu if lu else None for k in nfs],
            "NFS € per LU": [v / b["livestock_units"] for v in nfs.values()],
        }).round(1)
        cmp["difference %"] = ((cmp["your € per LU"] / cmp["NFS € per LU"] - 1) * 100).round(1)
        st.dataframe(cmp, hide_index=True, width="stretch")
        long = cmp.melt(id_vars="line", value_vars=["your € per LU", "NFS € per LU"],
                        var_name="who", value_name="eur_per_lu")
        st.altair_chart(alt.Chart(long).mark_bar().encode(
            x=alt.X("eur_per_lu:Q", title="€ per livestock unit"),
            y=alt.Y("who:N", title=None), row=alt.Row("line:N", title=None),
            color=alt.Color("who:N", legend=None),
            tooltip=["line", "who", "eur_per_lu"]))

# ---------------- Export ----------------
with tabs[6]:
    outputs = {"farm_summary": farm, "herd_summary": herd, "herd_cohorts": cohorts,
               "costs": costs, "price_summary": res["prices"]}
    xbuf = io.BytesIO()
    try:
        with pd.ExcelWriter(xbuf, engine="openpyxl") as xw:
            for name, df in outputs.items():
                df.to_excel(xw, sheet_name=name, index=False)
        st.download_button("Download all results (Excel)", xbuf.getvalue(),
                           file_name="farmpypl_results.xlsx",
                           mime="application/vnd.openxmlformats-officedocument."
                                "spreadsheetml.sheet")
    except ImportError:
        st.caption("Install `openpyxl` for Excel export.")
    zbuf = io.BytesIO()
    with zipfile.ZipFile(zbuf, "w") as z:
        for name, df in outputs.items():
            z.writestr(f"{name}.csv", df.to_csv(index=False))
        z.writestr("input_farms.csv", csv_text)
    st.download_button("Download all results (CSV zip)", zbuf.getvalue(),
                       file_name="farmpypl_results.zip", mime="application/zip")
    st.markdown("**Individual tables**")
    for name, df in outputs.items():
        st.download_button(f"{name}.csv", df.to_csv(index=False), file_name=f"{name}.csv",
                           mime="text/csv", key=f"dl_{name}")
