"""Visp calibration pipeline parameters."""

from datetime import datetime
from random import randint
from typing import Any

import astropy.units as u
from astropy.units import Quantity
from dkist_processing_common.models.parameters import ParameterArmIdMixin
from dkist_processing_common.models.parameters import ParameterBase
from dkist_processing_common.models.parameters import ParameterWavelengthMixin
from solar_wavelength_calibration import DownloadConfig


class VispParsingParameters(ParameterBase):
    """
    Parameters specifically (and only) for the Parse task.

    Needed because the Parse task doesn't know what the wavelength is yet and therefore can't use the
    `ParameterWaveLengthMixin`.
    """

    @property
    def max_cs_step_time_sec(self):
        """Time window within which CS steps with identical GOS configurations are considered to be the same."""
        return self._find_most_recent_past_value(
            "visp_max_cs_step_time_sec", start_date=datetime.now()
        )


class VispParameters(ParameterBase, ParameterWavelengthMixin, ParameterArmIdMixin):
    """Put all Visp parameters parsed from the input dataset document in a single property."""

    @property
    def beam_border(self):
        """Pixel location of the border between ViSP beams."""
        return self._find_most_recent_past_value("visp_beam_border")

    @property
    def background_on(self) -> bool:
        """Return True if background light correct should be done."""
        return self._find_most_recent_past_value("visp_background_on")

    @property
    def background_num_spatial_bins(self) -> int:
        """Return number of spatial bins to use when computing background light."""
        return self._find_parameter_closest_wavelength("visp_background_num_spatial_bins")

    @property
    def background_wavelength_subsample_factor(self) -> int:
        """Return the sub-sampling factor used to reduce the number of wavelength samples."""
        return self._find_parameter_closest_wavelength(
            "visp_background_wavelength_subsample_factor"
        )

    @property
    def background_num_fit_iterations(self) -> int:
        """Maximum number of fit iterations used to fit the background light."""
        return self._find_parameter_closest_wavelength("visp_background_num_fit_iterations")

    @property
    def background_continuum_index(self) -> list:
        """Return indices of a region to use when normalizing modulated polcals in the background task."""
        return self._find_parameter_closest_wavelength("visp_background_continuum_index")

    @property
    def hairline_median_spatial_smoothing_width_px(self) -> int:
        """Size of median filter in the spatial dimension with which to smooth data for hairline identification."""
        return self._find_most_recent_past_value("visp_hairline_median_spatial_smoothing_width_px")

    @property
    def hairline_fraction(self):
        """Relative difference from median used to identify slit positions covered by the hairlines."""
        return self._find_most_recent_past_value("visp_hairline_fraction")

    @property
    def hairline_mask_spatial_smoothing_width_px(self) -> float:
        """Amount to smooth the hairline mask in the spatial direction.

        This helps capture the higher-flux wings of the hairlines that would otherwise require a `hairline_fraction`
        that was so low it captures other optical features.
        """
        return self._find_most_recent_past_value("visp_hairline_mask_spatial_smoothing_width_px")

    @property
    def hairline_mask_gaussian_peak_cutoff_fraction(self) -> float:
        """Fraction of the maximum smoothed mask value used to truncate the smoothed mask.

        This ensures that very very small values way out in the wings are not included in the mask. For example, if
        this value is 0.01 then any mask points less than 1% of the maximum will be ignored.
        """
        return self._find_most_recent_past_value("visp_hairline_mask_gaussian_peak_cutoff_fraction")

    @property
    def geo_binary_opening_diameter(self) -> int:
        """
        Diameter threshold of morphological opening performed on binary image prior to spatial smoothing.

        The opening removes dot-like feautres that are smaller than the given diameter. Because the hairlines are long
        and thin it is hard to set this value too high.
        """
        return self._find_most_recent_past_value("visp_geo_binary_opening_diameter")

    @property
    def geo_hairline_flat_id_threshold(self) -> float:
        """Minimum fraction of binary pixels in a single spatial column for that column to be considered a hairline."""
        return self._find_most_recent_past_value("visp_geo_hairline_flat_id_threshold")

    @property
    def geo_hairline_fit_width_px(self) -> int:
        """Plus/minus distance around initial guess to look at when fitting a Gaussian to the hairline signal."""
        return self._find_most_recent_past_value("visp_geo_hairline_fit_width_px")

    @property
    def geo_hairline_angle_fit_sig_clip(self) -> float:
        """Plus/minus number of standard deviations away from the median used to clip bad hairline center fits.

        Clipping deviant values can greatly improve the fit to the slope and thus the beam angle.
        """
        return self._find_most_recent_past_value("visp_geo_hairline_angle_fit_sig_clip")

    @property
    def geo_max_beam_2_angle_refinement(self) -> float:
        """Maximum allowable refinement to the beam 2 spectral tilt angle, in radians."""
        return self._find_most_recent_past_value("visp_geo_max_beam_2_angle_refinement")

    @property
    def geo_upsample_factor(self):
        """Pixel precision (1/upsample_factor) to use during phase matching of beam/modulator images."""
        return self._find_most_recent_past_value("visp_geo_upsample_factor")

    @property
    def geo_max_shift(self):
        """Max allowed pixel shift when computing spectral curvature."""
        return self._find_most_recent_past_value("visp_geo_max_shift")

    @property
    def geo_poly_fit_order(self):
        """Order of polynomial used to fit spectral shift as a function of slit position."""
        return self._find_most_recent_past_value("visp_geo_poly_fit_order")

    @property
    def geo_zone_prominence(self):
        """Relative peak prominence threshold used to identify strong spectral features."""
        return self._find_parameter_closest_wavelength("visp_geo_zone_prominence")

    @property
    def geo_zone_width(self):
        """Pixel width used to search for strong spectral features."""
        return self._find_parameter_closest_wavelength("visp_geo_zone_width")

    @property
    def geo_zone_bg_order(self):
        """Order of polynomial fit used to remove continuum when identifying strong spectral features."""
        return self._find_parameter_closest_wavelength("visp_geo_zone_bg_order")

    @property
    def geo_zone_normalization_percentile(self):
        """Fraction of CDF to use for normalizing spectrum when search for strong features."""
        return self._find_parameter_closest_wavelength("visp_geo_zone_normalization_percentile")

    @property
    def geo_zone_rel_height(self):
        """Relative height at which to compute the width of strong spectral features."""
        return self._find_most_recent_past_value("visp_geo_zone_rel_height")

    @property
    def solar_spatial_median_filter_width_px(self):
        """Pixel width of spatial median filter used to compute characteristic solar spectra."""
        return self._find_parameter_closest_wavelength("visp_solar_spatial_median_filter_width_px")

    @property
    def solar_characteristic_spatial_normalization_percentile(self) -> float:
        """Percentile to pass to `np.nanpercentile` when normalizing each spatial position of the characteristic spectra."""
        return self._find_most_recent_past_value(
            "visp_solar_characteristic_spatial_normalization_percentile"
        )

    @property
    def solar_vignette_initial_continuum_poly_fit_order(self) -> int:
        """
        Define the order of polynomial to use when fitting the initial continuum function.

        Note that "initial" in this context does not refer to an initial guess in the wavecal fitter, but rather the
        fact that this represents the initial estimate of the vignette signal.
        """
        return self._find_most_recent_past_value(
            "visp_solar_vignette_initial_continuum_poly_fit_order"
        )

    @property
    def solar_vignette_crval_bounds_px(self) -> float:
        """
        Define the bounds (in *pixels*) on crval when fitting the initial vignette signal.

        The actual bounds on the value of crval are equal to ± the initial dispersion times this number. Note that the
        total range searched by the fitting algorithm will be twice this number (in pixels).
        """
        return self._find_most_recent_past_value("visp_solar_vignette_crval_bounds_px") * u.pix

    @property
    def solar_vignette_dispersion_bounds_fraction(self) -> float:
        """
        Define the ± fraction from the initial value for bounds on dispersion when fitting the initial vignette signal.

        This value should be between 0 and 1. For example, the minimum bound is `init_value * (1 - solar_vignette_dispersion_bounds_fraction)`.
        """
        return self._find_most_recent_past_value("visp_solar_vignette_dispersion_bounds_fraction")

    @property
    def solar_vignette_wavecal_fit_kwargs(self) -> dict[str, Any]:
        """Define extra keyword arguments to pass to the wavelength calibration fitter."""
        doc_dict = self._find_most_recent_past_value("visp_solar_vignette_wavecal_fit_kwargs")
        rng_kwarg = dict()
        fitting_method = doc_dict.get("method", False)
        if fitting_method in ["basinhopping", "differential_evolution", "dual_annealing"]:
            rng = randint(1, 1_000_000)
            rng_kwarg["rng"] = rng

        # The order here allows us to override `rng` in a parameter value
        fit_kwargs = rng_kwarg | doc_dict
        return fit_kwargs

    @property
    def solar_vignette_spectral_poly_fit_order(self) -> int:
        """Define the order of spectral polynomial used when computing the full, 2D vignette signal."""
        return self._find_most_recent_past_value("visp_solar_vignette_spectral_poly_fit_order")

    @property
    def solar_vignette_min_samples(self) -> float:
        """Return fractional number of samples required for the RANSAC regressor used to fit the 2D vignette signal."""
        return self._find_most_recent_past_value("visp_solar_vignette_min_samples")

    @property
    def wavecal_crval_bounds_px(self) -> Quantity:
        """
        Define the bounds (in *pix*) on crval when performing wavecal fitting.

        The actual bounds on the value of crval are equal to ± the initial dispersion times this number. Note that the
        total range searched by the fitting algorithm will be twice this number (in pixels).
        """
        return self._find_most_recent_past_value("visp_wavecal_crval_bounds_px") * u.pix

    @property
    def wavecal_dispersion_bounds_fraction(self) -> Quantity:
        """
        Define the ± fraction from the initial value for bounds on dispersion when performing wavecal fitting.

        This value should be between 0 and 1. For example, the minimum bound is `init_value * (1 - wavecal_dispersion_bounds_fraction)`.
        """
        return self._find_most_recent_past_value("visp_wavecal_dispersion_bounds_fraction")

    @property
    def wavecal_incident_light_angle_bounds_deg(self) -> Quantity:
        """Define the bounds (in *deg*) on incident_light_angle when performing wavecal fitting."""
        return (
            self._find_most_recent_past_value("visp_wavecal_incident_light_angle_bounds_deg")
            * u.deg
        )

    @property
    def wavecal_camera_lens_parameters(self) -> list[u.Quantity]:
        r"""
        Define the 2nd order polynomial coefficients for computing the total camera focal length as a function of wavelength.

        The total focal length of the lens is :math:`f = a_0 + a_1\lambda + a_2\lambda^2` where this property is
        :math:`[a_0, a_1, a_2]`
        """
        value_list = self._find_parameter_for_arm("visp_wavecal_camera_lens_parameters")
        unit_list = [u.m, u.m / u.nm, u.m / u.nm**2]
        return [v * u for v, u in zip(value_list, unit_list)]

    @property
    def wavecal_pixel_pitch_micron_per_pix(self) -> u.Quantity:
        """Define the physical size of ViSP detector pixels."""
        return (
            self._find_most_recent_past_value("visp_wavecal_pixel_pitch_micron_per_pix")
            * u.micron
            / u.pix
        )

    @property
    def wavecal_atlas_download_config(self) -> DownloadConfig:
        """Define the `~solar_wavelength_calibration.DownloadConfig` used to grab the Solar atlas used for wavelength calibration."""
        config_dict = self._find_most_recent_past_value("visp_wavecal_atlas_download_config")
        return DownloadConfig.model_validate(config_dict)

    @property
    def wavecal_init_crval_guess_normalization_percentile(self) -> float | None:
        """Define the CDF percentage used to normalize the Atlas to the input spectrum level when computing an initial CRVAL guess."""
        return self._find_most_recent_past_value(
            "visp_wavecal_init_crval_guess_normalization_percentile"
        )

    @property
    def wavecal_init_resolving_power(self) -> int:
        """Define the initial guess for ViSP resolving power in wavecal fits."""
        return self._find_most_recent_past_value("visp_wavecal_init_resolving_power")

    @property
    def wavecal_init_straylight_fraction(self) -> float:
        """Define the initial guess for straylight fraction in wavecal fits."""
        return self._find_most_recent_past_value("visp_wavecal_init_straylight_fraction")

    @property
    def wavecal_init_opacity_factor(self) -> float:
        """Define the initial guess for opacity factor in wavecal fits."""
        return self._find_most_recent_past_value("visp_wavecal_init_opacity_factor")

    @property
    def wavecal_fit_kwargs(self) -> dict[str, Any]:
        """Define extra keyword arguments to pass to the wavelength calibration fitter."""
        doc_dict = self._find_most_recent_past_value("visp_wavecal_fit_kwargs")
        rng_kwarg = dict()
        fitting_method = doc_dict.get("method", False)
        if fitting_method in ["basinhopping", "differential_evolution", "dual_annealing"]:
            rng = randint(1, 1_000_000)
            rng_kwarg["rng"] = rng

        # The order here allows us to override `rng` in a parameter value
        fit_kwargs = rng_kwarg | doc_dict
        return fit_kwargs

    @property
    def polcal_spatial_median_filter_width_px(self) -> int:
        """Return the size of the median filter to apply in the spatial dimension to polcal data."""
        return self._find_most_recent_past_value("visp_polcal_spatial_median_filter_width_px")

    @property
    def polcal_num_spatial_bins(self) -> int:
        """
        Return the number of spatial bins to pass to `dkist-processing-pac`.

        This sets the spatial resolution of the resulting demodulation matrices.
        """
        return self._find_most_recent_past_value("visp_polcal_num_spatial_bins")

    @property
    def polcal_demod_spatial_smooth_fit_order(self) -> int:
        """Return the polynomial fit order used to fit/smooth demodulation matrices in the spatial dimension."""
        return self._find_most_recent_past_value("visp_polcal_demod_spatial_smooth_fit_order")

    @property
    def polcal_demod_spatial_smooth_min_samples(self) -> float:
        """Return fractional number of samples required for the RANSAC regressor used to smooth demod matrices."""
        return self._find_most_recent_past_value("visp_polcal_demod_spatial_smooth_min_samples")

    @property
    def polcal_demod_upsample_order(self) -> int:
        """Interpolation order to use when upsampling the demodulation matrices to the full frame.

        See `skimage.transform.warp` for details.
        """
        return self._find_most_recent_past_value("visp_polcal_demod_upsample_order")

    @property
    def pac_remove_linear_I_trend(self) -> bool:
        """Flag that determines if a linear intensity trend is removed from the whole PolCal CS.

        The trend is fit using the average flux in the starting and ending clear steps.
        """
        return self._find_most_recent_past_value("visp_pac_remove_linear_I_trend")

    @property
    def pac_fit_mode(self):
        """Name of set of fitting flags to use during PAC Calibration Unit parameter fits."""
        return self._find_most_recent_past_value("visp_pac_fit_mode")
