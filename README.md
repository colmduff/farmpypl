# 📦 farmpypl
[![license](https://img.shields.io/badge/License-MIT-red)](https://github.com/colmduff/farmpypl/blob/main/LICENSE)
[![python](https://img.shields.io/badge/python-3.11+-blue?logo=python&logoColor=white)](https://github.com/colmduff/farmpypl)
[![version](https://img.shields.io/badge/version-0.1.0-informational)](https://github.com/colmduff/farmpypl/blob/main/CHANGELOG.md)
[![status](https://img.shields.io/badge/status-alpha-orange)](https://github.com/colmduff/farmpypl)
[![ci](https://github.com/colmduff/farmpypl/actions/workflows/main.yml/badge.svg)](https://github.com/colmduff/farmpypl/actions/workflows/main.yml)
[![docs](https://readthedocs.org/projects/farmpypl/badge/?version=latest)](https://farmpypl.readthedocs.io/en/latest/)
[![pydantic v2](https://img.shields.io/badge/pydantic-v2-e92063?logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![pandas](https://img.shields.io/badge/pandas-3.x-150458?logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Income and organic-conversion calculator for Irish dairy farms.

You describe a farm in a CSV (land, cows, milk yield and, optionally, what you
actually used: feed, fertiliser, diesel, electricity). farmpypl derives the
rest of the herd, prices each input line, fills anything you left blank with a
national average, and returns the results as pandas DataFrames. Averages come
from the Teagasc National Farm Survey (NFS); prices come from public sources
(CSO, Eurostat, the EU Weekly Oil Bulletin).

> **Status:** early development (v0.1.0). The API will change.

## Installation

From GitHub:

```bash
pip install "farmpypl@git+https://github.com/colmduff/farmpypl.git@main"
```

With the optional price-refresh dependencies (`openpyxl`):

```bash
pip install "farmpypl[refresh]@git+https://github.com/colmduff/farmpypl.git@main"
```

The package is not on PyPI yet. Requires Python 3.11+; `pydantic` and `pandas`
are installed automatically.

## Quick start

```python
from pathlib import Path

import farmpypl as fpl

# One farm per row. Optional columns can be left out or blank.
csv = Path("example_farm.csv")
csv.write_text(
    "farm_name,farm_type,uaa_ha,grassland_ha,tillage_ha,dairy_cows,yield_per_cow_l,diesel_liters\n"
    "Example farm,dairy,100,95,5,100,5500,6000\n"
)

manager = fpl.FarmManager.from_csv(csv)

manager.farm_summary()   # the farm as entered, plus annual milk yield
manager.herd_summary()   # cows, followers, livestock units, stocking rate
manager.herd_cohorts()   # head and LU per animal cohort
manager.costs()          # one row per cost line
manager.price_summary()  # the prices used, and how fresh they are
```

Every method returns a DataFrame with one or more rows per farm. For example,
`costs()` has the columns `farm_name, line, volume, unit, eur, source`, where
`source` says whether the figure came from the farmer (`farmer`) or from the
NFS average (`default`). In the example above only diesel is `farmer`.

### Input columns

| Column | Unit | Required |
|---|---|---|
| `farm_name` | text | yes |
| `farm_type` | NFS farm system (`dairy`) | yes |
| `uaa_ha`, `grassland_ha`, `tillage_ha` | ha (grassland + tillage ≤ UAA) | yes |
| `dairy_cows` | head | yes |
| `yield_per_cow_l` | litres per cow per year | yes |
| `concentrate_per_cow_kg` | kg per cow per year | no |
| `fertilizer_per_hectare_kg` | kg N per ha | no |
| `diesel_liters` | litres per year | no |
| `electricity_kwh` | kWh per year | no |
| `contractor_eur`, `animal_health_eur`, `repairs_eur`, `organic_feed_eur` | € per year | no |

A blank optional column means "use the NFS average for a farm this size"
(scaled by livestock units).

## Streamlit app

`streamlit_app.py` is a simple web front end for the library. It loads the
package from `src/`, so it runs straight from a clone.

```bash
poetry install                      # streamlit is a project dependency
poetry run streamlit run streamlit_app.py
```

Or with pip: `pip install streamlit openpyxl`, then `streamlit run streamlit_app.py`.
The app opens at http://localhost:8501.

**Enter a farm** in the sidebar form: name, farm type, land areas, dairy cows
and yield per cow. Optional inputs (feed, fertiliser, diesel, electricity,
contractor, animal health, repairs, organic feed) each have a tick box: ticked
uses your figure, unticked uses the NFS average. Click **Calculate**. The form's
fields are read from `FarmProfileInput`, so a new input field shows up on its own.

**Results** are shown in tabs:

| Tab | Shows |
|---|---|
| Overview | Annual milk, livestock units, stocking rate (checked against the NFS band), total cost, cost per litre and per cow |
| Farm | The farm as entered, plus a land-use chart |
| Herd | Herd summary, and head or livestock units per cohort |
| Costs | Each cost line, marked `farmer` or `default`, with totals per ha and per litre |
| NFS benchmark | The NFS average farm, and your cost per livestock unit against it |
| Prices | The prices used, which `prices.db` is in use, price history, and a **Refresh prices now** button (needs internet and `openpyxl`) |
| Export | All results as one Excel file, a CSV zip, or single CSVs |

A warning appears if any price was fetched more than 42 days ago.
Invalid input (for example grassland + tillage > UAA) shows the validation
message instead of results.

## What's in 0.1.0

- **Farm models and validation**: `Farm` / `DairyFarm` dataclasses, checked on
  load with pydantic (e.g. land areas must add up).
- **Herd calculator**: derives followers (calves, heifers, bulls…) from the
  number of adult cows using national herd ratios, then livestock units and
  stocking rate, and flags whether the stocking rate is in the usual band for
  the farm system.
- **Cost calculator**: feed, fertiliser, diesel, electricity, labour and other
  costs. Each line is volume × price; the farmer gives a volume, a € figure or
  nothing (NFS default), and the source is recorded. Contractor, animal health,
  repairs and organic feed are accepted as inputs and are being wired into the
  cost lines.
- **Bundled data**: read-only snapshots of the NFS benchmarks (`nfs.db`) and
  prices (`prices.db`), with the SQL queries that read them, so the package
  works offline.
- **Price refresh**: `farmpypl-refresh` (or `farmpypl.refresh_prices()`)
  fetches the latest prices into a user copy (`~/.local/share/farmpypl`). The
  package then uses whichever copy is fresher. Calculations never go to the
  network themselves.

## Data sources

| Data | Source |
|---|---|
| Farm benchmarks (costs and outputs per LU, cow, ha, litre) | Teagasc National Farm Survey |
| Concentrate feed and fertiliser prices | CSO agricultural input price series |
| Electricity price (non-household, incl. taxes) | Eurostat |
| Diesel price (incl. taxes) | EU Weekly Oil Bulletin |

Prices are averaged over the latest 12 months, because the model works on
annual figures and some prices are strongly seasonal.

## Roadmap

- **Income**: milk and product income, subsidies and a cash-income bottom line.
- **Benchmarking against NFS**: compare a farm's costs and outputs with the NFS
  dairy average per livestock unit, cow, hectare and litre.
- **Stocking-rate optimisation**: find the stocking rate that maximises income
  within the farm's land, feed and environmental limits.
- **Environmental impacts**: greenhouse-gas emissions, nitrogen balance and
  other sustainability indicators, before and after organic conversion.
- **Additional farm types**: beef (cattle rearing and other cattle), sheep,
  tillage and mixed systems, following the NFS farm systems.
- **Dashboard**: extend the Streamlit app (see above) as income, benchmarking
  and environmental results are added.

## Development

```bash
poetry install --all-extras
poetry run pytest                  # offline tests
poetry run pytest -m network       # live price-API test
poetry run make -C docs html       # docs -> docs/_build/html
```

See [CONTRIBUTING.md](CONTRIBUTING.md) and [CHANGELOG.md](CHANGELOG.md).

## License
This project is licensed under the terms of the MIT license.
