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
    