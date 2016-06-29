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

import argparse
import os


class AppArgs(object):

    def __init__(self, conf):

        self.parser = argparse.ArgumentParser()
        self.add_args(conf)

    def add_args(self, conf):

        self.parser.add_argument('-d', '--debug',
                                 help='Enable debug mode.',
                                 action='store_true')
        self.parser.add_argument('--version',
                                 help='Print NEOS version and leave.',
                                 action='store_true')
        self.parser.add_argument('--dry-run',
                                 help='Enable dry run mode which just print '
                                 'commands without actually running them.',
                                 action='store_true')
        self.parser.add_argument('-S', '--scenarios-dir',
                                 help='Path to directory with additional '
                                 'scenarios to load',
                                 nargs=1,
                                 required=False)
        self.parser.add_argument('-s', '--scenario',
                                 help="Name of scenario to run. Default is: "
                                 "%s" % (conf.scenario),
                                 nargs=1)
        self.parser.add_argument('-M', '--modules-dir',
                                 help='Path to directory with additional '
                                 'modules to load',
                                 nargs=1,
                                 required=False)
        self.parser.add_argument('-m', '--module',
                                 help='Name of environment module to load',
                                 nargs=1,
                                 required=False)
        self.parser.add_argument('-o', '--opts',
                                 help='Optional scenarios parameters. '
                                 'Ex: gdb:true,colors:24',
                                 nargs=1,
                                 required=False)
        self.parser.add_argument('-l', '--log',
                                 help='Log commands output instead of '
                                 'printing on stdout/stderr.',
                                 action='store_true')
        self.parser.add_argument('-k', '--keep',
                                 help='Do not delete temporary files generated'
                                 'by NEOS.',
                                 action='store_true')
        self.parser.add_argument('-L', '--list',
                                 dest='list_scenarios',
                                 help='List available scenarios and '
                                 'parameters.',
                                 action='store_true')

    def update_conf(self, conf):

        args = self.parser.parse_args()

        if args.version:
            conf.print_version = True
        if args.debug:
            conf.debug = True
        if args.dry_run:
            conf.dryrun = True
        if args.list_scenarios:
            conf.list_scenarios = True
        if args.log:
            conf.log = True
        if args.keep:
            conf.keep = True
        if args.scenarios_dir is not None:
            if os.path.isabs(args.scenarios_dir[0]):
                path = args.scenarios_dir[0]
            else:
                path = os.path.abspath(args.scenarios_dir[0])
            if not os.path.exists(path):
                raise Exception("additional scenarios directory %s does not "
                                "exist" % (path))
            if not os.path.isdir(path):
                raise Exception("additional scenarios directory %s is not a "
                                "valid directory" % (path))
            conf.scenario_user = path
        if args.scenario is not None:
            conf.scenario = args.scenario[0]
        if args.modules_dir is not None:
            if os.path.isabs(args.modules_dir[0]):
                path = args.modules_dir[0]
            else:
                path = os.path.abspath(args.modules_dir[0])
            if not os.path.exists(path):
                raise Exception("additional modules directory %s does not "
                                "exist" % (path))
            if not os.path.isdir(path):
                raise Exception("additional modules directory %s is not a "
                                "valid directory" % (path))
            conf.modules_dir = path
        if args.module is not None:
            conf.module = args.module[0]
        if args.opts is not None:
            if conf.opts is None:
                conf.opts = []
            for opt in args.opts[0].split(','):
                conf.opts.append(opt)
