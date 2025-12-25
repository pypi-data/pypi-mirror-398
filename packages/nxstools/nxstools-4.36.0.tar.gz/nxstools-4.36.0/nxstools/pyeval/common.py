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

"""  pyeval common helper functions """


def get_element(lst, index):
    """ get list element

    :param lst: list
    :type lst: :obj:`list` <:obj:`any`>
    :param index: list index
    :type index: :obj:`int`
    :returns: list element
    :rtype: :obj:`any`
    """
    return list(lst)[index]


def filestartnum_cb(commonblock, filestartnum, nbframes,
                    filestartnum_str):
    """ code for filestartnum_cb  datasource

    :param commonblock: commonblock of nxswriter
    :type commonblock: :obj:`dict`<:obj:`str`, `any`>
    :param filestartnum:  file start number
    :type filestartnum: :obj:`int`
    :param nbframs:  number of frames
    :type fnbrames: :obj:`int`
    :param filestartnum_str: name of filestartnum datasource
    :type filestartnum_str: :obj:`str`
    :returns: file start number  - number of frames
    :rtype: :obj:`int`
    """
    if filestartnum_str not in commonblock:
        commonblock[filestartnum_str] = filestartnum - nbframes + 1
    return filestartnum - nbframes


def blockitem_rm(commonblock, names):
    """ remove blockitems from commonblock

    :param commonblock: commonblock of nxswriter
    :type commonblock: :obj:`dict`<:obj:`str`, `any`>
    :param names: commonblock item names
    :type names: :obj:`list`<:obj:`str`>
    """
    for name in names:
        if name in commonblock:
            commonblock.pop(name)


blockitems_rm = blockitem_rm


def blockitem_add(commonblock, name, value):
    """ add block item to commonblock

    :param commonblock: commonblock of nxswriter
    :type commonblock: :obj:`dict`<:obj:`str`, `any`>
    :param name: name of block item
    :type name: :obj:`str`
    :param value:  item value
    :type value: :obj:`str`
    :returns:   item value
    :rtype: :obj:`str`
    """
    if name not in commonblock:
        commonblock[name] = [value]
    else:
        commonblock[name].append(value)
    return value


def blockitem_addint(commonblock, name, value):
    """ add block item to commonblock

    :param commonblock: commonblock of nxswriter
    :type commonblock: :obj:`dict`<:obj:`str`, `any`>
    :param name: name of block item
    :type name: :obj:`str`
    :param value:  item value
    :type value: :obj:`str`
    :returns:   item value
    :rtype: :obj:`str`
    """
    if name not in commonblock:
        commonblock[name] = [int(value)]
    else:
        commonblock[name].append(int(value))
    return value


def blockitem_addint_safe(commonblock, name, value):
    """ add block item to commonblock with default 0

    :param commonblock: commonblock of nxswriter
    :type commonblock: :obj:`dict`<:obj:`str`, `any`>
    :param name: name of block item
    :type name: :obj:`str`
    :param value:  item value
    :type value: :obj:`str`
    :returns:   item value
    :rtype: :obj:`str`
    """
    try:
        value = int(value)
    except Exception:
        value = 0
    if name not in commonblock:
        commonblock[name] = [value]
    else:
        commonblock[name].append(value)
    return value
