"""Farmer data entry: the one place where untrusted input is checked."""

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from farmpypl.common.constants import FarmType
from farmpypl.farms import DairyFarm


class FarmProfileInput(BaseModel):
    """What the farmer supplies about the farm, checked before we trust it."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    farm_name: str = Field(min_length=1)
    farm_type: FarmType
    uaa_ha: float = Field(gt=0, le=1000)
    grassland_ha: float = Field(gt=0, le=1000)
    tillage_ha: float = Field(ge=0, le=1000)
    dairy_cows: int = Field(ge=0)
    yield_per_cow_l: float = Field(gt=0, le=15000)

    # Optional: a blank cell means "I don't know, use the NFS average".
    concentrate_per_cow_kg: float | None = Field(default=None, ge=0, le=5000)
    fertilizer_per_hectare_kg: float | None = Field(default=None, ge=0, le=400)
    diesel_liters: float | None = Field(default=None, ge=0)
    electricity_kwh: float | None = Field(default=None, ge=0)
    contractor_eur: float | None = Field(default=None, ge=0)
    animal_health_eur: float | None = Field(default=None, ge=0)
    repairs_eur: float | None = Field(default=None, ge=0)
    organic_feed_eur: float | None = Field(default=None, ge=0)

    @field_validator(
        "concentrate_per_cow_kg", "fertilizer_per_hectare_kg", "diesel_liters", "electricity_kwh",
        "contractor_eur", "animal_health_eur", "repairs_eur", "organic_feed_eur",
        mode="before",
    )
    @classmethod
    def blank_is_none(cls, value):
        """CSV cells arrive as text; an empty cell means the farmer left it out."""
        return None if value == "" else value

    @model_validator(mode="after")
    def land_adds_up(self) -> Self:
        """Grassland and tillage are both part of the farmed land (UAA)."""
        if self.grassland_ha + self.tillage_ha > self.uaa_ha:
            raise ValueError(
                f"grassland_ha + tillage_ha must not exceed uaa_ha, "
                f"got {self.grassland_ha} + {self.tillage_ha} > {self.uaa_ha}"
            )
        return self

    def to_farm(self) -> DairyFarm:
        """Hand the checked values to the trusted dataclass."""
        return DairyFarm(**self.model_dump())
