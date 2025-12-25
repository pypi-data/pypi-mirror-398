"""Controlled list of visp-specific task tag names."""

from enum import Enum


class VispTaskName(str, Enum):
    """Controlled list of task tag names."""

    background = "BACKGROUND"
    solar_char_spec = "SOLAR_CHAR_SPEC"
    wavelength_calibration = "WAVELENGTH_CALIBRATION"
