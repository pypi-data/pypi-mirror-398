===============
Global settings
===============

In addition to the settings described in the previous sections, there are a
number of global settings that can be used to customise analyses.
These are set in the :code:`global` section of the ini file and apply to
all analyses.


Cosmology
=========

The cosmology to use in the analyses can be set using the :code:`cosmology`
argument. If not set, the default cosmology is :code:`Planck15` as implemented
in :code:`astropy`.

If using cosmological priors, for example :external:py:class:`bilby.gw.prior.UniformSourceFrame`,
then the prior cosmology must match the global :code:`cosmology`. If they do not
match, an error will be raised.

For a list of available cosmologies, :external:py:func:`bilby.gw.cosmology.get_available_cosmologies`.
