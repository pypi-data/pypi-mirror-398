"""Subclass of AssembleQualityData that causes the correct polcal metrics to build."""

import numpy as np
from dkist_processing_common.codecs.asdf import asdf_decoder
from dkist_processing_common.models.quality import Plot2D
from dkist_processing_common.models.quality import ReportMetric
from dkist_processing_common.models.quality import VerticalMultiPanePlot2D
from dkist_processing_common.tasks import AssembleQualityData

__all__ = ["VispAssembleQualityData"]

from dkist_processing_visp.models.constants import VispConstants
from dkist_processing_visp.models.metric_code import VispMetricCode
from dkist_processing_visp.models.tags import VispTag


class VispAssembleQualityData(AssembleQualityData):
    """Subclass just so that the polcal_label_list can be populated."""

    constants: VispConstants

    @property
    def constants_model_class(self):
        """Get ViSP pipeline constants."""
        return VispConstants

    @property
    def polcal_label_list(self) -> list[str]:
        """Return labels for beams 1 and 2."""
        return ["Beam 1", "Beam 2"]

    def quality_assemble_data(self, polcal_label_list: list[str] | None = None) -> list[dict]:
        """
        Assemble the full quality report and insert ViSP-specific metrics.

        We try to place the new metrics right before default polcal ones, if possible.
        """
        vignette_metrics = []
        for beam in range(1, self.constants.num_beams + 1):
            vignette_metrics.append(self.build_first_vignette_metric(beam=beam))
            vignette_metrics.append(self.build_final_vignette_metric(beam=beam))

        report = super().quality_assemble_data(polcal_label_list=polcal_label_list)

        # Look for the first "PolCal" metric
        first_polcal_metric_index = 0
        try:
            while not report[first_polcal_metric_index]["name"].lower().startswith("polcal"):
                first_polcal_metric_index += 1
        except:
            # Wasn't found for whatever reason. No big deal, just put the new metrics at the front of the list
            first_polcal_metric_index = 0

        final_report = (
            report[:first_polcal_metric_index]
            + vignette_metrics
            + report[first_polcal_metric_index:]
        )

        return final_report

    def build_first_vignette_metric(self, beam: int) -> dict:
        """Build a ReportMetric showing the initial atlas-with-continuum fit and residuals."""
        data = next(
            self.read(
                tags=[VispTag.quality(VispMetricCode.solar_first_vignette), VispTag.beam(beam)],
                decoder=asdf_decoder,
            )
        )

        wave_vec = data["output_wave_vec"].tolist()
        input_spectrum = data["input_spectrum"].tolist()
        best_fit_atlas = data["best_fit_atlas"].tolist()
        continuum = data["best_fit_continuum"].tolist()
        residuals = data["residuals"].tolist()

        fit_series = {
            "Raw input spectrum": [wave_vec, input_spectrum],
            "Best fit atlas": [wave_vec, best_fit_atlas],
            "Best fit continuum": [wave_vec, continuum],
        }

        fit_plot_kwargs = {
            "Raw input spectrum": {
                "ls": "-",
                "ms": 0,
                "color": "#FAA61C",
                "zorder": 2.0,
                "lw": 4,
                "alpha": 0.6,
            },
            "Best fit atlas": {"color": "k", "ls": "-", "ms": 0, "zorder": 2.1},
            "Best fit continuum": {"ls": "-", "ms": 0, "color": "g", "zorder": 2.2},
        }

        fit_plot = Plot2D(
            xlabel="Wavelength [nm]",
            ylabel="Signal",
            series_data=fit_series,
            plot_kwargs=fit_plot_kwargs,
            sort_series=False,
        )

        residuals_series = {"Residuals": [wave_vec, residuals]}
        residuals_plot_kwargs = {"Residuals": {"ls": "-", "color": "k", "ms": 0}}

        y_min = np.nanpercentile(residuals, 2)
        y_max = np.nanpercentile(residuals, 98)
        y_range = y_max - y_min
        y_min -= 0.1 * y_range
        y_max += 0.1 * y_range
        residuals_plot = Plot2D(
            xlabel="Wavelength [nm]",
            ylabel=r"$\frac{\mathrm{Obs - Atlas}}{\mathrm{Obs}}$",
            series_data=residuals_series,
            plot_kwargs=residuals_plot_kwargs,
            ylim=(y_min, y_max),
        )

        plot_list = [fit_plot, residuals_plot]
        height_ratios = [1.5, 1.0]

        full_plot = VerticalMultiPanePlot2D(
            top_to_bottom_plot_list=plot_list,
            match_x_axes=True,
            no_gap=True,
            top_to_bottom_height_ratios=height_ratios,
        )

        metric = ReportMetric(
            name=f"Initial Vignette Estimation - Beam {beam}",
            description="These plots show the solar atlas fit used to estimate the initial, 1D spectral vignette "
            "present in solar gain frames. The vignette signature is taken to be the fit continuum shown.",
            metric_code=VispMetricCode.solar_first_vignette,
            facet=self._format_facet(f"Beam {beam}"),
            multi_plot_data=full_plot,
        )

        return metric.model_dump()

    def build_final_vignette_metric(self, beam: int) -> dict:
        """Build a ReportMetric showing the quality of the vignette correction on solar gain data."""
        data = next(
            self.read(
                tags=[VispTag.quality(VispMetricCode.solar_final_vignette), VispTag.beam(beam)],
                decoder=asdf_decoder,
            )
        )

        wave_vec = data["output_wave_vec"].tolist()
        median_spec = data["median_spec"].tolist()
        low_deviation = data["low_deviation"]
        high_deviation = data["high_deviation"]
        diff = (high_deviation - low_deviation).tolist()
        low_deviation = low_deviation.tolist()
        high_deviation = high_deviation.tolist()

        bounds_series = {
            "Median solar signal": [wave_vec, median_spec],
            "5th percentile bounds": [wave_vec, low_deviation],
            "95th percentile bounds": [wave_vec, high_deviation],
        }

        bounds_plot_kwargs = {
            "Median solar signal": {"ls": "-", "color": "k", "alpha": 0.8, "ms": 0, "zorder": 2.2},
            "5th percentile bounds": {"color": "#1E317A", "ls": "-", "ms": 0, "zorder": 2.0},
            "95th percentile bounds": {"ls": "-", "color": "#FAA61C", "ms": 0, "zorder": 2.1},
        }

        bounds_plot = Plot2D(
            xlabel="Wavelength [nm]",
            ylabel="Signal",
            series_data=bounds_series,
            plot_kwargs=bounds_plot_kwargs,
            sort_series=False,
        )

        residuals_series = {"Residuals": [wave_vec, diff]}
        residuals_plot_kwargs = {"Residuals": {"ls": "-", "color": "k", "ms": 0}}

        y_min = np.nanpercentile(diff, 5)
        y_max = np.nanpercentile(diff, 95)
        y_range = y_max - y_min
        y_min -= 0.1 * y_range
        y_max += 0.1 * y_range
        residuals_plot = Plot2D(
            xlabel="Wavelength [nm]",
            ylabel="95th - 5th percentile",
            series_data=residuals_series,
            plot_kwargs=residuals_plot_kwargs,
            ylim=(y_min, y_max),
        )

        plot_list = [bounds_plot, residuals_plot]
        height_ratios = [1.5, 1.0]

        full_plot = VerticalMultiPanePlot2D(
            top_to_bottom_plot_list=plot_list,
            match_x_axes=True,
            no_gap=True,
            top_to_bottom_height_ratios=height_ratios,
        )

        metric = ReportMetric(
            name=f"Final Vignette Estimation - Beam {beam}",
            description="These plots show how well the full, 2D vignette signal was removed from solar gain frames. "
            "The median solar signal shows a full spatial median of the vignette corrected solar gain; "
            "this should be very close to the true solar spectrum incident on the DKIST optics. "
            "The 5th and 9th percentile ranges show how stable this spectrum is along the spatial dimension "
            "after removing the vignette signal.",
            metric_code=VispMetricCode.solar_final_vignette,
            facet=self._format_facet(f"Beam {beam}"),
            multi_plot_data=full_plot,
        )

        return metric.model_dump()
