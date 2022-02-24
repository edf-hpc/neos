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

import logging
logger = logging.getLogger(__name__)
from subprocess import Popen, check_output, call
from time import sleep
import sys
import os
import socket

from neos.utils import gen_password, FakePopen
from neos.opts import ScenarioOpts
from neos.conf import Conf
from neos.job import Job
from neos.log import LogFileSet


class Scenario(object):

    OPTS = ['logfile:str:${BASEDIR}/Xlog_${JOBID}']

    def __init__(self):

        self.conf = Conf()
        self.job = Job()
        self.pids = set()  # bg processes
        self.tmpfiles = set()
        self.user_logfiles = LogFileSet()
        self.password = gen_password()
        if 'SSH_CONNECTION' in os.environ:
            self.srcip = os.environ['SSH_CONNECTION'].split(' ')[0]
        else:
            logger.warning("unable to extract source IP from SSH_CONNECTION, "
                           "fallback to 127.0.0.1")
            self.srcip = '127.0.0.1'
        try:
            self.rinip = socket.gethostbyname(self.conf.wan_prefix +
                                              socket.gethostname())
        except socket.gaierror:
            logger.error("failed to get wan hostname, fallback to localhost")
            self.rinip = '127.0.0.1'
        self.opts = ScenarioOpts()
        self.declare_opts()

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

        if cls == object:
            return

        if hasattr(cls, 'OPTS'):
            for opt_s in cls.OPTS:
                logger.debug("class %s: opt %s", cls.__name__, opt_s)
                self.opts.add(opt_s)

        for xcls in cls.__bases__:
            self.declare_opts_cls(xcls)

    def set_opts(self):
        """Set scenario opts with values given by user in parameters."""
        if self.conf.opts is not None:
            for opt_s in self.conf.opts:
                self.opts.set(opt_s)

    def ensure_dir(self, filename):
        """Ensure the parent directory of the filename in parameter exists so
           that the file can be created witout problem then."""
        dirname = os.path.dirname(
            os.path.abspath(os.path.expanduser(filename)))
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
        if not self.conf.dryrun:
            sleep(time)

    def register_tmpfile(self, filename):

        if filename not in self.tmpfiles:
            logger.debug("register tmp file %s", filename)
            self.tmpfiles.add(filename)


    def _check_open_logfile(self, path):
        """Check path type (must be string), search for path in logfiles set,
           and try opening fd. Returns the fd if everything goes well, None on
           error."""

        if type(path) is not str:
            logger.warning("logfile path type is invalid, cannot "
                           "use it")
            return None

        # search for path into user_logfiles
        if path in self.user_logfiles:
            logfile = self.user_logfiles.get(path)
        else:
            logfile = self.user_logfiles.add(path)

        fd = logfile.open()  # returns None on error
        return fd

    def _output_streams(self, stdout, stderr):
        """Returns the files handlers for the stdout and stderr of the command
           based on user input and --log argument. By default, the neos
           stdout/stderr are selected, or --log file if set. Then, if the user
           has given either a stdout and a stderr for the command, check and
           open them before using them."""

        # use neos stdout/stderr by default or --log file if set
        if self.conf.log:
            p_stdout = self.logfile
            p_stderr = self.logfile
        else:
            p_stdout = sys.stdout
            p_stderr = sys.stderr

        # if the user either give a stdout or a stderr
        if stdout is not None or stderr is not None:

            if stdout is not None:

                fd = self._check_open_logfile(stdout)
                if fd is not None:
                    p_stdout = fd

            if stderr is not None:

                fd = self._check_open_logfile(stderr)
                if fd is not None:
                    p_stderr = fd

        return (p_stdout, p_stderr)

    def cmd_run_bg(self, cmd, shell=False, stdout=None, stderr=None):

        if self.conf.dryrun:
            logger.info("run cmd: %s", ' '.join(cmd))
            return FakePopen()
        else:
            logger.debug("run cmd: %s", ' '.join(cmd))
            (p_stdout, p_stderr) = self._output_streams(stdout, stderr)
            process = Popen(cmd, shell=shell, stdout=p_stdout, stderr=p_stderr)
            self.pids.add(process)
            logger.debug("Process added to monitoring: %s", process.pid)

    def cmd_wait(self, cmd, shell=False, stdout=None, stderr=None):

        if self.conf.dryrun:
            logger.info("run and wait cmd : %s", cmd)
            return 0
        else:
            logger.debug("run and wait cmd: %s", cmd)
            (p_stdout, p_stderr) = self._output_streams(stdout, stderr)
            return call(cmd, shell=shell, stdout=p_stdout, stderr=p_stderr)

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
                        logger.info("process pid %d ends with return code: %d",
                                    process.pid, returncode)
                        logger.info("now killing other processes")
                        self.kill(process)
                        return
                    else:
                        sleep(0.5)
        except KeyboardInterrupt:
            logger.info("SIGINT received, killing all processes")
            self.kill(None)

    def cleanup(self):
        logger.debug("cleaning up before exiting")
        if self.logfile is not None:
            logger.debug("closing logfile descriptor")
            self.logfile.close()
        for user_logfile in self.user_logfiles:
            user_logfile.close()
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
