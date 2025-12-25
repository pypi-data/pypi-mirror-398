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

"""  pyeval helper functions for lambda """


def m2_external_data(commonblock,
                     name,
                     savefilename,
                     saveallimages,
                     filepostfix,
                     filename,
                     modulename,
                     shortdetpath=None):
    """ code for external_data datasource

    :param commonblock: commonblock of nxswriter
    :type commonblock: :obj:`dict`<:obj:`str`, `any`>
    :param name: detector name
    :type name: :obj:`str`
    :param savefilename: name of saved file
    :type savefilename: :obj:`str`
    :param saveallimages: save all images flag
    :type saveallimages: :obj:`bool` or :obj:`int`
    :param filepostfix: file postfix
    :type filepostfix: :obj:`str`
    :param filename: file name
    :type filename: :obj:`str`
    :param filename: module name
    :type filename: :obj:`str`
    :param shortdetpath: shortdetpath
    :type shortdetpath: :obj:`bool`
    :returns: name of saved file
    :rtype: :obj:`str`
    """
    result = ""
    if saveallimages:
        if filename:
            sfname = (filename).split("/")
            result = sfname[-1].split(".")[0] + "/"
            if shortdetpath is None and \
                    len(sfname) > 1 and sfname[-2] == result[:-1]:
                result = ""
            elif shortdetpath:
                result = ""
        result += name + "/" + str(savefilename) + "_" + modulename \
            + "." + str(filepostfix) + "://entry/instrument/detector"
    return result


def external_data(commonblock,
                  name,
                  savefilename,
                  saveallimages,
                  framesperfile,
                  framenumbers,
                  filepostfix,
                  filename,
                  shortdetpath=None):
    """ code for external_data datasource

    :param commonblock: commonblock of nxswriter
    :type commonblock: :obj:`dict`<:obj:`str`, `any`>
    :param name: detector name
    :type name: :obj:`str`
    :param savefilename: name of saved file
    :type savefilename: :obj:`str`
    :param saveallimages: save all images flag
    :type saveallimages: :obj:`bool` or :obj:`int`
    :param framesperfile: frames per file
    :type framesperfile: :obj:`int`
    :param framenumbers: frames per file
    :type framenumbers: :obj:`int`
    :param filepostfix: file postfix
    :type filepostfix: :obj:`str`
    :param filename: file name
    :type filename: :obj:`str`
    :param shortdetpath: shortdetpath
    :type shortdetpath: :obj:`bool`
    :returns: name of saved file
    :rtype: :obj:`str`
    """
    result = ""
    if saveallimages:
        if filename:
            sfname = (filename).split("/")
            result = sfname[-1].split(".")[0] + "/"
            if shortdetpath is None and \
                    len(sfname) > 1 and sfname[-2] == result[:-1]:
                result = ""
            elif shortdetpath:
                result = ""
        fpf = framesperfile
        fn = framenumbers
        spf = 0
        cfid = 0
        if fpf != fn:
            if "__root__" in commonblock.keys():
                root = commonblock["__root__"]
                if hasattr(root, "currentfileid") and \
                   hasattr(root, "stepsperfile"):
                    spf = root.stepsperfile
                    cfid = root.currentfileid
        if spf > 0 and cfid > 0:
            result += name + "/" + str(savefilename) \
                + "_part%05d." % (cfid - 1) + str(filepostfix) \
                + "://entry/instrument/detector"
        else:
            result += name + "/" + str(savefilename) \
                + "." + str(filepostfix) + "://entry/instrument/detector"
    return result
