from dataclasses import dataclass
from farmpypl.common.constants import FarmType 

@dataclass(frozen=True, kw_only=True)
class Farm:
    """Base class for a farm."""

    farm_name: str
    farm_type: FarmType
    uaa_ha: float
    grassland_ha: float
    tillage_ha: float
    fertilizer_per_hectare_kg: float | None = None  # kg N per ha of grassland per year; None = NFS average
    diesel_liters: float | None = None      # per year; None = use the NFS average
    electricity_kwh: float | None = None    # per year; None = use the NFS average
    # Euro-only lines (no public price, so no volume): per year; None = NFS average.
    contractor_eur: float | None = None
    animal_health_eur: float | None = None  # vet, medicines, A.I. and breeding
    maintenance_eur: float | None = None    # buildings and land upkeep
    # Income, euro per year; None = NFS average.
    livestock_eur: float | None = None      # calves, cull cows and other cattle sold
    subsidies_eur: float | None = None      # all direct payments, excluding capital grants (TAMS)
    other_income_eur: float | None = None   # anything not milk, cattle or payments
    