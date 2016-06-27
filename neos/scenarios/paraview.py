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

import os
from neos import Scenario

class ScenarioParaview(Scenario):

    NAME = 'paraview'
    OPTS = [ 'xauthfile:str:${BASEDIR}/Xauthority_${JOBID}',
             'xlogfile:str:${BASEDIR}/Xlog_${JOBID}',
             'wm:str:xfce4-session',
             'paraviewpath:str:/opt/paraview/3.14',
             'resolution:str:4096x4096' ]

    def __init__(self):

        super(ScenarioParaview, self).__init__()

    def run(self):

        cookie = self.cmd_output([ 'mcookie' ])

        # create empty xauthfile
        self.create_file(self.opts.xauthfile)

        cmd = [ 'xauth', '-f', self.opts.xauthfile, '-q', 'add',
                ":%d" % (self.display), 'MIT-MAGIC-COOKIE-1', cookie ]
        self.cmd_wait(cmd)

        # redirect stdint/stdout to xlogfile
        # launch in background

        self.ensure_dir(self.opts.xlogfile)
        logfile = open(self.opts.xlogfile, 'w+')

        if self.display == 0:
            cmd = [ 'xrandr', '-d', ':0', '--fb', self.opts.resolution ]
        else:
            cmd = [ 'Xvfb', ":%d" % (self.display), '-once', '-screen', '0',
                    "%sx24+32" % (self.opts.resolution),
                    '-auth', self.opts.xauthfile ]
        self.cmd_run_bg(cmd, logfile=logfile)

        # start window manager to workaround a Paraview bug.
        # See https://github.com/edf-hpc/neos/issues/4 for full details.
        os.environ['DISPLAY'] = ":%s" % (self.display)
        os.environ['XAUTHORITY'] = self.opts.xauthfile;
        cmd = [ self.opts.wm ]
        self.cmd_run_bg(cmd, logfile=logfile)

        if not self.job.shared:
            vglrun = ['vglrun', '-display', ':0' ]
        else:
            vglrun = []

        # Run pvserver command
        cmd = [ 'mpirun', '-x', "DISPLAY=:%s" % (self.display), vglrun,
                "%s/bin/pvserver" % (self.opts.paraviewpath),
                "--connect-id=%s" % (self.display),
                '-rc', "-ch=%s" % (self.srcip) ]
        self.cmd_run_bg(cmd, logfile=logfile)

        logfile.close()

        return 0
