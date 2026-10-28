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
      else                        -> rate_per_lu / price * lu, source "default"
      euro = volume x price

    Defaults are NFS rates per livestock unit (LU) times this farm's LU:
    rate_per_lu["contractor_eur"] is EUR per LU on the NFS average farm.
    """

    def __init__(self, farm: DairyFarm, livestock_units: float,
                 benchmark: dict[str, float], prices: dict[str, float]):
        self.farm = farm
        self.prices = prices
        self.lu = livestock_units
        # Every NFS figure as a rate per LU of the NFS average farm (e.g. EUR/LU, labour units/LU).
        self.rate_per_lu = {name: value / benchmark["livestock_units"]
                            for name, value in benchmark.items() if name != "livestock_units"}


    def feed(self) -> CostLine:
        price = self.prices["concentrates"]
        bulky_eur = self.rate_per_lu["bulky_feed_eur"] * self.lu

        if self.farm.concentrate_per_cow_kg is not None:
            tonnes = self.farm.concentrate_per_cow_kg * self.farm.dairy_cows / 1000  # tonnes
            source = "farmer"
        else:
            tonnes = self.rate_per_lu["concentrates_eur"] / price * self.lu
            source = "default"

        return CostLine("feed", tonnes, "t concentrate", tonnes * price + bulky_eur, source) 

    def fertiliser(self) -> CostLine:
        price = self.prices["fertiliser"] / 1000 / CAN_N_FRACTION
        if self.farm.fertilizer_per_hectare_kg is not None:
            kg_n = self.farm.fertilizer_per_hectare_kg * self.farm.grassland_ha
            source = "farmer"
        else:
            kg_n = self.rate_per_lu["fertiliser_eur"] / price * self.lu
            source = "default"

        return CostLine("fertiliser", kg_n, "kg N", kg_n * price, source)

    def diesel(self) -> CostLine:
        price = self.prices["diesel"]
        if self.farm.diesel_liters is not None:
            litres = self.farm.diesel_liters
            source = "farmer"
        else:
            litres = self.rate_per_lu["diesel_eur"] / price * self.lu
            source = "default"

        return CostLine("diesel", litres, "L", litres * price, source)


    def electricity(self) -> CostLine:
        price = self.prices["electricity"]
        if self.farm.electricity_kwh is not None:
            kwh = self.farm.electricity_kwh
            source = "farmer"
        else:
            kwh = self.rate_per_lu["electricity_eur"] / price * self.lu
            source = "default"

        return CostLine("electricity", kwh, "kWh", kwh * price, source)

    def labour(self) -> CostLine:
        hours = self.rate_per_lu["labour_units"] * HOURS_PER_LABOUR_UNIT * self.lu
        return CostLine("labour", hours, "hours", self.rate_per_lu["labour_eur"] * self.lu, "default")

    def contractor(self) -> CostLine:
        if self.farm.contractor_eur is not None:                  
            eur = self.farm.contractor_eur
            source = "farmer"
        else:
            eur = self.rate_per_lu["contractor_eur"] * self.lu  
            source = "default"
        return CostLine("contractor", None, "EUR", eur, source)  

    def animal_health(self) -> CostLine:
        if self.farm.animal_health_eur is not None:
            eur = self.farm.animal_health_eur
            source = "farmer"
        else:
            eur = self.rate_per_lu["animal_health_eur"] * self.lu
            source = "default"
        return CostLine("animal_health", None, "EUR", eur, source)

    def maintenance(self) -> CostLine:
        if self.farm.maintenance_eur is not None:
            eur = self.farm.maintenance_eur
            source = "farmer"
        else:
            eur = self.rate_per_lu["maintenance_eur"] * self.lu
            source = "default"
        return CostLine("maintenance", None, "EUR", eur, source)
    
    def other(self) -> CostLine:
        named = ("concentrates_eur", "bulky_feed_eur", "fertiliser_eur",
                 "diesel_eur", "electricity_eur", "labour_eur", "contractor_eur", 
                 "animal_health_eur", "maintenance_eur", "depreciation_eur")
        other_rate = self.rate_per_lu["total_costs_eur"] - sum(self.rate_per_lu[k] for k in named)
        return CostLine("other", None, "EUR", other_rate * self.lu, "default")

    def lines(self) -> list[CostLine]:
        """All nine lines, in the order of COST_LINES."""
        return [self.feed(), self.fertiliser(), self.diesel(),
                self.electricity(), self.labour(), self.contractor(), self.animal_health(), self.maintenance(), self.other()]
