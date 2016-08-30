#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Copyright (C) 2016 EDF SA
#
#  This file is part of NEOS
#
#  This software is governed by the CeCILL license under French law and
#  abiding by the rules of distribution of free software. You can use,
#  modify and/ or redistribute the software under the terms of the CeCILL
#  license as circulated by CEA, CNRS and INRIA at the following URL
#  "http://www.cecill.info".
#
#  As a counterpart to the access to the source code and rights to copy,
#  modify and redistribute granted by the license, users are provided only
#  with a limited warranty and the software's author, the holder of the
#  economic rights, and the successive licensors have only limited
#  liability.
#
#  In this respect, the user's attention is drawn to the risks associated
#  with loading, using, modifying and/or developing or reproducing the
#  software by the user in light of its specific status of free software,
#  that may mean that it is complicated to manipulate, and that also
#  therefore means that it is reserved for developers and experienced
#  professionals having in-depth computer knowledge. Users are therefore
#  encouraged to load and test the software's suitability as regards their
#  requirements in conditions enabling the security of their systems and/or
#  data to be ensured and, more generally, to use and operate it in the
#  same conditions as regards security.
#
#  The fact that you are presently reading this means that you have had
#  knowledge of the CeCILL license and that you accept its terms.

import logging
logger = logging.getLogger(__name__)
import sys
from subprocess import Popen, PIPE
import os
import glob
import imp
import inspect
import signal

from neos.scenario import UsableScenario, Scenario
from neos.conf import Conf, ConfLoader
from neos.args import AppArgs
from neos.job import Job


class Launcher(object):
    """Launcher class is responsible of initializing runtime configuration
       based on configuration file and arguments, logger and then launching
       the application given in parameter."""

    def __init__(self, app=None, conf_path='/etc/neos/neos.conf'):
        """If the app is not set, the Launcher tries to figure out by itself
           the best choice between App and AppInEnv based on parameters."""

        self.app = app
        # first instanciations of Conf and Job singletons here
        self.conf = Conf()
        self.job = Job()
        self.load_conf_file(conf_path)
        self.args = AppArgs(self.conf)
        self.parse_args()
        self.setup_logger()

    def load_conf_file(self, conf_path):
        """Parse config file and update app conf accordingly"""

        loader = ConfLoader(conf_path)
        loader.update_conf(self.conf)

    def parse_args(self):
        """Parse args and update app conf accordingly"""

        self.args.update_conf(self.conf)

    def setup_logger(self):
        """Setup application logger"""

        app_logger = logging.getLogger('neos')
        if self.conf.debug is True:
            app_logger.setLevel(logging.DEBUG)
        else:
            app_logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(levelname)s: %(message)s')
        handler.setFormatter(formatter)
        app_logger.addHandler(handler)

    def can_run_outside_job(self):
        """NEOS can run out of job environment only to print help
           (automatically handled by argparse), version or list scenarios.
           In all other cases, NEOS will fail if run outside job
           environment."""
        return self.conf.print_version or self.conf.list_scenarios

    def run(self):
        """Initialize and run the application only if expected partition and
           job task 0. This way, NEOS behaves the same when launched with
           either srun and sbatch."""

        # Check if outside job environment and in authorized exceptions, else
        # leave with error.
        if self.job.unknown and not self.can_run_outside_job():
            logger.error("NEOS cannot run outside of job environment")
            return 1

        if self.job.known:
            if self.job.partition != self.conf.cluster_partition:
                logger.error("cannot run on partition %s", self.job.partition)
                return 1
            if self.job.procid:
                logger.debug("instantly leaving on procid %d", self.job.procid)
                return 0

        # If the app is not yet defined at this stage, the launcher tries to
        # find out the best one based on parameters.
        if self.app is None:
            if self.can_run_outside_job() or self.conf.module is None:
                self.app = AppInEnv
            else:
                self.app = App
            logger.debug("app selected: %s", self.app.__name__)

        app = self.app(self.conf, self.job)
        return app.run()


class App(object):
    """NEOS main application directly launched by the users. This application
       is responsible of loading the environment module (if specified by user)
       and launching the inenv app within this new fully populated
       environment."""

    def __init__(self, conf, job):

        self.conf = conf
        self.job = job

    def run(self):

        assert self.conf.module is not None

        # if user specified additional module dir, prepend it to MODULEPATH
        if self.conf.modules_dir is not None:
            logger.debug("prepending %s to MODULEPATH", self.conf.modules_dir)
            os.environ['MODULEPATH'] = self.conf.modules_dir + os.pathsep + \
                os.environ['MODULEPATH']

        cmd = [self.conf.cmd_mcmd, self.conf.cmd_shell,
               'load', self.conf.module]
        logger.debug("run cmd: %s", ' '.join(cmd))

        (pipe_out, pipe_in) = os.pipe()

        pipe_r = os.fdopen(pipe_out)
        pipe_w = os.fdopen(pipe_in, 'w')

        p1 = Popen(cmd, stdout=pipe_w)
        p1.wait()
        # Run `exec python` in bash to exec it without forking. This removes
        # bash process from the process tree and the App can easily send
        # signals to AppInEnv.
        cmd = "exec python %s %s" % (self.conf.cmd_inenv,
                                     ' '.join(sys.argv[1:]))
        logger.debug("exec in %s: %s", self.conf.cmd_shell, cmd)
        pipe_w.write(cmd + ';')
        pipe_w.close()
        p_inenv = Popen([self.conf.cmd_shell],
                        stdin=pipe_r, stdout=sys.stdout, stderr=sys.stderr)
        pipe_r.close()

        try:
            returncode = p_inenv.wait()
            logger.debug("return code: %d", returncode)
        except KeyboardInterrupt:
            logger.debug("received SIGINT, forwarding it to inenv sub-process")
            p_inenv.send_signal(signal.SIGINT)
            return 1
        return returncode


class AppInEnv(object):

    def __init__(self, conf, job):

        self.conf = conf
        self.job = job
        self.scenarios = set()
        # Send RPC to slurmctld now to fill-up all job properties if job is
        # known, ie. NEOS runs inside job environment. It must run before
        # loading the scenarios to make just job's related placeholders are
        # properly substituted. If run outside job environment, the
        # placeholders are simply ignored and left un-substituted.
        if job.known:
            self.job.rpc()
        self.load_scenarios()

    def load_scenarios(self):

        self.load_scenarios_dir(self.conf.scenario_dir)
        if self.conf.scenario_user is not None:
            self.load_scenarios_dir(self.conf.scenario_user)

    def load_scenarios_dir(self, scenario_dir):

        logger.debug("loading scenarios in dir %s", scenario_dir)
        self.load_scenarios_pkg(scenario_dir)

        scenario_files = glob.glob(os.path.join(scenario_dir, '*.py'))

        for scenario_file in scenario_files:
            self.load_scenario_file(scenario_file)

    def load_scenarios_pkg(self, scenario_dir):

        scenario_parent_dir = os.path.abspath(os.path.join(scenario_dir, '..'))
        scenario_basedir = os.path.basename(scenario_dir)
        try:
            (filemod, pathname, description) = \
                imp.find_module(scenario_basedir, [scenario_parent_dir])
            logger.debug("find_module on package: filemod: %s pathname: %s",
                         str(filemod), pathname)
        except ImportError, e:
            logger.debug("error while trying to find package: %s", str(e))
            return

        try:
            module = imp.load_module('scenarios', None,
                                     pathname, description)
            logger.debug("package %s (type %s)", str(module), type(module))
        except ImportError, e:
            logger.debug("error while trying to import package: %s", str(e))
            return

    def load_scenario_file(self, scenario_file):

        module_file = os.path.basename(os.path.splitext(scenario_file)[0])
        module_dir = os.path.dirname(scenario_file)
        logger.debug("loading file %s in %s to search for scenario",
                     module_file, module_dir)
        try:
            (filemod, pathname, description) = \
                imp.find_module(module_file, [module_dir])
            logger.debug("find_module on module: filemod: %s pathname: %s",
                         str(filemod), pathname)
        except ImportError, e:
            logger.debug("error while trying to find module: %s", str(e))
            return

        try:
            module = imp.load_module('scenario', filemod,
                                     pathname, description)
            logger.debug("module %s (type %s)", str(module), type(module))
        except ImportError, e:
            logger.debug("error while trying to import module: %s", str(e))
            filemod.close()
            return
        finally:
            filemod.close()

        # find usable scenario among module members
        for (elem_name, elem_type) in inspect.getmembers(module):
            if inspect.isclass(elem_type) and issubclass(elem_type, Scenario) \
               and elem_type is not Scenario and hasattr(elem_type, 'NAME'):

                logger.debug("loaded usable scenario: %s", elem_name)
                usable_scenario = \
                    UsableScenario(elem_type.NAME, elem_name, elem_type)
                # instantiate and register scenario only once
                if usable_scenario not in self.scenarios:
                    # the scenarios are instanciated here to load opts for
                    # print_scenarios() eventually.
                    usable_scenario.instantiate()
                    self.scenarios.add(usable_scenario)

    def find_scenario(self, name):

        scenario = filter(lambda x: x.name == name, self.scenarios)
        if not len(scenario):
            logger.error("unable to find scenario %s in loaded scenarios",
                         name)
            return None
        return scenario[0]

    def print_scenarios(self):
        """Print on stdout the list of usable scenarios with their optional
           parameters."""
        for scenario in self.scenarios:
            print "- %s (%s)" % (scenario.name, scenario.modname)
            for opt in scenario.instance.opts:
                print "    - %-15s (%s): %s" % opt

    def dump_env(self):

        logger.debug('environment:')
        for key, value in os.environ.iteritems():
            logger.debug(">> %s: %s", key, value)

    def run(self):

        # first dump conf
        self.conf.dump()

        self.dump_env()

        # if version flag, just print version and leave here
        if self.conf.print_version is True:
            print("NEOS v%s" % (self.conf.version))
            sys.exit(0)

        # if list_scenarios flag is set, print them and leave here
        if self.conf.list_scenarios is True:
            self.print_scenarios()
            sys.exit(0)

        assert self.job.known

        # dump job information
        self.job.dump()

        usable_scenario = self.find_scenario(self.conf.scenario)
        if usable_scenario is None:
            return 1
        scenario = usable_scenario.instance
        scenario.set_opts()
        result = scenario.run()
        scenario.wait()
        scenario.cleanup()
        return result
