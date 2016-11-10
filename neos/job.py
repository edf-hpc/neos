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

        self.jobid = None
        self.procid = None
        self.nodes = None
        self.partition = None

        # Test if NEOS is run inside a job context by checking an environment
        # variable. If run outside, the attributes of the object are None and
        # self.known() returns False.
        # Do not test SLURM_JOB_ID since it is defined on frontend node within
        # salloc shell (whereas SLURM_PROCID is not) and it should be
        # considered out of job environment in this case.
        if 'SLURM_PROCID' in os.environ:
            self.jobid = int(os.environ.get('SLURM_JOB_ID'))
            self.procid = int(os.environ.get('SLURM_PROCID'))
            self.nodes = NodeSet(os.environ.get('SLURM_NODELIST'))
            self.partition = os.environ.get('SLURM_JOB_PARTITION')
            self.gpu = int(os.environ.get('CUDA_VISIBLE_DEVICES'))
        else:
            logger.debug("running out of slurm job environment, "
                         "skipping job attributes filling")
        # data filled using pyslurm with RPC to slurmctld
        self.shared = None
        self.end = None

    @property
    def known(self):

        return self.jobid is not None

    @property
    def unknown(self):

        return not self.known

    def rpc(self):
        job_list = pyslurm.job().find_id(str(self.jobid))
        job = job_list[0]
        self.gres = job['gres']
        self.shared = job['shared'] != '0'
        self.end = datetime.fromtimestamp(job['end_time'], localtz())

    @property
    def firstnode(self):
        return self.nodes[0]

    @property
    def exclusive(self):
        return not self.shared

    def dump(self):
        """Dump job at debug level."""

        logger.debug("job data:")
        for attr in ['jobid',
                     'procid',
                     'nodes',
                     'partition',
                     'gpu',
                     'shared',
                     'end']:
            logger.debug(">> %s: %s", attr, str(getattr(self, attr)))


Job = SlurmJob  # alias
