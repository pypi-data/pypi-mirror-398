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

"""  pyeval helper functions for cobold """

from nxstools import filewriter


def time_of_flight(commonblock, binsize, entryname, histogram):
    """ code for time_of_flight  datasource

    :param commonblock: commonblock of nxswriter
    :type commonblock: :obj:`dict`<:obj:`str`, `any`>
    :param detector: bin size
    :type detector: :obj:`float`
    :param entryname:  entry group name
    :type entryname: :obj:`str`
    :param histogram:  histogram field name
    :type histogram: :obj:`str`
    :returns: time of flight axis data
    :rtype: :obj:`list` <:obj:`float`>
    """

    result = []
    fld = None
    names = []
    try:
        binsize = float(filewriter.first(binsize))

        root = commonblock["__root__"]
        nxentry = root.open(entryname)
        nxdata = nxentry.open("data")
        writer = root.parent.writer
        links = writer.get_links(nxdata)
        names = list(sorted([ch.name for ch in links]))

        if histogram in names:
            fld = nxdata.open(histogram)
            if isinstance(fld, filewriter.FTField) and \
               len(fld.shape) == 2 and fld.shape[1] > 0:
                result = fld.shape
                result = [it * binsize for it in range(fld.shape[1])]
    except Exception:
        result = []
    return result
