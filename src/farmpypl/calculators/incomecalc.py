"""Income for one farm: what it sells, and the direct payments it receives.

Skeleton only (Claude, 14 Oct, at Colm's request): signatures and what each
method should return. The bodies are Colm's (Workbook task F).
"""

from dataclasses import dataclass

from farmpypl.farms import DairyFarm


@dataclass(frozen=True)
class IncomeLine:
    """One income line: how much, in what unit, what it earned, and who said so."""

    line: str
    volume: float | None
    unit: str
    eur: float
    source: str  # "farmer" or "default"


class IncomeCalculator:
    """One farm's income, from its own figures or the NFS average.

    Same pattern as CostCalculator:
      if the farmer gave euros -> use them, source "farmer"
      else                     -> NFS rate x this farm's size, source "default"

    Most rates are per livestock unit (rate_per_lu x lu). Subsidies are paid
    on land, so theirs is per hectare (rate_per_ha x uaa_ha).

    Output (milk, livestock, other) and subsidies are kept apart, as NFS does:
    milk + livestock + other is gross output before payments (decision 27).
    """
    def __init__(self, farm, livestock_units, benchmark, prices):
        self.farm = farm
        self.prices = prices
        self.lu = livestock_units
        self.rate_per_lu = {name: value / benchmark["livestock_units"]
                            for name, value in benchmark.items() if name != "livestock_units"}
        self.rate_per_ha = {name: value / benchmark["uaa_ha"]                
                            for name, value in benchmark.items() if name != "uaa_ha"}

    def milk(self) -> IncomeLine:
        """Litres x milk price. Unit "L", source "farmer" (litres are the farmer's).

        Litres: farm.annual_yield_l. Price: prices["milk"], the 12-month mean
        of CSO "actual fat and protein" (the co-ops' A+B-C, averaged).
        """
        litres = self.farm.annual_yield_l

        return IncomeLine("milk", litres, "L", litres * self.prices["milk"], "farmer")

    def livestock(self) -> IncomeLine:
        """Calves, cull cows and other cattle sold, in euro (volume None).

        Farmer: farm.livestock_eur.
        Default: (dairying_eur - milk_eur + cattle_eur) per LU x lu.
        """
        if self.farm.livestock_eur is not None:
            eur = self.farm.livestock_eur
            source = "farmer"
        else:
            rate = (self.rate_per_lu["dairying_eur"] - self.rate_per_lu["milk_eur"]
                    + self.rate_per_lu["cattle_eur"])                            
            eur = rate * self.lu
            source = "default"
        return IncomeLine("livestock", None, "EUR", eur, source)

    def subsidies(self) -> IncomeLine:
        """All direct payments, in euro (volume None).

        Farmer: farm.subsidies_eur.
        Default: subsidies_eur per ha x farm.uaa_ha.
        """
        if self.farm.subsidies_eur is not None:
            eur = self.farm.subsidies_eur
            source = "farmer"
        else:
            eur = self.rate_per_ha["subsidies_eur"] * self.farm.uaa_ha
            source = "default"
        return IncomeLine("subsidies", None, "EUR", eur, source)

    def other(self) -> IncomeLine:
        """Everything that isn't milk, cattle or payments, in euro (volume None).

        Farmer: farm.other_income_eur.
        Default: (output_total_eur - dairying_eur - cattle_eur) per LU x lu.
        """
        if self.farm.other_income_eur is not None:
            eur = self.farm.other_income_eur
            source = "farmer"
        else:
            rate = (self.rate_per_lu["output_total_eur"] - self.rate_per_lu["dairying_eur"]
                    - self.rate_per_lu["cattle_eur"])
            eur = rate * self.lu
            source = "default"
        return IncomeLine("other", None, "EUR", eur, source)

    def lines(self) -> list[IncomeLine]:
        """All four lines, in the order of INCOME_LINES."""
        return [self.milk(), self.livestock(), self.subsidies(), self.other()]
