import json

import astropy.units as u
import numpy as np
import pytest
from astropy.stats import gaussian_fwhm_to_sigma
from astropy.units import Quantity
from dkist_processing_common._util.scratch import WorkflowFileSystem
from dkist_processing_common.codecs.fits import fits_array_encoder
from dkist_processing_common.codecs.json import json_decoder
from dkist_processing_common.models.metric_code import MetricCode
from scipy.ndimage import gaussian_filter

from dkist_processing_visp.models.tags import VispTag
from dkist_processing_visp.tasks.wavelength_calibration import WavelengthCalibration
from dkist_processing_visp.tasks.wavelength_calibration import compute_initial_dispersion
from dkist_processing_visp.tasks.wavelength_calibration import compute_input_wavelength_vector
from dkist_processing_visp.tasks.wavelength_calibration import compute_order
from dkist_processing_visp.tests.conftest import VispConstantsDb
from dkist_processing_visp.tests.conftest import VispInputDatasetParameterValues


@pytest.fixture(scope="session")
def opacity_factor() -> float:
    return 0.8


@pytest.fixture(scope="session")
def continuum_level() -> float:
    return 1.1


@pytest.fixture(scope="session")
def straylight_fraction() -> float:
    return 0.7


@pytest.fixture(scope="session")
def offset_factor() -> Quantity:
    # Given the wavelength we're using, a negative value here lets us have a larger offset. Positive offsets of a similar
    # magnitude at the same wavelength range push us into a tough-to-fit region of the spectrum.
    return 0.15 * u.nm


@pytest.fixture(scope="session")
def num_wave_pix() -> int:
    return 1000


@pytest.fixture(scope="session")
def wavelength() -> u.Quantity:
    return 589.23 * u.nm


@pytest.fixture(scope="session")
def grating_constant() -> u.Quantity:
    return 316.0 / u.mm


@pytest.fixture(scope="session")
def order() -> int:
    return 10


@pytest.fixture(scope="session")
def incident_light_angle() -> u.Quantity:
    return 73.22 * u.deg


@pytest.fixture(scope="session")
def reflected_light_angle() -> u.Quantity:
    return 64.91983 * u.deg


@pytest.fixture(scope="session")
def pixel_pitch() -> u.Quantity:
    return 6.5 * u.micron / u.pix


@pytest.fixture(scope="session")
def lens_parameters_no_units() -> list[float]:
    return [0.9512, 2.141e-4, -1.014e-7]


@pytest.fixture(scope="session")
def lens_parameters(lens_parameters_no_units) -> list[u.Quantity]:
    return [
        lens_parameters_no_units[0] * u.m,
        lens_parameters_no_units[1] * u.m / u.nm,
        lens_parameters_no_units[2] * u.m / u.nm**2,
    ]


@pytest.fixture(scope="session")
def dispersion(
    wavelength, incident_light_angle, reflected_light_angle, lens_parameters, pixel_pitch
) -> u.Quantity:
    return compute_initial_dispersion(
        central_wavelength=wavelength,
        incident_light_angle=incident_light_angle,
        reflected_light_angle=reflected_light_angle,
        lens_parameters=lens_parameters,
        pixel_pitch=pixel_pitch,
    )


@pytest.fixture(scope="session")
def resolving_power() -> int:
    return int(1.15e5)


@pytest.fixture(scope="function")
def visp_wavelength_correction_task(
    tmp_path,
    recipe_run_id,
    assign_input_dataset_doc_to_task,
    init_visp_constants_db,
    wavelength,
    solar_atlas,
    dispersion,
    num_wave_pix,
    resolving_power,
    incident_light_angle,
    reflected_light_angle,
    grating_constant,
    order,
    offset_factor,
    opacity_factor,
    continuum_level,
    straylight_fraction,
    num_start_nans,
):
    num_beams = 2
    char_spec_shape = (num_wave_pix, 2560)
    arm_id = 2

    constants_db = VispConstantsDb(
        NUM_BEAMS=num_beams,
        INCIDENT_LIGHT_ANGLE_DEG=incident_light_angle.value,
        GRATING_CONSTANT_INVERSE_MM=grating_constant.value,
        ARM_ID=arm_id,
        REFLECTED_LIGHT_ANGLE_DEG=reflected_light_angle.value,
        WAVELENGTH=wavelength.value,
    )
    init_visp_constants_db(recipe_run_id, constants_db)
    with WavelengthCalibration(
        recipe_run_id=recipe_run_id,
        workflow_name="wavelength_correction",
        workflow_version="VX.Y",
    ) as task:
        try:  # This try... block is here to make sure the dbs get cleaned up if there's a failure in the fixture

            # Create a realistic spectra
            wave_vec = compute_input_wavelength_vector(
                central_wavelength=wavelength,
                dispersion=dispersion,
                grating_constant=grating_constant,
                order=order,
                incident_light_angle=incident_light_angle,
                num_spec_px=num_wave_pix,
            )

            # Simulate a "realistic" input spectra with errors that need to be corrected
            solar_signal = np.interp(
                wave_vec,
                solar_atlas.solar_atlas_wavelength + offset_factor,
                solar_atlas.solar_atlas_transmission,
            )
            telluric_signal = np.interp(
                wave_vec,
                solar_atlas.telluric_atlas_wavelength + offset_factor,
                solar_atlas.telluric_atlas_transmission,
            )

            combined_spec_1d = solar_signal * telluric_signal
            combined_spec_1d_with_error = (
                combined_spec_1d**opacity_factor * continuum_level + straylight_fraction
            )

            sigma_wavelength = (
                wavelength.to_value(u.nm) / resolving_power
            ) * gaussian_fwhm_to_sigma
            sigma_pix = sigma_wavelength / np.abs(dispersion.to_value(u.nm / u.pix))
            spec_1d = gaussian_filter(combined_spec_1d_with_error, np.abs(sigma_pix))

            spec_1d[:num_start_nans] = np.nan

            spec = np.ones(char_spec_shape) * spec_1d[:, None]

            task.scratch = WorkflowFileSystem(
                scratch_base_path=tmp_path, recipe_run_id=recipe_run_id
            )
            params = VispInputDatasetParameterValues()
            assign_input_dataset_doc_to_task(task, params)

            # Create fake solar charcteristic spectra for one beam
            task.write(
                data=spec,
                tags=[
                    VispTag.intermediate_frame(beam=1),
                    VispTag.task_characteristic_spectra(),
                ],
                encoder=fits_array_encoder,
            )

            yield task
        except:
            raise
        finally:
            task._purge()


@pytest.mark.parametrize(
    "num_start_nans", [pytest.param(17, id="with_nans"), pytest.param(0, id="no_nans")]
)
def test_wavelength_correction(
    visp_wavelength_correction_task,
    mocker,
    fake_gql_client,
    wavelength,
    dispersion,
    offset_factor,
    incident_light_angle,
    num_wave_pix,
    num_start_nans,
):
    """
    Given: A `WavelengthCalibration` task with all the data needed to run
    When: Running the task
    Then: The correct output files are produced and the wavelength solution is close to what's expected
    """
    mocker.patch(
        "dkist_processing_common.tasks.mixin.metadata_store.GraphQLClient", new=fake_gql_client
    )

    task = visp_wavelength_correction_task
    task()
    tags = [
        VispTag.task_wavelength_calibration(),
        VispTag.intermediate(),
    ]
    fit_result = next(task.read(tags=tags, decoder=json_decoder))

    expected_crval = wavelength - offset_factor

    wavelength_solution_header_files = list(
        task.read(tags=[VispTag.intermediate(), VispTag.task_wavelength_calibration()])
    )
    assert len(wavelength_solution_header_files) == 1
    with open(wavelength_solution_header_files[0], "r") as f:
        wavecal_header_dict = json.load(f)

    # `num_wave_pix - num_start_nans` is the length of the input spectrum that the wavecal library sees
    assert fit_result["CRPIX2"] == (num_wave_pix - num_start_nans) // 2 + 1 + num_start_nans
    np.testing.assert_allclose(fit_result["CDELT2"], dispersion.value, rtol=1e-2)
    np.testing.assert_allclose(
        wavecal_header_dict["CRVAL2"], expected_crval.to_value(u.nm), rtol=1e-5
    )
    assert wavecal_header_dict["PV2_0"] == task.constants.grating_constant_inverse_mm.to_value(
        1 / u.m
    )
    assert wavecal_header_dict["PV2_1"] == compute_order(
        central_wavelength=wavelength,
        incident_light_angle=incident_light_angle,
        reflected_light_angle=task.constants.reflected_light_angle_deg,
        grating_constant=task.constants.grating_constant_inverse_mm,
    )

    np.testing.assert_allclose(
        wavecal_header_dict["PV2_2"], incident_light_angle.to_value(u.deg), rtol=1e-2
    )

    for primary_key in filter(lambda k: not k.endswith("A"), wavecal_header_dict.keys()):
        assert (
            wavecal_header_dict[primary_key] == wavecal_header_dict[f"{primary_key}A"]
        ), f"{primary_key} does not match {primary_key}A"

    quality_files = list(task.read(tags=[VispTag.quality(MetricCode.wavecal_fit)]))
    assert len(quality_files) == 1
    with open(quality_files[0]) as f:
        quality_dict = json.load(f)
        assert sorted(
            [
                "input_wavelength_nm",
                "input_spectrum",
                "best_fit_wavelength_nm",
                "best_fit_atlas",
                "normalized_residuals",
                "weights",
            ]
        ) == sorted(list(quality_dict.keys()))
