#!/usr/bin/env python
#   This file is part of nexdatas - Tango Server for NeXus data writer
#
#    Copyright (C) 2012-2017 DESY, Jan Kotanski <jkotan@mail.desy.de>
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
# \package test nexdatas
# \file NXSCollect_test.py
# unittests for field Tags running Tango Server
#
import unittest

try:
    import NXSCollect_test
except Exception:
    from . import NXSCollect_test


# test fixture
class NXSCollectH5CppTest(NXSCollect_test.NXSCollectTest):

    # constructor
    # \param methodName name of the test method

    def __init__(self, methodName):
        NXSCollect_test.NXSCollectTest.__init__(self, methodName)
        self.writer = "h5cpp"
        self.flags = "--h5cpp"


if __name__ == '__main__':
    unittest.main()
