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
import os


class LogFileSet(object):

    def __init__(self):

        self._logfiles = set()

    def __contains__(self, path):

        return LogFile(path) in self._logfiles

    def __iter__(self):

        for logfile in self._logfiles:
            yield logfile

    def add(self, path):
        """Add logfile to set."""
        logfile = LogFile(path)
        self._logfiles.add(logfile)
        return logfile

    def get(self, path):
        """Returns logfile found in set, raises KeyError if not found."""
        for logfile in self._logfiles:
            if logfile.path == path:
                return logfile
        raise KeyError("logfile %s not found" % (path))


class LogFile(object):

    def __init__(self, path):

        self.path = os.path.abspath(path)
        self.fd = None

    def __eq__(self, other):

        return self.path == other.path

    def __hash__(self):

        return hash(self.path)

    def open(self):
        """Open fd if not yet opened. Log error and returns None if error
           encountered while opening the file."""
        if self.fd is None:
            logger.debug("opening logfile %s", self.path)
            try:
                self.fd = open(self.path, 'a+')
            except IOError as err:
                logger.error("unable to open logfile %s: %s", self.path, err)
                return None
        return self.fd

    def close(self):
        """Close fd if opened."""
        if self.fd is not None:
            logger.debug("closing logfile %s", self.path)
            self.fd.close()
