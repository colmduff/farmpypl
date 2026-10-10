"""Inputs and costs for one farm: volume first, euro from volume x price."""

from dataclasses import dataclass

from farmpypl.common.constants import CAN_N_FRACTION, HOURS_PER_LABOUR_UNIT
from farmpypl.farms import DairyFarm


@dataclass(frozen=True)
class CostLine:
    """One input line: how much, in what unit, what it cost, and who said so."""

    line: str
    volume: float | None
    unit: str
    eur: float
    source: str  # "farmer" or "default"


class CostCalculator:
    """One farm's inputs and costs, from its own figures or the NFS average.

    Workbook task 3. Every line follows one pattern:
      if the farmer gave a volume -> use it, source "farmer"
      else                        -> NFS euro / price x scale, source "default"
      euro = volume x price
    """

    def __init__(self, farm: DairyFarm, livestock_units: float,
                 benchmark: dict[str, float], prices: dict[str, float]):
        self.farm = farm
        self.nfs = benchmark
        self.prices = prices
        self.scale = livestock_units / benchmark["livestock_units"]


    def feed(self) -> CostLine:
        price = self.prices["concentrates"]
        bulky_eur = self.nfs["bulky_feed_eur"] * self.scale

        if self.farm.concentrate_per_cow_kg is not None:
            tonnes = self.farm.concentrate_per_cow_kg * self.farm.dairy_cows / 1000  # tonnes
            source = "farmer"
        else:
            tonnes = self.nfs["concentrates_eur"] / price * self.scale  
            source = "default"

        return CostLine("feed", tonnes, "t concentrate", tonnes * price + bulky_eur, source) 

    def fertiliser(self) -> CostLine:
        price = self.prices["fertiliser"] / 1000 / CAN_N_FRACTION
        if self.farm.fertilizer_per_hectare_kg is not None:
            kg_n = self.farm.fertilizer_per_hectare_kg * self.farm.grassland_ha
            source = "farmer"
        else:
            kg_n = self.nfs["fertiliser_eur"] / price * self.scale
            source = "default"

        return CostLine("fertiliser", kg_n, "kg N", kg_n * price, source)

    def diesel(self) -> CostLine:
        price = self.prices["diesel"]
        if self.farm.diesel_liters is not None:
            litres = self.farm.diesel_liters
            source = "farmer"
        else:
            litres = self.nfs["diesel_eur"] / price * self.scale
            source = "default"

        return CostLine("diesel", litres, "L", litres * price, source)


    def electricity(self) -> CostLine:
        price = self.prices["electricity"]
        if self.farm.electricity_kwh is not None:
            kwh = self.farm.electricity_kwh
            source = "farmer"
        else:
            kwh = self.nfs["electricity_eur"] / price * self.scale
            source = "default"

        return CostLine("electricity", kwh, "kWh", kwh * price, source)

    def labour(self) -> CostLine:
        hours = self.nfs["labour_units"] * HOURS_PER_LABOUR_UNIT * self.scale
        return CostLine("labour", hours, "hours", self.nfs["labour_eur"] * self.scale, "default")

    def other(self) -> CostLine:
        named = ("concentrates_eur", "bulky_feed_eur", "fertiliser_eur",
                 "diesel_eur", "electricity_eur", "labour_eur", "depreciation_eur")
        other_eur = self.nfs["total_costs_eur"] - sum(self.nfs[k] for k in named)
        return CostLine("other", None, "EUR", other_eur * self.scale, "default")

    def lines(self) -> list[CostLine]:
        """All six lines, in the order of COST_LINES."""
        return [self.feed(), self.fertiliser(), self.diesel(),
                self.electricity(), self.labour(), self.other()]
