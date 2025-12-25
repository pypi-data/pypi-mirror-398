"""Controlled list of quality metric codes."""

from enum import StrEnum


class VispMetricCode(StrEnum):
    """Controlled list of quality metric codes."""

    solar_first_vignette = "SOLAR_CAL_FIRST_VIGNETTE"
    solar_final_vignette = "SOLAR_CAL_FINAL_VIGNETTE"
