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

"""  pyeval helper functions for qbpm """

import json


def foil(position, foildict):
    """ code for qbpm foil  datasource

    :param position: qpbm foil position
    :type position: :obj:`float`
    :param foildict:  foil JSON dictionary
    :type foildict: :obj:`str`
    :returns: absorber foil
    :rtype: :obj:`str`
    """
    foilposdict = json.loads(foildict)
    position = float(position)
    mindist = None
    foil = "None"
    for key, vl in foilposdict.items():
        if mindist is None:
            mindist = abs(vl - position)
            foil = key
        else:
            dist = abs(vl - position)
            if dist < mindist:
                mindist = dist
                foil = key
    return foil
