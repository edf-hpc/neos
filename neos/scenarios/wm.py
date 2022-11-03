#!/usr/bin/env python3
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

import os
from neos import Scenario


class ScenarioWM(Scenario):

    MAGIC_NUMBER = 59530

    OPTS = ['xauthfile:str:${BASEDIR}/Xauthority_${JOBID}',
            'resolution:str:1024x768',
            'skipwmerr:bool:true']

    def __init__(self):

        super(ScenarioWM, self).__init__()

    @property
    def display(self):
        if not self.job.shared:
            return 0
        if self.job.gres:
            return int(self.job.gpu)
        return self.job.jobid % ScenarioWM.MAGIC_NUMBER + 1

    def _run_wm(self, wm):

        cookie = self.cmd_output(['mcookie'])

        # create empty xauthfile
        self.create_file(self.opts.xauthfile)
        self.register_tmpfile(self.opts.xauthfile)

        cmd = ['xauth', '-f', self.opts.xauthfile, '-q', 'add',
               ":%d" % (self.display), 'MIT-MAGIC-COOKIE-1', cookie]
        self.cmd_wait(cmd)

        if self.opts.skipwmerr is True:
            stderr = '/dev/null'
        else:
            stderr = None

        if (self.display == 0 or self.display == 1):
            cmd = ['xrandr', '-d', ":%d" % (self.display), '--fb', self.opts.resolution]
            self.cmd_wait(cmd)
        else:
            cmd = ['Xvfb', ":%d" % (self.display), '-once', '-screen', '0',
                   "%sx24+32" % (self.opts.resolution),
                   '-auth', self.opts.xauthfile]
            self.cmd_run_bg(cmd, stderr=stderr)

        # start window manager
        os.environ['DISPLAY'] = ":%s" % (self.display)
        os.environ['XAUTHORITY'] = self.opts.xauthfile

        i = 0
        while self.cmd_wait(['xset', '-q']):
            i += 1
            if i >= 30:
                print('Error: X11 server not ready')
                return 1
            self.sleep(1)

        # The --exit-with-x11 parameter was added to dbus 1.11.4, make sure it's
        # supported
        dbus_version = self.cmd_output(['dbus-launch', '--help']).decode()
        if '--exit-with-x11' in dbus_version:
            dbus_exit = '--exit-with-x11'
        else:
            dbus_exit = '--exit-with-session'

        # Launch the window manager once on every nodes of the job, as this is
        # a requirement for distributed rendering solutions such as paraview.
        #
        # Additional parameter --overlap is required with Slurm >= 20.11 to run
        # the step within the same resources as the parent step launching neos.
        # Otherwise, this nested srun will wait endlessly the parent srun to
        # finish and release the ressources.
        cmd = ['srun', '--tasks-per-node=1', '--overlap',
               'dbus-launch', dbus_exit, wm]
        self.cmd_run_bg(cmd, stderr=stderr)

        self.sleep(1)

        return 0
