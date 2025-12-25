Wavelength Calibration
============================

Overview
--------

The `~dkist_processing_visp.tasks.wavelength_calibration` task provides an absolute wavelength calibration of
ViSP solar spectra by using the routines provided by the `solar-wavelength-calibration <https://docs.dkist.nso.edu/projects/solar-wavelength-calibration/en/latest/>`_ library.

Workflow
--------

#. Compute a representative spectrum by taking a median over all spatial positions of the :ref:`characteristic spectra <charspec-description>` of beam 1 computed in the solar gain task.
#. Use spectrograph setup parameters to generate a first-guess wavelength solution.
#. Feed the representative spectrum and setup parameters into the `solar-wavelength-calibration <https://docs.dkist.nso.edu/projects/solar-wavelength-calibration/en/latest/>`_ library.
#. Save the fit results as FITS header keywords, parameterizing the solution for downstream use.

Wavelength Solution Encoding
----------------------------

The wavelength solution is stored in FITS headers using the following keywords (see `Greisen et al (2006) <https://ui.adsabs.harvard.edu/abs/2006A%26A...446..747G/abstract>`_, Section 5 and Table 6):

+---------+--------------------------+----------------+
| Keyword | Description              | Units          |
+=========+==========================+================+
| `CTYPE2`| Spectral coordinate type | "AWAV-GRA"     |
+---------+--------------------------+----------------+
| `CUNIT2`| Wavelength unit          | "nm"           |
+---------+--------------------------+----------------+
| `CRPIX2`| Reference pixel          |                |
+---------+--------------------------+----------------+
| `CRVAL2`| Reference wavelength     | nm             |
+---------+--------------------------+----------------+
| `CDELT2`| Linear dispersion        | nm / px        |
+---------+--------------------------+----------------+
| `PV2_0` | Grating constant         | 1 / m          |
+---------+--------------------------+----------------+
| `PV2_1` | Spectral order           |                |
+---------+--------------------------+----------------+
| `PV2_1` | Incident light angle     | deg            |
+---------+--------------------------+----------------+

Note: The units of `PV2_0` are always 1 / m.

.. warning::
  Some data taken during OCP1 (2022) use the 1st WCS axis to record wavelength information. In rare cases OCP1 data have WCS information that is scrambled and completely incorrect.

Fitted Parameters
-----------------

The fitting process can optimize several parameters. The parameters that are free in ViSP fits are:

- **crval**: Wavelength zero-point.
- **dispersion**: Linear dispersion, allowed to vary within a few percent of the nominal value.
- **opacity_factor**: Atmospheric absorption scaling, to match telluric line strengths.
- **continuum_level**: Overall spectrum scaling, to match the observed continuum.
- **straylight_fraction**: Fraction of stray or scattered light added to the observed spectrum, affecting line depths and continuum.
- **resolving_power**: Spectral resolving power (:math:`R = \frac{\lambda}{\Delta\lambda}`), characterizing the instrument's ability to distinguish close spectral features.
- **incident_light_angle**: Angle at which light enters the grating, influencing the wavelength solution through the grating equation.


For more details on the fitting algorithms and parameterization, see the
`solar-wavelength-calibration documentation <https://docs.dkist.nso.edu/projects/solar-wavelength-calibration/en/latest/>`_
and `Greisen et al. (2006) <https://ui.adsabs.harvard.edu/abs/2006A%26A...446..747G/abstract>`_.
