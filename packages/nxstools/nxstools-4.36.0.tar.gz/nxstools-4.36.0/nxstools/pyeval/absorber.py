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

"""  pyeval helper functions for absorber """

import json


def thickness(position, thicknesslist):
    """ code for absorber thickness  datasource

    :param position:  absorber position
    :type position: :obj:`float`
    :param thicknesslist:  thickness JSON list
    :type thicknesslist: :obj:`str`
    :returns: absorber thickness
    :rtype: :obj:`float`
    """
    thicknesslist = json.loads(thicknesslist)
    iposition = int(float(position) + 0.5)
    thickness = []
    for pos, thick in enumerate(thicknesslist):
        thickness.append(thick if (1 << pos) & iposition else 0.)
    return thickness


def foil(position, foillist):
    """ code for absorber foil  datasource

    :param position:  absorber position
    :type position: :obj:`float`
    :param foillist:  foil JSON list
    :type foillist: :obj:`str`
    :returns: absorber foil
    :rtype: :obj:`str`
    """
    foillist = json.loads(foillist)
    iposition = int(float(position) + 0.5)
    foil = []
    for pos, mat in enumerate(foillist):
        foil.append(mat if (1 << pos) & iposition else "")
    return foil
