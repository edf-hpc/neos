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

from neos.scenarios.wm import ScenarioWM


class ScenarioVnc(ScenarioWM):

    OPTS = ['vauthfile:str:${BASEDIR}/vncpass_${JOBID}',
            'vncpasswd:str:x11vnc',
            'vnc:str:x11vnc']

    def __init__(self):

        super(ScenarioVnc, self).__init__()

    def _run_vnc(self, wm):

        self.dump_xml()

        wm_fail = self._run_wm(wm)
        if wm_fail:
            return wm_fail

        # store VNC password in vauthfile
        cmd = [self.opts.vncpasswd, '-storepasswd', self.password,
               self.opts.vauthfile]
        self.cmd_wait(cmd)
        self.register_tmpfile(self.opts.vauthfile)

        # start VNC server
        cmd = [self.opts.vnc, '-desktop', self.conf.cluster_name, '-xkb',
               '-ncache', '0', '-scale', self.opts.resolution, '-once',
               '-display', ":%d" % (self.display),
               '-auth', self.opts.xauthfile, '-rfbport', str(self.rfbport),
               '-rfbwait', '30000', '-localhost',
               '-rfbauth', self.opts.vauthfile,
               '-oa', self.opts.logfile, '-noxdamage']
        self.cmd_run_bg(cmd)

        return 0
