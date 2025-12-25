#!/usr/bin/env python
#   This file is part of nexdatas - Tango Server for NeXus data writer
#
#    Copyright (C) 2012-2018 DESY, Jan Kotanski <jkotan@mail.desy.de>
#
#    nexdatas is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    nexdatas is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with nexdatas.  If not, see <http://www.gnu.org/licenses/>.
#

"""  pyeval helper functions for timestamp """

import threading
import time
from dateutil import parser


timestamplock = threading.Lock()


def set_start_timestamp(commonblock, isotime=None, name=None):
    """ returns start timestamp from start isotime
        and store it in commonblock

    :param commonblock: common block
    :type commonblock: :obj:`dict`
    :param isotime: start iso time string
    :type isotime: :obj:`str`
    :param name: commonblock start timestamp key
    :type name: :obj:`str`
    :returns: start timestamp
    :rtype: :obj:`float`
    """
    name = name or "start_timestamp"
    try:
        result = parser.parse(isotime).timestamp()
    except Exception:
        result = time.time()
    with timestamplock:
        commonblock[name] = result
    return result


def start_timestamp(commonblock, name=None):
    """ return timestamp and store it in commonblock if does not exist

    :param commonblock: common block
    :type commonblock: :obj:`dict`
    :param name: commonblock start timestamp key
    :type name: :obj:`str`
    :returns: start timestamp
    :rtype: :obj:`float`
    """
    name = name or "start_timestamp"
    with timestamplock:
        if name in commonblock:
            result = commonblock[name]
        else:
            result = time.time()
            commonblock[name] = result
    return result


def relative_timestamp(commonblock, ctime=None, name=None):
    """ return timestamp and store it in commonblock if does not exist

    :param commonblock: common block
    :type commonblock: :obj:`dict`
    :param ctime: current timestamp in s
    :type ctime: :obj:`float`
    :param name: commonblock start timestamp key
    :type name: :obj:`str`
    :returns: relative timestamp in s
    :rtype: :obj:`float`
    """
    result = 0
    name = name or "start_timestamp"
    if ctime is None:
        ctime = time.time()
    with timestamplock:
        if name in commonblock:
            result = ctime - commonblock[name]
        else:
            commonblock[name] = ctime
    return result
