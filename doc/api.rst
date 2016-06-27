Write scenario
**************

Quickstart
==========

A scenario is a Python sub-class of the NEOS Scenario class. There are only two requirements to be a valid and usable scenario for the application:

* It must have a ``NAME`` class attribute,
* It must implement a ``run()`` method that returns an exit code.

A minimal Scenario would look like::

    #!/usr/bin/env python

    from neos import Scenario

    class ScenarioMinimal(Scenario):

        NAME = 'minimal'

        def run(self):
            return 0

The name of the class has no real importance. The name of the scenario accross
NEOS will be the value of the NAME class attribute.

NEOS considers the scenario run failed when the ``run()`` method returns
non-0 exit code. This exit code is also the exit code returned by ``neos``
command.

If you save this scenario code into ``~/scenarios/minimal.py``, you can run it
with the following command::

    neos --scenarios-dir=~/scenarios --scenario=minimal

Optional parameters
===================

The scenarios can be configured at runtime with optional parameters. The
declaration of optional parameters is done through the ``OPTS`` class
attribute. As an example, optional paramters can be added to the previous
*minimal* scenario this way::

    #!/usr/bin/env python

    from neos import Scenario

    class ScenarioMinimal(Scenario):

        NAME = 'minimal'
        OPTS = [ 'wait:bool:false',
                 'time:int:10',
                 'cmd:str:/bin/true' ]

        def run(self):

            output = self.cmd_output(self.opts.cmd)

            if self.opts.wait is True:
                self.sleep(self.opts.time)

            return 0

The OPTS class attribute is a list of strings. Each string is a triplet of
parameter name, type and default value separated by the ':' character.

In the previous example, the scenario has 3 optional parameters:

* the boolean ``wait`` which is false by default,
* the integer ``time`` whose default value is 10,
* t he string ``cmd`` with default value to ``/bin/true``.

The parameters are then accessible in the ``run()`` method as attributes of
the opts object attribute. Ex: ``self.opts.wait`` for the *wait* attribute.

Without options specified on ``neos`` command line, the default values are
used. Other values can be set with ``-o, --opts`` parameter::

    neos --scenarios-dir=~/scenarios --scenario=minimal --opts=wait:false

NEOS framework make sure parameters types are respected.

Reference API
=============

The ``run()`` method of the scenarios can run any arbitrary Python code.
However, the parent Scenario class provides a set of methods to ease most
common tasks and code patterns. This is highly recommended to widely use
those methods in the source code of your scenarios in order to get the
following benefits:

* significantly reduce the number of lines of code,
* integrates fully with NEOS framework and thus Slurm workload manager.

**TODO**
