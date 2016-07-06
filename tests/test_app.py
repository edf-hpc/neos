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

import sys
import os
import mock

sys.modules['pyslurm'] = mock.Mock()
sys.modules['pytz'] = mock.Mock()

from tests.utils import NeosTestCase

from tests.mocks import MockConfigParser, MockPySlurm

from neos.job import Job
from neos.conf import Conf, ConfLoader
from neos.app import AppInEnv


def set_job_env(jobid, procid, nodes, partition):
    os.environ['SLURM_JOB_ID'] = str(jobid)
    os.environ['SLURM_PROCID'] = str(procid)
    os.environ['SLURM_NODELIST'] = nodes
    os.environ['SLURM_JOB_PARTITION'] = partition


class TestsAppInEnv(NeosTestCase):

    @mock.patch("neos.job.pyslurm")
    @mock.patch("neos.job.timezone")
    @mock.patch("neos.conf.ConfigParser.RawConfigParser")
    def setUp(self, m_parser, m_timezone, m_pyslurm):

        self.parser = MockConfigParser()
        # Return our instance of MockConfigParser when RawConfigParser is
        # instanciated in neos.conf.ConfLoader
        m_parser.return_value = self.parser
        # pytz.timezone() is used to return a tzinfo given in args to
        # datetime.fromtimestamp(). This method accepts None value, so use this
        # instead of writing a fake tzinfo object.
        m_timezone.return_value = None

        # configuration content for MockConfigParser
        self.parser.conf = {
            'cluster': {
                'name': 'computer',
                'partition': 'cg',
                'wanprefix': '',
            },
            'scenarios': {
                'dir': './neos/scenarios',
                'default': 'xfce4',
            },
            'internals': {
                'basedir': '~/.neos',
                'inenv': '/usr/lib/neos/exec/neos_inenv',
                'mcmd': '/usr/bin/modulecmd',
                'shell': 'bash',
            },
        }
        self.conf = Conf()
        self.loader = ConfLoader('fakepath')
        self.loader.update_conf(self.conf)

        # set environment variables to simulate Slurm job step environment
        set_job_env(1, 0, 'nodes[1-2]', 'cg')
        self.job = Job()
        # neos.scenario.Scenario.__init__() needs to parse SSH_CONNECTION
        # environment variable, then set it here.
        os.environ['SSH_CONNECTION'] = '127.0.0.1 foo'

        self.app = AppInEnv(self.conf, self.job)

    def test_init(self):
        """AppInEnv.__init__() runs w/o problem
        """
        pass

    @mock.patch("neos.scenario.call")
    @mock.patch("neos.scenario.check_output")
    @mock.patch("neos.scenario.Popen")
    def test_run(self, m_popen, m_checkoutput, m_call):
        """AppInEnv.run() runs w/o problem
        """
        # subprocess.check_output() in neos.scenario must return a string
        # as expected by the scenarios
        m_checkoutput.return_value = "mockoutput"
        # This test is pretty similar to neos command without additional args.
        # It is actually more a blackbox than a pure unit test, in the sense it
        # runs the full app in sandboxed environment, without all external
        # deps (pyslurm, pytz, clustershell and so on). Its purpose is just to
        # make sure quite a large portion of the code runs without major issue,
        # since it covers ~67% of neos code base by itself (measured when it
        # was initially introduced).
        self.assertEquals(0, self.app.run())
