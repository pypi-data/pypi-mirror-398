=========================
Customising data analysis
=========================

It is possible to specify alternative likelihoods, default priors, source models, and suchlike through the ini file.
Each of these are done by passing a full :code:`python` path, for example, to use a :code:`WaveformGenerator` class
and source model from some external package the following should be included in the ini file.

.. code-block:: text

    waveform-generator-class = my_package.submodule.CustomWaveformGenerator
    frequency-domain-source-model = my_package.submodule.custom_source_model

In order to be compatible with the :code:`bilby_pipe` analysis scripts, custom classes should take the same arguments
as their parent classes. If you do not want to hard code all such arguments, you can use :code:`**kwargs` to capture
(and ignore) additional arguments. Parameters used for instantiating a ``waveform-generator-class`` can
be passed with the argument ``--waveform-generator-constructor-dict`` (for the template) or
``--injection-waveform-generator-constructor-dict`` (for the injection).

An exception to this is when passing custom likelihood classes.
In this case additional keyword arguments can be passed through the ini file, as below

.. code-block:: text

    likelihood-type = my_package.submodule.CustomLikelihood
    extra-likelihood-kwargs = {new_argument: value, other_argument: other_value}

Specifically, the following options allow one to pass a :code:`python` path:

.. code-block:: text

    analysis-executable-parser
    conversion-function
    default-prior
    frequency-domain-source-model
    generation-function
    likelihood-type
    waveform-generator-class
