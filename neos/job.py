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
from datetime import datetime
import time

from ClusterShell.NodeSet import NodeSet
import pyslurm
from pytz import timezone

from neos.utils import Singleton

def localtz():
    return timezone(time.tzname[0])

class SlurmJob(object):

    __metaclass__ = Singleton

    def __init__(self):

        self.jobid = int(os.environ.get('SLURM_JOB_ID'))
        self.procid = int(os.environ.get('SLURM_PROCID'))
        self.nodes = NodeSet(os.environ.get('SLURM_NODELIST'))
        self.partition = os.environ.get('SLURM_JOB_PARTITION')
        # data filled using pyslurm with RPC to slurmctld
        self.shared = None
        self.end = None

    def rpc(self):
        job = pyslurm.job().find_id(self.jobid)
        self.shared = job['shared'] != 0
        self.end = datetime.fromtimestamp(job['end_time'], localtz())

    @property
    def firstnode(self):
        return self.nodes[0]

    def dump(self):
        """Dump job at debug level."""

        logger.debug("job data:")
        for attr in [ 'jobid',
                      'procid',
                      'nodes',
                      'partition',
                      'shared',
                      'end' ]:
            logger.debug(">> %s: %s", attr, str(getattr(self, attr)))


Job = SlurmJob # alias
