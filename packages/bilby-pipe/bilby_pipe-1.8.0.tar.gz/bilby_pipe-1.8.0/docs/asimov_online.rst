==================================================
Automation of Online-Style Replication with Asimov
==================================================

Usage Guide
===========

For generalised instructions on the usage of Asimov, please see the `asimov`_
documentation.

.. _asimov: https://asimov.docs.ligo.org/asimov

.. note::
   Replication of online analysis requires that you be able to authenticate on
   `GraceDB`

To begin, a project may be initialised with e.g.

.. code-block:: console

   $ asimov init bilby_online_project

Default Settings
---------------- 

The following settings replicate the online analyses as deployed by `GWCelery`

.. literalinclude:: ../tests/ASIMOV/online_defaults.yaml
   :language: yaml

where the contents of the settings files are shown below. If these are contained
within a file `online_defaults.yaml`, they may be applied to an initialised
asimov project with

.. code-block:: console

   $ asimov apply -f online_defaults.yaml

This includes settings to allow the running of `PESummary` after the bilby
run is complete.

BNS Settings
~~~~~~~~~~~~

.. literalinclude:: ../tests/ASIMOV/bns_online_settings.json
   :language: json

BBH Settings
~~~~~~~~~~~~

.. literalinclude:: ../tests/ASIMOV/bbh_online_settings.json
   :language: json

Once applied, an event needs at a bare minimum only its GraceDB G-name. An
example of a minimal event would be

.. literalinclude:: ../tests/ASIMOV/online_event.yaml
   :language: yaml

and the subsequent analysis file would be given by

.. literalinclude:: ../tests/ASIMOV/online_analysis.yaml
   :language: yaml

Assuming these files were named `G298936.yaml` and `online.yaml` respectively,
these may be applied with

.. code-block:: console

   $ asimov apply -f G298936.yaml
   $ asimov apply -f online.yaml -e G298936

with the settings file being applied using a similar command to the application
of the event file. 

Ledger Options
--------------

``channels``
~~~~~~~~~~~~

May be given in the event YAML file to determine which set of channels to pull
the interferometer data for the event from. This is passed directly to the
`--channel_dict` option of `bilby_pipe_gracedb` so may be one of the options
specified on the :doc: `relevant page <gracedb>`.


``mass settings``
~~~~~~~~~~~~~~~~~

A dictionary of dictionaries that maps the relevant settings and likelihood mode
for the given mass constraint. These will be evaluated such that the lower bound
is inclusive and the higher bound is exclusive. If a `defaults` key is included, it
will be the fallback. Otherwise, an error will be raised if a mass is not within
any specified boundary.

  ``name``
      The name given to that setting constraint.
          ``low mass bound``
              Low mass edge of applicability of these settings (inclusive).
          ``high mass bound``
              High mass edge of applicability of these settings (exclusive).
          ``settings file``
              Path to JSON containing settings for the event.
          ``likelihood mode``
              Name of the ROQ likelihood that should be used. 

API
===

.. autoclass:: bilby_pipe.asimov.asimov.BilbyOnline
