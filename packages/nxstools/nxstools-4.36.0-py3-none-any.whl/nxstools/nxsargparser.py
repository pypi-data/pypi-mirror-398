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

""" NeXus tool argumen parser
"""

import argparse
import argcomplete


class Runner(object):

    """ abstract runner"""

    #: (:obj:`str`) command description
    description = "abstract runner"

    #: (:obj:`str`) command epilog
    epilog = None

    def __init__(self, parser):
        """ parser creator

        :param parser: option parser
        :type parser: :class:`NXSFileInfoArgParser`
        """
        #: (:class:`NXSFileInfoArgParser`) option parser
        self._parser = parser

    def create(self):
        """ parser creator """

    def postauto(self):
        """ parser creator after autocomplete run """

    def run(self, options):
        """ run commandthe main program function

        :param options: parser options
        :type options: :class:`argparse.Namespace`
        """


class ErrorException(Exception):

    """ error parser exception """
    pass


class NXSArgParser(argparse.ArgumentParser):

    """ Argument parser with error exception
    """

    def __init__(self, **kwargs):
        """ constructor

        :param kwargs: :class:`argparse.ArgumentParser`
                       parameter dictionary
        :type kwargs: :obj: `dict` <:obj:`str`, `any`>
        """
        argparse.ArgumentParser.__init__(self, **kwargs)
        self.subparsers = {}
        #: (:obj:`dict` <:obj:`str`, :class:`Runner`>) \
        #    nxsfileinfo sub-command classes
        self.cmdrunners = []

    def error(self, message):
        """ error handler

        :param message: error message
        :type message: :obj:`str`
        """
        raise ErrorException(message)

    def createSubParsers(self):
        """ creates command-line parameters parser

        :returns: command runner
        :rtype: :class:`Runner`
        """

        pars = {}
        subparsers = self.add_subparsers(
            help='sub-command help', dest="subparser")

        for cmd, klass in self.cmdrunners:
            self.subparsers[cmd] = subparsers.add_parser(
                cmd, help='%s' % klass.description,
                description=klass.description,
                epilog=klass.epilog,
                formatter_class=argparse.RawDescriptionHelpFormatter
            )
            pars[cmd] = klass(self.subparsers[cmd])
            pars[cmd].create()

        argcomplete.autocomplete(self)

        for cmd, klass in self.cmdrunners:
            pars[cmd].postauto()

        return pars
