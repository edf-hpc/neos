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

from neos.scenario import UsableScenario, Scenario
from neos.conf import Conf, ConfLoader
from neos.args import AppArgs
from neos.job import Job

class Launcher(object):
    """Launcher class is responsible of initializing runtime configuration
       based on configuration file and arguments, logger and then launching
       the application given in parameter."""

    def __init__(self, app, conf_path='/etc/neos/neos.conf'):

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

    def run(self):
        """Initialize and run the application only if expected partition and
           job task 0. This way, NEOS behaves the same when launched with
           either srun and sbatch."""

        if self.job.partition != self.conf.cluster_partition:
            logger.error("cannot run on partition %s", self.job.partition)
            return 1
        if self.job.procid:
            logger.debug("instantly leaving on procid %d", self.job.procid)
            return 0
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

        # first dump conf
        self.conf.dump()

        # if version flag, just print version and leave here
        if self.conf.print_version is True:
            print("NEOS v%s" % (self.conf.version))
            sys.exit(0)

        if self.conf.module is not None:

            cmd = [self.conf.cmd_mcmd, self.conf.cmd_shell, 'load', self.conf.module ]
            logger.debug("run cmd: %s", ' '.join(cmd))

            (pipe_out, pipe_in) = os.pipe()

            pipe_r = os.fdopen(pipe_out)
            pipe_w = os.fdopen(pipe_in, 'w')

            p1 = Popen(cmd, stdout=pipe_w)
            p1.wait()
            cmd = "python %s %s" % (self.conf.cmd_inenv, ' '.join(sys.argv[1:]))
            logger.debug("exec in %s: %s", self.conf.cmd_shell, cmd)
            pipe_w.write(cmd + ';')
            pipe_w.close()
            p_inenv = Popen([self.conf.cmd_shell], stdin=pipe_r, stdout=sys.stdout, stderr=sys.stderr)
            pipe_r.close()

        else:
            cmd = [ 'python', self.conf.cmd_inenv ]
            cmd.extend(sys.argv[1:])
            logger.debug("run cmd: %s", str(cmd))
            p_inenv = Popen(cmd, stdout=sys.stdout, stderr=sys.stderr)

        returncode = p_inenv.wait()
        logger.debug("return code: %d", returncode)
        return returncode

class AppInEnv(object):

    def __init__(self, conf, job):

        self.conf = conf
        self.job = job
        self.scenarios = set()
        self.load_scenarios()
        # send RPC to slurmctld now to fill-up all job properties
        self.job.rpc()

    def load_scenarios(self):

        self.load_scenarios_dir(self.conf.scenario_dir)
        if self.conf.scenario_user is not None:
            self.load_scenarios_dir(self.conf.scenario_user)

    def load_scenarios_dir(self, scenario_dir):

        logger.debug("loading scenarios in dir %s", scenario_dir)

        scenario_files = glob.glob(os.path.join(scenario_dir, '*.py'))

        for scenario_file in scenario_files:
            self.load_scenario_file(scenario_file)

    def load_scenario_file(self, scenario_file):

        module_file = os.path.basename(os.path.splitext(scenario_file)[0])
        module_dir = os.path.dirname(scenario_file)
        logger.debug("loading file %s in %s to search for scenario",
                     module_file, module_dir)
        try:
            (filemod, pathname, description) = \
                imp.find_module(module_file, [ module_dir ])
            logger.debug("find_module: filemod: %s pathname: %s",
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
                and elem_type is not Scenario:
                logger.debug("loaded usable scenario: %s", elem_name)
                usable_scenario = \
                    UsableScenario(elem_type.NAME, elem_name, elem_type)
                # register scenario only once
                if usable_scenario not in self.scenarios:
                    self.scenarios.add(usable_scenario)

    def find_scenario(self, name):

        scenario = filter(lambda x: x.name == name, self.scenarios)
        if not len(scenario):
            logger.error("unable to find scenario %s in loaded scenarios",
                         name)
            return None
        return scenario[0]

    def run(self):

        usable_scenario = self.find_scenario(self.conf.scenario)
        if usable_scenario is None:
            return 1
        scenario = usable_scenario.init()
        result = scenario.run()
        scenario.wait()
        return result
