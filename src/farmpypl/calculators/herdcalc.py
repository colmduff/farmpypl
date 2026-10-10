"""Herd numbers for one farm: follower cohorts from the adults, livestock units, stocking rate."""

from farmpypl.common.constants import ADULT_COHORTS, HERD_RELATION, LU_COEFF, NATIONAL_HERD, SR_BANDS
from farmpypl.farms import DairyFarm


class HerdCalculator:
    """Performs calculations related to the herd on a farm."""

    def __init__(self, farm: DairyFarm, adults: dict[str, float] | None = None,
                 overrides: dict[str, float] | None = None):
        self.farm = farm
        self.herd_relation_dict = HERD_RELATION
        self.cohorts = NATIONAL_HERD
        self.adults = {cohort: 0.0 for cohort in ADULT_COHORTS} | {"dairy_cows": farm.dairy_cows} | (adults or {})
        self.herd = self.adults | self.compute_cohort_population() | (overrides or {})

    def compute_coef_cohort_population(self) -> dict[str, float]:
        """
        Computes the coefficients for each cohort by dividing the individual cohort's population
        by the sum of the populations of related cohorts.
        """
        coef = {}
        for animal_type in ["Cattle", "Sheep"]:
            herd_dict = self.herd_relation_dict[animal_type]

            for cohort_index in herd_dict.keys():
                parents = sum(self.cohorts[i] for i in herd_dict[cohort_index])
                coef[cohort_index] = self.cohorts[cohort_index] / parents if parents else 0.0

        return coef

    def compute_cohort_population(self) -> dict[str, float]:
        """Each follower cohort = its coefficient x this farm's parent adults."""
        relation = self.herd_relation_dict["Cattle"] | self.herd_relation_dict["Sheep"]
        return {
            cohort: coef * sum(self.adults[parent] for parent in relation[cohort])
            for cohort, coef in self.compute_coef_cohort_population().items()
        }

    def followers(self) -> float:
        """Total head of every cohort that isn't an entered adult."""
        return sum(head for cohort, head in self.herd.items() if cohort not in self.adults)

    def livestock_units(self) -> float:
        return sum(head * LU_COEFF[cohort] for cohort, head in self.herd.items())

    def stocking_rate(self) -> float:
        """Livestock units per hectare of grassland."""
        return self.livestock_units() / self.farm.grassland_ha

    def in_sr_band(self) -> bool:
        """Is the stocking rate inside the plausible NFS range for this farm type?"""
        low, high = SR_BANDS[self.farm.farm_type]
        return low <= self.stocking_rate() <= high
