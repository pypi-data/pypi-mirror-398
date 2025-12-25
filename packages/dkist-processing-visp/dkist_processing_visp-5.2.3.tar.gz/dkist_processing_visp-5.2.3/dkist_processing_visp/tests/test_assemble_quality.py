from typing import Generator
from unittest.mock import MagicMock

import numpy as np
import pytest
from dkist_processing_common._util.scratch import WorkflowFileSystem
from dkist_processing_common.codecs.asdf import asdf_encoder
from dkist_processing_common.codecs.quality import quality_data_decoder

from dkist_processing_visp.models.metric_code import VispMetricCode
from dkist_processing_visp.models.tags import VispTag
from dkist_processing_visp.tasks.l1_output_data import VispAssembleQualityData


@pytest.fixture
def visp_assemble_quality_data_task(
    tmp_path, recipe_run_id
) -> Generator[VispAssembleQualityData, None, None]:

    with VispAssembleQualityData(
        recipe_run_id=recipe_run_id, workflow_name="visp_assemble_quality", workflow_version="VX.Y"
    ) as task:
        task.scratch = WorkflowFileSystem(scratch_base_path=tmp_path, recipe_run_id=recipe_run_id)
        yield task
        task._purge()


def write_raw_vignette_metrics_to_task(task):
    for beam in [1, 2]:
        dummy_vec = np.arange(10)
        first_vignette_quality_outputs = {
            "output_wave_vec": dummy_vec,
            "input_spectrum": dummy_vec,
            "best_fit_atlas": dummy_vec,
            "best_fit_continuum": dummy_vec,
            "residuals": dummy_vec,
        }
        task.write(
            data=first_vignette_quality_outputs,
            tags=[VispTag.quality(VispMetricCode.solar_first_vignette), VispTag.beam(beam)],
            encoder=asdf_encoder,
        )
        final_correction_quality_outputs = {
            "output_wave_vec": dummy_vec,
            "median_spec": dummy_vec,
            "low_deviation": dummy_vec,
            "high_deviation": dummy_vec,
        }
        task.write(
            data=final_correction_quality_outputs,
            tags=[VispTag.quality(VispMetricCode.solar_final_vignette), VispTag.beam(beam)],
            encoder=asdf_encoder,
        )


@pytest.fixture
def dummy_quality_data() -> list[dict]:
    return [{"dummy_key": "dummy_value"}]


@pytest.fixture
def common_quality_assemble_data_mock(mocker, dummy_quality_data) -> MagicMock:
    yield mocker.patch(
        "dkist_processing_common.tasks.mixin.quality.QualityMixin.quality_assemble_data",
        return_value=dummy_quality_data,
        autospec=True,
    )


def test_vignette_metrics_built(visp_assemble_quality_data_task):
    """
    Given: A `VispAssembleQualityData` task with raw vignette metrics in scratch
    When: Building the quality report data
    Then: The vignette metrics are included in the data
    """
    task = visp_assemble_quality_data_task
    write_raw_vignette_metrics_to_task(task)

    task()

    final_report_list = list(
        task.read(tags=[VispTag.output(), VispTag.quality_data()], decoder=quality_data_decoder)
    )
    assert len(final_report_list) == 1
    final_report = final_report_list[0]

    initial_vignette_metrics = list(
        filter(lambda i: i["name"].startswith("Initial Vignette Estimation"), final_report)
    )
    assert len(initial_vignette_metrics) == 2
    facet_set = set()
    for m in initial_vignette_metrics:
        assert m["metric_code"] == VispMetricCode.solar_first_vignette.value
        assert m["description"]
        assert m["multi_plot_data"]
        facet_set.add(m["facet"])

    assert facet_set == {"BEAM_1", "BEAM_2"}

    final_vignette_metrics = list(
        filter(lambda i: i["name"].startswith("Final Vignette Estimation"), final_report)
    )
    assert len(final_vignette_metrics) == 2
    facet_set = set()
    for m in final_vignette_metrics:
        assert m["metric_code"] == VispMetricCode.solar_final_vignette.value
        assert m["description"]
        assert m["multi_plot_data"]
        facet_set.add(m["facet"])

    assert facet_set == {"BEAM_1", "BEAM_2"}


def test_correct_polcal_label_list(
    visp_assemble_quality_data_task, common_quality_assemble_data_mock
):
    """
    Given: A VispAssembleQualityData task
    When: Calling the task
    Then: The correct polcal_label_list property is passed to .quality_assemble_data
    """
    task = visp_assemble_quality_data_task
    write_raw_vignette_metrics_to_task(task)

    task()
    common_quality_assemble_data_mock.assert_called_once_with(
        task, polcal_label_list=["Beam 1", "Beam 2"]
    )
