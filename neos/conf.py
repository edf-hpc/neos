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
import ConfigParser
from StringIO import StringIO
import os

from neos.version import __version__
from neos.utils import Singleton

class AppConf(object):

    __metaclass__ = Singleton

    def __init__(self):

        # app global param
        self.version = __version__
        self.cluster_name = None
        self.cluster_partition = None
        self.wan_prefix = None
        self.scenario_dir = None

        # internal settings
        self.base_dir = None
        self.cmd_inenv = None
        self.cmd_mcmd = None
        self.cmd_shell = None

        # user args
        self.print_version = False
        self.list_scenarios = False
        self.debug = False
        self.dryrun = False

        self.scenario_user = None
        self.scenario = None
        self.modules_dir = None
        self.module = None
        self.opts = None

    def dump(self):
        """Dump config at debug level."""

        logger.debug("app conf:")
        for attr in [ 'version',
                      'cluster_name',
                      'cluster_partition',
                      'wan_prefix',
                      'scenario_dir',
                      'base_dir',
                      'cmd_inenv',
                      'cmd_mcmd',
                      'cmd_shell',
                      'print_version',
                      'list_scenarios',
                      'debug',
                      'dryrun',
                      'scenario_user',
                      'scenario',
                      'modules_dir',
                      'module',
                      'opts' ]:
            logger.debug(">> %s: %s", attr, getattr(self, attr))

Conf = AppConf # alias

class ConfLoader(object):

    def __init__(self, path):

        defaults = StringIO(
            "[cluster]\n"
            "name = computer\n"
            "partition = cg\n"
            "wanprefix = rin\n"
            "[scenarios]\n"
            "dir = /var/lib/neos/scenarios\n"
            "default = xfce4\n"
            "[internals]\n"
            "basedir = ~/.neos\n"
            "inenv = /usr/lib/neos/exec/neos_inenv\n"
            "mcmd = /usr/bin/modulecmd\n"
            "shell = bash\n")

        self.cf = ConfigParser.RawConfigParser()
        self.cf.readfp(defaults)
        self.cf.read(path)

    def update_conf(self, conf):

        conf.cluster_name = self.cf.get('cluster', 'name')
        conf.cluster_partition = self.cf.get('cluster', 'partition')
        conf.wan_prefix = self.cf.get('cluster', 'wanprefix')
        conf.scenario_dir = self.cf.get('scenarios', 'dir')
        conf.scenario = self.cf.get('scenarios', 'default')
        conf.base_dir = os.path.expanduser(self.cf.get('internals', 'basedir'))
        conf.cmd_inenv = self.cf.get('internals', 'inenv')
        conf.cmd_mcmd = self.cf.get('internals', 'mcmd')
        conf.cmd_shell = self.cf.get('internals', 'shell')
