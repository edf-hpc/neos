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
from string import Template

from neos.job import Job
from neos.conf import Conf


class ScenarioOpts(object):

    def __init__(self):

        self._opts = {}

    def __getattr__(self, key):
        try:
            return self._opts[key].value
        except KeyError:
            raise KeyError("opt %s does not exist" % (key))

    def add(self, opt_s):

        opt = ScenarioOptParam(*ScenarioOpts.parse_scen_opt(opt_s))
        if opt.name not in self._opts.keys():
            self._opts[opt.name] = opt

    def set(self, opt_s):
        (opt, value) = self.parse_user_opt(opt_s)
        if opt is not None and value is not None:
            logger.debug("setting opt %s with value %s", opt, str(value))
            self._opts[opt].value = value

    def __iter__(self):

        for name, opt in self._opts.iteritems():
            yield (opt.name, opt.p_type.__name__, str(opt.value))

    @staticmethod
    def _subst_placeholders(value):
        tpl = Template(value)
        job = Job()
        conf = Conf()
        # if outside of job context, do not try to substitute placeholders
        # since some variables are unknown.
        if job.unknown:
            return value
        placeholders = {'BASEDIR': conf.base_dir,
                        'JOBID': job.jobid}
        return tpl.substitute(placeholders)

    @staticmethod
    def _parse_value(xtype, value_s):
        if xtype is str:
            return ScenarioOpts._subst_placeholders(value_s)
        elif xtype is bool:
                return ScenarioOpts._parse_bool(value_s)
        else:
            return int(value_s)

    @staticmethod
    def _parse_bool(bool_s):
        if bool_s in ['true', 'True', 'yes', 'y', '1']:
            return True
        elif bool_s in ['false', 'False', 'no', 'n', '0']:
            return False
        else:
            raise TypeError("unable to parse boolean value %s" % (bool_s))

    @staticmethod
    def parse_scen_opt(opt_s):

        opt_elems = opt_s.split(':')
        if len(opt_elems) != 3:
            logger.error("unable to parse opt %s", opt_s)
            return (None, None, None)

        (opt_name, opt_type_s, opt_defval_s) = opt_elems

        if opt_type_s == 'str':
            opt_type = str
        elif opt_type_s == 'boolean':
            opt_type = bool
        elif opt_type_s == 'int':
            opt_type = int
        else:
            logger.error("unknown opt type %s", opt_type_s)
            return (None, None, None)

        try:
            opt_defval = ScenarioOpts._parse_value(opt_type, opt_defval_s)
        except TypeError, e:
            logger.error("error while parsing value: %s", e)
            return (None, None, None)

        return (opt_name, opt_type, opt_defval)

    def parse_user_opt(self, opt_s):

        opt_elems = opt_s.split(':')
        if len(opt_elems) != 2:
            logger.error("unable to parse opt %s", opt_s)
            return (None, None)

        (opt_name, opt_val_s) = opt_elems

        try:
            opt_type = self._opts[opt_name].p_type
        except KeyError, e:
            logger.error("unknown opt %s: %s", opt_name, e)
            return (None, None)

        try:
            opt_val = ScenarioOpts._parse_value(opt_type, opt_val_s)
        except TypeError, e:
            logger.error("error while parsing value: %s", e)
            return (None, None)

        return (opt_name, opt_val)


class ScenarioOptParam(object):

    def __init__(self, name, p_type, value):

        self.name = name
        self.p_type = p_type
        self.value = value
