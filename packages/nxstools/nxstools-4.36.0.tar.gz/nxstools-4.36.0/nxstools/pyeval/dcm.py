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

"""  pyeval helper functions for dcm """

try:
    import tango
except Exception:
    import PyTango as tango


def unitcalibration(dcmdevice):
    """ code for dcm unitcalibration datasource

    :param dcmdevice:  dcm device name
    :type dcmdevice: :obj:`str`
    :returns: unit calibration
    :rtype: :obj:`float`
    """
    dp = tango.DeviceProxy(dcmdevice)
    bdv = dp.get_property("BraggDevice")['BraggDevice'][0]
    bdp = tango.DeviceProxy(bdv)
    return bdp.unitcalibration


def reflection(dcmdevice):
    """ code for dcm crystal reflection datasource

    :param dcmdevice:  dcm device name
    :type dcmdevice: :obj:`str`
    :returns: dcm crystal reflection
    :rtype: :obj:`list` <:obj:`int`>
    """
    dp = tango.DeviceProxy(dcmdevice)
    version = dp.get_property("Version")['Version'][0]
    crystal = dp.crystal
    if version != '11':
        return [3, 1, 1] if crystal == 1 else [1, 1, 1]
    else:
        return [2, 2, 0] if crystal == 1 else [1, 1, 1]


def crystal(dcmdevice):
    """ code for dcm crystal datasource

    :param dcmdevice:  dcm device name
    :type dcmdevice: :obj:`str`
    :returns: dcm crystal
    :rtype: :obj:`in`
    """
    dp = tango.DeviceProxy(dcmdevice)
    return dp.crystal
