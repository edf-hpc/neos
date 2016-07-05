.. _installation:

Installation
************

NEOS is only supported on GNU/Linux systems. The installation must be
performed with ``root`` user.

Requirements
============

NEOS software has the following dependencies:

* Python >= 2.7
* ClusterShell
* pytz
* PySLURM >= 15.08

From sources
============

First, install Python packaging system ``setuptools`` on the system. It is
probably available through the packaging system of your distribution. For
example, on Debian/Ubuntu::

    apt-get install python-setuptools

Then, download the source of NEOS from the Git source code repository::

    wget https://github.com/edf-hpc/neos/archive/master.tar.gz

Then, extract the sources and run the following command to install NEOS
with all its dependencies::

    python setup.py install

Debian packages
===============

Build
-----

Install build dependencies::

    apt-get install dh-python

Then build package::

    dpkg-buildpackage -us -uc

Install
-------

The Debian package can be installed manually using `dpkg` utility::

    dpkg -i neos*.deb

However, it is recommended to deploy the package in a repository (with
`reprepro`_ or similar). Then, the package can be installed with all its
dependencies using `apt` command::

    apt-get install neos

.. _reprepro: http://mirrorer.alioth.debian.org/

.. _configuration:

Configuration
=============

NEOS has a unique configuration file `/etc/neos/neos.conf`. This format of
this file follows the INI conventions with sections and key/value pairs. All
parameters are optional and may be commented out.

Here is the complete configuration file with all its default values::

    [cluster]
    name = computer
    partition = cg
    wanprefix = rin

    [scenarios]
    dir = /var/lib/neos/scenarios
    default = xfce4

    [internals]
    basedir = ~/.neos
    inenv = /usr/lib/neos/exec/neos_inenv
    mcmd = /usr/bin/modulecmd
    shell = bash

The files has 3 sections detailled in the following parts.

cluster section
---------------

This section contains settings about the general cluster configuration:

* ``name`` (default: *computer*): the name of the cluster in Slurm
  configuration.
* ``partition`` (default: *cg*): the name of the Slurm partition that is able
  to run NEOS scenarios. Running NEOS scenarios on another partition will
  produce an error.
* ``wanprefix`` (default: *rin*): the hostname prefix of the nodes on the WAN
  network.

scenarios section
-----------------

This sections contains global scenarios settings:

* ``dir`` (default: */var/lib/neos/scenarios*): the absolute path to directory
  that contains the system-wide scenarios available to all users.
* ``default`` (default: *xfce4*): the name of the default scenario run by NEOS.

internals section
-----------------

This section contains NEOS internal settings. Default values may be fine for
most users, you should not probably not modify those settings unless you really
know what you are doing.

* ``basedir`` (default: *~/.neos*): the path to the directory used to store
  files created by the scenarios by default. Technically, this value replaces
  the `${BASEDIR}` placeholder in the optional parameters of the scenarios. All
  NEOS users must have write access to this directory.
* ``inenv`` (default: */usr/lib/neos/exec/neos_inenv*): the absolute path to the
  executable run by NEOS in modified environment after loading a module.
* ``mcmd`` (default: */usr/bin/modulecmd*): the absolute path to the executable
  that produces the list of shell commands to tune the environment providing it
  a module file.
* ``shell`` (default: *bash*): the shell used to setup the environment when
  loading a module file.
