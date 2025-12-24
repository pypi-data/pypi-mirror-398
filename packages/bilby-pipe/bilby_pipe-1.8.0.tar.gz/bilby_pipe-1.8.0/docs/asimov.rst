==================================
Large Scale Automation with Asimov
==================================

.. automodule:: bilby_pipe.asimov.asimov

Asimov is an external framework designed to assist with deploying analyses at
scale. Bilby has a plugin to allow the framework to deploy Bilby analyses. 

Review Status
=============

.. note::
    The current integration with bilby will require code review before it is fully compatible with collaboration analyses.

Usage Guide
===========

Applying Default Settings
--------------------------

After the initialisation of an Asimov project, the first step will be to define
any project-wide configuration options for Bilby deployment. An example of this
that are the defaults for an LVK style analysis, including a default set of
priors, are shown below

Default Settings
~~~~~~~~~~~~~~~~

.. literalinclude:: ../tests/ASIMOV/bilby_defaults.yaml
   :language: yaml

Default Priors
~~~~~~~~~~~~~~

.. literalinclude:: ../tests/ASIMOV/bilby_priors.yaml
   :language: yaml

Once the configuration options are saved within files---in this instance
`bilby_defaults.yaml` and `bilby_priors.yaml` respectively---these may be
applied to the project with

.. code-block:: console

        $ asimov apply -f bilby_defaults.yaml
        $ asimov apply -f bilby_priors.yaml

Applying an Event
-----------------

The next step is to add the data related to a specific gravitational wave such
as the trigger time, data channels, etc. There are a number of ways to do this,
but for the purposes of this example we apply GW150914_090545---the first
gravitational wave detection---in a configuration that mirrors that used for the
creation of GWTC-2.1. These settings are provided below:

.. literalinclude:: ../tests/ASIMOV/GW150914.yaml

Saving this to a file (in this example `GW150914.yaml`), this may be applied to
the ledger similarly to the previous applications by running

.. code-block:: console

   $ asimov apply -f GW150914.yaml


Applying Analysis to Event
--------------------------

Once the project-wide defaults are set and an event has been added to the
project, the next step is to apply the specific Bilby analysis that you wish to
perform. This is again done through the application of a YAML file. Below we
show an example of a file that would set up an analysis a binary black hole
signal using the IMRPhenomXPHM waveform model. This will first run a Bayeswave
analysis to generate the PSD files. 

.. literalinclude:: ../tests/ASIMOV/bilby_analysis.yaml
   :language: yaml

Once again, saving this to a file (in this example in ``bilby_analysis.yaml``),
this may be applied to the event (in this example `GW150914`) by running

.. code-block:: console

    $ asimov apply -f bilby_analysis.yaml -e GW150914


Launching the Analysis
----------------------

With all of the requisite information within the ledger, the analysis may then
be built and submitted to the cluster by running

.. code-block:: console

       $ asimov manage build submit


A More Complex Analysis
-----------------------

The above example, as stated, would set up an analysis of a standard binary
black hole signal. A more complex analysis such as an ROQ analysis of a BNS
signal requires more specific customisation. An example of this is shown below:

.. code-block:: yaml

        kind: analysis
        pipeline: bilby
        name: bilby-roq
        needs:
            - Bayeswave
        approximant: IMRPhenomPv2_NRTidalv2
        comment: IMRPhenomPv2_NRTidalv2 256s ROQ job
        likelihood:
            marginalization:
                phase: True
            frequency domain source model: lal_binary_neutron_star_roq
            calibration:
                sample: True
            type: ROQGravitationalWaveTransient
            roq:
                folder: None
                linear matrix: /home/roq/IMRPhenomPv2_NRTidalv2/bns/basis_256s.hdf5
                quadratic matrix: /home/roq/IMRPhenomPv2_NRTidalv2/bns/basis_256s.hdf5
                scale: 1.0
        sampler:
            sampler: dynesty
        priors:
            default: BNSPriorDict
            chirp mass:
                minimum: 0.92
                maximum: 1.70
            spin 1:
                maximum: 0.4
            spin 2:
                maximum: 0.4



Bilby Specific Metadata
=======================

Ledger Options
--------------

The bilby pipeline interface looks for the sections and values listed below in
addition to the information which is required for analysing *all* gravitational
wave events such as the locations of calibration envelopes and data.

``likelihood``
~~~~~~~~~~~~~~

These settings affect the behaviour of the bilby likelihood module.

``marginalization``
    This section takes a list of types of marginalization to apply the analysis.

    ``distance``
        Activates distance marginalization.
    ``phase``
        Activates phase marginalization.
    ``time``
        Activates time marginalization.

``roq``
    This section allows ROQs to be defined for the likelihood function.

    ``folder``
            The location of the ROQs.

            Defaults to None.
    ``scale factor``
            The scale factor of the ROQs.

            Defaults to 1.

``kwargs``
    Additional keyword arguments to pass to the likelihood function in the form
    of a YAML or JSON format dictionary.

    Defaults to None.

``sampling``
~~~~~~~~~~~~

The sampling section of the ledger can be used to specify both the bilby sampler
which should be used, and the settings for that sampler. 

``sampler``
    The name of the sampler which should be used.

    Defaults to `dynesty`.

``seed``
    The random seed to be used for sampling.

    Defaults to `None`.

``parallel jobs``
    The number of parallel jobs to be used for sampling.

    Defaults to `4`.

``sampler kwargs``
    Additional keyword arguments to pass to the sampler in the form of a YAML or
    JSON format dictionary.

    Defaults to `"{'nlive':2000, 'sample':'rwalk', 'walks':100, 'nact':50, 'check_point_delta_t':1800, 'check_point_plot':True}"`


Further Information
===================
For additional information, see the `asimov`_ documentation. 

    .. _asimov: https://asimov.docs.ligo.org/asimov


Bilby Integration Class
=======================

.. autoclass:: bilby_pipe.asimov.asimov.Bilby
