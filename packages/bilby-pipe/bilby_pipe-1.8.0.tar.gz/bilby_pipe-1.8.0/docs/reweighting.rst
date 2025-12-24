=============================================
Importance sampling (reweighting) an analysis
=============================================

Often we want to perform the analysis with a simplified model, e.g., using an
ROQ approximation or a less-sophisticated waveform approximant. However, we
also want to know what result we would have got without the simplifying
assumptions.

In order to facilitate this, we provide an option to specify modifications to
the run configuration as an additional argument
:code:`----reweighting-configuration`. This should be either a :code:`json` file
or string containing a new :code:`prior-file` or any of the likelihood arguments
that can be passed to the :code:`bilby_pipe` parser.

If you are specifying a new prior file, the parameterization should remain the
same, reweighting to include new parameters will generally not work with this
implementation and should be done on a case-by-case basis. The exception to this
is adding calibration marginalization which can be included by specifying a new
:code:`calibration-model` as described in
`arXiv:2009.10193 <https://arxiv.org/abs/2009.10193>`_.

If you are using the file transfer option, you must list this configuration file
and any other needed files, e.g., a new prior file/calibration envelopes.

Reweighting nested samples
--------------------------

If the initial sampling is done with a nested sampler, it is possible to apply
the importance sampling directly to the nested samples. This can lead to larger
reweighting efficiency as the nested samples probe the tails of the posterior
more deeply. To enable this, set `reweight-nested-samples=True`.

Example using the configuration file
------------------------------------

In this example, we perform the initial analysis with the "relative binning"
method and a waveform without higher-order emission modes (:code:`IMRPhenomXAS`)
and then we reweight to the full likelihood with a waveform with higher-order
modes (:code:`IMRPhenomXHM`).

The configuration file for the initial analysis is a modified version of the
injection example in the examples page.

.. literalinclude:: ../examples/reweighting/bbh_injection.ini

Since we are changing the likelihood used, we need to specify a new
:code:`likelihood-type` and :code:`frequency-domain-waveform-model`.
To change the waveform approximant, we just specify the new model.

.. literalinclude:: ../examples/reweighting/reweight.json
    :language: json


Example for a completed analysis
--------------------------------

It is also possible to reweight a result for an analysis that has fully
completed without having to modify the configuration. In this case you
can use the :code:`bilby_pipe_reweight_result`
`executable <executables/reweighting>`_.

