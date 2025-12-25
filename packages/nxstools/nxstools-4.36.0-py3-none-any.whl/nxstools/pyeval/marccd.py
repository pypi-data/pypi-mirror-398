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

"""  pyeval helper functions for marccd """


def postrun(commonblock,
            savingdirectory,
            savingprefix,
            savingpostfix):
    """ code for postrun datasource

    :param commonblock: commonblock of nxswriter
    :type commonblock: :obj:`dict`<:obj:`str`, `any`>
    :param savingdirectory: saving directory
    :type savingdirectory: :obj:`str`
    :param savingprefix: saving prefix
    :type savingprefix: :obj:`str`
    :param savingpostfix: saving postfix
    :type savingpostfix: :obj:`str`
    :returns: name of saved file
    :rtype: :obj:`str`
    """
    unixdir = str(savingdirectory).replace("\\", "/")
    if len(unixdir) > 1 and unixdir[1] == ":":
        unixdir = "/data" + unixdir[2:]
    if unixdir and unixdir[-1] == "/":
        unixdir = unixdir[:-1]
    result = "" + unixdir + "/" + str(savingprefix) + "." + str(savingpostfix)
    return result
