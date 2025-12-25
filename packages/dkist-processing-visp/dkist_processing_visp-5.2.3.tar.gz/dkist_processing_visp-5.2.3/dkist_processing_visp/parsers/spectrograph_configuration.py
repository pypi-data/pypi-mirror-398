"""Buds for parsing the incident and reflected light angles of the ViSP spectrograph."""

from dkist_processing_common.models.flower_pot import SpilledDirt
from dkist_processing_common.models.flower_pot import Stem
from dkist_processing_common.models.task_name import TaskName
from dkist_processing_common.parsers.task import parse_header_ip_task_with_gains
from dkist_processing_common.parsers.unique_bud import TaskUniqueBud

from dkist_processing_visp.models.constants import VispBudName
from dkist_processing_visp.models.fits_access import VispMetadataKey
from dkist_processing_visp.parsers.visp_l0_fits_access import VispL0FitsAccess


def convert_grating_angle_to_incident_light_angle(grating_angle: float) -> float:
    """Convert the raw header "grating angle" to the incident light angle expected by the solar wavecal library."""
    return -1 * grating_angle


class IncidentLightAngleBud(TaskUniqueBud):
    """Special case of `TaskUniqueBud` so we can apply the sign shift to the header incident light angle values."""

    def __init__(self):
        super().__init__(
            constant_name=VispBudName.incident_light_angle_deg.value,
            metadata_key=VispMetadataKey.grating_angle_deg,
            ip_task_types=[TaskName.observe.value, TaskName.solar_gain.value],
            task_type_parsing_function=parse_header_ip_task_with_gains,
        )

    def setter(self, fits_obj: VispL0FitsAccess) -> float | type[SpilledDirt]:
        """Apply a sign flip to the raw header value for incident light angle."""
        grating_angle = super().setter(fits_obj)

        if grating_angle is SpilledDirt:
            return grating_angle

        return convert_grating_angle_to_incident_light_angle(grating_angle)


class ReflectedLightAngleBud(Stem):
    """Bud that combines the incident light angle and arm position header values to compute the reflected light angle."""

    key_to_petal_dict: dict[str, float]

    def __init__(self):
        super().__init__(stem_name=VispBudName.reflected_light_angle_deg.value)
        self.ip_task_types = [
            task.casefold() for task in [TaskName.observe.value, TaskName.solar_gain.value]
        ]

    def setter(self, fits_obj: VispL0FitsAccess) -> float | type[SpilledDirt]:
        """
        Compute the reflected light angle.

        The reflected light angle is `-1 * fits_objs.grating_angle_deg + fits_obj.arm_position_deg`.
        """
        task = parse_header_ip_task_with_gains(fits_obj)

        if task.casefold() in self.ip_task_types:
            incident_light_angle = convert_grating_angle_to_incident_light_angle(
                fits_obj.grating_angle_deg
            )
            arm_position = fits_obj.arm_position_deg
            return incident_light_angle + arm_position

        return SpilledDirt

    def getter(self, key: str) -> float:
        """Get the value for the reflected light angle and raise an error if it is not unique."""
        value_set = set(self.key_to_petal_dict.values())
        if len(value_set) > 1:
            raise ValueError(
                f"Multiple {self.stem_name} values found for key {key}. Values: {value_set}"
            )
        return value_set.pop()
