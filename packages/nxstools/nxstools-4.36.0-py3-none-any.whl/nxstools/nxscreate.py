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

"""Command-line tool for creating NXSConfigServer configuration of Nexus Files
"""

import os
import sys
import argparse


from nxstools.nxsargparser import (Runner, NXSArgParser, ErrorException)
from nxstools.nxsdevicetools import (
    checkServer, getAttributes, getServerTangoHost)
from nxstools.nxscreator import (
    TangoDSCreator, ClientDSCreator, WrongParameterError,
    DeviceDSCreator, OnlineDSCreator, OnlineCPCreator, CPExistsException,
    DSExistsException, SECoPCPCreator,
    StandardCPCreator, ComponentCreator, CompareOnlineDS, PoolDSCreator)


#: (:obj:`bool`) True if PyTango available
PYTANGO = False
try:
    try:
        __import__("tango")
    except Exception:
        __import__("PyTango")
    PYTANGO = True
except Exception:
    pass


class TangoDS(Runner):

    """ tangods runner"""

    #: (:obj:`str`) command description
    description = "create tango datasources"
    #: (:obj:`str`) command epilog
    epilog = "" \
        + " * with -b: datasources are created" \
        + " in Configuration Server database\n" \
        + " * without -b: datasources are created" \
        + " on the local filesystem in -d <directory> \n" \
        + " * default: <directory> is '.' \n" \
        + "            <server> is taken from Tango DB\n" \
        + "            <datasource> is 'exp_mot' \n" \
        + "            <host>, <port> are taken from <server>\n" \
        + "\n" \
        + " examples:\n" \
        + "\n" \
        + "       nxscreate tangods -f1 -l2 -v p09/motor/exp. -s exp_mot \n" \
        + "\n" \
        + "           - create the 'exp_mot01' and 'exp_mot02' datasources " \
        + "of the 'TANGO' type\n" \
        + "               with the corresponding 'p09/motor/exp.0?' " \
        + "device names\n" \
        + "               and 'Position' tango attribute names" \
        + " in the local directory\n" \
        + "               where '?' is 1, 2 respectively \n" \
        + "\n" \
        + "       nxscreate tangods -f1 -l32 -v p02/motor/eh1a. -s exp_mot" \
        + " -b \n" \
        + "\n" \
        + "           - create the 'exp_mot01', ... ,'exp_mot32'"\
        " datasources " \
        + "of the 'TANGO' type\n" \
        + "               with the corresponding 'p09/motor/eh1a.??' " \
        + "device names\n" \
        + "               while their attribute name is 'Position' " \
        + " and upload them to the NXSConfigServer database\n" \
        + "               where '??' is 01, 02, ... ,32 respectively \n" \
        + "\n" \
        + "       nxscreate tangods -v petra/globals/keyword " \
        + "-s source_current -u haso228 -t 10000 \\ \n "\
        + "                        -a BeamCurrent " \
        + "-b -r p09/nxsconfigserver/haso228 -o -g __CLIENT__\n" \
        + "\n" \
        + "           - create the a 'source_current' datasource " \
        + "of the 'TANGO' type belonging to the '__CLIENT__' group \n" \
        + "               with the 'petra/globals/keyword' device name\n" \
        + "               while their attribute name is 'BeamCurrent', \n" \
        + "               their hostname is 'haso228', " \
        + "their tango port is '10000'\n" \
        + "               and upload them to the NXSConfigServer " \
        + "'p09/nxsconfigserver/haso228' database\n" \
        + "\n" \
        + "       nxscreate tangods -f1 -l8  -v pXX/slt/exp. -s slt_exp_ -u" \
        + " hasppXX.desy.de -b \n" \
        + "\n" \
        + "           - create the 'slt_exp_01', ... ,'slt_exp_08'" \
        " datasources " \
        + "of the 'TANGO' type\n" \
        + "               with the corresponding 'pXX/slt/exp.0?' " \
        + "device names\n" \
        + "               while their attribute name is 'Position', \n" \
        + "               their hostname is 'hasppXX.desy.de' " \
        + " and upload them to the NXSConfigServer database\n" \
        + "               where '??' is 1, 2, ... ,8 respectively \n" \
        + "\n"

    def create(self):
        """ creates parser

        """
        parser = self._parser
        parser.add_argument(
            "-v", "--device-prefix",
            help="device prefix, i.e. exp_c (mandatory)",
            dest="device", default="")
        parser.add_argument(
            "-f", "--first", help="first index",
            dest="first", default="1")
        parser.add_argument(
            "-l", "--last",
            help="last index",
            dest="last", default=None)

        parser.add_argument(
            "-a", "--attribute",
            help="tango attribute name",
            dest="attribute", default="Position")

        parser.add_argument(
            "-s", "--datasource-prefix",
            help="datasource-prefix "
            "(useful for avoiding duplicated datasource names)",
            dest="datasource", default="exp_mot")

        parser.add_argument(
            "-o", "--overwrite", action="store_true",
            default=False, dest="overwrite",
            help="overwrite existing datasources")
        parser.add_argument(
            "-d", "--directory",
            help="output datasource directory",
            dest="directory", default=".")
        parser.add_argument(
            "-x", "--file-prefix",
            help="file prefix, i.e. counter",
            dest="file", default="")
        parser.add_argument(
            "-u", "--host",
            help="tango host name",
            dest="host", default="")
        parser.add_argument(
            "-t", "--port",
            help="tango host port",
            dest="port", default="10000")
        parser.add_argument(
            "-b", "--database", action="store_true",
            default=False, dest="database",
            help="store datasources in "
            "Configuration Server database")
        parser.add_argument(
            "-g", "--group",
            help="device group name",
            dest="group", default="")
        parser.add_argument(
            "-e", "--elementtype",
            help="element type, i.e. attribute, property or command",
            dest="elementtype", default="attribute")

        parser.add_argument(
            "-r", "--server", dest="server",
            help="configuration server device name")
        return parser

    def run(self, options):
        """ the main program function

        :param options: parser options
        :type options: :class:`argparse.Namespace`
        """

        parser = self._parser
        if (options.database and not options.server) or \
           (not options.host and not options.server):
            if not PYTANGO:
                sys.stderr.write("Info: No PyTango installed\n")
                sys.stderr.flush()
                sys.exit(255)
            options.server = checkServer()
            if options.database and not options.server:
                parser.print_help()
                sys.exit(0)

        if not options.host:
            if not PYTANGO:
                sys.stderr.write(
                    "Info: No Tango Host or PyTango installed\n")
                sys.stderr.flush()
                sys.exit(255)
            hostport = getServerTangoHost(options.server)
            options.host, options.port = hostport.split(":")

        if options.database:
            print("CONFIG SERVER: %s" % str(options.server))
        else:
            print("OUTPUT DIRECTORY: %s" % str(options.directory))

        creator = TangoDSCreator(options, [])
        try:
            creator.create()
        except WrongParameterError as e:
            sys.stderr.write(str(e))
            sys.stderr.flush()
            parser.print_help()
            sys.exit(255)


class DeviceDS(Runner):

    """ deviceds runner"""
    #: (:obj:`str`) command description
    description = "create datasources for all device attributes"
    #: (:obj:`str`) command epilog
    epilog = "" \
             + " * without <dv_attr1>: datasources for all" \
             + " attributes are created\n" \
             + " * with -b: datasources are created" \
             + " in Configuration Server database\n" \
             + " * without -b: datasources are created" \
             + " on the local filesystem in -d <directory> \n" \
             + " * default: <directory> is '.' \n" \
             + "            <server> is taken from Tango DB\n" \
             + "            <datasource> is 'exp_mot' \n" \
             + "            <host>, <port> are taken from <server>\n" \
             + "\n" \
             + " examples:\n" \
             + "\n" \
             + "       nxscreate deviceds  -v p09/pilatus/haso228k \n" \
             + "\n" \
             + "           - create datasources of the 'TANGO' type\n" \
             + "               for all attribute of 'p09/pilatus/haso228k'" \
             + " tango device\n" \
             + "               in the local file directory " \
             + "database \n" \
             + "\n" \
             + "       nxscreate deviceds  -v p09/lambda2m/haso228k -u" \
             + "haslambda -b \n" \
             + "\n" \
             + "           - create datasources of the 'TANGO' type\n" \
             + "               for all attribute of 'p09/lambda2m/haso228k'" \
             + " tango device\n" \
             + "               with their hostname 'haslambda' \n" \
             + "               and upload them to the NXSConfigServer " \
             + "database \n" \
             + "\n" \
             + "       nxscreate deviceds  -v p09/pilatus300k/haso228k -b" \
             + " -s pilatus300k_ RoI Energy ExposureTime\n" \
             + "\n" \
             + "           - create datasources of the 'TANGO' type\n" \
             + "               for RoI Energy ExposureTime attribute of" \
             + " 'p09/lambda2m/haso228k'" \
             + " tango device\n" \
             + "               with the 'pilatus300k_' datasource prefix \n" \
             + "               and upload them to the NXSConfigServer " \
             + "database \n" \
             + "\n"

    def create(self):
        """ creates parser
        """
        parser = self._parser
        parser.add_argument("-v", "--device",
                            help="device, i.e. p09/pilatus300k/01 (mandatory)",
                            dest="device", default="")
        parser.add_argument("-s", "--datasource-prefix",
                            help="datasource-prefix"
                            " (useful for avoiding duplicated"
                            " datasource names)",
                            dest="datasource", default="")

        parser.add_argument("-o", "--overwrite", action="store_true",
                            default=False, dest="overwrite",
                            help="overwrite existing datasources")
        parser.add_argument("-d", "--directory",
                            help="output datasource directory",
                            dest="directory", default=".")
        parser.add_argument("-x", "--file-prefix",
                            help="file prefix, i.e. counter",
                            dest="file", default="")
        parser.add_argument("-u", "--host",
                            help="tango host name",
                            dest="host", default="")
        parser.add_argument("-t", "--port",
                            help="tango host port",
                            dest="port", default="10000")

        parser.add_argument("-b", "--database", action="store_true",
                            default=False, dest="database",
                            help="store components in Configuration"
                            " Server database")

        parser.add_argument("-n", "--no-group", action="store_true",
                            default=False, dest="nogroup",
                            help="don't create common group with a name of"
                            " datasource prefix")

        parser.add_argument("-r", "--server", dest="server",
                            help="configuration server device name")

        parser.add_argument('args', metavar='attribute_name',
                            type=str, nargs='*',
                            help='attribute names of the tango device')

    def run(self, options):
        """ the main program function

        :param options: parser options
        :type options: :class:`argparse.Namespace`
        """

        parser = self._parser
        if (options.database and not options.server) or \
           (not options.host and not options.server):
            if not PYTANGO:
                sys.stderr.write("Info: No PyTango installed\n")
                sys.stderr.flush()
                sys.exit(255)

            options.server = checkServer()
            if options.database and not options.server:
                parser.print_help()
                sys.exit(0)

        if not options.host:
            if not PYTANGO:
                sys.stderr.write("Info: No Tango Host or PyTango installed\n")
                sys.stderr.flush()
                sys.exit(255)
            hostport = getServerTangoHost(options.server)
            options.host, options.port = hostport.split(":")

        if options.database:
            print("CONFIG SERVER: %s" % options.server)
        else:
            print("OUTPUT DIRECTORY: %s" % options.directory)

        if not options.device.strip():
            parser.print_help()
            sys.exit(255)

        if options.args:
            aargs = list(options.args)
        else:
            if not PYTANGO:
                sys.stderr.write("CollCompCreator No PyTango installed\n")
                sys.stderr.flush()
                parser.print_help()
                sys.exit(255)
            aargs = getAttributes(options.device, options.host, options.port)

        creator = DeviceDSCreator(options, aargs)
        creator.create()


class OnlineDS(Runner):

    """ onlineds runner"""

    #: (:obj:`str`) command description
    description = "create datasources from online.xml file"
    #: (:obj:`str`) command epilog
    epilog = "" \
        + " * with -b: datasources are created" \
        + " in Configuration Server database\n" \
        + " * with -d <directory>: datasources are created" \
        + " on the local filesystem\n" \
        + " * without -b or -d <directory>: run in the test mode\n" \
        + " * default: <inputFile> is '/online_dir/online.xml' \n" \
        + "            <server> is taken from Tango DB\n\n" \
        + " `onlineds` overwrites existing datasources\n\n" \
        + " examples:\n" \
        + "\n" \
        + "       nxscreate onlineds -b  \n" \
        + "\n" \
        + "           - create datasources from online.xml file \n" \
        + "               and upload them to the NXSConfigServer database \n" \
        + "\n" \
        + "       nxscreate onlineds -b -t \n" \
        + "\n" \
        + "           - like above but set motor tango datasources to \n" \
        + "               be no __CLIENT__ like\n" \
        + "\n" \
        + "       nxscreate onlineds -d /home/user/xmldir \n" \
        + "\n" \
        + "           - create datasources from online.xml file \n" \
        + "               and save them" \
        " in the '/home/user/xmldir' directory \n" \
        + "\n" \
        + "       nxscreate onlineds \n" \
        + "\n" \
        + "           - run the command in test mode" \
        + " without creating datasources \n"

    def create(self):
        """ creates parser
        """
        parser = self._parser
        parser.add_argument("-b", "--database", action="store_true",
                            default=False, dest="database",
                            help="store components in"
                            " Configuration Server database")
        parser.add_argument("-t", "--noclientlike", action="store_false",
                            default=True, dest="clientlike",
                            help="set motor tango datasources to "
                            "be no __CLIENT__ like, i.e. pure tango-like")
        parser.add_argument("-d", "--directory",
                            help="output directory where"
                            " datasources will be saved",
                            dest="directory", default="")
        parser.add_argument("-n", "--nolower", action="store_false",
                            default=True, dest="lower",
                            help="do not change aliases into lower case")
        parser.add_argument("-r", "--server", dest="server",
                            help="configuration server device name")
        parser.add_argument("-x", "--file-prefix",
                            help="file prefix, i.e. counter",
                            dest="file", default="")
        parser.add_argument("-e", "--external",
                            help="external configuration server",
                            dest="external", default="")
        parser.add_argument("-p", "--xml-package", dest="xmlpackage",
                            help="xml template package")
        parser.add_argument("-c", "--clientlike", action="store_true",
                            default=False, dest="oldclientlike",
                            help="set motor tango datasources to "
                            "be __CLIENT__ like (deprecated)")
        parser.add_argument("--verbose", action="store_true",
                            default=False, dest="verbose",
                            help="printout verbose mode")

    def postauto(self):
        """ creates parser
        """
        self._parser.add_argument('args', metavar='online_file',
                                  type=str, nargs='?',
                                  help='online.xml file')

    def run(self, options):
        """ the main program function

        :param options: parser options
        :type options: :class:`argparse.Namespace`
        """

        parser = self._parser
        if not PYTANGO:
            sys.stderr.write("Info: No PyTango installed\n")
            sys.stderr.flush()
            sys.exit(255)

        if not options.server:
            options.server = checkServer()
            if not options.server and options.database:
                parser.print_help()
                sys.exit(0)
        args = [options.args] if options.args else []
        if not len(args) and os.path.isfile('/online_dir/online.xml'):
            args = ['/online_dir/online.xml']

        if not len(args):
            parser.print_help()
            sys.exit(255)

        print("INPUT: %s" % args)
        if options.directory:
            print("OUTPUT DIR: %s" % options.directory)
        elif options.database:
            print("SERVER: %s" % options.server)
        else:
            print("TEST MODE: %s" % options.server)

        creator = OnlineDSCreator(options, args)
        creator.create()


class PoolDS(Runner):

    """ poolds runner"""

    #: (:obj:`str`) command description
    description = "create datasources from sardana pool device"
    #: (:obj:`str`) command epilog
    epilog = "" \
        + " * with -b: datasources are created" \
        + " in Configuration Server database\n" \
        + " * with -d <directory>: datasources are created" \
        + " on the local filesystem\n" \
        + " * without -b or -d <directory>: run in the test mode\n" \
        + " * default: <channel> is 'ALL' \n" \
        + "            <server> is taken from Tango DB\n\n" \
        + "            <pool> is taken from Tango DB\n\n" \
        + " `poolds` overwrites existing datasources\n\n" \
        + " examples:\n" \
        + "\n" \
        + "       nxscreate poolds -b  \n" \
        + "\n" \
        + "           - create all datasources defined in the local Pool \n" \
        + "               and upload them to the NXSConfigServer database \n" \
        + "\n" \
        + "       nxscreate poolds -b -t \n" \
        + "\n" \
        + "           - like above but set motor tango datasources to \n" \
        + "               be no __CLIENT__ like\n" \
        + "\n" \
        + "       nxscreate poolds -d . -p p09/pool/haso228 \n" \
        + "\n" \
        + "           - create all datasources defined in the" \
        " 'p09/pool/haso228' Pool \n" \
        + "               and save them in the local directory \n" \
        + "\n" \
        + "       nxscreate poolds -b Motor CTExpChannel \n" \
        + "\n" \
        + "           - create datasources of " \
        + "'Motor' and CTExpChannel classes \n" \
        + "               defined in the local Pool \n" \
        + "               and upload them to the NXSConfigServer database \n" \
        + "\n" \
        + "       nxscreate poolds -b mot01 mot03 \n" \
        + "\n" \
        + "           - create 'mot01' and 'mot03' datasources\n" \
        + "               defined in the local Pool \n" \
        + "               and upload them to the NXSConfigServer database \n" \
        + "\n" \
        + "       nxscreate poolds \n" \
        + "\n" \
        + "           - run the command in test mode" \
        + " without creating datasources \n"

    def create(self):
        """ creates parser
        """
        parser = self._parser
        parser.add_argument("-b", "--database", action="store_true",
                            default=False, dest="database",
                            help="store components in"
                            " Configuration Server database")
        parser.add_argument("-t", "--noclientlike", action="store_false",
                            default=True, dest="clientlike",
                            help="set motor tango datasources to "
                            "be no __CLIENT__ like, i.e. pure tango-like")
        parser.add_argument("-d", "--directory",
                            help="output directory where"
                            " datasources will be saved",
                            dest="directory", default="")
        parser.add_argument("-n", "--nolower", action="store_false",
                            default=True, dest="lower",
                            help="do not change aliases into lower case")
        parser.add_argument("-r", "--server", dest="server",
                            help="configuration server device name")
        parser.add_argument("-x", "--file-prefix",
                            help="file prefix, i.e. counter",
                            dest="file", default="")
        parser.add_argument("-p", "--pool",
                            help="sardana pool device name",
                            dest="pool", default="")

    def postauto(self):
        """ creates parser
        """
        self._parser.add_argument('args', metavar='channel',
                                  type=str, nargs='*',
                                  help='sardana pool channel types '
                                  'or name of aliases, '
                                  'e.g. Motor CTExpChannel ZeroDExpChannel '
                                  'OneDExpChannel TwoDExpChannel '
                                  ' PseudoMotor PseudoCounter ALL')

    def run(self, options):
        """ the main program function

        :param options: parser options
        :type options: :class:`argparse.Namespace`
        """

        parser = self._parser
        if not PYTANGO:
            sys.stderr.write("Info: No PyTango installed\n")
            sys.stderr.flush()
            sys.exit(255)
        if not options.server:
            options.server = checkServer()
            if options.database and not options.server:
                parser.print_help()
                sys.exit(0)

        if not options.pool:
            options.pool = checkServer("Pool")
            if not options.pool:
                parser.print_help()
                sys.exit(0)
        args = options.args

        print("INPUT: %s" % args)
        if options.directory:
            print("OUTPUT DIR: %s" % options.directory)
        elif options.database:
            print("SERVER: %s" % options.server)
        else:
            print("TEST MODE: %s" % options.server)

        creator = PoolDSCreator(options, args)
        creator.create()


class Compare(Runner):

    """ compare runner"""

    #: (:obj:`str`) command description
    description = "compare two online.xml files"
    #: (:obj:`str`) command epilog
    epilog = "" \
        + " * default: second file <online_file> is " \
        + "'/online_dir/online.xml' \n" \
        + "            if only file is given\n\n" \
        + " examples:\n" \
        + "\n" \
        + "       nxscreate compare online.xml \n"\
        + "\n" \
        + "           - compare 'online.xml' to '/online_dir/online.xml\n' " \
        + "\n" \
        + "       nxscreate compare /online_dir/online_040.xml online.xml \n" \
        + "\n" \
        + "           - compare '/online_dir/online_040.xml' to 'online.xml'" \
        + "\n"

    def create(self):
        """ creates parser
        """
        parser = self._parser
        parser.add_argument("-n", "--nolower", action="store_false",
                            default=True, dest="lower",
                            help="do not change aliases into lower case")

    def postauto(self):
        """ creates parser
        """
        self._parser.add_argument('args', metavar='online_file',
                                  type=str, nargs='+',
                                  help='online.xml files')

    def run(self, options):
        """ the main program function

        :param options: parser options
        :type options: :class:`argparse.Namespace`
        """
        args = options.args if options.args else []
        parser = self._parser

        if len(args) == 1 and os.path.isfile('/online_dir/online.xml'):
            args.append('/online_dir/online.xml')

        if len(args) == 1:
            parser.print_help()
            sys.exit(255)

        creator = CompareOnlineDS(options, args)
        creator.compare()


class OnlineCP(Runner):

    """ onlinecp runner"""
    #: (:obj:`str`) command description
    description = "create component from online.xml file"
    #: (:obj:`str`) command epilog
    epilog = "" \
        + " * without '-c <component>': show a list of possible components\n" \
        + " * with -b: datasources are created" \
        + " in Configuration Server database\n" \
        + " * without -b: datasources are created" \
        + " on the local filesystem in -d <directory> \n" \
        + " * default: <directory> is '.' \n" \
        + " * default: <inputFile> is '/online_dir/online.xml' \n" \
        + "            <server> is taken from Tango DB\n\n" \
        + " examples:\n" \
        + "\n" \
        + "       nxscreate onlinecp  \n" \
        + "\n" \
        + "           - list possible components which " \
        + "can be created from online.xml \n" \
        + "\n" \
        + "       nxscreate onlinecp -c pilatus -b \n" \
        + "\n" \
        + "           - create the 'pilatus' component and its datasources\n" \
        + "               in the NXSConfigServer database\n"\
        + "\n" \
        + "       nxscreate onlinecp -c lambda -d /home/user/xmldir/ \n" \
        + "\n" \
        + "           - create the 'lambda' component and its datasources\n" \
        + "               in the '/home/user/xmldir/' directory\n"\
        + "\n"\
        + "       nxscreate onlinecp -c lmbd -t lambda -b \n" \
        + "\n" \
        + "           - create the 'lmbd' component of 'lambda' type " \
        + "and its datasources\n" \
        + "               in the NXSConfigServer database\n"\
        + "\n"\
        + "\n"\
        + "       nxscreate onlinecp -c lmbd -t lambda  -v p00/lmbd/1 " \
        + "-u haso000 -w 10000 -b \n" \
        + "\n" \
        + "           - create the 'lmbd' component of 'lambda' type " \
        + "and its datasources without online.xml\n" \
        + "               in the NXSConfigServer database\n"\
        + "\n"

    def create(self):
        """ creates parser
        """
        parser = self._parser
        parser.add_argument("-c", "--component",
                            help="component name" +
                            "related to the device name from <inputFile>",
                            dest="component", default="")
        parser.add_argument("-b", "--database", action="store_true",
                            default=False, dest="database",
                            help="store components in"
                            "Configuration Server database")
        parser.add_argument("-r", "--server", dest="server",
                            help="configuration server device name")
        parser.add_argument("-t", "--type",
                            help="component type",
                            dest="cptype", default="")
        parser.add_argument("-v", "--device",
                            help="device, i.e. p09/pilatus300k/01",
                            dest="device", default="")
        parser.add_argument("-u", "--host",
                            help="tango host name",
                            dest="host", default="")
        parser.add_argument("-w", "--port",
                            help="tango host port",
                            dest="port", default="")
        parser.add_argument("-n", "--nolower", action="store_false",
                            default=True, dest="lower",
                            help="do not change aliases into lower case")
        parser.add_argument("-o", "--overwrite", action="store_true",
                            default=False, dest="overwrite",
                            help="overwrite existing component")
        parser.add_argument("-d", "--directory",
                            help="output datasource directory",
                            dest="directory", default=".")
        parser.add_argument("-x", "--file-prefix",
                            help="file prefix, i.e. counter",
                            dest="file", default="")
        parser.add_argument("-e", "--external",
                            help="external configuration server",
                            dest="external", default="")
        parser.add_argument("-p", "--xml-package", dest="xmlpackage",
                            help="xml template package")
        parser.add_argument("-y", "--entryname", dest="entryname",
                            help="entry group name (prefix)", default="scan")
        parser.add_argument("-i", "--insname", dest="insname",
                            help="instrument group name", default="instrument")

    def postauto(self):
        """ creates parser
        """
        self._parser.add_argument('args', metavar='online_file',
                                  type=str, nargs='?',
                                  help='online.xml file')

    def run(self, options):
        """ the main program function

        :param options: parser options
        :type options: :class:`argparse.Namespace`
        """

        parser = self._parser
        if not PYTANGO:
            sys.stderr.write("Info: No PyTango installed\n")
            sys.stderr.flush()
            sys.exit(255)

        if not options.server:
            options.server = checkServer()
            if not options.server and options.database:
                parser.print_help()
                sys.exit(0)

        args = [options.args] if options.args else []
        if not options.component or not options.device or not options.cptype:
            if not len(args) and os.path.isfile('/online_dir/online.xml'):
                args = ['/online_dir/online.xml']

            if not len(args):
                parser.print_help()
                sys.exit(255)

            print("INPUT: %s" % args[0])
        if options.database:
            print("SERVER: %s" % options.server)
        else:
            print("OUTPUT DIR: %s" % options.directory)

        creator = OnlineCPCreator(options, args)
        if options.component:
            try:
                creator.create()
            except CPExistsException as e:
                print(str(e))
                sys.exit(255)
        else:
            lst = creator.listcomponents()
            print("\nPOSSIBLE COMPONENTS: \n   %s" % " ".join(list(lst)))
            lst = creator.listcomponenttypes()
            print("\nPOSSIBLE COMPONENT TYPES: \n   %s" % " ".join(list(lst)))


class StdComp(Runner):

    """  stdcomp runner"""

    #: (:obj:`str`) command description
    description = "create component from the standard templates"
    #: (:obj:`str`) command epilog
    epilog = "" \
        + " * without '-t <type>': show a list of possible" \
        + " component types\n" \
        + " * with '-t <type>  and without -c <component>:" \
        + " show a list of component variables " \
        + "for the given component type\n" \
        + " * with -b: datasources are created" \
        + " in Configuration Server database\n" \
        + " * without -b: datasources are created" \
        + " on the local filesystem in -d <directory> \n" \
        + " * default: <directory> is '.' \n" \
        + " * [name1 value1 [name2 value2] ...] sequence" \
        + "  defines component variable values \n\n" \
        + " examples:\n" \
        + "\n" \
        + "       nxscreate stdcomp  \n" \
        + "\n" \
        + "           - list possible component types\n" \
        + "               from the 'nxstools.xmltemplates' package\n" \
        + "\n" \
        + "       nxscreate stdcomp  -p nxsextrasp00  \n" \
        + "\n" \
        + "           - list possible component types" \
        + " from the 'nxsextrasp00' package\n" \
        + "\n" \
        + "       nxscreate stdcomp  -t source \n" \
        + "\n" \
        + "           - list a description of 'source' component variables\n" \
        + "\n" \
        + "       nxscreate stdcomp  -t default  -c default  -m  -b\n" \
        + "\n" \
        + "           - create 'default' component  of the 'default' type\n" \
        + "               in the NXSConfigServer database"\
        + " and set it as mandatory\n" \
        + "\n" \
        + "       nxscreate stdcomp  -t slit  -c front_slit1" \
        + "   xgap slt1x  ygap slt1y\n" \
        + "\n" \
        + "           - create 'front_slit1' component  of the 'slit' type\n" \
        + "               where variables xgap='slt1x' and ygap='slt1and'" \
        + " in the local directory \n" \
        + "\n" \
        + "       nxscreate stdcomp  -p nxsextrasp08  -t analyzer " \
        + " -c analyzer1  v anav  roll anaroll  -b\n" \
        + "\n" \
        + "           - create 'analyzer1' component of " \
        + "the 'analyzer type'\n" \
        + "               where variables v='anav' and roll='amaroll'"\
        + " in the NXSConfigServer database\n"

    def create(self):
        """ creates parser
        """
        parser = self._parser
        parser.add_argument("-c", "--component",
                            help="component name",
                            dest="component", default="")
        parser.add_argument("-t", "--type",
                            help="component type",
                            dest="cptype", default="")
        parser.add_argument("-r", "--server", dest="server",
                            help="configuration server device name")
        parser.add_argument("-p", "--xml-package", dest="xmlpackage",
                            help="xml template package")
        parser.add_argument("-n", "--nolower", action="store_false",
                            default=True, dest="lower",
                            help="do not change aliases into lower case")
        parser.add_argument("-o", "--overwrite", action="store_true",
                            default=False, dest="overwrite",
                            help="overwrite existing component")
        parser.add_argument("-b", "--database", action="store_true",
                            default=False, dest="database",
                            help="store components in"
                            "Configuration Server database")
        parser.add_argument("-d", "--directory",
                            help="output datasource directory",
                            dest="directory", default=".")
        parser.add_argument("-m", "--mandatory", action="store_true",
                            default=False, dest="mandatory",
                            help="set the component as mandatory")
        parser.add_argument("-e", "--external",
                            help="external configuration server",
                            dest="external", default="")
        parser.add_argument("-x", "--file-prefix",
                            help="file prefix, i.e. counter",
                            dest="file", default="")
        parser.add_argument("-y", "--entryname", dest="entryname",
                            help="entry group name (prefix)", default="scan")
        parser.add_argument("-i", "--insname", dest="insname",
                            help="instrument group name", default="instrument")
        parser.add_argument('args', metavar='key value',
                            type=str, nargs='*',
                            help='pairs of (key value) for template variables')

    def postauto(self):
        """ creates parser
        """
        self._parser.add_argument('-f', '--online-xml-file',
                                  help="online.xml file",
                                  dest="onlinexmlfile", default="")

    def run(self, options):
        """ the main program function

        :param options: parser options
        :type options: :class:`argparse.Namespace`
        """
        parser = self._parser
        if not PYTANGO:
            sys.stderr.write("Info: No PyTango installed\n")
            parser.print_help()
            sys.exit(255)

        args = options.args or []

        creator = StandardCPCreator(options, args)
        if options.component and options.cptype:
            if not options.server:
                options.server = checkServer()
                if not options.server and options.database:
                    parser.print_help()
                    sys.exit(0)
            if options.database:
                print("SERVER: %s" % options.server)
            else:
                print("OUTPUT DIR: %s" % options.directory)

            try:
                creator.create()
            except CPExistsException as e:
                print(str(e))
                sys.exit(255)
            except DSExistsException as e:
                print(str(e))
                sys.exit(255)
        elif options.cptype:
            dct = creator.listcomponentvariables()
            print("\nCOMPONENT VARIABLES:")
            for var in sorted(dct.keys()):
                desc = dct[var]
                if not var.startswith('__') and not var.endswith('__'):
                    print("  %s - %s [default: '%s']"
                          % (var, desc['doc'], desc['default']))
        else:
            parser.print_help()
            print("")
            lst = sorted(creator.listcomponenttypes())
            print("\nPOSSIBLE COMPONENT TYPES: \n   %s" % " ".join(lst))


class Comp(Runner):

    """ comp runner"""
    #: (:obj:`str`) command description
    description = "create simple components"
    #: (:obj:`str`) command epilog
    epilog = "" \
        + " * with -b: components are created (without datasources)" \
        + " in Configuration Server database\n" \
        + " * without -b: components are created (without datasources)" \
        + " on the local filesystem in -d <directory> \n" \
        + " * default: <directory> is '.' \n" \
        + "            <server> is taken from Tango DB\n" \
        + "            <strategy> is step\n" \
        + "            <type> is NX_FLOAT\n" \
        + "            <chunk> is SCALAR\n" \
        + "            <nexuspath> is " \
        + "\"/\\$var.entryname#'scan'\\$var.serialno:NXentry" \
        + "/instrument/collection/\"\n" \
        + "\n" \
        + " examples:\n" \
        + "\n" \
        + "       nxscreate comp counter \n" \
        + "\n" \
        + "           - create the 'counter' component" \
        + " in the local directory \n" \
        + "               which sets fetching data in the 'STEP' mode from " \
        + "a 'counter' datasource to \n" \
        + "               '/\\$var.entryname#'scan'\\$var.serialno:NXentry/" \
        + "instrument:NXinstrument/collection:NXcollection/counter' \n" \
        + "\n" \
        + "       nxscreate comp -f5 -l7 -v exp_c -b \n" \
        + "\n" \
        + "           - create the 'exp_c05', 'exp_c06' 'exp_c07' components" \
        + " in the NXSConfigServer database \n" \
        + "               which set fetching data in the 'STEP' mode from " \
        + " corresponding 'exp_c0?' datasources to corresponding\n" \
        + "               '/\\$var.entryname#'scan'\\$var.serialno:NXentry/" \
        + "instrument:NXinstrument/collection:NXcollection/exp_c0?'\n" \
        + "                where '?' is 5, 6, 7 respectively \n" \
        + "\n" \
        + "       nxscreate comp lambda -d /home/user/xmldir/ \n" \
        + "\n" \
        + "           - create the 'lambda' component" \
        + " in the '/home/user/xmldir/' directory \n" \
        + "               which sets fetching data in the 'STEP' mode from " \
        + "a 'lambda' datasource to \n" \
        + "               '/\\$var.entryname#'scan'\\$var.serialno:NXentry/" \
        + "instrument:NXinstrument/collection:NXcollection/lambda' \n" \
        + "\n" \
        + "       nxscreate comp -n " \
        + "\"/\\$var.entryname#'scan'\\$var.serialno:NXentry/instrument/" \
        + "sis3302:NXdetector/collection:NXcollection/\" " \
        + "-v sis3302_1_roi -f1 -l3 " \
        + " -g FINAL -t NX_FLOAT64 -k -b -m \n" \
        + "\n" \
        + "           - create the 'sis3302_1_roi1', sis3302_1_roi2'," \
        + " sis3302_1_roi3' components" \
        + " in the NXSConfigServer database \n" \
        + "               which set fetching data in the 'FINAL' mode from" \
        + " corresponding 'sis3302_1_roi?' datasources to corresponding\n" \
        + "               '/\\$var.entryname#'scan'\\$var.serialno:NXentry/" \
        + "instrument:NXinstrument/sis3302:NXdetector/" \
        + "collection:NXcollection/sis3302_1_roi?'\n" \
        + "               float64 fields and creates corresponding\n" \
        + "               '/\\$var.entryname#'scan'\\$var.serialno:NXentry/" \
        + "data:NXdata/sis3302_1_roi?' links\n" \
        + "               where '?' is 1, 2, 3 respectively \n" \
        + "\n" \
        + "       nxscreate comp -n " \
        + "\"/\\$var.entryname#'scan'\\$var.serialno:NXentry/instrument/" \
        + "eh1_mca01:NXdetector/data\" eh1_mca01 -g STEP -t NX_FLOAT64" \
        + " -i -b -c SPECTRUM\n" \
        + "\n" \
        + "           - create the 'eh1_mca01' component" \
        + " in the NXSConfigServer database \n" \
        + "               which set fetching STECTRUM data in the " \
        + "'STEP' mode from" \
        + " a 'eh1_mca01' datasource to \n" \
        + "               '/\\$var.entryname#'scan'\\$var.serialno:NXentry/" \
        + "instrument:NXinstrument/eh1_mca01:NXdetector/data\n" \
        + "               float64 fields and creates \n" \
        + "               '/\\$var.entryname#'scan'\\$var.serialno:NXentry/" \
        + "data:NXdata/eh1_mca01' links\n" \
        + "\n" \
        + "\n"

    def create(self):
        """ creates parser
        """
        parser = self._parser
        parser.add_argument(
            "-v", "--device-prefix", help="device prefix, i.e. exp_c",
            dest="device", default="")
        parser.add_argument(
            "-f", "--first", help="first index",
            dest="first", default="1")
        parser.add_argument(
            "-l", "--last", help="last index",
            dest="last", default=None)
        parser.add_argument(
            "-o", "--overwrite", action="store_true",
            default=False, dest="overwrite",
            help="overwrite existing components")
        parser.add_argument(
            "-a", "--can-fail", action="store_true",
            default=False, dest="canfail",
            help="can fail strategy flag")
        parser.add_argument(
            "-d", "--directory",
            help="output component directory",
            dest="directory", default=".")
        parser.add_argument(
            "-x", "--file-prefix",
            help="file prefix, i.e. counter",
            dest="file", default="")

        parser.add_argument(
            "-n", "--nexuspath",
            help="nexus path with field name",
            dest="nexuspath", default="")

        parser.add_argument(
            "-g", "--strategy",
            help="writing strategy, i.e. "
            "STEP, INIT, FINAL, POSTRUN",
            dest="strategy", default="STEP")
        parser.add_argument(
            "-s", "--datasource-prefix",
            help="datasource-prefix or datasourcename",
            dest="datasource", default="")
        parser.add_argument(
            "-t", "--type",
            help="nexus type of the field",
            dest="type", default="NX_FLOAT")
        parser.add_argument(
            "-u", "--units",
            help="nexus units of the field",
            dest="units", default="")

        parser.add_argument(
            "-k", "--links", action="store_true",
            default=False, dest="fieldlinks",
            help="create links with field name")

        parser.add_argument(
            "-i", "--source-links", action="store_true",
            default=False, dest="sourcelinks",
            help="create links with datasource name")

        parser.add_argument(
            "-b", "--database", action="store_true",
            default=False, dest="database",
            help="store components in "
            "Configuration Server database")

        parser.add_argument(
            "-r", "--server", dest="server",
            help="configuration server device name")

        parser.add_argument(
            "-c", "--chunk", dest="chunk",
            default="SCALAR", help="chunk format, "
            "i.e. SCALAR, SPECTRUM, IMAGE")

        parser.add_argument(
            "-m", "--minimal-device", action="store_true",
            default=False, dest="minimal",
            help="device name without first '0'")

        parser.add_argument(
            "-e", "--depends",
            help="list of component dependencies separated by ','",
            dest="depends", default="")

        parser.add_argument(
            'args', metavar='component_name',
            type=str, nargs='*',
            help='component names to be created')

        return parser

    def run(self, options):
        """ the main program function

        :param options: parser options
        :type options: :class:`argparse.Namespace`
        """
        args = options.args or []
        parser = self._parser
        if options.database and not options.server:
            if not PYTANGO:
                sys.stderr.write("Info: No PyTango installed\n")
                sys.stderr.flush()
                sys.exit(255)

            options.server = checkServer()
            if not options.server:
                parser.print_help()
                sys.exit(0)

        if options.database:
            print("CONFIG SERVER: %s" % options.server)
        else:
            print("OUTPUT DIRECTORY: %s" % options.directory)

        creator = ComponentCreator(options, args)
        try:
            creator.create()
        except WrongParameterError as e:
            sys.stderr.write(str(e))
            sys.stderr.flush()
            parser.print_help()
            sys.exit(255)


class SECoPCP(Runner):

    """ secop component runner"""
    #: (:obj:`str`) command description
    description = "create secop components"
    #: (:obj:`str`) command epilog
    epilog = "" \
        + " * with -b: components are created (without datasources)" \
        + " in Configuration Server database\n" \
        + " * without -b: components are created (without datasources)" \
        + " on the local filesystem in -d <directory> \n" \
        + " * default: <directory> is '.' \n" \
        + "            <port> is 5001\n" \
        + "\n" \
        + " examples:\n" \
        + "\n" \
        + "       nxscreate secopcp \n" \
        + "       nxscreate secopcp -l \n" \
        + "\n" \
        + "           - list all modules of the given node \n" \
        + "\n" \
        + "       nxscreate secopcp -c temp_node -d . -j secopn_node.json \n" \
        + "\n" \
        + "           - create the all secop components" \
        + " in the local directory for the node configured" \
        + " with the json file \n" \
        + "\n" \
        + "       nxscreate secopcp T -t 5001 -b \n" \
        + "\n" \
        + "           - create the component for the T secop module " \
        + " in the NXSConfigServer database for the node on the port 5000 \n" \
        + "\n" \
        + "       nxscreate secopcp -d /home/user/xmldir/ \n" \
        + "\n" \
        + "           - create the all secop components" \
        + " in the given directory\n" \
        + "\n"

    def create(self):
        """ creates parser
        """
        parser = self._parser
        parser.add_argument("-l", "--list", action="store_true",
                            default=False, dest="listmodules",
                            help="list modules of the given node")
        parser.add_argument("-o", "--overwrite", action="store_true",
                            default=False, dest="overwrite",
                            help="overwrite existing components")
        parser.add_argument("-a", "--can-fail", action="store_true",
                            default=False, dest="canfail",
                            help="can fail strategy flag")
        parser.add_argument("-q", "--dynamic", action="store_true",
                            default=False, dest="dynamiclinks",
                            help="create dynamic links")
        parser.add_argument("--sample-nxdata", action="store_true",
                            default=False, dest="samplenxdata",
                            help="create NXdata in NXsample")
        parser.add_argument("-c", "--component",
                            help="component name" +
                            "secop component name",
                            dest="component", default="")
        parser.add_argument("-e", "--param-strategy",
                            help="sensor parameter strategy, " +
                            "i.e. INIT, STEP or FINAL, " +
                            "default: INIT",
                            dest="paramstrategy", default="INIT")
        parser.add_argument("-g", "--strategy",
                            help="sensor value strategy, " +
                            "i.e. INIT, STEP or FINAL, " +
                            "default: INIT",
                            dest="strategy", default="INIT")
        parser.add_argument("-m", "--timeout",
                            help="sensor minimum timeout " +
                            "default: 0.001",
                            dest="timeout", default=0.001)
        parser.add_argument("-s", "--sample",
                            help="sample name",
                            dest="samplename", default="sample")
        parser.add_argument("-w", "--sample-environment",
                            help="sample environment name",
                            dest="sampleenvname",
                            default="sample_environment")
        parser.add_argument("-k", "--links",
                            help="NXlog links of physical "
                            "quantities to sensors "
                            "separated by comman. Default: "
                            "'temperature,magnetic_field,"
                            "electric_field,"
                            "stress_field,pressure'",
                            dest="meanings",
                            default="temperature,magnetic_field,"
                            "electric_field,"
                            "stress_field,pressure")
        parser.add_argument("-v", "--environments",
                            help="NXenvironment links of physical quantities "
                            "separated by comman. "
                            "Default: 'temperature,magnetic_field'",
                            dest="environments",
                            default="temperature,magnetic_field")
        parser.add_argument("-f", "--first",
                            help="first linked targets separated by comman",
                            dest="first", default="")
        parser.add_argument(
            "-z", "--transformation-attributes", dest="transattrs",
            default='{"rotation_z":'
            '{"transformation_type":"rotation","vector":[0,1,0]}}',
            help=("a JSON dictionary with transformation parameters i.e, "
                  '"transformation_type", "vector", "depends_on".'
                  ' Default: {"rotation_z":'
                  '{"transformation_type":"rotation","vector":[0,1,0]}}'))
        parser.add_argument("-p", "--xml-package", dest="xmlpackage",
                            help="xml template package")
        parser.add_argument("-y", "--entryname", dest="entryname",
                            help="entry group name (prefix)", default="scan")
        parser.add_argument("-i", "--insname", dest="insname",
                            help="instrument group name", default="instrument")
        parser.add_argument("-d", "--directory",
                            help="output component directory",
                            dest="directory")
        parser.add_argument("-j", "--json-file",
                            help="json configuration file",
                            dest="json")
        parser.add_argument("-x", "--file-prefix",
                            help="file prefix, i.e. counter",
                            dest="file", default="")
        parser.add_argument("-n", "--nolower", action="store_false",
                            default=True, dest="lower",
                            help="do not change aliases into lower case")

        parser.add_argument("-b", "--database", action="store_true",
                            default=False, dest="database",
                            help="store components in "
                            "Configuration Server database")
        parser.add_argument("-u", "--host",
                            help="secop host name",
                            dest="host", default="")
        parser.add_argument("-t", "--port",
                            help="secop host port",
                            dest="port", default="5000")
        parser.add_argument("-r", "--server", dest="server",
                            help="configuration server device name")

        parser.add_argument('args', metavar='component_name',
                            type=str, nargs='*',
                            help='component names to be created')

        return parser

    def run(self, options):
        """ the main program function

        :param options: parser options
        :type options: :class:`argparse.Namespace`
        """
        args = options.args or []
        parser = self._parser
        if options.database and not options.server:
            if not PYTANGO:
                sys.stderr.write("Info: No PyTango installed\n")
                sys.stderr.flush()
                sys.exit(255)

            options.server = checkServer()
            if not options.server:
                parser.print_help()
                sys.exit(0)

        if not options.listmodules:
            if not options.database and not options.directory:
                options.listmodules = True
            elif options.database:
                print("CONFIG SERVER: %s" % options.server)
            else:
                print("OUTPUT DIRECTORY: %s" % options.directory)

        creator = SECoPCPCreator(options, args)
        try:
            if options.listmodules:
                modules = creator.listmodules()
                if modules:
                    print("MODULES:\n %s" % " ".join(modules))
            else:
                creator.create()
        except WrongParameterError as e:
            sys.stderr.write(str(e))
            sys.stderr.flush()
            parser.print_help()
            sys.exit(255)


class ClientDS(Runner):

    """ clientds runner"""
    #: (:obj:`str`) command description
    description = "create client datasources"

    #: (:obj:`str`) command epilog
    epilog = "" \
             + "\n" \
             + " * with -b: datasources are created" \
             + " in Configuration Server database\n" \
             + " * without -b: datasources are created" \
             + " on the local filesystem in -d <directory> \n" \
             + " * default: <directory> is '.' \n" \
             + "            <server> is taken from Tango DB\n" \
             + "\n" \
             + " examples:\n" \
             + "\n" \
             + "       nxscreate clientds starttime -b  \n" \
             + "\n" \
             + "           - create the 'starttime' datasource " \
             + "of the 'CLIENT' type with the 'starttime' record name\n" \
             + "               and upload them to the NXSConfigServer " \
             + "database \n" \
             + "\n" \
             + "       nxscreate clientds title -d /home/user/xmldir \n" \
             + "\n" \
             + "           - create the 'title' datasource " \
             + "of the 'CLIENT' type with the 'title' record name\n" \
             + "               in the '/home/user/xmldir' directory\n" \
             + "\n" \
             + "       nxscreate clientds -v exp_c -f1 -l4 -b  \n" \
             + "\n" \
             + "           - create the 'exp_c01', 'exp_c02', " \
             "'exp_c03', 'exp_c04' datasources " \
             + "of the 'CLIENT' type\n" \
             + "               with the corresponding 'exp_c0? " \
             + "record names\n" \
             + "               and upload them to the NXSConfigServer " \
             + "database \n" \
             + "               where '?' is 1, 2, 3, 4 respectively \n" \
             + "\n" \
             + "       nxscreate clientds -v " \
             + "hasppXX:10000/expchan/vfcadc_exp/" \
             + " -f5 -l8  -m -b -s exp_vfc\n" \
             + "\n" \
             + "           - create the 'exp_vfc05', 'exp_vfc06', " \
             "'exp_vfc07', 'exp_vfc08' datasources " \
             + "of the 'CLIENT' type\n" \
             + "               with the corresponding " \
             + "'hasppXX:10000/expchan/vfcadc_exp/?' record names\n" \
             + "               and upload them to the NXSConfigServer " \
             + "database \n" \
             + "               where '?' is 5, 6, 7, 8 respectively \n" \
             + "\n"

    def create(self):
        """ parser creator
        """
        parser = self._parser
        parser.add_argument("-v", "--device-prefix",
                            help="device prefix, i.e. exp_c "
                            "(mandatory w/o <name1>)",
                            dest="device", default="")
        parser.add_argument("-f", "--first",
                            help="first index (mandatory w/o <name1>)",
                            dest="first", default="1")
        parser.add_argument("-l", "--last",
                            help="last index (mandatory w/o <name1>)",
                            dest="last", default=None)

        parser.add_argument("-o", "--overwrite", action="store_true",
                            default=False, dest="overwrite",
                            help="overwrite existing datasources")
        parser.add_argument("-d", "--directory",
                            help="output datasource directory",
                            dest="directory", default=".")
        parser.add_argument("-x", "--file-prefix",
                            help="file prefix, i.e. counter",
                            dest="file", default="")

        parser.add_argument("-s", "--datasource-prefix",
                            help="datasource prefix, i.e. counter"
                            " (useful for avoiding duplicated "
                            "datasource names)",
                            dest="dsource", default="")

        parser.add_argument("-b", "--database", action="store_true",
                            default=False, dest="database",
                            help="store datasources in "
                            "Configuration Server database")
        parser.add_argument("-m", "--minimal-device", action="store_true",
                            default=False, dest="minimal",
                            help="device name without first '0'")

        parser.add_argument("-r", "--server", dest="server",
                            help="configuration server device name")

        parser.add_argument('args', metavar='device_name',
                            type=str, nargs='*',
                            help='device names to create')

    def run(self, options):
        """ the main program function

        :param options: parser options
        :type options: :class:`argparse.Namespace`
        """

        parser = self._parser
        if options.database and not options.server:
            if not PYTANGO:
                sys.stderr.write("Info: No PyTango installed\n")
                sys.stderr.flush()
                sys.exit(255)

            options.server = checkServer()
            if not options.server:
                parser.print_help()
                sys.exit(0)

        if options.database:
            print("CONFIG SERVER: %s" % options.server)
        else:
            print("OUTPUT DIRECTORY: %s" % options.directory)

        creator = ClientDSCreator(options, options.args or [])
        try:
            creator.create()
        except WrongParameterError as e:
            sys.stderr.write(str(e))
            sys.stderr.flush()
            parser.print_help()
            sys.exit(255)


def _supportoldcommands():
    """ replace the old command names to the new ones
    """

    oldnew = {
        'compare': 'cmp_onlinexml',
    }

    if sys.argv and len(sys.argv) > 1:
        if sys.argv[1] in oldnew.keys():
            sys.argv[1] = oldnew[sys.argv[1]]


def main():
    """ the main program function
    """
    description = " Command-line tool for creating NXSConfigServer" \
                  + " configuration of Nexus Files"

    # _supportoldcommands()

    epilog = 'For more help:\n  nxscreate <sub-command> -h'
    parser = NXSArgParser(
        description=description, epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.cmdrunners = [('clientds', ClientDS),
                         ('tangods', TangoDS),
                         ('deviceds', DeviceDS),
                         ('onlinecp', OnlineCP),
                         ('onlineds', OnlineDS),
                         ('poolds', PoolDS),
                         ('stdcomp', StdComp),
                         ('comp', Comp),
                         ('secopcp', SECoPCP),
                         ('compare', Compare)]
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

    runners[options.subparser].run(options)


if __name__ == "__main__":
    main()
