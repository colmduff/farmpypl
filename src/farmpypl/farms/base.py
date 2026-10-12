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
    diesel_liters: float | None = None      # per year; None = use the NFS average
    electricity_kwh: float | None = None    # per year; None = use the NFS average
    # Euro-only lines (no public price, so no volume): per year; None = NFS average.
    contractor_eur: float | None = None
    animal_health_eur: float | None = None  # vet, medicines, A.I. and breeding
    repairs_eur: float | None = None        # buildings and land upkeep
    