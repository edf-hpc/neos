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
from xml.dom.minidom import Document

import socket
from scenarios.wm import ScenarioWM


class ScenarioVnc(ScenarioWM):

    MAGIC_NUMBER = 59530

    OPTS = ['vauthfile:str:${BASEDIR}/vncpass_${JOBID}',
            'vncpasswd:str:x11vnc',
            'vnc:str:x11vnc',
            'skipvncoutput:bool:true']

    def __init__(self):

        super(ScenarioVnc, self).__init__()

    @property
    def rfbport(self):
        return self.job.jobid % ScenarioVnc.MAGIC_NUMBER + 1024

    def dump_xml(self):
        """Dump scenario information in XML format, something like:
           <$job_partition>
             <nodes>
               <node>node1</node>
               <node>node2</node>
             </nodes>
             <config>
               <node>$firstnode</node>
               <ipaddress>$iprin</ipaddress>
               <session>$rfbport</session>
               <password>$mdp</password>
             </config>
             <enddatetime>$daylimit</enddatetime>
             <pid>$jobid</pid>
           </$job_partition>
        """
        doc = Document()
        root = doc.createElement(self.conf.cluster_partition)
        doc.appendChild(root)

        nodes = doc.createElement('nodes')
        root.appendChild(nodes)

        for nodename in self.job.nodes:
            node = doc.createElement('node')
            node.appendChild(doc.createTextNode(nodename))
            nodes.appendChild(node)

        config = doc.createElement('config')
        config_elmt = doc.createElement('node')
        config_elmt.appendChild(doc.createTextNode(self.job.firstnode))
        config.appendChild(config_elmt)

        config_elmt = doc.createElement('ipaddress')
        config_elmt.appendChild(doc.createTextNode(self.rinip))
        config.appendChild(config_elmt)

        config_elmt = doc.createElement('fqdn')
        try:
            # try to find a string representing the canonical name of the firstnode
            fqdn = socket.getaddrinfo(self.job.firstnode, 0, 0, 0, 0, socket.AI_CANONNAME)[0][3]
        except:
            fqdn = self.job.firstnode
        config_elmt.appendChild(doc.createTextNode(fqdn))
        config.appendChild(config_elmt)

        config_elmt = doc.createElement('session')
        config_elmt.appendChild(doc.createTextNode(str(self.rfbport)))
        config.appendChild(config_elmt)

        config_elmt = doc.createElement('password')
        config_elmt.appendChild(doc.createTextNode(self.password))
        config.appendChild(config_elmt)
        root.appendChild(config)

        enddatetime = doc.createElement('enddatetime')
        enddatetime.appendChild(doc.createTextNode(self.job.end.isoformat()))
        root.appendChild(enddatetime)

        pid = doc.createElement('pid')
        pid.appendChild(doc.createTextNode(str(self.job.jobid)))
        root.appendChild(pid)

        print doc.toprettyxml()
        sys.stdout.flush()  # force flush to avoid buffering

    def _run_vnc(self, wm):

        self.dump_xml()

        wm_fail = self._run_wm(wm)
        if wm_fail:
            return wm_fail

        if self.opts.skipvncoutput is True:
            stdout = stderr = '/dev/null'
        else:
            stdout = stderr = None

        # store VNC password in vauthfile
        cmd = [self.opts.vncpasswd, '-storepasswd', self.password,
               self.opts.vauthfile]
        self.cmd_wait(cmd, stderr=stderr)
        self.register_tmpfile(self.opts.vauthfile)

        # start VNC server
        cmd = [self.opts.vnc, '-desktop', self.conf.cluster_name, '-xkb',
               '-ncache', '0', '-scale', self.opts.resolution, '-once',
               '-display', ":%d" % (self.display),
               '-auth', self.opts.xauthfile, '-rfbport', str(self.rfbport),
               '-rfbwait', '30000', '-localhost',
               '-rfbauth', self.opts.vauthfile,
               '-oa', self.opts.logfile, '-noxdamage']
        self.cmd_run_bg(cmd, stdout=stdout)

        return 0
