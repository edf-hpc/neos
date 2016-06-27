.. _installation:

Installation
************

NEOS is only supported on GNU/Linux systems. The installation must be
performed with ``root`` user.

Dependencies
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
