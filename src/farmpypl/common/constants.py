"""Reference constants: farm systems, herd cohorts, livestock units, herd relation, NFS templates.

Started 7 Oct 2026 from AGRISYN's ``constants.py``; the herd cohorts, herd relation
and national herd come from GOBLIN ``livestock_generation`` (decision 16 in
``.data/doc/development/architecture.md``). Pure data: no functions, and no
imports of our own, so any layer may import it.
"""

from typing import Literal, get_args

# =============================================================================
# FARM SYSTEMS
# =============================================================================
# The six NFS farm systems. A mixed farm picks its main system or "mixed";
# its real mix shows up in the herd.
FarmType = Literal["dairy", "cattle_rearing", "cattle_other", "sheep", "tillage", "mixed"]
FARM_TYPES: tuple[str, ...] = get_args(FarmType)

# =============================================================================
# HERD: GOBLIN cohorts, herd relation, national herd
# =============================================================================
# Source: GOBLIN livestock_generation (MIT). HERD_RELATION is copied from
# resource_manager/livestock_data_manager.py; NATIONAL_HERD is the 2020 column of
# table 2012_to_2020_herd_numbers in database/livestock_database.db (thousand
# head, Ireland; 2020 is the latest year in the table). Cohort names are GOBLIN's.

# Adults the farmer enters; every other cohort is derived from them.
ADULT_COHORTS: tuple[str, ...] = ("dairy_cows", "suckler_cows", "Lowland ewes", "Upland ewes")

# Each follower cohort -> the adult cohorts it comes from.
HERD_RELATION: dict[str, dict[str, list[str]]] = {
    "Cattle": {
        "DxD_calves_f": ["dairy_cows"],
        "DxD_calves_m": ["dairy_cows"],
        "DxB_calves_f": ["dairy_cows"],
        "DxB_calves_m": ["dairy_cows"],
        "BxB_calves_f": ["suckler_cows"],
        "BxB_calves_m": ["suckler_cows"],
        "DxD_heifers_less_2_yr": ["dairy_cows"],
        "DxD_steers_less_2_yr": ["dairy_cows"],
        "DxB_heifers_less_2_yr": ["dairy_cows"],
        "DxB_steers_less_2_yr": ["dairy_cows"],
        "BxB_heifers_less_2_yr": ["suckler_cows"],
        "BxB_steers_less_2_yr": ["suckler_cows"],
        "DxD_heifers_more_2_yr": ["dairy_cows"],
        "DxD_steers_more_2_yr": ["dairy_cows"],
        "DxB_heifers_more_2_yr": ["dairy_cows"],
        "DxB_steers_more_2_yr": ["dairy_cows"],
        "BxB_heifers_more_2_yr": ["suckler_cows"],
        "BxB_steers_more_2_yr": ["suckler_cows"],
        "bulls": ["dairy_cows", "suckler_cows"],
    },
    "Sheep": {
        "Lowland lamb_less_1_yr": ["Lowland ewes"],
        "Lowland male_less_1_yr": ["Lowland ewes"],
        "Lowland lamb_more_1_yr": ["Lowland ewes"],
        "Lowland ram": ["Lowland ewes"],
        "Upland lamb_less_1_yr": ["Upland ewes"],
        "Upland male_less_1_yr": ["Upland ewes"],
        "Upland lamb_more_1_yr": ["Upland ewes"],
        "Upland ram": ["Upland ewes"],
    },
}

# National herd, 2020, thousand head: the reference the coefficients come from.
NATIONAL_HERD: dict[str, float] = {
    "dairy_cows":             1511.85,
    "suckler_cows":           953,
    "DxD_calves_m":           248.6034044,
    "DxD_calves_f":           353.7365672,
    "DxB_calves_m":           320.162304,
    "DxB_calves_f":           318.9379177,
    "BxB_calves_m":           405.9951708,
    "BxB_calves_f":           404.151345,
    "DxD_heifers_less_2_yr":  346.5882016,
    "DxD_steers_less_2_yr":   239.4693704,
    "DxB_heifers_less_2_yr":  308.3218997,
    "DxB_steers_less_2_yr":   309.2563276,
    "BxB_heifers_less_2_yr":  390.8494704,
    "BxB_steers_less_2_yr":   392.3285725,
    "DxD_heifers_more_2_yr":  10.46702461,
    "DxD_steers_more_2_yr":   58.23656831,
    "DxB_heifers_more_2_yr":  20.2147923,
    "DxB_steers_more_2_yr":   71.21756859,
    "BxB_heifers_more_2_yr":  56.56798695,
    "BxB_steers_more_2_yr":   62.66366722,
    "bulls":                  50.95,
    "Lowland ewes":           2137.04,
    "Upland ewes":            534.26,
    "Lowland lamb_less_1_yr": 960.3852,
    "Lowland male_less_1_yr": 960.3852,
    "Lowland lamb_more_1_yr": 102.7080746,
    "Lowland ram":            68.76,
    "Upland lamb_less_1_yr":  240.0963,
    "Upland male_less_1_yr":  240.0963,
    "Upland lamb_more_1_yr":  25.67701864,
    "Upland ram":             17.19,
}
COHORTS: tuple[str, ...] = tuple(NATIONAL_HERD)

# Livestock units per head (NFS 2020 Appendix 4, from AGRISYN's GOBLIN-cohort table).
LU_COEFF: dict[str, float] = {
    "dairy_cows":             1.00,
    "suckler_cows":           0.90,
    "DxD_calves_m":           0.30,
    "DxD_calves_f":           0.30,
    "DxB_calves_m":           0.30,
    "DxB_calves_f":           0.30,
    "BxB_calves_m":           0.30,
    "BxB_calves_f":           0.30,
    "DxD_heifers_less_2_yr":  0.70,
    "DxD_steers_less_2_yr":   0.70,
    "DxB_heifers_less_2_yr":  0.70,
    "DxB_steers_less_2_yr":   0.70,
    "BxB_heifers_less_2_yr":  0.70,
    "BxB_steers_less_2_yr":   0.70,
    "DxD_heifers_more_2_yr":  1.00,
    "DxD_steers_more_2_yr":   1.00,
    "DxB_heifers_more_2_yr":  1.00,
    "DxB_steers_more_2_yr":   1.00,
    "BxB_heifers_more_2_yr":  1.00,
    "BxB_steers_more_2_yr":   1.00,
    "bulls":                  1.00,
    "Lowland ewes":           0.20,
    "Upland ewes":            0.14,
    "Lowland lamb_less_1_yr": 0.12,
    "Lowland male_less_1_yr": 0.12,
    "Lowland lamb_more_1_yr": 0.15,
    "Lowland ram":            0.20,
    "Upland lamb_less_1_yr":  0.10,
    "Upland male_less_1_yr":  0.10,
    "Upland lamb_more_1_yr":  0.10,
    "Upland ram":             0.14,
}

# =============================================================================
# STOCKING RATE
# =============================================================================
# Plausible stocking rate, LU per ha of grassland, for commercial farms (NFS).
# Outside the band is not an error, but worth a second look.
SR_BANDS: dict[str, tuple[float, float]] = {
    "dairy":          (1.60, 2.80),
    "cattle_rearing": (0.70, 1.65),
    "cattle_other":   (0.70, 1.65),
    "sheep":          (0.40, 2.00),
    "tillage":        (0.00, 2.50),   # residual livestock only
    "mixed":          (0.50, 2.00),
}

# =============================================================================
# NFS COHORTS, SIZE BANDS AND 2020 TEMPLATES (kept for other farm types)
# =============================================================================
# The herd rows of NFS Table 8B ("Cattle (avg no.)", "Sheep (avg. no)"): what a
# farmer can count, and what the NFS templates below give a default for. Kept for other farm types
# and for comparison; the herd calculator uses the GOBLIN cohorts above.
NFS_COHORT_LABELS: dict[str, str] = {
    "dairy_cows":   "Dairy cows",
    "suckler_cows": "Suckler (other) cows",
    "hic":          "Heifers in calf",
    "c_lt1":        "Cattle under 1 year",
    "m12":          "Male cattle 1-2 years",
    "f12":          "Female cattle 1-2 years",
    "m_gt2":        "Male cattle 2 years and over",
    "f_gt2":        "Female cattle 2 years and over",
    "bulls":        "Bulls",
    "ewes":         "Ewes",
    "other_sheep":  "Other sheep (lambs, hoggets, rams)",
}
NFS_COHORTS: tuple[str, ...] = tuple(NFS_COHORT_LABELS)

# Livestock units per head (NFS 2020 Appendix 4, via AGRISYN).
# "hic" is not in the source: 0.7 (as for 1-2 year heifers) is inferred.
# Checked 7 Oct 2026 against every template's own total_lu: cattle and dairy
# bands land within 1.6%, so 0.7 holds. Sheep bands come out 12-23% HIGH,
# because these are lowland per-head values and NFS counts lambs as a yearly
# average. Do not use sheep LU for anything precise until that is resolved.
NFS_LU_COEFF: dict[str, float] = {
    "dairy_cows":   1.00,
    "suckler_cows": 0.90,
    "hic":          0.70,
    "c_lt1":        0.30,
    "m12":          0.70,
    "f12":          0.70,
    "m_gt2":        1.00,
    "f_gt2":        1.00,
    "bulls":        1.00,
    "ewes":         0.20,
    "other_sheep":  0.12,
}

# The NFS size bands: (code, lower ha inclusive, upper ha exclusive). The
# NFS_TEMPLATES bands use these codes. (AGRISYN's SIZE_CLASSES were the CSO census
# bands, which split under 20 ha into lt10 / s10_20 and so match no template.)
SIZE_CLASSES: list[tuple[str, float, float]] = [
    ("lt20",       0.0,  20.0),
    ("s20_30",    20.0,  30.0),
    ("s30_50",    30.0,  50.0),
    ("s50_100",   50.0, 100.0),
    ("s100plus", 100.0, 1000.0),   # 1,000 ha is FarmProfileInput's ceiling
]
SC_CODES: list[str] = [code for code, _lo, _hi in SIZE_CLASSES]


# =============================================================================
# NFS 2020 TEMPLATES: the average farm, per system and size band
# =============================================================================
# Land in ha, herd in average head, from NFS 2020 Tables 01B (dairy),
# 02B (cattle rearing), 03B (cattle other), 04B (sheep), 05B (tillage) and
# 08B (mixed livestock; n=15, so treat with care). "all" is the all-sizes average.
# Herd keys are NFS_COHORTS; total_lu is NFS's own total, for checking LU_COEFF.
# Bands the NFS did not publish for a system are absent.
NFS_TEMPLATES: dict[str, dict] = {
    "dairy": {
        "source": "NFS 2020 Table 01B Dairying System",
        "bands": {
            "lt20":    dict(uaa=13.8,  cereals=0.0,  tillage=0.0,  silage=5.4,  hay=0.1,
                            pasture=8.3,   rough=0.0,  dairy_cows=21.1,  suckler_cows=0.4,
                            hic=1.3,  c_lt1=7.2,   m12=0.2,  f12=2.1,  m_gt2=0.3,  f_gt2=0.0,
                            bulls=0.4, ewes=0.0,  other_sheep=0.0,  total_lu=26.5),
            "s20_30":  dict(uaa=25.4,  cereals=0.0,  tillage=0.0,  silage=8.4,  hay=0.0,
                            pasture=16.3,  rough=0.5,  dairy_cows=38.2,  suckler_cows=1.0,
                            hic=3.9,  c_lt1=18.0,  m12=2.2,  f12=4.5,  m_gt2=0.4,  f_gt2=0.4,
                            bulls=0.5, ewes=2.2,  other_sheep=2.2,  total_lu=53.1),
            "s30_50":  dict(uaa=41.0,  cereals=0.4,  tillage=0.5,  silage=15.3, hay=0.3,
                            pasture=24.1,  rough=0.4,  dairy_cows=58.8,  suckler_cows=0.9,
                            hic=6.1,  c_lt1=30.6,  m12=3.5,  f12=9.2,  m_gt2=0.3,  f_gt2=0.7,
                            bulls=0.6, ewes=1.4,  other_sheep=1.2,  total_lu=83.0),
            "s50_100": dict(uaa=71.3,  cereals=0.7,  tillage=1.2,  silage=24.4, hay=0.3,
                            pasture=43.0,  rough=1.1,  dairy_cows=98.4,  suckler_cows=1.4,
                            hic=11.8, c_lt1=56.2,  m12=8.9,  f12=17.3, m_gt2=1.0,  f_gt2=1.2,
                            bulls=1.3, ewes=2.0,  other_sheep=1.7,  total_lu=145.7),
            "s100plus": dict(uaa=139.2, cereals=1.9, tillage=5.9,  silage=46.4, hay=0.6,
                            pasture=84.3,  rough=1.2,  dairy_cows=185.3, suckler_cows=3.3,
                            hic=28.4, c_lt1=113.2, m12=21.6, f12=34.8, m_gt2=2.0,  f_gt2=2.3,
                            bulls=2.2, ewes=3.3,  other_sheep=4.0,  total_lu=286.9),
            "all":     dict(uaa=60.7,  cereals=0.6,  tillage=1.2,  silage=21.0, hay=0.3,
                            pasture=35.9,  rough=1.6,  dairy_cows=83.1,  suckler_cows=1.3,
                            hic=10.1, c_lt1=46.7,  m12=7.2,  f12=14.1, m_gt2=0.8,  f_gt2=1.0,
                            bulls=1.1, ewes=1.8,  other_sheep=1.7,  total_lu=122.4),
        },
    },
    "cattle_rearing": {
        "source": "NFS 2020 Table 02B Cattle Rearing System",
        "bands": {
            "lt20":    dict(uaa=15.4,  cereals=0.0,  tillage=0.0,  silage=6.1,  hay=0.1,
                            pasture=9.0,   rough=0.3,  dairy_cows=0.0,   suckler_cows=14.3,
                            hic=0.6,  c_lt1=13.3,  m12=1.5,  f12=2.5,  m_gt2=0.1,  f_gt2=0.5,
                            bulls=0.5, ewes=1.4,  other_sheep=1.8,  total_lu=21.4),
            "s20_30":  dict(uaa=24.8,  cereals=0.0,  tillage=0.0,  silage=6.7,  hay=0.4,
                            pasture=16.7,  rough=0.5,  dairy_cows=0.0,   suckler_cows=17.9,
                            hic=0.9,  c_lt1=13.9,  m12=2.1,  f12=4.4,  m_gt2=0.2,  f_gt2=0.6,
                            bulls=0.5, ewes=1.0,  other_sheep=1.2,  total_lu=27.1),
            "s30_50":  dict(uaa=38.2,  cereals=0.0,  tillage=0.3,  silage=10.8, hay=0.6,
                            pasture=24.5,  rough=1.1,  dairy_cows=0.0,   suckler_cows=28.8,
                            hic=1.6,  c_lt1=25.3,  m12=3.7,  f12=6.5,  m_gt2=0.3,  f_gt2=1.6,
                            bulls=1.1, ewes=1.8,  other_sheep=1.8,  total_lu=45.8),
            "s50_100": dict(uaa=66.6,  cereals=0.4,  tillage=0.7,  silage=15.1, hay=2.0,
                            pasture=38.4,  rough=7.4,  dairy_cows=0.0,   suckler_cows=42.7,
                            hic=2.0,  c_lt1=38.5,  m12=4.3,  f12=12.6, m_gt2=0.3,  f_gt2=2.6,
                            bulls=1.6, ewes=7.9,  other_sheep=7.0,  total_lu=69.3),
            "all":     dict(uaa=30.7,  cereals=0.0,  tillage=0.1,  silage=8.4,  hay=0.5,
                            pasture=19.5,  rough=1.3,  dairy_cows=0.0,   suckler_cows=22.6,
                            hic=1.3,  c_lt1=19.6,  m12=2.6,  f12=5.2,  m_gt2=0.2,  f_gt2=1.0,
                            bulls=0.8, ewes=2.2,  other_sheep=2.3,  total_lu=35.3),
        },
    },
    "cattle_other": {
        "source": "NFS 2020 Table 03B Cattle Other System",
        "bands": {
            "lt20":    dict(uaa=15.0,  cereals=0.0,  tillage=0.0,  silage=4.0,  hay=0.5,
                            pasture=10.4,  rough=0.0,  dairy_cows=0.0,   suckler_cows=2.5,
                            hic=0.3,  c_lt1=10.9,  m12=7.2,  f12=10.4, m_gt2=2.1,  f_gt2=2.1,
                            bulls=0.1, ewes=3.4,  other_sheep=3.0,  total_lu=23.7),
            "s20_30":  dict(uaa=25.1,  cereals=0.0,  tillage=0.1,  silage=7.4,  hay=0.7,
                            pasture=15.9,  rough=0.0,  dairy_cows=0.0,   suckler_cows=7.1,
                            hic=0.5,  c_lt1=19.8,  m12=10.0, f12=7.3,  m_gt2=3.8,  f_gt2=1.6,
                            bulls=0.3, ewes=4.0,  other_sheep=3.3,  total_lu=31.9),
            "s30_50":  dict(uaa=39.1,  cereals=0.2,  tillage=0.2,  silage=9.7,  hay=1.0,
                            pasture=24.6,  rough=1.8,  dairy_cows=0.0,   suckler_cows=7.7,
                            hic=1.2,  c_lt1=21.0,  m12=13.5, f12=12.7, m_gt2=7.1,  f_gt2=2.1,
                            bulls=0.3, ewes=9.4,  other_sheep=12.6, total_lu=45.2),
            "s50_100": dict(uaa=65.6,  cereals=1.8,  tillage=2.3,  silage=14.6, hay=1.3,
                            pasture=43.2,  rough=1.6,  dairy_cows=0.0,   suckler_cows=22.9,
                            hic=1.1,  c_lt1=37.3,  m12=29.4, f12=16.5, m_gt2=10.2, f_gt2=4.7,
                            bulls=0.8, ewes=21.5, other_sheep=28.6, total_lu=87.6),
            "s100plus": dict(uaa=145.7, cereals=9.5, tillage=12.2, silage=22.2, hay=2.0,
                            pasture=91.3,  rough=12.4, dairy_cows=0.0,   suckler_cows=56.7,
                            hic=4.4,  c_lt1=88.7,  m12=49.6, f12=31.2, m_gt2=15.6, f_gt2=8.1,
                            bulls=2.0, ewes=85.6, other_sheep=87.4, total_lu=187.9),
            "all":     dict(uaa=36.8,  cereals=0.6,  tillage=0.8,  silage=8.7,  hay=0.9,
                            pasture=23.8,  rough=1.3,  dairy_cows=0.0,   suckler_cows=10.1,
                            hic=0.9,  c_lt1=22.5,  m12=14.3, f12=11.7, m_gt2=5.6,  f_gt2=2.6,
                            bulls=0.4, ewes=10.4, other_sheep=12.3, total_lu=46.8),
        },
    },
    "sheep": {
        "source": "NFS 2020 Table 04B Sheep System",
        "bands": {
            "s20_30":  dict(uaa=25.4,  cereals=0.0,  tillage=0.0,  silage=3.7,  hay=0.6,
                            pasture=19.1,  rough=1.0,  dairy_cows=0.0,   suckler_cows=4.0,
                            hic=0.1,  c_lt1=7.0,   m12=0.8,  f12=2.2,  m_gt2=0.1,  f_gt2=0.2,
                            bulls=0.2, ewes=92.3, other_sheep=85.5, total_lu=30.2),
            "s30_50":  dict(uaa=38.3,  cereals=0.4,  tillage=1.3,  silage=7.6,  hay=0.8,
                            pasture=27.0,  rough=1.4,  dairy_cows=0.0,   suckler_cows=10.4,
                            hic=0.6,  c_lt1=10.6,  m12=4.4,  f12=4.6,  m_gt2=2.1,  f_gt2=2.1,
                            bulls=0.4, ewes=121.4, other_sheep=127.4, total_lu=56.7),
            "s50_100": dict(uaa=72.8,  cereals=1.2,  tillage=1.4,  silage=13.7, hay=2.9,
                            pasture=46.7,  rough=6.1,  dairy_cows=0.0,   suckler_cows=22.3,
                            hic=0.8,  c_lt1=26.6,  m12=11.5, f12=11.4, m_gt2=4.4,  f_gt2=2.3,
                            bulls=0.8, ewes=260.2, other_sheep=245.1, total_lu=117.8),
            "all":     dict(uaa=44.4,  cereals=0.5,  tillage=0.8,  silage=6.3,  hay=0.8,
                            pasture=29.4,  rough=5.9,  dairy_cows=0.0,   suckler_cows=9.0,
                            hic=0.5,  c_lt1=10.4,  m12=4.4,  f12=3.8,  m_gt2=1.2,  f_gt2=1.1,
                            bulls=0.3, ewes=127.3, other_sheep=124.1, total_lu=52.0),
        },
    },
    "tillage": {
        "source": "NFS 2020 Table 05B Tillage System (livestock are residual)",
        "bands": {
            "s30_50":  dict(uaa=38.4,  cereals=19.2, tillage=21.1, silage=3.9,  hay=2.0,
                            pasture=9.0,   rough=0.0,  dairy_cows=0.0,   suckler_cows=0.7,
                            hic=0.0,  c_lt1=2.2,   m12=4.7,  f12=2.2,  m_gt2=1.8,  f_gt2=0.2,
                            bulls=0.0, ewes=32.7, other_sheep=40.6, total_lu=18.2),
            "s50_100": dict(uaa=70.4,  cereals=36.0, tillage=39.5, silage=7.6,  hay=2.3,
                            pasture=18.2,  rough=0.0,  dairy_cows=0.0,   suckler_cows=9.8,
                            hic=0.3,  c_lt1=11.3,  m12=11.0, f12=11.9, m_gt2=6.8,  f_gt2=3.1,
                            bulls=0.4, ewes=17.8, other_sheep=19.4, total_lu=44.2),
            "s100plus": dict(uaa=161.3, cereals=76.6, tillage=94.3, silage=15.5, hay=1.2,
                            pasture=40.3,  rough=2.2,  dairy_cows=0.0,   suckler_cows=15.5,
                            hic=0.5,  c_lt1=36.7,  m12=34.0, f12=18.3, m_gt2=10.1, f_gt2=6.9,
                            bulls=0.3, ewes=44.8, other_sheep=39.9, total_lu=93.0),
            "all":     dict(uaa=61.2,  cereals=30.6, tillage=34.9, silage=6.1,  hay=1.6,
                            pasture=15.4,  rough=0.3,  dairy_cows=0.0,   suckler_cows=5.9,
                            hic=0.3,  c_lt1=10.5,  m12=11.0, f12=7.5,  m_gt2=4.3,  f_gt2=2.2,
                            bulls=0.2, ewes=21.8, other_sheep=23.3, total_lu=35.1),
        },
    },
    "mixed": {
        "source": "NFS 2020 Table 08B Mixed Livestock System",
        "bands": {
            "all":     dict(uaa=64.2,  cereals=1.7,  tillage=1.7,  silage=17.7, hay=0.6,
                            pasture=41.7,  rough=2.2,  dairy_cows=23.7,  suckler_cows=6.2,
                            hic=3.2,  c_lt1=35.3,  m12=20.5, f12=15.0, m_gt2=2.7,  f_gt2=1.0,
                            bulls=0.4, ewes=68.0, other_sheep=66.0, total_lu=89.4),
        },
    },
}

# =============================================================================
# NFS 2020 ECONOMICS PER UNIT (Tables 08A + 08B)
# =============================================================================
# Per-farm system averages divided by the farm's LU or UAA. Output is MARKET
# output (gross output minus direct payments); subsidy is kept separate and is
# per ha for every system. Drystock costs exceed market output: the subsidy is
# the income there. Tillage has no meaningful per-LU figure.
NFS_OUTPUT_PER_LU: dict[str, float] = {
    "dairy": 1664.76, "cattle_rearing": 628.61, "cattle_other": 728.76,
    "sheep": 643.62, "mixed": 1156.25,
}
NFS_COST_PER_LU: dict[str, float] = {        # direct + overhead costs
    "dairy": 1225.92, "cattle_rearing": 773.99, "cattle_other": 771.28,
    "sheep": 662.29, "mixed": 1075.66,
}
NFS_OUTPUT_PER_HA: dict[str, float] = {
    "dairy": 3249.87, "cattle_rearing": 676.52, "cattle_other": 890.50,
    "sheep": 709.07, "mixed": 1570.96, "tillage": 1259.86,
}
NFS_COST_PER_HA: dict[str, float] = {        # direct + overhead costs
    "dairy": 2393.17, "cattle_rearing": 832.99, "cattle_other": 942.45,
    "sheep": 729.64, "mixed": 1461.46, "tillage": 1154.18,
}
NFS_SUBSIDY_PER_HA: dict[str, float] = {     # direct payments, area-based
    "dairy": 327.50, "cattle_rearing": 432.16, "cattle_other": 444.18,
    "sheep": 400.11, "mixed": 328.48, "tillage": 402.22,
}

# =============================================================================
# SOIL GROUPS
# =============================================================================
# The NFS collapse of the six AFT land-use-potential classes (Gardiner & Radford
# 1980) into three groups. Soil group drives grass growth.
SOIL_GROUPS: list[int] = [1, 2, 3]
SOIL_GROUP_LABELS: dict[int, str] = {
    1: "wide / moderately wide use range",
    2: "somewhat limited / limited use range",
    3: "very / extremely limited use range",
}
# % of farms in each soil group, per system (NFS 2020 Table 08A). A default when
# the farmer does not know their soil group.
SOIL_GROUP_BY_TYPE: dict[tuple[str, int], float] = {
    ("dairy",          1): 55.4, ("dairy",          2): 39.3, ("dairy",          3):  5.0,
    ("cattle_rearing", 1): 33.7, ("cattle_rearing", 2): 57.0, ("cattle_rearing", 3):  9.3,
    ("cattle_other",   1): 50.3, ("cattle_other",   2): 43.6, ("cattle_other",   3):  6.1,
    ("sheep",          1): 33.5, ("sheep",          2): 49.8, ("sheep",          3): 16.7,
    ("tillage",        1): 84.6, ("tillage",        2): 15.4, ("tillage",        3):  0.0,
    ("mixed",          1): 18.9, ("mixed",          2): 73.7, ("mixed",          3):  7.4,
}

# =============================================================================
# INPUTS AND COSTS (decision 18)
# =============================================================================
# The cost lines the calculator returns, in order. Volume first where an input
# has one (feed t, fertiliser kg N, diesel L, electricity kWh, labour hours).
COST_LINES: tuple[str, ...] = ("feed", "fertiliser", "diesel", "electricity", "labour", "other")

# Our farm type -> the NFS system name used in nfs.db (tables 8A-8E only).
NFS_SYSTEM: dict[str, str] = {
    "dairy": "Dairying", "cattle_rearing": "Cattle Rearing", "cattle_other": "Cattle Other",
    "sheep": "Sheep", "tillage": "Tillage", "mixed": "Mixed Livestock",
}
NFS_YEAR: int = 2025

# Each benchmark figure is the sum of these nfs.db rows, read by (section, line_item)
# for one system and year. Labels are NFS's own, typos and all.
_D, _O = "DIRECT COSTS (€)", "OVERHEAD COSTS (€)"
NFS_BENCHMARK_ITEMS: dict[str, list[tuple[str, str]]] = {
    "concentrates_eur": [(_D, "Purchased Concentrates")],
    "bulky_feed_eur":   [(_D, "Purchased Bulky Feed")],
    "fertiliser_eur":   [(_D, "Fertiliser")],
    "diesel_eur":       [(_O, "of which Fuel & Lub")],
    "electricity_eur":  [(_O, "Car, Electricity, Phone")],
    "labour_eur":       [(_D, "Casual Labour"), (_O, "Current Hired Labour")],
    "total_costs_eur":  [(_O, "TOTAL NET EXPENSES")],
    "depreciation_eur": [(_O, "Machinery Depreciation"), (_O, "Buildings Depreciation"),
                         (_O, "Land Improvement Depreciation")],
    "livestock_units":  [("Grazing Livestock Units", "Total Livestock Units")],
    "labour_units":     [("LABOUR UNITS", "Total")],
}

# Price series in cso.db (item names verbatim), by our own short name. All are the
# price actually paid, taxes included. Sources, cadence and staleness: DATA-SOURCES.md.
PRICE_ITEMS: dict[str, str] = {
    "concentrates": "Dairy nuts and cubes (16-18% protein)",         # CSO AJM08, EUR/t, monthly
    "fertiliser": "Calcium Ammonium Nitrate (27.5% N)",                # CSO AJM09, EUR/t, monthly
    "diesel": "Heating gas oil (Ireland), with taxes",                 # EU Oil Bulletin, EUR/L, weekly
    "electricity": "Electricity, non-household band IA (<20 MWh), all taxes",  # Eurostat nrg_pc_205, EUR/kWh, half-yearly
}
CAN_N_FRACTION: float = 0.275        # kg N per kg of CAN
HOURS_PER_LABOUR_UNIT: float = 1800  # NFS definition of one labour unit
