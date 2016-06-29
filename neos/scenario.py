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
from subprocess import Popen, check_output, call
from time import sleep
import sys
import os
import socket

from xml.dom.minidom import Document

from neos.utils import gen_password, FakePopen
from neos.opts import ScenarioOpts
from neos.conf import Conf
from neos.job import Job

class Scenario(object):

    MAGIC_NUMBER = 59530

    OPTS = [ 'logfile:str:${BASEDIR}/Xlog_${JOBID}' ]

    def __init__(self):

        self.conf = Conf()
        self.job = Job()
        self.pids = set() # bg processes
        self.tmpfiles = set()
        self.password = gen_password()
        self.srcip = os.environ['SSH_CONNECTION'].split(' ')[0]
        self.rinip = socket.gethostbyname(self.conf.wan_prefix + socket.gethostname())

        self.opts = ScenarioOpts()
        self.declare_opts()
        self.set_opts()

        if self.conf.log:
            self.ensure_dir(self.opts.logfile)
            logger.debug("opening logfile %s", self.opts.logfile)
            self.logfile = open(self.opts.logfile, 'w+')
        else:
            self.logfile = None

    def declare_opts(self):

        logger.debug("scenario %s: declaring opts", self.NAME)
        self.declare_opts_cls(type(self))

    def declare_opts_cls(self, cls):

        if cls == object: return

        if hasattr(cls, 'OPTS'):
            for opt_s in cls.OPTS:
                logger.debug("class %s: opt %s", cls.__name__, opt_s)
                self.opts.add(opt_s)

        for xcls in cls.__bases__:
            self.declare_opts_cls(xcls)


    def set_opts(self):

        if self.conf.opts is not None:
            for opt_s in self.conf.opts:
                self.opts.set(opt_s)

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
        sys.stdout.flush() # force flush to avoid buffering

    @property
    def display(self):
        if not self.job.shared:
            return 0
        return self.job.jobid % Scenario.MAGIC_NUMBER + 1

    @property
    def rfbport(self):
        return self.job.jobid % Scenario.MAGIC_NUMBER + 1024;

    def ensure_dir(self, filename):
        """Ensure the parent directory of the filename in parameter exists so
           that the file can be created witout problem then."""
        dirname = os.path.dirname(os.path.abspath(os.path.expanduser(filename)))
        if not os.path.isdir(dirname):
            logger.debug("creating directory %s", dirname)
            os.makedirs(dirname)

    def create_file(self, filename):
        """Create empty file if not existing"""
        # first ensure directory exists
        self.ensure_dir(filename)
        absfile = os.path.abspath(os.path.expanduser(filename))
        if not os.path.exists(absfile):
            logger.debug("creating empty file %s", absfile)
            fh = open(absfile, 'w+')
            fh.close()

    def sleep(self, time):
        """Sleep if not in dry-run mode."""
        if self.conf.dryrun:
            sleep(time)

    def register_tmpfile(self, filename):

        if filename not in self.tmpfiles:
            logger.debug("register tmp file %s", filename)
            self.tmpfiles.add(filename)

    def cmd_run_bg(self, cmd, shell=False):

        if self.conf.dryrun:
            logger.info("run cmd: %s", ' '.join(cmd))
            return FakePopen()
        else:
            logger.debug("run cmd: %s", ' '.join(cmd))
            if self.conf.log:
                process = Popen(cmd, shell=shell, stdout=self.logfile, stderr=self.logfile)
            else:
                process = Popen(cmd, shell=shell, stdout=sys.stdout, stderr=sys.stderr)
            self.pids.add(process)

    def cmd_wait(self, cmd, shell=False):

        if self.conf.dryrun:
            logger.info("run cmd: %s", ' '.join(cmd))
            return 0
        else:
            logger.debug("run cmd: %s", ' '.join(cmd))
            if self.conf.log:
                return call(cmd, shell=shell, stdout=self.logfile, stderr=self.logfile)
            else:
                return call(cmd, shell=shell, stdout=sys.stdout, stderr=sys.stderr)

    def cmd_output(self, cmd, shell=False):

        if self.conf.dryrun:
            logger.info("run cmd: %s", ' '.join(cmd))
            return 'drynrunoutput'
        else:
            logger.debug("run cmd: %s", ' '.join(cmd))
            return check_output(cmd, shell=shell)

    def kill(self, exception):
        for process in self.pids:
            if process is not exception:
                logger.debug("killing process %s", process.pid)
                process.kill()
                process.wait()

    def wait(self):
        # do not wait in dry-run mode
        if self.conf.dryrun:
            return
        # do not wait if nothing to wait for
        if len(self.pids) == 0:
            return
        logger.debug("now waiting for processes to end")
        try:
            while True:
                for process in self.pids:
                    returncode = process.poll()
                    if returncode is not None:
                        logger.info("process pid %d ends with return code: %d", process.pid, returncode)
                        logger.info("now killing other processes")
                        self.kill(process)
                        return
                    else:
                        sleep(0.5)
        except KeyboardInterrupt, e:
            logger.info("SIGINT received, killing all processes")
            self.kill(None)

    def cleanup(self):
        logger.debug("cleaning up before exiting")
        if self.logfile is not None:
            logger.debug("closing logfile descriptor")
            self.logfile.close()
        if not self.conf.keep:
            for filename in self.tmpfiles:
                if os.path.exists(filename):
                    logger.debug("removing tmp file %s", filename)
                    os.remove(filename)

class UsableScenario(object):

    def __init__(self, name, modname, init):

        self.name = name
        self.modname = modname
        self.init = init
        # Not instantiated here to avoid multiple instantiations of the same
        # scenario during scenarios discovery. Discovery logic calls
        # instantiate() after making sure the scenario is new.
        self.instance = None

    def instantiate(self):

        self.instance = self.init()

    def __eq__(self, other):

        return self.name == other.name and self.modname == other.modname

    def __hash__(self):

        return hash(self.name + self.modname)
