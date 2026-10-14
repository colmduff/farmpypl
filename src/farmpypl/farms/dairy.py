from dataclasses import dataclass

from .base import Farm

@dataclass(frozen=True, kw_only=True)
class DairyFarm(Farm):
    """Class representing a dairy farm."""


    dairy_cows: int
    yield_per_cow_l: float
    concentrate_per_cow_kg: float | None = None     # per year; None = use the NFS average
    

    @property
    def annual_yield_l(self) -> float:
        """Litres per year: cows x yield per cow."""
        return self.dairy_cows * self.yield_per_cow_l