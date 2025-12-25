from dataclasses import asdict
from dataclasses import dataclass

import astropy.units as u
import pytest

from dkist_processing_visp.tasks.visp_base import VispTaskBase


@dataclass
class testing_constants:
    arm_id: int = 2
    obs_ip_start_time: str = "1999-12-31T23:59:59"
    num_modstates: int = 10
    num_beams: int = 2
    num_cs_steps: int = 18
    num_raster_steps: int = 1000
    polarimeter_mode: str = "observe_polarimetric"
    wavelength: float = 666.6
    lamp_exposure_times: tuple[float] = (100.0,)
    solar_exposure_times: tuple[float] = (1.0,)
    observe_exposure_times: tuple[float] = (0.01,)
    lamp_readout_exp_times: tuple[float] = (200.0,)
    solar_readout_exp_times: tuple[float] = (2.0,)
    observe_readout_exp_times: tuple[float] = (0.02,)
    retarder_name: str = "SiO2 OC"
    incident_light_angle_deg: float = 74.2
    reflected_light_angle_deg: float = 71.3
    grating_constant_inverse_mm: float = 316.0
    solar_gain_ip_start_time: str = "2000-01-01T00:00:01"
    # We don't need all the common ones, but let's put one just to check
    instrument: str = "CHECK_OUT_THIS_INSTRUMENT"


@pytest.fixture(scope="session")
def unit_constant_names_and_units() -> dict[str, u.Unit]:
    return {
        "incident_light_angle_deg": u.deg,
        "reflected_light_angle_deg": u.deg,
        "grating_constant_inverse_mm": 1 / u.mm,
    }


@pytest.fixture(scope="session")
def expected_constant_dict() -> dict:
    lower_dict = asdict(testing_constants())
    return {k.upper(): v for k, v in lower_dict.items()}


@pytest.fixture(scope="function")
def visp_science_task_with_constants(recipe_run_id, expected_constant_dict, init_visp_constants_db):
    class Task(VispTaskBase):
        def run(self): ...

    init_visp_constants_db(recipe_run_id, expected_constant_dict)
    task = Task(
        recipe_run_id=recipe_run_id,
        workflow_name="parse_visp_input_data",
        workflow_version="VX.Y",
    )

    yield task

    task._purge()


def test_visp_constants(
    visp_science_task_with_constants, unit_constant_names_and_units, expected_constant_dict
):
    """
    Given: A task with an attached `VispConstants` object and a populated constants db
    When: Accessing values through the `.constants.VALUE` machinery
    Then: The correct values form the db are returned
    """
    task = visp_science_task_with_constants
    for k, v in expected_constant_dict.items():
        if k in ["ARM_ID", "POLARIMETER_MODE", "RETARDER_NAME"]:
            # These have some extra logic after db retrieval
            continue
        if k.lower() in unit_constant_names_and_units:
            united_value = getattr(task.constants, k.lower())
            assert united_value.value == v
            assert united_value.unit == unit_constant_names_and_units[k.lower()]
        else:
            if type(v) is tuple:
                v = list(v)
            assert getattr(task.constants, k.lower()) == v

    assert task.constants.correct_for_polarization == True
    assert task.constants.pac_init_set == "OCCal_VIS"
    assert task.constants.arm_id == str(expected_constant_dict["ARM_ID"])
