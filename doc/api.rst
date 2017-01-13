Scenario API
************

Quickstart
==========

A scenario is a Python sub-class of the NEOS Scenario class. There are only two
requirements to be a valid and usable scenario for the application:

* Have a ``NAME`` class attribute,
* Implement a ``run()`` method that returns an exit code.

A minimal Scenario would look like::

    #!/usr/bin/env python

    from neos import Scenario

    class ScenarioMinimal(Scenario):

        NAME = 'minimal'

        def run(self):

            return 0

The name of the class has no real importance. The name of the scenario across
NEOS will be the value of the **NAME** class attribute.

NEOS considers the scenario run failed when the ``run()`` method returns
non-0 exit code. This exit code is also the exit code returned by ``neos``
command.

If you save this scenario code into *~/scenarios/minimal.py*, you can run it
with the following command::

    srun neos --scenarios-dir=~/scenarios --scenario=minimal

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
        OPTS = ['wait:bool:false',
                'time:int:10',
                'msg:str:foo']

        def run(self):

            output = self.cmd_output(['echo', self.opts.msg])

            if self.opts.wait is True:
                self.sleep(self.opts.time)

            return 0

The **OPTS** class attribute is a list of strings. Each string is a triplet of
parameter name, type and default value separated by the ':' character.

In the previous example, the scenario has 3 optional parameters:

* the boolean **wait** which is false by default,
* the integer **time** whose default value is 10,
* the string **msg** with default value to *foo*.

The parameters are then accessible in the ``run()`` method as attributes of
the opts object attribute. Ex: ``self.opts.wait`` for the **wait** attribute.

Without options specified on ``neos`` command line, the default values are
used. Other values can be set with ``-o, --opts`` parameter::

    srun neos --scenarios-dir=~/scenarios --scenario=minimal --opts=wait:false

NEOS framework make sure parameters types are respected.

Command level logfiles
======================

Additionally to ``-l,--log`` argument which redirect the outputs of all
sub-commands of a scenario, NEOS also supports fine-grain redirections of the
stdout and stderr outputs to arbitrary files at command level. This is
controlled with optional ``stdout`` and ``stderr`` arguments of ``cmd_run_bg()``
and ``cmd_wait()`` scenarios methods. Here is a commented example::

    #!/usr/bin/env python
    
    from neos import Scenario
    
    class ScenarioOutputs(Scenario):
    
        NAME = 'outputs'
    
        def run(self):
    
            # bar1 printed to neos stdout or --log file if set
            self.cmd_wait(['echo', 'bar1'])
    
            # bar2 printed in foo2 file
            self.cmd_wait(['echo', 'bar2'], stdout='foo2')
    
            # bar3 redirected to /dev/null, foo3 created but empty
            self.cmd_wait(['echo', 'bar3'], stdout='/dev/null', stderr='foo3')
    
            # error printed on stderr by cat redirected to /dev/null
            self.cmd_wait(['cat', '/root/fail'], stderr='/dev/null')
    
            # neos cannot open /root/fail (permission denied), bar4 is printed to
            # neos stdout or --log file is set.
            self.cmd_wait(['echo', 'bar4'], stdout='/root/fail')
    
            return 0

NEOS automatically takes care of opening and closing all files descriptors as
needed.

Abstract scenarios
==================

A scenario does not need to have the Scenario base class as its direct parent
class. As soon as one its parents inherits from the Scenario class, directly
or not, it is valid scenario. Here comes the concept of **abstract scenario**.

An abstract scenario is a class that inherits from the Scenario base class but
has no **NAME** attribute. Those classes can define code and optional
parameters but cannot be run directly with NEOS. They are useful to define
generic code shared by multiple scenarios.

Here is a complete example::

    #!/usr/bin/env python

    from neos import Scenario

    class ScenarioEchoWait(Scenario):

        OPTS = ['wait:bool:false',
                'time:int:10']

        def _echo_wait(self, msg):

            output = self.cmd_output(['echo', msg])

            if self.opts.wait is True:
                self.sleep(self.opts.time)

            return 0


    class ScenarioFoo(ScenarioEchoWait):

        NAME = 'true'
        OPTS = ['msg:str:foo']

        def run(self):
            self._echo_wait(self.opts.msg)


    class ScenarioBar(ScenarioEchoWait):

        NAME = 'false'
        OPTS = ['msg:str:bar']

        def run(self):
            self._echo_wait(self.opts.msg)

In this example, the ``ScenarioEchoWait`` class does not have a **NAME** class
attribute. Then, NEOS consider it as an abtract scenario.

The other classes ``ScenarioFoo`` and ``ScenarioBar`` inherits from the
``Scenario`` base class (through the ``ScenarioEchoWait`` class), have a
**NAME** class attribute and define a ``run()`` method. Then, NEOS consider
those classes as valid scenarios that can be run.

Using this mechanism, ``ScenarioFoo`` and ``ScenarioBar`` can share code: they
both use the same method ``_echo_wait()`` and the optional parameters defined
in the ``ScenarioEchoWait`` class.

Then, the scenarios can be run with::

    srun neos --scenarios-dir=~/scenarios --scenario=foo

Or::

    srun neos --scenarios-dir=~/scenarios --scenario=bar

Reference API
=============

The ``run()`` method of the scenarios can run any arbitrary Python code.
However, the parent Scenario class provides a set of methods to ease most
common tasks and code patterns. This is highly recommended to widely use
those methods in the source code of your scenarios in order to get the
following benefits:

* significantly reduce the number of lines of code,
* integrates fully with NEOS framework and thus Slurm workload manager.

Here are the available public methods of the base Scenario class:

.. py:method:: ensure_dir(filename)

   Creates recursively all the parent directories of a file if they do not
   exist.

   :param str filename: the relative or absolute path of the file.
   :return: None

.. py:method:: create_file(filename)

   First ensures the parent the directory of the file exists, then create an
   empty file if it does not exist.

   :param str filename: the relative or absolute path of the file.
   :return: None

.. py:method:: register_tmpfile(filename)

   Register a temporary file to remove on NEOS exit. All temporary files
   created by the scenarios must be registered using this method.

   :param str filename: the absolute path to the file.
   :return: None

.. py:method:: sleep(time)

   Sleep the specified amount of time unless in dry-run mode.

   :param time: the time in seconds to sleep for.
   :type time: int or float
   :return: None

.. py:method:: cmd_run_bg(cmd, shell=False, stdout=None, stderr=None)

   Run the given command in background, unless in dry-run mode. In dry-run mode,
   the command is just printed as an information message. If the shell parameter
   is True, the command is run in a new spawned shell. If stdout and stderr are
   valid file paths and can be opened, respectively stdout and stderr outputs of
   the command are redirected to these files. If not set or an error is
   encountered while opening the files, the outputs of the command will be
   either connected to neos stdout/stderr or redirected to the logfile if
   ``-l,--log`` parameter is set.

   :param cmd: the command to run in background.
   :type cmd: a list of strings with the command and its parameters.
   :param bool shell: whether the command is run in a new shell or not.
   :param str stdout: file path where to redirect stdout of the command.
   :param str stderr: file path where to redirect stderr of the command.
   :return: the handler on the process launched in background.
   :rtype: Popen object

.. py:method:: cmd_wait(cmd, shell=False, stdout=None, stderr=None)

   Run the given command and wait for it to complete, unless in dry-run mode. In
   dry-run mode, the command is just printed as an information message. If the
   shell parameter is True, the command is run in a new spawned shell. If stdout
   and stderr are valid file paths and can be opened, respectively stdout and
   stderr outputs of the command are redirected to these files. If not set or an
   error is encountered while opening the files, the outputs of the command will
   be either connected to neos stdout/stderr or redirected to the logfile if
   ``-l,--log`` parameter is set.

   :param cmd: the command to run in background.
   :type cmd: a list of strings with the command and its parameters.
   :param bool shell: whether the command is run in a new shell or not.
   :param str stdout: file path where to redirect stdout of the command.
   :param str stderr: file path where to redirect stderr of the command.
   :return: the command exit code
   :rtype: int

.. py:method:: cmd_output(cmd, shell=False)

   Run the given command, wait for it to complete and returns its output,
   unless in dry-run mode. If the shell parameter is True, the command is run
   in a new spawned shell. In dry-run mode, the command is just printed as an
   information message and the fake output *dryrunoutput* is returned.

   :param cmd: the command to run in background.
   :type cmd: a list of strings with the command and its parameters.
   :param bool shell: whether the command is run in a new shell or not.
   :return: the output the command
   :rtype: string
