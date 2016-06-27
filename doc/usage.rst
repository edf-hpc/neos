.. _usage:

Usage guide
***********

Synopsis
========

**neos** *options* [-s --scenario *scenario*]

Description
===========

NEOS is a software which provides a generic framework to manage job sessions
on HPC clusters.

The framework is based on scenarios. A scenario defines the sequential steps to
properly setup and initialize the job session. Users select the scenario for
their jobs and can even define their own scenarios. The frawework can manage a
wide variety of workloads from classic MPI parallel computing to advanced
visualization sessions with 3D remote rendering.

Global options
==============

    -h, --help      Show help message and exit.
    --version       Print NEOS version and exit.
    -d, --debug     Enable debug output.
    --dry-run       Dry-run mode: print commands to run without actually running them.
    -s, --scenario=SCENARIO
                    Name of scenario to run.
    --scenarios-dir=DIR
                    Path to directory with additional scenarios to load.
    -m, --module=MODULE
                    Name of environment module to load?
    --modules-dir=DIR
                    Path to directory with additional modules.
    --opts=OPTS     Optional parameters for scenarios.

.. _examples:

Examples
========

Run default scenario::

    neos

Run `gnome` scenario with specific resolution::

    neos --scenario=gnome --opts=resolution:1280x1024

Run `paraview` scenario within `openmpi-1.10` module environment::

    neos --scenario=paraview --module=openmpi-1.10

Run user-specific `foo` scenario within `bar` specific module in dry run mode::

    neos --dry-run --scenario-dirs=~/scenarios --scenario=foo --modules-dir=~/modules --module=bar
