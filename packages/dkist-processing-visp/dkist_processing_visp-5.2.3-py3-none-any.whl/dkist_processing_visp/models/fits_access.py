"""ViSP control of FITS key names and values."""

from enum import StrEnum


class VispMetadataKey(StrEnum):
    """Controlled list of names for FITS metadata header keys."""

    arm_id = "VSPARMID"
    number_of_modulator_states = "VSPNUMST"
    raster_scan_step = "VSPSTP"
    total_raster_steps = "VSPNSTP"
    modulator_state = "VSPSTNUM"
    polarimeter_mode = "VISP_006"
    grating_angle_deg = "VSPGRTAN"
    arm_position_deg = "VSPARMPS"
    grating_constant_inverse_mm = "VSPGRTCN"
    axis_1_type = "CTYPE1"
    axis_2_type = "CTYPE2"
    axis_3_type = "CTYPE3"
