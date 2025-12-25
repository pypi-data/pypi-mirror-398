"""ViSP FITS access for L0 data."""

from astropy.io import fits
from dkist_processing_common.parsers.l0_fits_access import L0FitsAccess

from dkist_processing_visp.models.fits_access import VispMetadataKey


class VispL0FitsAccess(L0FitsAccess):
    """
    Class to provide easy access to L0 headers.

    i.e. instead of <VispL0FitsAccess>.header['key'] this class lets us use <VispL0FitsAccess>.key instead

    Parameters
    ----------
    hdu :
        Fits L0 header object

    name : str
        The name of the file that was loaded into this FitsAccess object

    auto_squeeze : bool
        When set to True, dimensions of length 1 will be removed from the array
    """

    def __init__(
        self,
        hdu: fits.ImageHDU | fits.PrimaryHDU | fits.CompImageHDU,
        name: str | None = None,
        auto_squeeze: bool = True,
    ):
        super().__init__(hdu=hdu, name=name, auto_squeeze=auto_squeeze)

        self.arm_id: int = self.header[VispMetadataKey.arm_id]
        self.number_of_modulator_states: int = self.header[
            VispMetadataKey.number_of_modulator_states
        ]
        self.raster_scan_step: int = self.header[VispMetadataKey.raster_scan_step]
        self.total_raster_steps: int = self.header[VispMetadataKey.total_raster_steps]
        self.modulator_state: int = self.header[VispMetadataKey.modulator_state]
        self.polarimeter_mode: str = self.header[VispMetadataKey.polarimeter_mode]
        self.grating_angle_deg: float = self.header[VispMetadataKey.grating_angle_deg]
        self.arm_position_deg: float = self.header[VispMetadataKey.arm_position_deg]
        self.grating_constant_inverse_mm: float = self.header[
            VispMetadataKey.grating_constant_inverse_mm
        ]
        self.axis_1_type: str = self.header[VispMetadataKey.axis_1_type]
        self.axis_2_type: str = self.header[VispMetadataKey.axis_2_type]
        self.axis_3_type: str = self.header[VispMetadataKey.axis_3_type]
