import json
from functools import partial
from typing import Callable

import asdf
import astropy.units as u
import numpy as np
import pytest
from asdf.tags.core import NDArrayType
from astropy import constants
from astropy.coordinates import EarthLocation
from astropy.stats import gaussian_fwhm_to_sigma
from astropy.time import Time
from dkist_processing_common._util.scratch import WorkflowFileSystem
from dkist_processing_common.codecs.fits import fits_array_decoder
from dkist_processing_common.codecs.fits import fits_array_encoder
from dkist_processing_common.models.tags import Tag
from scipy.ndimage import gaussian_filter1d
from sunpy.coordinates import HeliocentricInertial

from dkist_processing_visp.models.tags import VispTag
from dkist_processing_visp.tasks.solar import SolarCalibration
from dkist_processing_visp.tasks.solar import WavelengthCalibrationParametersWithContinuum
from dkist_processing_visp.tasks.solar import compute_initial_dispersion
from dkist_processing_visp.tests.conftest import VispConstantsDb
from dkist_processing_visp.tests.conftest import VispInputDatasetParameterValues
from dkist_processing_visp.tests.conftest import tag_on_modstate
from dkist_processing_visp.tests.conftest import write_frames_to_task
from dkist_processing_visp.tests.conftest import write_intermediate_background_to_task
from dkist_processing_visp.tests.conftest import write_intermediate_darks_to_task
from dkist_processing_visp.tests.conftest import write_intermediate_geometric_to_task
from dkist_processing_visp.tests.header_models import VispHeadersInputSolarGainFrames


def lamp_signal_func(beam: int):
    return 10 * beam


@pytest.fixture(scope="session")
def num_wave_pix() -> int:
    return 1000


@pytest.fixture(scope="session")
def telluric_opacity_factor() -> float:
    return 5.0


@pytest.fixture(scope="session")
def solar_ip_start_time() -> str:
    return "1988-07-02T10:00:00"


@pytest.fixture(scope="session")
def doppler_velocity(solar_ip_start_time) -> u.Quantity:
    _dkist_site_info = {
        "aliases": ["DKIST", "ATST"],
        "name": "Daniel K. Inouye Solar Telescope",
        "elevation": 3067,
        "elevation_unit": "meter",
        "latitude": 20.7067,
        "latitude_unit": "degree",
        "longitude": 203.7436,
        "longitude_unit": "degree",
        "timezone": "US/Hawaii",
        "source": "DKIST website: https://www.nso.edu/telescopes/dki-solar-telescope/",
    }
    location_of_dkist = EarthLocation.from_geodetic(
        _dkist_site_info["longitude"] * u.Unit(_dkist_site_info["longitude_unit"]),
        _dkist_site_info["latitude"] * u.Unit(_dkist_site_info["latitude_unit"]),
        _dkist_site_info["elevation"] * u.Unit(_dkist_site_info["elevation_unit"]),
    )

    coord = location_of_dkist.get_gcrs(obstime=Time(solar_ip_start_time))
    heliocentric_coord = coord.transform_to(HeliocentricInertial(obstime=Time(solar_ip_start_time)))
    obs_vr_kms = heliocentric_coord.d_distance

    return obs_vr_kms


@pytest.fixture(scope="session")
def central_wavelength() -> u.Quantity:
    return 854.2 * u.nm


@pytest.fixture(scope="session")
def grating_constant() -> u.Quantity:
    return 316.0 / u.mm


@pytest.fixture(scope="session")
def incident_light_angle() -> u.Quantity:
    return 73.22 * u.deg


@pytest.fixture(scope="session")
def reflected_light_angle() -> u.Quantity:
    return 68.76 * u.deg


@pytest.fixture(scope="session")
def pixel_pitch() -> u.Quantity:
    return 6.5 * u.micron / u.pix


@pytest.fixture(scope="session")
def lens_parameters_no_units() -> list[float]:
    return [0.7613, 1.720e-4, -8.139e-8]


@pytest.fixture(scope="session")
def lens_parameters(lens_parameters_no_units) -> list[u.Quantity]:
    return [
        lens_parameters_no_units[0] * u.m,
        lens_parameters_no_units[1] * u.m / u.nm,
        lens_parameters_no_units[2] * u.m / u.nm**2,
    ]


@pytest.fixture(scope="session")
def dispersion(
    central_wavelength, incident_light_angle, reflected_light_angle, lens_parameters, pixel_pitch
) -> u.Quantity:
    return compute_initial_dispersion(
        central_wavelength=central_wavelength,
        incident_light_angle=incident_light_angle,
        reflected_light_angle=reflected_light_angle,
        lens_parameters=lens_parameters,
        pixel_pitch=pixel_pitch,
    )


@pytest.fixture(scope="session")
def resolving_power() -> int:
    return int(1.15e5)


@pytest.fixture(scope="session")
def spectral_vignette_function(num_wave_pix) -> np.ndarray:
    return (np.arange(num_wave_pix) - num_wave_pix // 2) / (num_wave_pix * 10) + 1.0


@pytest.fixture
def observed_solar_spectrum(
    central_wavelength,
    dispersion,
    num_wave_pix,
    solar_atlas,
    telluric_opacity_factor,
    doppler_velocity,
    resolving_power,
) -> np.ndarray:
    """Make an "observed" solar spectrum from a shifted and atmospherically corrected combination of solar and telluric atlases."""
    # Making a simple solution with just y = mx + b (no higher order angle or order stuff)
    wave_vec = (
        np.arange(num_wave_pix) - num_wave_pix // 2
    ) * u.pix * dispersion + central_wavelength

    doppler_shift = doppler_velocity / constants.c * central_wavelength
    solar_signal = np.interp(
        wave_vec,
        solar_atlas.solar_atlas_wavelength + doppler_shift,
        solar_atlas.solar_atlas_transmission,
    )
    telluric_signal = (
        np.interp(
            wave_vec,
            solar_atlas.telluric_atlas_wavelength,
            solar_atlas.telluric_atlas_transmission,
        )
        ** telluric_opacity_factor
    )

    combined_spec = solar_signal * telluric_signal

    sigma_wavelength = (
        central_wavelength.to_value(u.nm) / resolving_power
    ) * gaussian_fwhm_to_sigma
    sigma_pix = sigma_wavelength / np.abs(dispersion.to_value(u.nm / u.pix))
    observed_spec = gaussian_filter1d(combined_spec, np.abs(sigma_pix))

    return observed_spec


def write_full_set_of_intermediate_lamp_cals_to_task(
    task,
    data_shape: tuple[int, int],
    lamp_signal_func: Callable[[int], float] = lamp_signal_func,
):
    for beam in [1, 2]:
        lamp_signal = lamp_signal_func(beam)
        lamp_array = np.ones(data_shape) * lamp_signal
        task.write(
            data=lamp_array,
            tags=[
                VispTag.intermediate_frame(beam=beam),
                VispTag.task_lamp_gain(),
            ],
            encoder=fits_array_encoder,
        )


def make_solar_input_array_data(
    frame: VispHeadersInputSolarGainFrames,
    dark_signal: float,
    true_solar_signal: np.ndarray,
    spectral_vignette_signal: np.ndarray,
    lamp_signal_func: Callable[[int], float] = lamp_signal_func,
):
    data_shape = frame.array_shape[1:]
    beam_shape = (data_shape[0] // 2, data_shape[1])
    modstate = frame.current_modstate("")  # Weird signature due to key_function
    num_raw_per_fpa = frame.header()["CAM__014"]

    beam_list = []
    for beam in [1, 2]:
        true_gain = np.ones(beam_shape) * spectral_vignette_signal[:, None]
        true_solar_gain = true_gain * true_solar_signal[:, None]
        lamp_signal = lamp_signal_func(beam)
        raw_beam = (true_solar_gain * lamp_signal) + dark_signal
        if beam == 2:
            beam_list.append(raw_beam[::-1, :])
        else:
            beam_list.append(raw_beam)

    raw_solar = np.concatenate(beam_list) * num_raw_per_fpa
    return raw_solar


def write_input_solar_gains_to_task(
    task,
    data_shape: tuple[int, int],
    dark_signal: float,
    readout_exp_time: float,
    num_modstates: int,
    true_solar_signal: np.ndarray,
    spectra_vignette_signal: np.ndarray,
    lamp_signal_func: Callable[[int, int], float] = lamp_signal_func,
):
    array_shape = (1, *data_shape)
    dataset = VispHeadersInputSolarGainFrames(
        array_shape=array_shape,
        time_delta=10,
        num_modstates=num_modstates,
    )
    data_func = partial(
        make_solar_input_array_data,
        dark_signal=dark_signal,
        lamp_signal_func=lamp_signal_func,
        true_solar_signal=true_solar_signal,
        spectral_vignette_signal=spectra_vignette_signal,
    )
    write_frames_to_task(
        task=task,
        frame_generator=dataset,
        extra_tags=[
            VispTag.input(),
            VispTag.task_solar_gain(),
            VispTag.readout_exp_time(readout_exp_time),
        ],
        tag_func=tag_on_modstate,
        data_func=data_func,
    )


@pytest.fixture(scope="function")
def solar_gain_task(
    tmp_path,
    recipe_run_id,
    init_visp_constants_db,
    central_wavelength,
    incident_light_angle,
    reflected_light_angle,
    grating_constant,
    solar_ip_start_time,
):
    number_of_modstates = 3
    readout_exp_time = 40.0
    constants_db = VispConstantsDb(
        ARM_ID=1,
        WAVELENGTH=central_wavelength.to_value(u.nm),
        NUM_MODSTATES=number_of_modstates,
        SOLAR_READOUT_EXP_TIMES=(readout_exp_time,),
        SOLAR_GAIN_IP_START_TIME=solar_ip_start_time,
        INCIDENT_LIGHT_ANGLE_DEG=incident_light_angle.to_value(u.deg),
        REFLECTED_LIGHT_ANGLE_DEG=reflected_light_angle.to_value(u.deg),
        GRATING_CONSTANT_INVERSE_MM=grating_constant.to_value(1 / u.mm),
    )
    init_visp_constants_db(recipe_run_id, constants_db)
    with SolarCalibration(
        recipe_run_id=recipe_run_id, workflow_name="geometric_calibration", workflow_version="VX.Y"
    ) as task:
        try:  # This try... block is here to make sure the dbs get cleaned up if there's a failure in the fixture
            task.scratch = WorkflowFileSystem(
                scratch_base_path=tmp_path, recipe_run_id=recipe_run_id
            )

            yield task, readout_exp_time, number_of_modstates
        except:
            raise
        finally:
            task._purge()


@pytest.mark.parametrize(
    "background_on",
    [
        pytest.param(True, id="background_on"),
        pytest.param(False, id="background_off"),
    ],
)
def test_solar_gain_task(
    solar_gain_task,
    background_on,
    num_wave_pix,
    spectral_vignette_function,
    observed_solar_spectrum,
    solar_ip_start_time,
    lens_parameters_no_units,
    resolving_power,
    telluric_opacity_factor,
    assign_input_dataset_doc_to_task,
    mocker,
    fake_gql_client,
):
    """
    Given: A set of raw solar gain images and necessary intermediate calibrations
    When: Running the solargain task
    Then: The task completes and the outputs are correct
    """
    mocker.patch(
        "dkist_processing_common.tasks.mixin.metadata_store.GraphQLClient", new=fake_gql_client
    )

    task, readout_exp_time, num_modstates = solar_gain_task
    dark_signal = 3.0
    input_shape = (num_wave_pix * 2, 100)
    intermediate_shape = (num_wave_pix, 100)
    beam_border = input_shape[0] // 2
    assign_input_dataset_doc_to_task(
        task,
        VispInputDatasetParameterValues(
            visp_background_on=background_on,
            visp_beam_border=beam_border,
            visp_wavecal_init_opacity_factor=telluric_opacity_factor,
            visp_wavecal_init_resolving_power=resolving_power,
            visp_wavecal_camera_lens_parameters_1=lens_parameters_no_units,
            visp_solar_vignette_initial_continuum_poly_fit_order=1,
        ),
        arm_id=1,
    )
    write_intermediate_darks_to_task(
        task=task,
        dark_signal=dark_signal,
        readout_exp_time=readout_exp_time,
        data_shape=intermediate_shape,
    )
    if background_on:
        write_intermediate_background_to_task(
            task=task, background_signal=0.0, data_shape=intermediate_shape
        )
    write_full_set_of_intermediate_lamp_cals_to_task(
        task=task,
        data_shape=intermediate_shape,
    )
    write_intermediate_geometric_to_task(
        task=task, num_modstates=num_modstates, data_shape=intermediate_shape
    )
    write_input_solar_gains_to_task(
        task=task,
        data_shape=input_shape,
        dark_signal=dark_signal,
        readout_exp_time=readout_exp_time,
        num_modstates=num_modstates,
        true_solar_signal=observed_solar_spectrum,
        spectra_vignette_signal=spectral_vignette_function,
    )

    task()
    for beam in range(1, task.constants.num_beams + 1):
        # We need to multiply by the percentile normalization factor that is divided from the characteristic spectra.
        # I.e., the `true_solar_signal` defined above is modified by this scalar prior to removal from the raw spectra
        # so we need to undo that modification here.
        expected_signal = (
            np.ones(intermediate_shape)
            * spectral_vignette_function[:, None]
            * 10
            * beam  # Lamp signal
            * np.nanpercentile(
                observed_solar_spectrum,
                task.parameters.solar_characteristic_spatial_normalization_percentile,
            )
        )

        solar_gain = next(
            task.read(
                tags=[
                    VispTag.intermediate_frame(beam=beam),
                    VispTag.task_solar_gain(),
                ],
                decoder=fits_array_decoder,
            )
        )

        # Testing that the ratio is close to 1.0 give us a bit more leeway in the deviation
        np.testing.assert_allclose(expected_signal / solar_gain, 1.0, atol=1e-2, rtol=1e-2)

    quality_files = task.read(tags=[Tag.quality("TASK_TYPES")])
    for file in quality_files:
        with file.open() as f:
            data = json.load(f)
            assert isinstance(data, dict)
            assert data["total_frames"] == task.scratch.count_all(
                tags=[VispTag.input(), VispTag.frame(), VispTag.task_solar_gain()]
            )

    first_vignette_quality_files = list(task.read(tags=[Tag.quality("SOLAR_CAL_FIRST_VIGNETTE")]))
    assert len(first_vignette_quality_files) == 2
    for beam_file in first_vignette_quality_files:
        with asdf.open(beam_file, lazy_load=False, memmap=False) as f:
            results = f.tree
            assert isinstance(results["output_wave_vec"], NDArrayType)
            assert isinstance(results["input_spectrum"], NDArrayType)
            assert isinstance(results["best_fit_atlas"], NDArrayType)
            assert isinstance(results["best_fit_continuum"], NDArrayType)
            assert isinstance(results["residuals"], NDArrayType)

    final_vignette_quality_files = list(task.read(tags=[Tag.quality("SOLAR_CAL_FINAL_VIGNETTE")]))
    assert len(final_vignette_quality_files) == 2
    for beam_file in final_vignette_quality_files:
        with asdf.open(beam_file, lazy_load=False, memmap=False) as f:
            results = f.tree
            assert isinstance(results["output_wave_vec"], NDArrayType)
            assert isinstance(results["median_spec"], NDArrayType)
            assert isinstance(results["low_deviation"], NDArrayType)
            assert isinstance(results["high_deviation"], NDArrayType)


def test_continuum_wavecal_parameters():
    """
    Given: A `WavelengthCalibrationParametersWithContinuum` class instantiated with a poly fit order
    When: Constructing the `lmfit_parameters` object
    Then: The polynomial coefficients are present
    """
    order = 3
    zeroth_order = 6.28
    param_object = WavelengthCalibrationParametersWithContinuum(
        continuum_poly_fit_order=order,
        zeroth_order_continuum_coefficient=zeroth_order,
        crval=400 * u.nm,
        dispersion=3 * u.nm / u.pix,
        incident_light_angle=4 * u.deg,
        grating_constant=3 / u.mm,
        doppler_velocity=0 * u.km / u.s,
        order=1,
        normalized_abscissa=np.arange(10),
        continuum_level=99999.9,
    )
    lmfit_params = param_object.lmfit_parameters

    assert "poly_coeff_03" in lmfit_params
    assert "poly_coeff_02" in lmfit_params
    assert "poly_coeff_01" in lmfit_params
    assert "poly_coeff_00" in lmfit_params

    assert lmfit_params["poly_coeff_03"].init_value == zeroth_order
    assert lmfit_params["poly_coeff_02"].init_value == 0
    assert lmfit_params["poly_coeff_01"].init_value == 0
    assert lmfit_params["poly_coeff_00"].init_value == 0

    assert lmfit_params["poly_coeff_03"].min == zeroth_order * 0.5
    assert lmfit_params["poly_coeff_03"].max == zeroth_order * 1.5
    assert lmfit_params["poly_coeff_02"].min == -1
    assert lmfit_params["poly_coeff_02"].max == 1
    assert lmfit_params["poly_coeff_01"].min == -1
    assert lmfit_params["poly_coeff_01"].max == 1
    assert lmfit_params["poly_coeff_00"].min == -1
    assert lmfit_params["poly_coeff_00"].max == 1
