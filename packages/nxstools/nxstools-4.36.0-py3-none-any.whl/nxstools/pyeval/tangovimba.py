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

"""  pyeval helper functions for tangovimba """


def external_data(commonblock,
                  name,
                  fileprefix,
                  filepostfix,
                  filestartnum,
                  filename,
                  shortdetpath=None):
    """ code for external_data datasource

    :param commonblock: commonblock of nxswriter
    :type commonblock: :obj:`dict`<:obj:`str`, `any`>
    :param name: detector name
    :type name: :obj:`str`
    :param fileprefix: file prefix
    :type fileprefix: :obj:`str`
    :param filepostfix: file postfix
    :type filepostfix: :obj:`str`
    :param filestartnum: file start number
    :type filestartnum: :obj:`int`
    :param filename: file name
    :type filename: :obj:`str`
    :param shortdetpath: shortdetpath
    :type shortdetpath: :obj:`bool`
    :returns: name of saved file
    :rtype: :obj:`str`
    """
    result = ""
    try:
        filestartnum = int(filestartnum)
    except Exception:
        filestartnum = 0

    if fileprefix and filepostfix:
        postfix = str(filepostfix)
        if not postfix.startswith("."):
            postfix = "." + postfix
        if postfix in [".nxs", ".nx"]:
            prefix = str(fileprefix)
            if not prefix.endswith("_"):
                prefix = prefix + "_"
            if filename:
                sfname = (filename).split("/")
                result = sfname[-1].split(".")[0] + "/"
                if shortdetpath is None and \
                        len(sfname) > 1 and sfname[-2] == result[:-1]:
                    result = ""
                elif shortdetpath:
                    result = ""

            result += name + "/" + prefix + "%06i" % filestartnum + \
                postfix + "://entry/instrument/detector"
    return result
