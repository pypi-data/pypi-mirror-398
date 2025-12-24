============
Installation
============

:code:`bilby_pipe` is developed and tested for Python 3.9-3.10. In the
following, we demonstrate how to install a development version of
:code:`bilby_pipe` on a LIGO Data Grid (LDG) cluster.
For instructions on how to set up a Python environment, see the `Python
installation`_ section below.

Installing bilby_pipe
---------------------

.. tabs::

   .. tab:: conda

      To install the latest :code:`bilby_pipe` release from `conda-forge
      <https://anaconda.org/conda-forge/bilby_pipe>`_, run

      .. code-block:: console

         $ conda install -c conda-forge bilby_pipe

      Note, this is the recommended installation process as it ensures all
      dependencies are met.

   .. tab:: pypi

      To install the latest :code:`bilby_pipe` release from `PyPi
      <https://pypi.org/project/bilby-pipe/>`_, run

      .. code-block:: console

         $ pip install --upgrade bilby_pipe

      WARNING: this is not the recommended installation process, some
      dependencies (see below) are only automatically installed by using the
      conda installation method.
   
   .. tab:: development

      First off, clone the repository

      .. code-block:: console

         $ git clone git@git.ligo.org:lscsoft/bilby_pipe.git
         $ cd bilby_pipe/
         $ pip install -e .

      .. note::
         If you receive an error message:

         .. code-block:: console

            git@git.ligo.org: Permission denied (publickey,gssapi-keyex,gssapi-with-mic).
            fatal: Could not read from remote repository.

         Then this indicates you have not correctly authenticated with your
         git.ligo account. It is recommended to resolve the authentication issue, but
         you can alternatively use the HTTPS URL: replace the first line above with

         .. code-block:: console

            $ git clone https://git.ligo.org/lscsoft/bilby.git

      .. note::

         This will install :code:`bilby_pipe` in development mode so any changes
         made locally will immediately be reflected in the code you are running.
         If you don't want to use development mode, you can install the code
         using

         .. code-block:: console

            $ pip install .

Verifying the installation
--------------------------

To see which version of the code you are using, call

.. code-block:: console

  $ bilby_pipe --version

If the output contains something like

.. code-block:: console

  bilby_pipe=1.3.2.dev3+gb89cabe bilby=2.2.1.dev13+g33d620b7.d20240212

rather than

.. code-block:: console

  bilby_pipe=1.3.1 bilby=2.2.2

Then you have installed :code:`bilby_pipe` from source. This information is
also printed every time the code is called and therefore will be at the top of
your log files. If you see the version as something like

.. code-block:: console

   bilby_pipe=0.0.1.dev1234+g12345678 bilby=0.0.1.dev1234+g12345678

you have may have not fetched the tags associated with the code or not installed
:code:`setuptools_scm`, these can be addressed by running

.. code-block:: console

   $ git fetch --tags
   $ pip install setuptools_scm

Python installation
-------------------

.. tabs::

   .. tab:: conda

      :code:`conda` is a recommended package manager which allows you to manage
      installation and maintenance of various packages in environments. For
      help getting started, see the `IGWN Conda Distribution documentation
      <https://computing.docs.ligo.org/conda/>`_.

      For detailed help on creating and managing environments see `these help pages
      <https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html>`_.
      Here is an example of creating and activating an environment named  bilby

      .. code-block:: console

         $ conda create -n bilby python=3.10
         $ conda activate bilby

   .. tab:: virtualenv

      :code`virtualenv` is a similar tool to conda. To obtain an environment, run

      .. code-block:: console

         $ virtualenv --python=/usr/bin/python3.10 $HOME/virtualenvs/bilby_pipe
         $ source virtualenvs/bilby_pipe/bin/activate


   .. tab:: CVMFS

      To source a :code:`Python 3.9` installation on the LDG using CVMFS, run the
      commands

      .. code-block:: console

         $ source /cvmfs/software.igwn.org/conda/etc/profile.d/conda.sh
         $ conda activate igwn

     Documentation for this conda setup can be found `here 
     <https://computing.docs.ligo.org/conda/>`_. Note that you cannot install
     packages in this environment, but you can use it to run bilby_pipe
     with a reviewed version.

Dependencies
------------

:code:`bilby_pipe` handles data from the interferometers using the `gwpy
<https://gwpy.github.io/docs/stable/timeseries/remote-access.html>`_ library.
When requesting data, we first look for local frame-files, then use the `NDS2
<https://www.lsc-group.phys.uwm.edu/daswg/projects/nds-client/doc/manual/>`_
library to fetch proprietary data remotely, finally we search the open data.

To best utilise this tool, you should ensure your python installation has
access to `LDAStools-frameCPP
<https://anaconda.org/conda-forge/python-ldas-tools-framecpp>`_
for local frame-file lookup and `the NDS2 library
<https://anaconda.org/conda-forge/python-nds2-client>`_ for proprietary remote
data look up. These libraries are typically part of most LIGO data stacks and
can be installed with conda using the commands

.. code-block:: console

   $ conda install -c conda-forge python-ldas-tools-framecpp
   $ conda install -c conda-forge python-nds2-client
