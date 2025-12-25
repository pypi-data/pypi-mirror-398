Gain Calibration
================

Introduction
------------

NOTE: The usage of the term "gain" throughout this document refers to the total system response of the DKIST/ViSP optical
train; it does NOT refer to the detector gain that has units of ADU / electron. Often the term "flat" is used in
a way that is interchangeable with the usage of "gain" in this document.

The ViSP gain calibration is broken down into the following steps across two pipeline tasks
(`~dkist_processing_visp.tasks.lamp` and `~dkist_processing_visp.tasks.solar`). Each step is explained in more detail below.

#. Subtract dark and :doc:`background <background_light>` signals from all input gain images.

#. Compute an average lamp gain and mask the hairlines.

#. Divide the solar gain by the resulting lamp image and correct for :doc:`geometric </geometric>` rotation and
   spectral curvature.

#. Separate the true solar spectrum from vignetting effects by fitting a solar atlas to the solar gain data.

#. Mask hairlines and compute a 2D characteristic solar spectra with a spatial median filter over the vignette-corrected solar gain data.

#. Re-curve and rotate the characteristic spectra into the same coordinates as the input frames.

#. Remove the characteristic spectra from solar gain images that have NOT had a lamp correction applied.

The result is a final gain image that can be applied to science data. Note that all steps happen separately for each
beam to capture the differences in optical response between the two beams.

Important Features
------------------

The final gain images (those used to correct science frames) are *not* normalized; they retain their original input values.
As a result, pixel values in the L1 data will be normalized to the average solar signal at disk center on the day of calibration
acquisition (usually the same day as science acquisition). Note that this is **NOT** intended to be an accurate photometric calibration.

Algorithm Detail
----------------

Subtract Dark and Background Signals
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This step is exactly how it sounds. Pre-computed dark and :doc:`background light <background_light>` frames are subtracted
from all input frames.

.. _hairline-description:

Average Lamp Frames and Mask Hairlines
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

All lamp frames for a single beam are averaged into a single array. The slit hairlines are then identified by smoothing
the image in the spatial dimension and then computing the relative difference between this smoothed image and the
original image. Any pixels that deviate by a large amount (set by the ``hairline_fraction`` parameter) are considered to
be hairline pixels. These hairline pixels are masked by replacing them with values from the smoothed array.

Prepare and Rectify Solar Frames
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The averaged lamp frames from the previous step are applied to dark/background subtracted solar gain frames through
division. Then the pre-computed :doc:`geometric </geometric>` correction removes any spectral rotation and spectral
curvature (in that order). Note that at this point we do NOT correct for X/Y offsets for two reasons: 1). a separate gain
is computed for each beam so applying the beam offsets is not necessary, and 2). it has been found that the
modstate-to-modstate offsets are small enough to ignore when making gain frames. At the end of this step the dispersion
axis will be parallel to a pixel axis and a single spectral pixel will have the same physical wavelength value for all
spatial pixels.

Separate Solar and Vignette Signals
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Aperture masks in ViSP cause known vignetting in both the spatial and spectral dimensions and we need to capture this
vignetting in our final gain images so it can be correctly removed from science data. To separate the spectral vignette
signature from the true solar spectrum we fit a representative spectrum to a solar atlas with a parameterized continuum.
The representative spectrum is a spatial median of the rectified solar gain array, and the continuum is parameterized as
a polynomial with an order set by the ``solar_vignette_initial_continuum_poly_fit_order`` parameter. Atlas fits are
done with the `solar-wavelength-calibration <https://docs.dkist.nso.edu/projects/solar-wavelength-calibration/en/latest/>`_
package. We take the fit continuum as a first estimate of the vignette signal in the spectral dimension.

This first vignette estimate is then removed from the representative spectrum, thus producing an estimate of the true
solar signal, and that spectrum is divided from every spatial pixel of the gain array. The residuals capture how the
vignette signal varies with spatial and spectral position across the chip. We fit these residuals for each spatial pixel
to compute a fully 2D estimate of the true vignette signal. The order of this polynomial fit is set by the
``solar_vignette_spectral_poly_fit_order`` parameter.


.. _charspec-description:

Compute Characteristic Spectra
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

First, the 2D vignette signal is divided from the solar gain array and the slit hairlines are masked using the same
method as :ref:`above <hairline-description>`.

The goal of this step is to derive pure solar spectra, free from any optical effects of the DKIST/ViSP system. By applying
lamp gain and vignette corrections to our solar images we have already removed a lot of optical effects, but some spatial
variations still remain. Thus, the characteristic spectra is computed by applying a median filter (with width controlled
by the ``solar_spatial_median_filter_width_px`` parameter) in the spatial direction. Previously, a single, median spectrum had been
used, but it did not accurately capture small, but important variations in spectral shape along the slit.

Finally, the smooth characteristic spectra have any spatial gradients removed by normalizing each spatial position by its
continuum level. This ensures that the characteristic spectra contain *only* pure solar spectra, and thus any real spatial
gradients are preserved in the final gain image. This normalization also ensures the absolute flux of the final
gain images is preserved so that science frames will have values relative to average disk center (where the solar images
are taken).

Un-rectify Characteristic Spectra
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The characteristic spectra have spectral shifts and spectral rotation re-applied to bring them back into raw input pixel
coordinates.

Remove Characteristic Solar Spectra from Input Solar Frames
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The dark/background corrected solar gain image is simply divided by the re-distorted characteristic spectra. Because we
do NOT use a solar image with a lamp or vignette correction applied, the resulting gain image includes the full optical
response of the system and can be applied directly to the science data.

As mentioned above, these gain calibration images are not normalized. The result is that L1 science data will have
values that are relative to solar disk center (where the solar gain images are observed).
