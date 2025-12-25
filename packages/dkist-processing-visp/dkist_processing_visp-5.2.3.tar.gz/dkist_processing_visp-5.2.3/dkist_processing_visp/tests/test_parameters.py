from dataclasses import asdict
from dataclasses import dataclass

import astropy.units as u
import numpy as np
import pytest
from hypothesis import HealthCheck
from hypothesis import example
from hypothesis import given
from hypothesis import settings
from hypothesis import strategies as st
from pydantic import BaseModel

from dkist_processing_visp.models.parameters import VispParameters
from dkist_processing_visp.models.parameters import VispParsingParameters
from dkist_processing_visp.tasks.visp_base import VispTaskBase
from dkist_processing_visp.tests.conftest import VispConstantsDb
from dkist_processing_visp.tests.conftest import VispInputDatasetParameterValues


@pytest.fixture(scope="session")
def parse_parameter_names() -> list[str]:
    # The property names of all parameters on `VispParsingParameters`
    return [k for k, v in vars(VispParsingParameters).items() if isinstance(v, property)]


@pytest.fixture(scope="session")
def arm_parameter_names() -> list[str]:
    return [
        "wavecal_camera_lens_parameters",
    ]


@pytest.fixture(scope="session")
def unit_parameter_names_and_units() -> dict[str, u.Unit | list[u.Unit]]:
    return {
        "solar_vignette_crval_bounds_px": u.pix,
        "wavecal_camera_lens_parameters": [u.m, u.m / u.nm, u.m / u.nm**2],
        "wavecal_pixel_pitch_micron_per_pix": u.um / u.pix,
        "wavecal_crval_bounds_px": u.pix,
        "wavecal_incident_light_angle_bounds_deg": u.deg,
    }


@pytest.fixture(scope="function")
def basic_science_task_with_parameter_mixin(
    recipe_run_id,
    assign_input_dataset_doc_to_task,
    init_visp_constants_db,
    testing_obs_ip_start_time,
    arm_id,
):
    def make_task(
        parameters_part: dataclass,
        parameter_class=VispParameters,
        obs_ip_start_time=testing_obs_ip_start_time,
    ):
        class Task(VispTaskBase):
            def run(self): ...

        init_visp_constants_db(recipe_run_id, VispConstantsDb())
        task = Task(
            recipe_run_id=recipe_run_id,
            workflow_name="parse_visp_input_data",
            workflow_version="VX.Y",
        )
        try:  # This try... block is here to make sure the dbs get cleaned up if there's a failure in the fixture
            assign_input_dataset_doc_to_task(
                task,
                parameters_part,
                parameter_class=parameter_class,
                obs_ip_start_time=obs_ip_start_time,
                arm_id=arm_id,
            )
            yield task, asdict(parameters_part)
        except:
            raise
        finally:
            task._purge()

    return make_task


@pytest.mark.parametrize("arm_id", [pytest.param("1"), pytest.param("2"), pytest.param("3")])
def test_non_wave_parameters(
    basic_science_task_with_parameter_mixin,
    parse_parameter_names,
    arm_parameter_names,
    unit_parameter_names_and_units,
    arm_id,
):
    """
    Given: A Science task with the parameter mixin
    When: Accessing properties for parameters that do not depend on wavelength
    Then: The correct value is returned
    """
    task, expected = next(
        basic_science_task_with_parameter_mixin(VispInputDatasetParameterValues())
    )
    task_param_attr = task.parameters
    parameter_properties = [k for k, v in vars(VispParameters).items() if isinstance(v, property)]
    for parameter_name in parameter_properties:
        pn = f"visp_{parameter_name}"
        if parameter_name in arm_parameter_names:
            pn = f"{pn}_{arm_id}"
        pv = expected[pn]
        is_wavelength_param = isinstance(pv, dict) and "wavelength" in pv
        if (
            parameter_name not in parse_parameter_names
            and not is_wavelength_param
            and parameter_name not in ["solar_vignette_wavecal_fit_kwargs", "wavecal_fit_kwargs"]
        ):
            param_obj_value = getattr(task_param_attr, parameter_name)
            if isinstance(pv, tuple):
                pv = list(pv)

            if parameter_name in unit_parameter_names_and_units:
                expected_units = unit_parameter_names_and_units[parameter_name]
                if not isinstance(param_obj_value, list):
                    param_obj_value = [param_obj_value]
                    pv = [pv]
                    expected_units = [expected_units]

                assert all([param_obj_value[i].value == pv[i] for i in range(len(pv))])
                assert all(
                    [param_obj_value[i].unit == expected_units[i] for i in range(len(pv))]
                ), f"Units {[v.unit for v in param_obj_value]} does not match expected {expected_units}"
            elif isinstance(param_obj_value, BaseModel):
                assert param_obj_value.model_dump() == pv
            else:
                assert getattr(task_param_attr, parameter_name) == pv


@pytest.mark.parametrize("arm_id", ["1"])
def test_parse_parameters(basic_science_task_with_parameter_mixin, parse_parameter_names):
    """
    Given: A Science task with Parsing parameters
    When: Accessing properties for Parse parameters
    Then: The correct value is returned
    """
    task, expected = next(
        basic_science_task_with_parameter_mixin(
            VispInputDatasetParameterValues(),
            parameter_class=VispParsingParameters,
            obs_ip_start_time=None,
        )
    )
    task_param_attr = task.parameters
    for pn, pv in expected.items():
        property_name = pn.removeprefix("visp_")
        if property_name in parse_parameter_names and type(pv) is not dict:
            assert getattr(task_param_attr, property_name) == pv


@given(wave=st.floats(min_value=500.0, max_value=2000.0))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@example(wave=492.5)
@pytest.mark.parametrize("arm_id", ["1"])
def test_wave_parameters(
    basic_science_task_with_parameter_mixin, parse_parameter_names, arm_parameter_names, wave
):
    """
    Given: A Science task with the paramter mixin
    When: Accessing properties for parameters that depend on wavelength
    Then: The correct value is returned
    """
    task, expected = next(
        basic_science_task_with_parameter_mixin(VispInputDatasetParameterValues())
    )
    task_param_attr = task.parameters
    task_param_attr._wavelength = wave
    pwaves = np.array(expected["visp_geo_zone_normalization_percentile"]["wavelength"])
    midpoints = 0.5 * (pwaves[1:] + pwaves[:-1])
    idx = np.sum(midpoints < wave)
    for pn, pv in expected.items():
        property_name = pn.removeprefix("visp_")
        is_wavelength_param = isinstance(pv, dict) and "wavelength" in pv
        if is_wavelength_param and property_name not in parse_parameter_names + arm_parameter_names:
            assert getattr(task_param_attr, property_name) == pv["values"][idx]


class AnyInt:
    pass


@pytest.mark.parametrize("arm_id", [pytest.param("1")])
@pytest.mark.parametrize(
    "db_value, expected",
    [
        pytest.param({"method": "nelder"}, {"method": "nelder"}, id="non_rng_method"),
        pytest.param(
            {"method": "basinhopping"}, {"method": "basinhopping", "rng": AnyInt}, id="random_rng"
        ),
        pytest.param(
            {"method": "differential_evolution", "rng": 6.28},
            {"method": "differential_evolution", "rng": 6.28},
            id="override_rng",
        ),
        pytest.param(dict(), dict(), id="no_kwargs"),
    ],
)
@pytest.mark.parametrize(
    "fit_kwarg_name", ["visp_solar_vignette_wavecal_fit_kwargs", "visp_wavecal_fit_kwargs"]
)
def test_fit_kwarg_parameters(
    basic_science_task_with_parameter_mixin,
    db_value,
    expected,
    fit_kwarg_name,
):
    """
    Given: A Science task with the parameter mixin
    When: Accessing properties for parameters that do not depend on wavelength
    Then: The correct value is returned
    """
    kwargs = {fit_kwarg_name: db_value}

    task, _ = next(
        basic_science_task_with_parameter_mixin(VispInputDatasetParameterValues(**kwargs))
    )
    kwarg_dict = getattr(task.parameters, fit_kwarg_name.removeprefix("visp_"))
    assert kwarg_dict.keys() == expected.keys()
    for k in expected.keys():
        if expected[k] is AnyInt:
            assert type(kwarg_dict[k]) is int
        else:
            assert expected[k] == kwarg_dict[k]
