.. NEOS documentation master file, created by
   sphinx-quickstart on Wed Jun 22 08:06:17 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to NEOS's documentation!
==================================


NEOS is a software which provides a generic framework to manage job sessions
on HPC clusters.

The framework is based on scenarios. A scenario defines the sequential steps to
properly setup and initialize the job session. Users select the scenario for
their jobs and can even define their own scenarios. The frawework can manage a
wide variety of workloads from classic MPI parallel computing to advanced
visualization sessions with 3D remote rendering.

Scenarios are defined in Python programming language with a fully documented
API.

NEOS is fully integrated with open-source `Slurm`_ workload manager and
`Modules`_ environment manager.

NEOS is a free software distributed under the terms of the CeCILL v2.1
license.

.. _Slurm: http://slurm.schedmd.com
.. _Modules: http://modules.sourceforge.net

.. toctree::
   :maxdepth: 2

   architecture
   installation
   configuration
   usage
   api

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

