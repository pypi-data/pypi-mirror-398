===================================
The Open Science Grid and IGWN-grid
===================================

The `IGWN Grid <https://computing.docs.ligo.org/guide/condor/>`_ is now the
recommended way to submit :code:`bilby_pipe` analyses using LVK resources.
The IGWN Grid allows access to all dedicated resources (i.e. CIT, LHO), but also
resources such as the Open Science Grid.

To run jobs through the OSG, login to on of the IGWN grid submit nodes
(:code:`{ldas-osg,ldas-osg2,ldas-osg3}.ligo.caltech.edu` at CIT), see
`here <https://computing.docs.ligo.org/guide/htcondor/access/>`_ for more
details

.. code-block:: console

   ssh albert.einstein@ldas-osg.ligo.caltech.edu

Then submit usual :code:`bilby_pipe` jobs, but with the flag

.. code-block:: console

   osg = True

in your configuration (ini) files.

When running on the IGWN-grid, the software you run needs to be available on
the compute nodes. A detailed guide to accessing software in the IGWN-grid is
given on the `IGWN computing docs 
<https://computing.docs.ligo.org/guide/htcondor/software/>`_.
:code:`bilby_pipe` supports all of the methods described on that page.

:code:`CVMFS`
-------------

To use the `IGWN conda distribution available through cvmfs
<https://computing.docs.ligo.org/conda/>`_ you should either
submit your job using an IGWN environment, or use the :code:`conda-env` flag to
choose one of the IGWN environments.

:code:`containers`
------------------

Containers provide an isolated, distributable, computing environment.
There are multiple methods to leverage containers in the IGWN grid and
there are detailed instructions for how to build and distribute images
on the `IGWN computing docs <https://computing.docs.ligo.org/guide/dhtc/containers/>`_.

.. warning::
    In the future we plan to make production-ready containers available, however, this
    is currently a work in progress.

To use a singularity image you should set the :code:`container` argument to
point to the container. If the container is provided as a path in the local
filesystem it will be automatically transferred to the job. Additionally, you
will most likely need to specify the :code:`conda-env` argument to point to the
appropriate environment within the container.

.. note::
    Using containers requires the use of the :code:`HTCondor` file transfer mechanism.


Standalone executables
----------------------

Specifying the analysis executable is another way to leverage grid computing.
If an executable is provided to point to a CVMFS-distributed environment, that
environment can then be used if the remainder of the workflow uses a local environment.

When using the IGWN-grid, you can specify which site you would like your job
to run on by using the :code:`desired-sites` option.
