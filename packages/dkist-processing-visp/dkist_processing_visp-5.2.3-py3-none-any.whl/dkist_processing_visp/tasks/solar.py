"""ViSP solar calibration task. See :doc:`this page </gain_correction>` for more information."""

from __future__ import annotations

from functools import partial
from typing import Callable

import astropy.units as u
import numpy as np
import scipy.ndimage as spnd
from astropy.units import Quantity
from dkist_processing_common.codecs.asdf import asdf_encoder
from dkist_processing_common.codecs.fits import fits_access_decoder
from dkist_processing_common.codecs.fits import fits_array_decoder
from dkist_processing_common.codecs.fits import fits_array_encoder
from dkist_processing_common.models.task_name import TaskName
from dkist_processing_common.tasks.mixin.quality import QualityMixin
from dkist_processing_math.arithmetic import divide_arrays_by_array
from dkist_processing_math.arithmetic import subtract_array_from_arrays
from dkist_processing_math.statistics import average_numpy_arrays
from dkist_service_configuration.logging import logger
from lmfit.parameter import Parameters
from sklearn.linear_model import RANSACRegressor
from sklearn.pipeline import Pipeline
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures
from sklearn.preprocessing import RobustScaler
from solar_wavelength_calibration import AngleBoundRange
from solar_wavelength_calibration import Atlas
from solar_wavelength_calibration import BoundsModel
from solar_wavelength_calibration import DispersionBoundRange
from solar_wavelength_calibration import FitFlagsModel
from solar_wavelength_calibration import LengthBoundRange
from solar_wavelength_calibration import UnitlessBoundRange
from solar_wavelength_calibration import WavelengthCalibrationFitter
from solar_wavelength_calibration import WavelengthCalibrationParameters
from solar_wavelength_calibration.fitter.wavelength_fitter import FitResult
from solar_wavelength_calibration.fitter.wavelength_fitter import calculate_initial_crval_guess

from dkist_processing_visp.models.metric_code import VispMetricCode
from dkist_processing_visp.models.tags import VispTag
from dkist_processing_visp.parsers.visp_l0_fits_access import VispL0FitsAccess
from dkist_processing_visp.tasks.mixin.beam_access import BeamAccessMixin
from dkist_processing_visp.tasks.mixin.corrections import CorrectionsMixin
from dkist_processing_visp.tasks.visp_base import VispTaskBase
from dkist_processing_visp.tasks.wavelength_calibration import compute_initial_dispersion
from dkist_processing_visp.tasks.wavelength_calibration import compute_input_wavelength_vector
from dkist_processing_visp.tasks.wavelength_calibration import compute_order
from dkist_processing_visp.tasks.wavelength_calibration import estimate_relative_continuum_level
from dkist_processing_visp.tasks.wavelength_calibration import get_doppler_velocity

__all__ = [
    "SolarCalibration",
    "WavelengthCalibrationParametersWithContinuum",
    "polynomial_continuum_model",
]


class WavelengthCalibrationParametersWithContinuum(WavelengthCalibrationParameters):
    """
    Subclass of `~solar_wavelength_calibration.WavelengthCalibrationParameters` that adds a polynomial continuum parameterization.

    The order of the continuum polynomial is set with the new ``continuum_poly_fit_oder`` model field. The `lmfit_parameters`
    property now adds a set of parameters that represent the polynomial coefficients.
    """

    continuum_poly_fit_order: int
    normalized_abscissa: np.ndarray
    zeroth_order_continuum_coefficient: float

    @property
    def continuum_function(self) -> Callable[[np.ndarray, Parameters], np.ndarray]:
        """Return a partial function of `polynomial_continuum_model` pre-loaded with the fit order and normalized abscissa."""
        return partial(
            polynomial_continuum_model,
            fit_order=self.continuum_poly_fit_order,
            abscissa=self.normalized_abscissa,
        )

    @property
    def lmfit_parameters(self) -> Parameters:
        """
        Add continuum polynomial coefficient parameters to the standard `~solar_wavelength_calibration.WavelengthCalibrationParameters.lmfit_parameters`.

        Each coefficient gets its own parameter called ``poly_coeff_{o:02n}``. The 0th order (i.e., constant continuum
        level) coefficient has bounds [0.7, 1.3] and all higher-order coefficients have bounds [-1, 1].
        """
        # NOTE: We set `vary=True` because otherwise we just wouldn't use this class
        #       We set the bounds here because it's easier that defining a custom `BoundsModel` class that can
        #       dynamically create the required number of "poly_coeff_{o:02n}" fields. Sorry if this bites you!
        params = super().lmfit_parameters
        for o in range(self.continuum_poly_fit_order + 1):
            # `np.polyval` uses its input coefficient list "backwards", so `poly_coeff_{self.continuum_poly_fit_order}`
            # is the 0th order polynomial term.
            params.add(
                f"poly_coeff_{o:02n}",
                vary=True,
                value=(
                    self.zeroth_order_continuum_coefficient
                    if o == self.continuum_poly_fit_order
                    else 0
                ),
                min=-1,
                max=1,
            )

        params[f"poly_coeff_{self.continuum_poly_fit_order:02n}"].min = (
            self.zeroth_order_continuum_coefficient * 0.5
        )
        params[f"poly_coeff_{self.continuum_poly_fit_order:02n}"].max = (
            self.zeroth_order_continuum_coefficient * 1.5
        )

        # Remove the default continuum parameterization
        del params["continuum_level"]

        return params


class SolarCalibration(
    VispTaskBase,
    BeamAccessMixin,
    CorrectionsMixin,
    QualityMixin,
):
    """
    Task class for generating Solar Gain images for each beam.

    Parameters
    ----------
    recipe_run_id
        id of the recipe run used to identify the workflow run this task is part of

    workflow_name
        name of the workflow to which this instance of the task belongs

    workflow_version
        version of the workflow to which this instance of the task belongs

    """

    record_provenance = True

    def run(self) -> None:
        """
        For each beam.

        #. Do dark, background, lamp, and geometric corrections
        #. Compute an initial separation of low-order spectral vignette signal from the true solar spectrum
        #. Compute a 2D vignette signal by fitting solar spectrum residuals along the slit
        #. Remove the 2D vignette signal from the averaged gain array
        #. Compute the characteristic spectra
        #. Re-apply the spectral curvature to the characteristic spectra
        #. Re-apply angle and state offset distortions to the characteristic spectra
        #. Remove the distorted characteristic solar spectra from the original, dark-corrected spectra
        #. Write final gain to disk
        """
        for beam in range(1, self.constants.num_beams + 1):

            apm_str = f"{beam = }"
            with self.telemetry_span(f"Initial corrections for {apm_str}"):
                self.do_initial_corrections(beam=beam)

            with self.telemetry_span(f"Fit atlas with continuum for {apm_str}"):
                representative_spectrum = self.get_representative_spectrum(beam)

                self.write(
                    data=representative_spectrum,
                    tags=[VispTag.debug(), VispTag.beam(beam), VispTag.task("REP_SPEC")],
                    encoder=fits_array_encoder,
                )

                logger.info("Deriving values from instrument configuration")
                order = compute_order(
                    central_wavelength=self.constants.wavelength * u.nm,
                    incident_light_angle=self.constants.incident_light_angle_deg,
                    reflected_light_angle=self.constants.reflected_light_angle_deg,
                    grating_constant=self.constants.grating_constant_inverse_mm,
                )

                initial_dispersion = compute_initial_dispersion(
                    central_wavelength=self.constants.wavelength * u.nm,
                    incident_light_angle=self.constants.incident_light_angle_deg,
                    reflected_light_angle=self.constants.reflected_light_angle_deg,
                    lens_parameters=self.parameters.wavecal_camera_lens_parameters,
                    pixel_pitch=self.parameters.wavecal_pixel_pitch_micron_per_pix,
                )

                doppler_velocity = get_doppler_velocity(
                    solar_gain_ip_start_time=self.constants.solar_gain_ip_start_time
                )

                self._log_wavecal_parameters(
                    dispersion=initial_dispersion, order=order, doppler_velocity=doppler_velocity
                )

                fit_result = self.fit_initial_vignette(
                    representative_spectrum=representative_spectrum,
                    dispersion=initial_dispersion,
                    spectral_order=order,
                    doppler_velocity=doppler_velocity,
                )

                first_vignette_estimation = self.compute_initial_vignette_estimation(
                    beam=beam,
                    representative_spectrum=representative_spectrum,
                    continuum=fit_result.best_fit_continuum,
                )

                self.write(
                    data=first_vignette_estimation,
                    tags=[VispTag.debug(), VispTag.beam(beam), VispTag.task("FIRST_VIGNETTE_EST")],
                    encoder=fits_array_encoder,
                )

            with self.telemetry_span(f"Estimate 2D vignetting signature for {apm_str}"):
                final_vignette = self.compute_final_vignette_estimate(
                    init_vignette_correction=first_vignette_estimation
                )
                vignette_corrected_gain = self.geo_corrected_beam_data(beam=beam) / final_vignette

                self.write(
                    data=final_vignette,
                    tags=[VispTag.debug(), VispTag.beam(beam), VispTag.task("FINAL_VIGNETTE")],
                    encoder=fits_array_encoder,
                )
                self.write(
                    data=vignette_corrected_gain,
                    tags=[VispTag.debug(), VispTag.beam(beam), VispTag.task("VIGNETTE_CORR")],
                    encoder=fits_array_encoder,
                )

            with self.telemetry_span(f"Save vignette quality metrics for {apm_str}"):
                self.record_vignette_quality_metrics(
                    beam=beam,
                    representative_spectrum=representative_spectrum,
                    fit_result=fit_result,
                    vignette_corrected_gain=vignette_corrected_gain,
                )

            with self.telemetry_span(f"Compute characteristic spectra for {apm_str}"):
                char_spec = self.compute_characteristic_spectra(vignette_corrected_gain)
                self.write(
                    data=char_spec,
                    encoder=fits_array_encoder,
                    tags=[
                        VispTag.intermediate_frame(beam=beam),
                        VispTag.task_characteristic_spectra(),
                    ],
                    overwrite=True,
                )

            with self.telemetry_span(
                f"Applying spectral shifts to characteristic spectra for {apm_str}"
            ):
                spec_shift = next(
                    self.read(
                        tags=[
                            VispTag.intermediate_frame(beam=beam),
                            VispTag.task_geometric_spectral_shifts(),
                        ],
                        decoder=fits_array_decoder,
                    )
                )
                redistorted_char_spec = next(
                    self.corrections_remove_spec_geometry(
                        arrays=char_spec, spec_shift=-1 * spec_shift
                    )
                )
                self.write(
                    data=redistorted_char_spec,
                    encoder=fits_array_encoder,
                    tags=[VispTag.debug(), VispTag.frame()],
                    relative_path=f"DEBUG_SC_CHAR_DISTORT_BEAM_{beam}.dat",
                    overwrite=True,
                )

            with self.telemetry_span(f"Re-distorting characteristic spectra for {apm_str}"):
                reshifted_char_spec = self.distort_characteristic_spectra(
                    char_spec=redistorted_char_spec, beam=beam
                )
                self.write(
                    data=reshifted_char_spec,
                    encoder=fits_array_encoder,
                    tags=[
                        VispTag.beam(beam),
                        VispTag.task("CHAR_SPEC_DISTORT_SHIFT"),
                    ],
                    relative_path=f"DEBUG_SC_CHAR_SPEC_DISTORT_SHIFT_BEAM_{beam}.dat",
                    overwrite=True,
                )

            with self.telemetry_span(f"Removing solar signal from {apm_str}"):
                gain = self.remove_solar_signal(char_solar_spectra=reshifted_char_spec, beam=beam)

            with self.telemetry_span(f"Masking hairlines from {apm_str}"):
                final_gain = self.corrections_mask_hairlines(gain)

            with self.telemetry_span(f"Writing solar gain for {beam = }"):
                self.write_solar_gain_calibration(
                    gain_array=final_gain,
                    beam=beam,
                )

        with self.telemetry_span("Computing and logging quality metrics"):
            no_of_raw_solar_frames: int = self.scratch.count_all(
                tags=[
                    VispTag.input(),
                    VispTag.frame(),
                    VispTag.task_solar_gain(),
                ],
            )

            self.quality_store_task_type_counts(
                task_type=TaskName.solar_gain.value, total_frames=no_of_raw_solar_frames
            )

    def geo_corrected_beam_data(self, beam: int) -> np.ndarray:
        """
        Array for a single beam that has dark, lamp, and ALL of the geometric corrects.

        Parameters
        ----------
        beam
            The beam number for this array

        Returns
        -------
        Fully corrected array
            Array with dark signal, and lamp signal removed, and all geometric corrections made
        """
        tags = [
            VispTag.intermediate_frame(beam=beam),
            VispTag.task("SC_GEO_ALL"),
        ]
        array_generator = self.read(tags=tags, decoder=fits_array_decoder)
        return next(array_generator)

    def bg_corrected_beam_data(self, beam: int) -> np.ndarray:
        """
        Array for a single beam that has only has dark and background corrects applied.

        Parameters
        ----------
        beam
            The beam number for this array


        Returns
        -------
        np.ndarray
            Array with dark and background signals removed
        """
        tags = [
            VispTag.intermediate_frame(beam=beam),
            VispTag.task("SC_BG_ONLY"),
        ]
        array_generator = self.read(tags=tags, decoder=fits_array_decoder)
        return next(array_generator)

    def do_initial_corrections(self, beam: int) -> None:
        """
        Do dark, lamp, and geometric corrections for all data that will be used.

        We also save an intermediate product of the average solar gain array with only dark and background corrections.
        This array will later be used to produce the final solar gain. It's task tag is SC_BG_ONLY.

        Parameters
        ----------
        beam
            The beam number for this array
        """
        all_exp_time_arrays = []
        for readout_exp_time in self.constants.solar_readout_exp_times:
            dark_array = next(
                self.read(
                    tags=VispTag.intermediate_frame_dark(
                        beam=beam, readout_exp_time=readout_exp_time
                    ),
                    decoder=fits_array_decoder,
                )
            )

            background_array = np.zeros(dark_array.shape)
            if self.constants.correct_for_polarization and self.parameters.background_on:
                background_array = next(
                    self.read(
                        tags=[VispTag.intermediate_frame(beam=beam), VispTag.task_background()],
                        decoder=fits_array_decoder,
                    )
                )

            logger.info(f"Doing dark, background, lamp, and geo corrections for {beam=}")
            ## Load frames
            tags = [
                VispTag.input(),
                VispTag.frame(),
                VispTag.task_solar_gain(),
                VispTag.readout_exp_time(readout_exp_time),
            ]
            input_solar_gain_objs = self.read(
                tags=tags, decoder=fits_access_decoder, fits_access_class=VispL0FitsAccess
            )

            readout_normalized_arrays = (
                self.beam_access_get_beam(o.data, beam=beam) / o.num_raw_frames_per_fpa
                for o in input_solar_gain_objs
            )

            avg_solar_array = average_numpy_arrays(readout_normalized_arrays)

            dark_corrected_solar_array = subtract_array_from_arrays(
                arrays=avg_solar_array, array_to_subtract=dark_array
            )

            background_corrected_solar_array = next(
                subtract_array_from_arrays(dark_corrected_solar_array, background_array)
            )

            all_exp_time_arrays.append(background_corrected_solar_array)

        avg_dark_bg_corrected_array = average_numpy_arrays(all_exp_time_arrays)

        # Save the only-dark-corr because this will be used to make the final Solar Gain object
        self.write(
            data=avg_dark_bg_corrected_array,
            tags=[
                VispTag.intermediate_frame(beam=beam),
                VispTag.task("SC_BG_ONLY"),
            ],
            encoder=fits_array_encoder,
        )

        ## Lamp correction
        lamp_array = next(
            self.read(
                tags=[
                    VispTag.intermediate_frame(beam=beam),
                    VispTag.task_lamp_gain(),
                ],
                decoder=fits_array_decoder,
            )
        )
        lamp_corrected_solar_array = next(
            divide_arrays_by_array(
                arrays=avg_dark_bg_corrected_array, array_to_divide_by=lamp_array
            )
        )

        self.write(
            data=lamp_corrected_solar_array,
            tags=[
                VispTag.debug(),
                VispTag.beam(beam),
                VispTag.task("SC_LAMP_CORR"),
            ],
            encoder=fits_array_encoder,
        )

        ## Geo correction
        angle_array = next(
            self.read(
                tags=[VispTag.intermediate_frame(beam=beam), VispTag.task_geometric_angle()],
                decoder=fits_array_decoder,
            )
        )
        angle = angle_array[0]

        # Because we have averaged over all modstates, the per-modestate offsets don't matter. Also, we're going to
        # undo these corrections to make the final gain, so the beam2 -> beam1 offset doesn't matter either.
        state_offset = np.array([0.0, 0.0])
        spec_shift = next(
            self.read(
                tags=[
                    VispTag.intermediate_frame(beam=beam),
                    VispTag.task_geometric_spectral_shifts(),
                ],
                decoder=fits_array_decoder,
            )
        )

        geo_corrected_array = next(
            self.corrections_correct_geometry(lamp_corrected_solar_array, state_offset, angle)
        )
        self.write(
            data=geo_corrected_array,
            tags=[
                VispTag.debug(),
                VispTag.beam(beam),
                VispTag.task("SC_GEO_NOSHIFT"),
            ],
            encoder=fits_array_encoder,
        )

        # Now finish the spectral shift correction
        spectral_corrected_array = next(
            self.corrections_remove_spec_geometry(geo_corrected_array, spec_shift)
        )
        self.write(
            data=spectral_corrected_array,
            tags=[
                VispTag.intermediate_frame(beam=beam),
                VispTag.task("SC_GEO_ALL"),
            ],
            encoder=fits_array_encoder,
        )

    def get_representative_spectrum(self, beam: int) -> np.ndarray:
        """
        Compute a representative spectrum that will be used for solar atlas and continuum fitting.

        The spectrum is the spatial median of the lamp-and-spectral-shift corrected solar gain image for this beam.
        Prior to computing the spatial median each spatial pixel is normalized by its continuum level so that variations
        in overall scaling as a function of slit position don't skew the median line shapes. The continuum for each
        spatial pixel is estimated from a percentage of the CDF; this percentage is a pipeline parameter.
        """
        normalization_percentile = (
            self.parameters.solar_characteristic_spatial_normalization_percentile
        )
        logger.info(
            f"Computing representative spectra for {beam = } with {normalization_percentile = }"
        )
        full_spectra = self.geo_corrected_beam_data(beam=beam)

        full_spectra = self.corrections_mask_hairlines(full_spectra)
        # Normalize each spatial pixel by its own percentile. This removes large spatial gradients that are not solar
        # signal.
        normed_spectra = full_spectra / np.nanpercentile(
            full_spectra, normalization_percentile, axis=0
        )

        representative_spectrum = np.nanmedian(normed_spectra, axis=1)

        return representative_spectrum

    def fit_initial_vignette(
        self,
        representative_spectrum: np.ndarray,
        dispersion: Quantity,
        spectral_order: int,
        doppler_velocity: Quantity,
    ) -> FitResult:
        """
        Fit a global continuum to a single, representative spectrum.

        The representative spectrum's continuum is estimated by fitting the spectrum to a solar atlas. The continuum
        is parameterized with a polynomial as seen in `WavelengthCalibrationParametersWithContinuum` and
        `polynomial_continuum_model`.
        """
        atlas = Atlas(self.parameters.wavecal_atlas_download_config)

        logger.info("Initializing wavecal fit parameters")
        init_parameters = self.initialize_starting_fit_parameters(
            representative_spectrum=representative_spectrum,
            dispersion=dispersion,
            spectral_order=spectral_order,
            doppler_velocity=doppler_velocity,
            atlas=atlas,
        )

        fitter = WavelengthCalibrationFitter(input_parameters=init_parameters, atlas=atlas)
        with self.telemetry_span("Fit atlas and continuum"):
            extra_kwargs = self.parameters.solar_vignette_wavecal_fit_kwargs
            logger.info(f"Calling fitter with extra kwargs: {extra_kwargs}")
            fit_result = fitter(
                input_spectrum=representative_spectrum,
                **extra_kwargs,
            )

        return fit_result

    def compute_initial_vignette_estimation(
        self, beam: int, representative_spectrum: np.ndarray, continuum: np.ndarray
    ) -> np.ndarray:
        """
        Compute the initial, 1D estimate of the spectral vignette signal.

        The continuum is first removed from the representative spectrum to make the first guess at a vignette-corrected
        solar spectrum. Then this solar spectrum is divided from the 2D lamp-and-spectral-shift corrected solar gain data.

        Because the continuum was fit for a single spectrum, the result is a 2D array that contains the *spatial*
        variation in the vignetting signal.
        """
        first_vignette_array = (
            self.geo_corrected_beam_data(beam=beam) / (representative_spectrum / continuum)[:, None]
        )
        return first_vignette_array

    def initialize_starting_fit_parameters(
        self,
        representative_spectrum: np.ndarray,
        dispersion: Quantity,
        spectral_order: int,
        doppler_velocity: Quantity,
        atlas: Atlas,
    ) -> WavelengthCalibrationParametersWithContinuum:
        """
        Construct a `WavelengthCalibrationParametersWithContinuum` object containing initial guesses, fit flags, and bounds.

        A rough estimate of the initial CRVAL value is made using `solar_wavelength_calibration.calculate_initial_crval_guess`.
        """
        num_wave = representative_spectrum.size
        normalized_abscissa = np.linspace(-1, 1, num_wave)

        logger.info("Computing input wavelength vector")
        input_wavelength_vector = compute_input_wavelength_vector(
            central_wavelength=self.constants.wavelength * u.nm,
            dispersion=dispersion,
            grating_constant=self.constants.grating_constant_inverse_mm,
            order=spectral_order,
            incident_light_angle=self.constants.incident_light_angle_deg,
            num_spec_px=representative_spectrum.size,
        )
        wavelength_range = input_wavelength_vector.max() - input_wavelength_vector.min()

        logger.info("Computing initial CRVAL guess")
        crval_init = calculate_initial_crval_guess(
            input_wavelength_vector=input_wavelength_vector,
            input_spectrum=representative_spectrum,
            atlas=atlas,
            negative_limit=-wavelength_range / 2,
            positive_limit=wavelength_range / 2,
            num_steps=500,
            normalization_percentile=self.parameters.wavecal_init_crval_guess_normalization_percentile,
        )

        logger.info(f"{crval_init = !s}")

        fit_flags = FitFlagsModel(
            continuum_level=False,  # Because we're fitting the continuum with a function
            incident_light_angle=False,
            straylight_fraction=True,
            resolving_power=True,
            opacity_factor=True,
        )

        incident_light_angle = self.constants.incident_light_angle_deg
        grating_constant = self.constants.grating_constant_inverse_mm
        resolving_power = self.parameters.wavecal_init_resolving_power
        opacity_factor = self.parameters.wavecal_init_opacity_factor
        straylight_faction = self.parameters.wavecal_init_straylight_fraction
        relative_atlas_scaling = estimate_relative_continuum_level(
            crval_init=crval_init,
            wavelength_range=wavelength_range,
            atlas=atlas,
            representative_spectrum=representative_spectrum,
            normalization_percentile=self.parameters.wavecal_init_crval_guess_normalization_percentile,
        )
        logger.info(f"0th order coefficient initial guess: {relative_atlas_scaling}")

        wavelength_search_width = dispersion * self.parameters.solar_vignette_crval_bounds_px
        bounds = BoundsModel(
            crval=LengthBoundRange(
                min=crval_init - wavelength_search_width, max=crval_init + wavelength_search_width
            ),
            dispersion=DispersionBoundRange(
                min=dispersion * (1 - self.parameters.solar_vignette_dispersion_bounds_fraction),
                max=dispersion * (1 + self.parameters.solar_vignette_dispersion_bounds_fraction),
            ),
            incident_light_angle=AngleBoundRange(
                min=incident_light_angle - 1 * u.deg, max=incident_light_angle + 1 * u.deg
            ),
            resolving_power=UnitlessBoundRange(min=1e5, max=5e5),
            opacity_factor=UnitlessBoundRange(min=1.0, max=10),
            straylight_fraction=UnitlessBoundRange(min=0.0, max=0.8),
        )

        init_params = WavelengthCalibrationParametersWithContinuum(
            crval=crval_init,
            dispersion=dispersion,
            incident_light_angle=incident_light_angle,
            grating_constant=grating_constant,
            doppler_velocity=doppler_velocity,
            order=spectral_order,
            continuum_level=1,
            resolving_power=resolving_power,
            opacity_factor=opacity_factor,
            straylight_fraction=straylight_faction,
            fit_flags=fit_flags,
            bounds=bounds,
            continuum_poly_fit_order=self.parameters.solar_vignette_initial_continuum_poly_fit_order,
            normalized_abscissa=normalized_abscissa,
            zeroth_order_continuum_coefficient=relative_atlas_scaling,
        )

        return init_params

    def compute_final_vignette_estimate(self, init_vignette_correction: np.ndarray) -> np.ndarray:
        """
        Fit the spectral shape of continuum residuals for each spatial pixel.

        The vignette estimation produced by `compute_initial_vignette_estimation` used a single continuum function for
        the entire slit. This method fits the continuum for all pixels along the slit to build up a fully 2D estimate
        of the vignette signal.

        Each spatial pixel is fit separately with a polynomial via a RANSAC estimator.
        """
        model = self.build_RANSAC_model()
        num_spectral, num_spatial = init_vignette_correction.shape
        abscissa = np.arange(num_spectral)[
            :, None
        ]  # Add extra dimension because sklearn requires it

        logger.info(f"Fitting spectral vignetting for {num_spatial} spatial pixels")
        final_vignette = np.zeros_like(init_vignette_correction)
        for spatial_px in range(num_spatial):
            finite_idx = np.isfinite(init_vignette_correction[:, spatial_px])
            model.fit(abscissa[finite_idx, :], init_vignette_correction[finite_idx, spatial_px])
            final_vignette[:, spatial_px] = model.predict(abscissa)

        return final_vignette

    def build_RANSAC_model(self) -> Pipeline:
        """
        Build a scikit-learn pipeline from a set of estimators.

        Namely, construct a `~sklearn.pipeline.Pipeline` built from

        `~sklearn.preprocessing.PolynomialFeatures` -> `~sklearn.preprocessing.RobustScaler` -> `~sklearn.linear_model.RANSACRegressor`
        """
        fit_order = self.parameters.solar_vignette_spectral_poly_fit_order
        min_samples = self.parameters.solar_vignette_min_samples
        logger.info(f"Building RANSAC model with {fit_order = } and {min_samples = }")

        # PolynomialFeatures casts the pipeline as a polynomial fit
        # see https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.PolynomialFeatures.html#sklearn.preprocessing.PolynomialFeatures
        poly_feature = PolynomialFeatures(degree=fit_order)

        # RobustScaler is a scale factor that is robust to outliers
        # see https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.RobustScaler.html#sklearn.preprocessing.RobustScaler
        scaler = RobustScaler()

        # The RANSAC regressor iteratively sub-samples the input data and constructs a model with this sub-sample.
        # The method used allows it to be robust to outliers.
        # see https://scikit-learn.org/stable/modules/linear_model.html#ransac-regression
        RANSAC = RANSACRegressor(min_samples=min_samples)

        return make_pipeline(poly_feature, scaler, RANSAC)

    def compute_characteristic_spectra(self, vignette_corrected_data: np.ndarray) -> np.ndarray:
        """
        Compute the 2D characteristic spectra via a median smooth in the spatial dimension.

        A 2D characteristic spectra is needed because the line shape varys along the slit to the degree that a
        single, 1D characteristic spectrum will not fully remove the solar lines for all positions in the final gain.

        In this step we also normalize each spatial position by its continuum value. This removes low-order gradients in
        the spatial direction that are known to be caused by imperfect illumination of the Lamp gains (which were used
        to correct the data that will become the characteristic spectra).

        Parameters
        ----------
        beam
            The beam number for this array

        Returns
        -------
        char_spec
            2D characteristic spectra
        """
        spatial_median_window = self.parameters.solar_spatial_median_filter_width_px
        normalization_percentile = (
            self.parameters.solar_characteristic_spatial_normalization_percentile
        )
        logger.info(
            f"Computing characteristic spectra for {spatial_median_window = } and {normalization_percentile = }"
        )

        masked_spectra = self.corrections_mask_hairlines(vignette_corrected_data)
        # Normalize each spatial pixel by its own percentile. This removes large spatial gradients that are not solar
        # signal.
        normed_spectra = masked_spectra / np.nanpercentile(
            masked_spectra, normalization_percentile, axis=0
        )

        # size = (1, window) means don't smooth in the spectral dimension
        char_spec = spnd.median_filter(normed_spectra, size=(1, spatial_median_window))

        normed_char_spec = char_spec / np.nanpercentile(char_spec, normalization_percentile, axis=0)

        return normed_char_spec

    def distort_characteristic_spectra(
        self,
        char_spec: np.ndarray,
        beam: int,
    ) -> np.ndarray:
        """
        Re-apply angle and state offset distortions to the characteristic spectra.

        Parameters
        ----------
        char_spec
            Computed characteristic spectra

        beam
            The beam number for this array


        Returns
        -------
        distorted characteristic array
            Characteristic spectra array with angle and offset distortions re-applied
        """
        logger.info(f"Re-distorting characteristic spectra for {beam=}")
        angle_array = next(
            self.read(
                tags=[VispTag.intermediate_frame(beam=beam), VispTag.task_geometric_angle()],
                decoder=fits_array_decoder,
            )
        )
        angle = angle_array[0]

        # See comment in `do_initial_corrections`; we don't care about the state_offset when making the solar gain
        state_offset = np.array([0.0, 0.0])

        distorted_spec = next(
            self.corrections_correct_geometry(char_spec, -1 * state_offset, -1 * angle)
        )

        return distorted_spec

    def remove_solar_signal(
        self,
        char_solar_spectra: np.ndarray,
        beam: int,
    ) -> np.ndarray:
        """
        Remove the distorted characteristic solar spectra from the original spectra.

        Parameters
        ----------
        char_solar_spectra
            Characteristic solar spectra

        beam
            The beam number for this array

        Returns
        -------
        final gain
            Original spectral array with characteristic solar spectra removed
        """
        logger.info(f"Removing characteristic solar spectra from {beam=}")
        input_gain = self.bg_corrected_beam_data(beam=beam)

        final_gain = input_gain / char_solar_spectra

        return final_gain

    def write_solar_gain_calibration(
        self,
        gain_array: np.ndarray,
        beam: int,
    ) -> None:
        """
        Write a solar gain array for a single beam.

        Parameters
        ----------
        gain_array
            Solar gain array

        beam
            The beam number for this array
        """
        logger.info(f"Writing final SolarGain for {beam = }")
        self.write(
            data=gain_array,
            tags=[
                VispTag.intermediate_frame(beam=beam),
                VispTag.task_solar_gain(),
            ],
            encoder=fits_array_encoder,
        )

    def record_vignette_quality_metrics(
        self,
        beam: int,
        representative_spectrum: np.ndarray,
        fit_result: FitResult,
        vignette_corrected_gain: np.ndarray,
    ) -> None:
        """
        Save vignette fit results to disk for later quality metric building.

        We save the atlas fit of the initial vignette estimation and the global solar spectrum derived from the
        vignette-corrected 2D gain images.
        """
        logger.info(f"Recording initial vignette quality data for {beam = }")
        first_vignette_quality_outputs = {
            "output_wave_vec": fit_result.best_fit_wavelength_vector,
            "input_spectrum": representative_spectrum,
            "best_fit_atlas": fit_result.best_fit_atlas,
            "best_fit_continuum": fit_result.best_fit_continuum,
            "residuals": fit_result.minimizer_result.residual,
        }
        self.write(
            data=first_vignette_quality_outputs,
            tags=[VispTag.quality(VispMetricCode.solar_first_vignette), VispTag.beam(beam)],
            encoder=asdf_encoder,
        )

        logger.info(f"Recording final vignette-correced gain quality data for {beam = }")
        global_median = np.nanmedian(vignette_corrected_gain, axis=1)
        low_deviation = np.nanpercentile(vignette_corrected_gain, 5, axis=1)
        high_deviation = np.nanpercentile(vignette_corrected_gain, 95, axis=1)
        final_correction_quality_outputs = {
            "output_wave_vec": fit_result.best_fit_wavelength_vector,
            "median_spec": global_median,
            "low_deviation": low_deviation,
            "high_deviation": high_deviation,
        }
        self.write(
            data=final_correction_quality_outputs,
            tags=[VispTag.quality(VispMetricCode.solar_final_vignette), VispTag.beam(beam)],
            encoder=asdf_encoder,
        )

    def _log_wavecal_parameters(
        self, dispersion: Quantity, order: int, doppler_velocity: Quantity
    ) -> None:
        """Log initial guess and instrument-derived wavecal parameters."""
        logger.info(f"central_wavelength = {self.constants.wavelength * u.nm !s}")
        logger.info(f"{dispersion = !s}")
        logger.info(f"{order = }")
        logger.info(f"grating constant = {self.constants.grating_constant_inverse_mm !s}")
        logger.info(f"incident light angle = {self.constants.incident_light_angle_deg !s}")
        logger.info(f"reflected light angle = {self.constants.reflected_light_angle_deg !s}")
        logger.info(f"{doppler_velocity = !s}")
        logger.info(f"pixel pitch = {self.parameters.wavecal_pixel_pitch_micron_per_pix !s}")
        logger.info(f"solar ip start time = {self.constants.solar_gain_ip_start_time}")


def polynomial_continuum_model(
    wavelength_vector: np.ndarray, fit_parameters: Parameters, fit_order: int, abscissa: np.ndarray
) -> np.ndarray:
    """
    Parameterize the continuum as a polynomial.

    Polynomial coefficients are taken from the input ``fit_parameters`` object. The ``wavelength_vector`` argument is not
    used by required to conform to the signature expected by `WavelengthCalibrationFitter`.

    Parameters
    ----------
    wavelength_vector
        Unused, but required by `WavelengthCalibrationFitter`

    fit_parameters
        Object containing the current fit parameters

    fit_order
        Polynomial order. This needs to match the number of polynomial coefficients in the ``fit_parameters`` argument.
        Specifically, this method expects parameters called `[f"poly_coeff_{i:02n}" for i in range(fit_order + 1)]`.

    abscissa
        Array of values used to compute the continuum. For the fit to be independent of wavelength these values should
        be in the range [-1, 1].
    """
    coeffs = [fit_parameters[f"poly_coeff_{i:02n}"].value for i in range(fit_order + 1)]
    return np.polyval(coeffs, abscissa)
