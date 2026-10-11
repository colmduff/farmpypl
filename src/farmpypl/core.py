"""The route data takes through farmpypl: file in, DataFrame out.

This is the coordinator. It calls each layer in order and is the only
module that knows the whole route. Nothing below it imports it.
"""

from contextlib import closing
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from farmpypl.calculators import CostCalculator, HerdCalculator
from farmpypl.common.constants import LU_COEFF
from farmpypl.db import connect, load_benchmark, load_prices, price_status
from farmpypl.farms import DairyFarm
from farmpypl.loaders import load_profiles

class FarmManager:
    """Class responsible for managing farm data."""

    def __init__(self, farms: list[DairyFarm],
                 benchmarks: dict[str, dict[str, float]],
                 prices: dict[str, float],
                 price_info: list[dict] | None = None):
        self.farms = farms
        self.benchmarks = benchmarks
        self.prices = prices
        self.price_info = price_info or []

    @classmethod
    def from_csv(cls, path: str | Path) -> "FarmManager":
        """Read a farm profile CSV, then the NFS benchmarks and prices those farms need.

        Route: load_profiles (read + check) -> .to_farm() (checked -> trusted);
        nfs.db and prices.db are opened once, read-only, and closed straight after.
        prices.db is the refreshed user copy if there is one, else the bundled snapshot.
        """
        profiles = load_profiles(path)  
        farms =[profile.to_farm() for profile in profiles]

        with closing(connect("nfs.db")) as nfs:
            benchmarks = {t: load_benchmark(nfs, t) for t in {farm.farm_type for farm in farms}}
        with closing(connect("prices.db")) as con:
            prices = load_prices(con)
            price_info = price_status(con)

        return cls(farms=farms, benchmarks=benchmarks, prices=prices, price_info=price_info)   

    def herd_summary(self) -> pd.DataFrame:
        """One row per farm: the headline herd figures.

        Columns: farm_name, dairy_cows, followers, livestock_units, stocking_rate, in_sr_band.
        """
        rows = []
        for farm in self.farms:
            herd = HerdCalculator(farm)
            rows.append({
                "farm_name": farm.farm_name,
                "dairy_cows": farm.dairy_cows,
                "followers": round(herd.followers(), 1),
                "livestock_units": round(herd.livestock_units(), 1),
                "stocking_rate": round(herd.stocking_rate(), 2),
                "in_sr_band": herd.in_sr_band(),
            })
        return pd.DataFrame(rows)

    def herd_cohorts(self) -> pd.DataFrame:
        """One row per farm and cohort: head and livestock units. Zeros are kept."""
        rows = []
        for farm in self.farms:
            herd = HerdCalculator(farm)
            for cohort, head in herd.herd.items():
                rows.append({
                    "farm_name": farm.farm_name,
                    "cohort": cohort,
                    "head": round(head, 1),
                    "lu": round(head * LU_COEFF[cohort], 1),
                })
        return pd.DataFrame(rows)

    def farm_summary(self) -> pd.DataFrame:
        """One summary row per farm held by this manager.

        Columns: every DairyFarm field, plus annual_yield_l.
        """

        rows = [{**asdict(farm), "annual_yield_l": farm.annual_yield_l} for farm in self.farms]
        return pd.DataFrame(rows)

    def costs(self) -> pd.DataFrame:
        """One row per farm and input line: volume, unit, euro, and where it came from.
        """
        rows = []

        for farm in self.farms:
            livestock_units = HerdCalculator(farm).livestock_units() 
            calc = CostCalculator(farm, livestock_units, self.benchmarks[farm.farm_type], self.prices)
            for line in calc.lines():
                rows.append({"farm_name": farm.farm_name, **asdict(line)})
        return pd.DataFrame(rows).round({"volume": 0, "eur": 0})

    def price_summary(self) -> pd.DataFrame:
        """One row per price the costs use: 12-month mean, window, fetch date, file."""
        return pd.DataFrame(self.price_info).round({"mean_12mo": 4})
