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

""" Command-line tool to ascess to Tango Data Server"""

import sys

import argparse

from .nxsdevicetools import (checkServer, listServers, openServer)
from .nxsargparser import (Runner, NXSArgParser, ErrorException)


class NexusServer(object):

    """ configuration server adapter
    """

    def __init__(self, device):
        """ constructor

        :param device: device name of configuration server
        :type device: :obj:`str`
        """
        #: (:class:`PyTango.DeviceProxy`) NeXus writer device proxy
        self.tdwServer = openServer(device)

    def openFile(self, filename):
        """ opens the h5 file

        :param filename: h5 file name
        :type filename: :obj:`str`
        """
        self.tdwServer.Init()
        self.tdwServer.FileName = str(filename)
        self.tdwServer.OpenFile()

    def setData(self, jsondata):
        """ sets the global JSON data

        :param jsondata: global JSON data
        :type jsondata: :obj:`str`
        """
        self.tdwServer.JSONRecord = str(jsondata)

    def openEntry(self, xmlconfig):
        """ opens an entry

        :param xmlconfig: xml configuration string
        :type xmlconfig: :obj:`str`
        """
        self.tdwServer.XMLSettings = str(xmlconfig)
        self.tdwServer.OpenEntry()

    def record(self, jsondata):
        """ records one step

        :param jsondata: step JSON data
        :type jsondata: :obj:`str`
        """
        self.tdwServer.Record(jsondata)

    def closeEntry(self):
        """ closes the entry
        """
        self.tdwServer.CloseEntry()

    def closeFile(self):
        """ closes the file

        """
        self.tdwServer.CloseFile()


class OpenFile(Runner):

    """ OpenFile runner"""

    #: (:obj:`str`) command description
    description = "open a new H5 file"
    epilog = "" \
        + " examples:\n" \
        + "       nxsdata openfile /tmp/watertest.nxs \n" \
        + "       nxsdata openfile -s p02/tangodataserver/exp.01  " \
        + "/user/data/myfile.h5\n" \
        + "\n"

    def create(self):
        """ creates parser

        """
        parser = self._parser
        parser.add_argument(
            "-s", "--server", dest="server",
            help="writer server device name")

    def postauto(self):
        """ parser creator after autocomplete run """
        parser = self._parser
        parser.add_argument(
            'args', metavar='file_name', type=str, nargs='?',
            help='new newxus file name')

    def run(self, options):
        """ the main program function

        :param options: parser options
        :type options: :class:`argparse.Namespace`
        :returns: output information
        :rtype: :obj:`str`
        """
        tdwserver = NexusServer(options.server)
        if not options.args or len(options.args) < 1:
            self._parser.print_help()
            sys.exit(255)
        return tdwserver.openFile(options.args[0])


class SetData(Runner):

    """ SetData runner"""

    #: (:obj:`str`) command description
    description = "assign global JSON data"
    epilog = "" \
        + " examples:\n" \
        + "       nxsdata setdata ... \n" \
        + "\n"

    def create(self):
        """ creates parser

        """
        parser = self._parser
        parser.add_argument(
            "-s", "--server", dest="server",
            help="writer server device name"
        )
        parser.add_argument(
            'args', metavar='json_data_string', type=str, nargs='?',
            help='json data string')

    def run(self, options):
        """ the main program function

        :param options: parser options
        :type options: :class:`argparse.Namespace`
        :returns: output information
        :rtype: :obj:`str`
        """
        tdwserver = NexusServer(options.server)
        if not options.args or len(options.args) < 1:
            self._parser.print_help()
            sys.exit(255)
        return tdwserver.setData(options.args[0].strip())


class OpenEntry(Runner):

    """ OpenEntry runner"""

    #: (:obj:`str`) command description
    description = "create new entry"
    epilog = "" \
        + " examples:\n" \
        + "       nxsdata openentry ... \n" \
        + "\n"

    def create(self):
        """ creates parser

        """
        parser = self._parser
        parser.add_argument(
            "-s", "--server", dest="server",
            help="writer server device name")
        parser.add_argument(
            'args', metavar='xml_config', type=str, nargs='?',
            help='nexus writer configuration string')

    def run(self, options):
        """ the main program function

        :param options: parser options
        :type options: :class:`argparse.Namespace`
        :returns: output information
        :rtype: :obj:`str`
        """
        tdwserver = NexusServer(options.server)
        if not options.args or len(options.args) < 1:
            self._parser.print_help()
            sys.exit(255)
        return tdwserver.openEntry(options.args[0].strip())


class Record(Runner):

    """ Record runner"""

    #: (:obj:`str`) command description
    description = "record one step with step JSON data"
    epilog = "" \
        + " examples:\n" \
        + "       nxsdata record ... \n" \
        + "\n"

    def create(self):
        """ creates parser

        """
        parser = self._parser
        parser.add_argument(
            "-s", "--server", dest="server",
            help="writer server device name")
        parser.add_argument(
            'args', metavar='json_data_string', type=str, nargs='?',
            help='json data string')

    def run(self, options):
        """ the main program function

        :param options: parser options
        :type options: :class:`argparse.Namespace`
        :returns: output information
        :rtype: :obj:`str`
        """
        tdwserver = NexusServer(options.server)
        return tdwserver.record(
            options.args[0].strip() if options.args else '{}')


class CloseEntry(Runner):

    """ CloseEntry runner"""

    #: (:obj:`str`) command description
    description = "close the current entry"
    epilog = "" \
        + " examples:\n" \
        + "       nxsdata closeentry \n" \
        + "\n"

    def create(self):
        """ creates parser

        """
        parser = self._parser
        parser.add_argument(
            "-s", "--server", dest="server",
            help="writer server device name"
        )

    def run(self, options):
        """ the main program function

        :param options: parser options
        :type options: :class:`argparse.Namespace`
        :returns: output information
        :rtype: :obj:`str`
        """
        tdwserver = NexusServer(options.server)
        return tdwserver.closeEntry()


class CloseFile(Runner):

    """ CloseFile runner"""

    #: (:obj:`str`) command description
    description = "close the current file"
    epilog = "" \
        + " examples:\n" \
        + "       nxsdata closefile \n" \
        + "\n"

    def create(self):
        """ creates parser

        """
        parser = self._parser
        parser.add_argument(
            "-s", "--server", dest="server",
            help="writer server device name"
        )

    def run(self, options):
        """ the main program function

        :param options: parser options
        :type options: :class:`argparse.Namespace`
        :returns: output information
        :rtype: :obj:`str`
        """
        tdwserver = NexusServer(options.server)
        return tdwserver.closeFile()


class Servers(Runner):

    """ Servers runner"""

    #: (:obj:`str`) command description
    description = "get lists of tango data servers from " \
                  + "the current tango host"
    epilog = "" \
        + " examples:\n" \
        + "       nxsdata servers \n" \
        + "\n"

    def create(self):
        """ creates parser

        """
        parser = self._parser
        parser.add_argument(
            "-s", "--server", dest="server",
            help="tango host or writer server device name"
        )

    def run(self, options):
        """ the main program function

        :param options: parser options
        :type options: :class:`argparse.Namespace`
        :returns: output information
        :rtype: :obj:`str`
        """
        return "\n".join(listServers(options.server, 'NXSConfigServer'))


def main():
    """ the main program function
    """

    #: pipe arguments
    pipe = ""
    if not sys.stdin.isatty():
        pp = sys.stdin.readlines()
        #: system pipe
        pipe = "".join(pp)

    description = "Command-line tool for writing NeXus files" \
                  + " with NXSDataWriter"

    epilog = 'For more help:\n  nxsdata <sub-command> -h'
    parser = NXSArgParser(
        description=description, epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.cmdrunners = [('openfile', OpenFile),
                         ('setdata', SetData),
                         ('openentry', OpenEntry),
                         ('record', Record),
                         ('closefile', CloseFile),
                         ('closeentry', CloseEntry)]
    runners = parser.createSubParsers()

    try:
        options = parser.parse_args()
    except ErrorException as e:
        sys.stderr.write("Error: %s\n" % str(e))
        sys.stderr.flush()
        parser.print_help()
        print("")
        sys.exit(255)

    if options.subparser is None:
        sys.stderr.write(
            "Error: %s\n" % str("too few arguments"))
        sys.stderr.flush()
        parser.print_help()
        print("")
        sys.exit(255)

    if options.subparser != 'servers':
        if not options.server:
            options.server = checkServer('NXSDataWriter')

        if not options.server:
            parser.subparsers[options.subparser].print_help()
            print("")
            sys.exit(255)

    #: command-line and pipe arguments
    parg = []
    if hasattr(options, "args"):
        parg = [options.args] if options.args else []
    if pipe:
        parg.append(pipe)
    options.args = parg

    result = runners[options.subparser].run(options)
    if result and str(result).strip():
        print(result)


if __name__ == "__main__":
    main()
