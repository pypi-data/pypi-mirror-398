==========
Injections
==========

Injection files
---------------
The most straight-forward way of defining a set of injections is to provide an
:code:`injection-file=` line in your ini. This should point to either a :code:`dat`
(essentially a CSV file containing rows of injections and columns of parameter
names) or :code:`json` injection file.
To generate an injection file, we provide a `command-line utility <executables/create_injections.html>`_.
More details on the format is also provided on that page.

General tips
------------

No injection file
=================
If :code:`injection-file` is not given in the configuration, but
:code:`injection=True`, then a set of injections will be generated from the
:code:`prior-file` (using :code:`bilby_pipe_create_injection_file`).

Interaction with :code:`n-simulation`
=====================================
If :code:`n-simulation` and :code:`injection-file` are both specified, the number
of injections needs to match :code:`n-simulation` or a subset of injections needs
to be specified. In this case, coloured
Gaussian noise is simulated used the power-spectal-density (psd) defined in
:code:`psd-dict` or the default aLIGO psd. Then, the injections are simulated
and injected into this noise.

Interaction with :code:`gps-times` or :code:`gps-tuple`
=======================================================
If either :code:`gps-times` or :code:`gps-tuple` are given with
:code:`injection-file` or :code:`injection=True` then injections are added to
the inteferometer data. Again, the number of injections needs to match the number
of gps times or a subset to use must be specified.

Specifying a subset of injections
=================================
A subset of injections can be selected using the :code:`injection-numbers`
argument. Note, the size of this restricted set must then match either the number
of simulations or the number of gps-times.

Specifying the injection waveform
=================================
A different waveform argument can be given via the :code:`injection-waveform-approximant` option.

XML files
=========
XML files were a common standard for gravitational wave data analysis. We do
not support them natively (as an input file to bilby_pipe), but we provide a
conversion mechanism. For help with this, see

.. code-block:: console

   $ bilby_pipe_xml_converter --help
