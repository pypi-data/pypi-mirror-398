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
# \package test nexdatas
# \file XMLConfiguratorTest.py
# unittests for field Tags running Tango Server
#

import unittest

try:
    import NXSCreatePyEvalH5Cpp_test
except Exception:
    from . import NXSCreatePyEvalH5Cpp_test
import nxstools.h5pywriter as H5PYWriter


# test fixture
class NXSCreatePyEvalH5PYTest(
        NXSCreatePyEvalH5Cpp_test.NXSCreatePyEvalH5CppTest):

    # constructor
    # \param methodName name of the test method

    def __init__(self, methodName):
        NXSCreatePyEvalH5Cpp_test.NXSCreatePyEvalH5CppTest.__init__(
            self, methodName)
        self.fwriter = H5PYWriter


if __name__ == '__main__':
    unittest.main()
