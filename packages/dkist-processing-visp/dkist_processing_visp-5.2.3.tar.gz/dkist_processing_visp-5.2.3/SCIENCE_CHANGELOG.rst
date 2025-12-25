v5.2.0 (2025-12-12)
===================




- L1 data now have a correct wavelength solution encoded in their headers. See :doc:`here </wavelength_calibration>`
    for more information. (`#234 <https://bitbucket.org/dkistdc/dkist-processing-visp/pull-requests/234>`__)


v5.0.0 (2025-12-02)
===================




- Major update to the gain algorithm to mitigate polarization artifacts in L1 science frames. This change can be split into
  three parts. See the `gain correction <https://docs.dkist.nso.edu/projects/visp/en/stable/gain_correction.html>`_ page for more information.

  #. Compute a single gain correction image for each beam. In the past we had computed a separate gain image for each modstate as well, but this was found to couple residual polarization structure into the final science frames.

  #. Stop "refining" (i.e., applying small spectral offsets to) the characteristic solar spectrum on a per-spatial-pixel basis. This was initially done to minimize line residuals in Telluric lines but was found to have a more-negative on polarimetric residuals.

  #. Separate vignetting caused by aperture masks from the solar signal used to remove spectral lines in the final gain image. This is done by fitting a solar atlas and taking the deviation in continuum to be the vignetting signal.

  Computing a single gain per beam will greatly reduce the polarization artifacts in L1 data. Measuring the vignette
  signal directly will further reduce these artifacts and improve flatness across the array. (`#246 <https://bitbucket.org/dkistdc/dkist-processing-visp/pull-requests/246>`__)


v4.0.0 (2025-11-12)
===================




- Change how interpolations are done by copying edge pixels as opposed to reflecting them when filling gaps left behind by shifts. This will eliminate "ghost" lines. Replace L1 frame pixels with NaNs where the source data comes from a single beam. (`#235 <https://bitbucket.org/dkistdc/dkist-processing-visp/pull-requests/235>`__)
- Update how edges are cropped in areas where both beams did not contribute to the L1 data array. The wrong edges were being cropped before. (`#242 <https://bitbucket.org/dkistdc/dkist-processing-visp/pull-requests/242>`__)


v3.0.0 (2025-04-01)
===================




- Update polarization calibration to use the darks and gains taken as part of the instrument polarization calibration (PolCal) sequence.

  Using darks from the polarization calibration sequence:

  This change should not fundamentally alter the results of calibration of the ViSP data, with the exception of small variations. It is however required for consistency with the other spectro-polarimetric instruments that use the darks taken in the PolCal sequence to reduce the PolCal data.

  Using gains from the polarization calibration sequence:

  This change means that moving forward, we will stop using the processed solar gain images (i.e., with lines removed) and instead use the average of the PolCal clear frames. The issue being addressed is that when a median value is calculated across the spectral axis for the “basic corrected” PolCal data, that median value will be biased by the spectral structure. The worst case is for the deep chromospheric lines, for which the median value may correspond to a particular region of the line wing. If, instead, the average clear data is applied to all PolCal data, then the line signatures are largely removed from the data and the median value more adequately represents the median signal across the spectral axis as determined by the polarimetric response of the instrument. (`#202 <https://bitbucket.org/dkistdc/dkist-processing-visp/pull-requests/202>`__)


v2.0.0 (2023-04-13)
===================




- Major update to gain correction algorithm. Previously we had attributed a signal now known to be :doc:`background light </background_light>`
  to the lamp gain images and therefore highly processed the lamp gains to remove this signal. Now that the true source
  of that signal is known we have reverted to a simpler and more accurate gain calibration. See
  :doc:`the page on the gain correction </gain_correction>` for more detailed information, but the import point is that
  lamp gain image are used *only* to remove optical patterns and aid in the separation of the raw solar spectra from solar
  gain images. A consequence of this is that the solar spectra are removed from raw solar gain frames (i.e., *not* those
  with a lamp correction applied) and thus the subsequent gain images contain the full optical response of the system and
  can be applied directly to the science data. Another **IMPORTANT** consequence is that the gain images are un-normalized,
  which means L1 science frames will have values relative to the average solar signal at disk center.
  Many other minor improvements have been made, which are detailed in the pull request and :doc:`online documentation </gain_correction>`. (`#105 <https://bitbucket.org/dkistdc/dkist-processing-visp/pull-requests/105>`__)
- Major improvements to polarimetric calibration; see :doc:`this page </polarization_calibration>` for more information.
  There are two main improvements here. The first is that the total system throughput is fit separately for each step of a
  PolCal Calibration Sequence. This allows us to mitigate any changes in the total incident intensity that occurs over the
  course of a Calibration Sequence (from, e.g., solar granulation). The second major change is that we now compute demodulation
  matrices with high spatial resolution. This allows us to capture real variation in the retardance of the calibration
  optics over the ViSP FOV and improve the accuracy of the derived demodulation matrices. (`#106 <https://bitbucket.org/dkistdc/dkist-processing-visp/pull-requests/106>`__)
- Update to how the two orthogonally polarized beams are combined. See :doc:`this page </science_calibration>` for more
  information. Briefly, the two beams are now combined in a way that cancels out the majority of residual polarization
  artifacts resulting from temporal-based modulation and, e.g., the effects of seeing. (`#107 <https://bitbucket.org/dkistdc/dkist-processing-visp/pull-requests/107>`__)
- Improvements to beam-registration calibration, especially the spectral angle. See the pull request for more information.
  A result is that hairline features are better identified and produce fewer interpolation artifacts. (`#108 <https://bitbucket.org/dkistdc/dkist-processing-visp/pull-requests/108>`__)
- Use `dkist-processing-pac` >= 2.0.0 to correct a bug in how the final coordinate transform was applied. As of now, all
  L1 data are in a coordinate frame consistent with SDO/HMI and Hinode-SP. See :doc:`this page </science_calibration>` for
  more information. (`#109 <https://bitbucket.org/dkistdc/dkist-processing-visp/pull-requests/109>`__)


v1.3.0 (2022-11-14)
===================




- Fixed a bug that could cause incorrect calculation of the region overlapped by both beams. It is unlikely this bug was ever encountered in the wild.


v1.1.0 (2022-11-01)
===================




- Uses a new version of the PA&C library that fixes a bug in how the inverse telescope Mueller matrices were computed. Previously, the Mueller matrices did not account for small intrinsic rotations between mirror groups.
