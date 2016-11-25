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

from scenarios.wm import ScenarioWM


class ScenarioParaview(ScenarioWM):

    NAME = 'paraview'
    OPTS = ['wm:str:xfce4-session',
            'resolution:str:4096x4096',
            'paraviewpath:str:/opt/paraview/3.14']

    def __init__(self):

        super(ScenarioParaview, self).__init__()

    def run(self):

        wm_fail = self._run_wm(self.opts.wm)
        if wm_fail:
            return wm_fail

        # print the first node WAN IP address
        print("ip: %s" % (self.rinip))
        sys.stdout.flush()  # force flush to avoid buffering

        if self.job.shared:
            vglrun = ['vglrun', '-display', ':0']
        else:
            vglrun = None

        # Run pvserver command
        cmd = ['mpirun', '-x', "DISPLAY=:%s" % (self.display),
               "%s/bin/pvserver" % (self.opts.paraviewpath),
               "--connect-id=%s" % (self.display),
               '-rc', "-ch=%s" % (self.srcip)]
        # insert vglrun command if enable
        if vglrun is not None:
            cmd[3:3] = vglrun
        self.cmd_run_bg(cmd)

        return 0
