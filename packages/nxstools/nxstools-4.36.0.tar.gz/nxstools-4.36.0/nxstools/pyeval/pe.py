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

"""  pyeval helper functions for perkinelmerdetector """


def fileindex_cb(commonblock, name, value):
    """ add block item to commonblock

    :param commonblock: commonblock of nxswriter
    :type commonblock: :obj:`dict`<:obj:`str`, `any`>
    :param name: name of block item
    :type name: :obj:`str`
    :param value: item value
    :type value: :obj:`str`
    :returns: item value
    :rtype: :obj:`str`
    """
    if name not in commonblock:
        commonblock[name] = value
    return value - 1


def postrun(commonblock,
            outputdirectory,
            filepattern,
            filename,
            fileindex,
            fileindex_str):
    """ code for postrun  datasource

    :param commonblock: commonblock of nxswriter
    :type commonblock: :obj:`dict`<:obj:`str`, `any`>
    :param outputdirectory: file directorentry name
    :type outputdirectory: :obj:`str`
    :param filepattern: file pattern
    :type filepattern: :obj:`str`
    :param filename: file name
    :type filename: :obj:`str`
    :param fileindex: file index
    :type fileindex: :obj:`int`
    :param fileindex_str: file index string
    :type fileindex_str: :obj:`str`
    :returns: postrun string
    :rtype: :obj:`str`
    """
    unixdir = str(outputdirectory).replace("\\", "/")
    startfileindex = commonblock[fileindex_str] - 1
    lastfileindex = fileindex - 1
    if len(unixdir) > 1 and unixdir[1] == ":":
        unixdir = "/data" + unixdir[2:]
    if unixdir and unixdir[-1] == "/":
        unixdir = unixdir[:-1]
    result = "" + unixdir + "/" + filepattern + "-%05d."
    result += str(filename.split(".")[-1])
    if "__root__" in commonblock.keys():
        root = commonblock["__root__"]
        if hasattr(root, "currentfileid") and hasattr(root, "stepsperfile"):
            spf = root.stepsperfile
            cfid = root.currentfileid
            if spf > 0 and cfid > 0:
                lastfileindex = min(
                    startfileindex + cfid * spf - 1, lastfileindex)
                startfileindex = startfileindex + (cfid - 1) * spf
    result += ":" + str(startfileindex) + ":" + str(lastfileindex)
    return result
