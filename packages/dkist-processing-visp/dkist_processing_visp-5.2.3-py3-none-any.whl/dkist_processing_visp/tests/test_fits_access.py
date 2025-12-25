import pytest
from dkist_header_validator.translator import translate_spec122_to_spec214_l0

from dkist_processing_visp.models.fits_access import VispMetadataKey
from dkist_processing_visp.parsers.visp_l0_fits_access import VispL0FitsAccess
from dkist_processing_visp.parsers.visp_l1_fits_access import VispL1FitsAccess
from dkist_processing_visp.tests.header_models import VispHeadersValidObserveFrames


@pytest.fixture(scope="session")
def complete_header():
    dataset = VispHeadersValidObserveFrames(
        array_shape=(1, 1, 1),
        time_delta=10,
        num_maps=1,
        num_raster_steps=1,
        num_modstates=1,
    )
    header = translate_spec122_to_spec214_l0(dataset.header())
    return header


def test_metadata_keys_in_access_bases(complete_header):
    """
    Given: the set of metadata key names in VispMetadataKey
    When: the ViSP FITS access classes define a set of new attributes
    Then: the sets are the same and the attributes have the correct values
    """
    # Given
    visp_metadata_key_names = {vmk.name for vmk in VispMetadataKey}
    # When
    all_visp_fits_access_attrs = set()
    for access_class in [VispL0FitsAccess, VispL1FitsAccess]:
        fits_obj = access_class.from_header(complete_header)
        visp_instance_attrs = set(vars(fits_obj).keys())
        parent_class = access_class.mro()[1]
        parent_fits_obj = parent_class.from_header(complete_header)
        parent_instance_attrs = set(vars(parent_fits_obj).keys())
        visp_fits_access_attrs = visp_instance_attrs - parent_instance_attrs
        for attr in visp_fits_access_attrs:
            assert getattr(fits_obj, attr) == fits_obj.header[VispMetadataKey[attr]]
        all_visp_fits_access_attrs |= visp_fits_access_attrs
    assert visp_metadata_key_names == all_visp_fits_access_attrs
