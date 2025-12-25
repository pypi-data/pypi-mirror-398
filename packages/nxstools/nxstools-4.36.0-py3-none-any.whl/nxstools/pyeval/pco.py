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

"""  pyeval helper functions for pco """


def postrun(commonblock,
            filestartnum,
            filedir,
            nbframes,
            filepostfix,
            fileprefix,
            filestartnum_str):
    """ code for postrun  datasource

    :param commonblock: commonblock of nxswriter
    :type commonblock: :obj:`dict`<:obj:`str`, `any`>
    :param filestartnum:  file start number
    :type filestartnum: :obj:`int`
    :param filedir: file directorentry name
    :type filedir: :obj:`str`
    :param nbframes: number of frams
    :type nbframes: :obj:`int`
    :param filepostfix: file postfix
    :type filepostfix: :obj:`str`
    :param fileprefix: file prefix
    :type fileprefix: :obj:`str`
    :param filestartnum_str: filestartnum string
    :type filestartnum_str: :obj:`str`
    :returns: postrun string
    :rtype: :obj:`str`
    """
    unixdir = filedir.replace("\\", "/")
    if len(unixdir) > 1 and unixdir[1] == ":":
        unixdir = "/data" + unixdir[2:]
    if unixdir and unixdir[-1] == "/":
        unixdir = unixdir[:-1]
    filestartnumer = commonblock[filestartnum_str] - 1
    result = "" + unixdir + "/" + fileprefix + "%05d"
    result += filepostfix + ":"
    filelastnumber = filestartnum - 1
    if "__root__" in commonblock.keys():
        root = commonblock["__root__"]
        if hasattr(root, "currentfileid") and hasattr(root, "stepsperfile"):
            spf = root.stepsperfile
            cfid = root.currentfileid
            if spf > 0 and cfid > 0:
                filelastnumber = min(
                    filestartnumer + cfid * nbframes * spf - 1, filelastnumber)
                filestartnum = filestartnumer + \
                    (cfid - 1) * nbframes * spf
    result += str(filestartnumer) + ":" + str(filelastnumber)
    return result
