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

""" NDTS TANGO device tools """

import sys
import os
import time
import socket

#: (:obj:`dict` <:obj:`str` , :obj:`dict` <:obj:`str` , :obj:`str` > >)
#:     standard component template variables
#:     and its [default value, doc string]
standardComponentVariables = {}
#: (:obj:`dict` <:obj:`str` , :obj:`list` <:obj:`str`> >)
#:     xml template files of modules
standardComponentTemplateFiles = {}
#: (:obj:`dict` <:obj:`str` , :obj:`list` <:obj:`str`> >)
#:     xml template files of modules
moduleTemplateFiles = {}
#: (:obj:`dict` <:obj:`str` , :obj:`list` <:obj:`str`> >)
#:     important attributes of modules
moduleMultiAttributes = {}


class PackageHandler(object):

    """ xml templates package loader
    """

    def __init__(self, packagename='nxstools.xmltemplates'):
        """ constructor

        :param packagename: full package name
        :type packagename: :obj:`str`
        """
        self.packagename = None
        self.package = None
        self.packagepath = None
        self.loadXMLTemplates(packagename)

    def loadXMLTemplates(self, packagename):
        """ load xml template module variables

        :param packagename: full package name
        :type packagename: :obj:`str`
        """
        self.packagename = packagename
        global standardComponentVariables
        global standardComponentTemplateFiles
        global moduleTemplateFiles
        global moduleMultiAttributes
        self.package = __import__(
            packagename, globals(), locals(), packagename[-1])
        standardComponentVariables = \
            self.package.standardComponentVariables
        standardComponentTemplateFiles = \
            self.package.standardComponentTemplateFiles
        moduleTemplateFiles = \
            self.package.moduleTemplateFiles
        moduleMultiAttributes = \
            self.package.moduleMultiAttributes
        self.packagepath = os.path.dirname(self.package.__file__)


#: (:class:`PackageHandler`) xml template package handler
xmlPackageHandler = PackageHandler()


#: attributes of device modules to acquire with elements:
#  'module': [<sardana_pool_attr>, <original_tango_attr>]
moduleAttributes = {
    'counter_tango': ['Value', 'Counts'],
    'v260': ['Value', 'Counts'],
    'dgg2': ['Value', 'SampleTime'],
    'mca_8701': ['Value', 'Data'],
    'mca_sis3302new': ['Value', 'Data'],
    'mca_sis3302': ['Value', 'Data'],
    'mythenroi': ['Value', None],
    'mca8715roi': ['Value', None],
    'sis3302roi': ['Value', None],
    'sis3302': ['Value', None],
    'sis3302multiscan': ['Value', None],
    'sis3610': ['Value', 'Value'],
    'vdot32in': ['Value', 'Value'],
    'sis3820': ['Value', 'Counts'],
    'tangoattributectctrl': ['Value', None],
    'tip551': ['Value', 'Voltage'],
    'tip850dac': ['Value', 'Voltage'],
    'tip830': ['Value', 'Counts'],
    'tip850adc': ['Value', 'Value'],
    'vfcadc': ['Value', 'Counts'],
    'xmcd': ['Value', None],
}

#: attributes of device modules to acquire with elements:
#  'module': {<device_parts[4]>, <tango_attr>}
moduleAttributeMap = {
    'amptekroi': {
        '1': 'CountsRoI1',
        '2': 'CountsRoI2',
        '3': 'CountsRoI3',
        '4': 'CountsRoI4',
        '5': 'CountsRoI5',
        '6': 'CountsRoI6',
        '7': 'CountsRoI7',
        '8': 'CountsRoI8',
    },
}

#: (:obj:`list` <:obj:`str`>) modules of 2d detectors
twoDModules = [
    'pilatus100k', 'pilatus300k', 'pilatus1m',
    'pilatus2m', 'pilatus6m', 'pco4000', 'perkinelmerdetector',
    'lambda', 'pedetector', 'perkinelmer',
    'pco', 'pcoedge', 'marccd', 'perkinelmer',
    #
    'lcxcamera', 'limaccd', 'eigerpsi',
    'eigerdectris'
]


#: (:obj:`list` <:obj:`str`>) modules of motors
motorModules = [
    'absbox', 'motor_tango', 'kohzu', 'smchydra', 'lom', 'oms58', 'e6c',
    'omsmaxv', 'spk', 'pie710', 'pie712', 'e6c_p09_eh2', 'smaract'
    #
    #    'analyzerep01', 'tth', 'atto300',  'phaseretarder',
    #    'hexa',
    #    'tm', 'cube', , 'piezonv40', 'smaractmcs',
    #    'slt', 'bscryotempcontrolp01',
    #    'dcm_energy', 'elom', 'diffracmu',  'tcpipmotor',
    #    'galil_dmc', 'pico8742', 'oxfcryo700ctrl', 'analyzer', 'nfpaxis',
    #    'smarpod', 'mult',
    #
    #    'oxfcryo700',
]

#: (:obj:`list` <:obj:`str`>) counter/timer modules
ctModules = [
    'mca8715roi', 'onedroi', 'sis3820', 'sis3302roi',
    'xmcd', 'vfcadc', 'mythenroi', 'mhzdaqp01', 'dgg2',
    'tangoattributectctrl'
]

#: (:obj:`list` <:obj:`str`>) modules of 0D detectors
zeroDModules = ['tip830']

#: (:obj:`list` <:obj:`str`>) modules of 1D detectors
oneDModules = ['mca_xia']

#: (:obj:`list` <:obj:`str`>) IO register modules
ioRegModules = ['sis3610']


#: (:obj:`bool`) True if tango available
PYTANGO = False
try:
    try:
        import tango
    except Exception:
        import PyTango as tango
    PYTANGO = True
except Exception:
    pass


for mn in motorModules:
    moduleAttributes[mn] = ['Position', 'Position']

for nm in ctModules + zeroDModules + oneDModules:
    if nm not in moduleAttributes:
        moduleAttributes[nm] = ['Value', None]


def generateDeviceNames(prefix, first, last, minimal=False):
    """ generates device names

    :param prefix: device name prefix
    :type prefix: :obj:`str`
    :param first: first device index
    :type first: :obj:`int`
    :param last: last device index
    :type last: :obj:`int`
    :returns: device names
    :rtype: :obj:`list` <:obj:`str`>
    """
    names = []
    if prefix.strip():
        for i in range(first, last + 1):
            if not minimal:
                names.append(prefix + ("0" if len(str(i)) == 1 else "")
                             + str(i))
            else:
                names.append(prefix + str(i))
    return names


def getAttributes(device, host=None, port=10000):
    """ provides a list of device attributes

    :param device: tango device name
    :type device: :obj:`str`
    :param host: device host
    :type host: :obj:`str`
    :param port: device port
    :type port: :obj:`int`
    :returns: list of device attributes
    :rtype: :obj:`list` <:obj:`str`>
    """
    if host:
        dp = tango.DeviceProxy("%s:%s/%s" % (host, port, device))
    else:
        dp = tango.DeviceProxy(device)
    attr = dp.attribute_list_query()
    return [at.name for at in attr if at.name not in ['State', 'Status']]


def openServer(device):
    """ opens connection to the configuration server

    :param configuration: server device name
    :type configuration: :obj:`str`
    :returns: configuration server proxy
    :rtype: :class:`tango.DeviceProxy`
    """
    found = False
    cnt = 0
    # spliting character
    try:
        #: configuration server proxy
        cnfServer = tango.DeviceProxy(device)
    except tango.DevFailed:
        found = True

    if found:
        sys.stderr.write(
            "Error: Cannot connect to the server: %s\n" % device)
        sys.stderr.flush()
        sys.exit(0)

    while not found and cnt < 1000:
        if cnt > 1:
            time.sleep(0.02)
        try:
            if cnfServer.state() != tango.DevState.RUNNING:
                found = True
        except tango.DevFailed:
            time.sleep(0.02)
            found = False
        cnt += 1

    if not found:
        sys.stderr.write("Error: Setting up %s takes to long\n" % device)
        sys.stderr.flush()
        sys.exit(0)

    return cnfServer


def storeDataSource(name, xml, server):
    """ stores datasources in Configuration Server

    :param name: datasource name
    :type name: :obj:`str`
    :param xml: datasource xml string
    :type xml: :obj:`str`
    :param server: configuration server
    :type server: :obj:`str`
    """
    proxy = openServer(server)
    proxy.Open()
    proxy.XMLString = str(xml)
    proxy.StoreDataSource(str(name))


def getServerTangoHost(server):
    """ fetches the server tango_host:tango_port

    :param server: tango server
    :type server: :obj:`str`
    :returns: tango host
    :rtype: :obj:`str`
    """
    if server:
        proxy = openServer(server)
        host = proxy.get_db_host()
        port = proxy.get_db_port()
    else:
        db = tango.Database()
        host = db.get_db_host().split(".")[0]
        port = db.get_db_port()
    shost = str(host).split(".")
    if len(shost) > 0:
        host = shost[0]
    return "%s:%s" % (host, port)


def getDataSourceComponents(server, verbose=False):
    """ gets datasource components

    :param server: configuration server
    :type server: :obj:`str`
    :param verbose: additional printouts
    :type verbose: :obj:`bool`
    :returns: dictionary with datasource components
    :rtype: :obj:`dict` <:obj:`str`, :obj:`list` <:obj:`str`>>
    """
    dscps = {}
    proxy = openServer(server)
    proxy.Open()
    acps = proxy.availableComponents()
    errcps = []
    for cp in acps:
        try:
            depcps = proxy.dependentComponents([cp])
            for dcp in depcps:
                dss = proxy.componentDataSources(dcp)
                for ds in dss:
                    if ds not in dscps:
                        dscps[ds] = []
                    if cp not in dscps[ds]:
                        dscps[ds].append(cp)
        except Exception as e:
            errcps.append(cp)
            if verbose:
                sys.stderr.write(str(e))
                sys.stderr.write(
                    "Error: Internal error of the %s component\n" % cp)
                sys.stderr.flush()
    if not verbose and errcps:
        sys.stderr.write(
            "Info: Inconsistent components is the NeXus database - %s\n"
            % ", ".join(errcps))
        sys.stderr.flush()

    return dscps


def storeComponent(name, xml, server, mandatory=False):
    """ stores components in Configuration Server

    :param name: component name
    :type name: :obj:`str`
    :param xml: component xml string
    :type xml: :obj:`str`
    :param server: configuration server
    :type server: :obj:`str`
    :param mandatory: set component as mandatory
    :type mandatory: :obj:`bool`
    """
    proxy = openServer(server)
    proxy.Open()
    proxy.XMLString = str(xml)
    proxy.StoreComponent(str(name))
    if mandatory:
        proxy.SetMandatoryComponents([str(name)])


def getClassName(devicename):
    """ provides device class name

    :param devicename: device name
    :type devicename: :obj:`str`
    :returns: class name
    :rtype: :obj:`str`
   """
    try:
        db = tango.Database()
    except Exception:
        sys.stderr.write(
            "Info: Cannot connect to %s" % devicename
            + " on host %s\n" % os.environ['TANGO_HOST'])
        sys.stderr.flush()
        return ""

    return db.get_class_for_device(devicename)


def getServers(name='NXSConfigServer'):
    """ provides server device names

    :param name: server instance name
    :type name: :obj:`str`
    :returns: list of the server device names
    :rtype: :obj:`list` <:obj:`str`>
    """

    try:
        db = tango.Database()
    except Exception:
        sys.stderr.write(
            "Error: Cannot connect to %s" % name
            + " on host %s\n" % os.environ['TANGO_HOST'])
        sys.stderr.flush()
        return ""

    servers = db.get_device_exported_for_class(name).value_string
    return servers


def _remoteCall(server, func, *args, **kwargs):
    """ executes function on remove tango host db setup

    :param server: remove tango server device name
    :type server: :obj:`str`
    :param func: executed function
    :type func: :obj:`instancemethod`
    :param args: function list arguments
    :type args: :obj:`list` <`and`>
    :param kwargs: function dict arguments
    :type kwargs: :obj:`dict` <:obj:`str` , `any`>
    :returns: function result
    :rtype: `any`
    """
    lserver = None
    localtango = None
    if server and ":" in server and server.strip():
        lserver = server.split("/")[0]
    if lserver:
        lserver = lserver.strip()
    if lserver:
        if ":" not in lserver:
            lserver = lserver + ":10000"
        localtango = os.environ.get('TANGO_HOST')
        os.environ['TANGO_HOST'] = lserver

    res = func(*args, **kwargs)
    if lserver:
        if localtango is not None:
            os.environ['TANGO_HOST'] = localtango
        else:
            os.environ.pop('TANGO_HOST')
    return res


def listServers(server, name='NXSConfigServer'):
    """ finds server names

    :param name: server instance name
    :type name: :obj:`str`
    :returns: server list
    :rtype: :obj:`list` <:obj:`str`>
    """
    return _remoteCall(server, getServers, name)


def findClassName(server, name):
    """ finds class name

    :param name: device name
    :type name: :obj:`str`
    :returns: class name
    :rtype: :obj:`str`
    """
    return _remoteCall(server, getClassName, name)


def checkServer(name='NXSConfigServer'):
    """ provides server device name if only one or error in the other case

    :param name: server name
    :type name: :obj:`str`
    :returns: server device name or empty string if error appears
    :rtype: :obj:`str`
    """
    servers = getServers(name)
    if not servers:
        sys.stderr.write(
            "Info: NeXus hasn't been setup yet. \n\n")
        sys.stderr.flush()
        return ""
    if len(servers) > 1:
        thost = os.getenv('TANGO_HOST')
        if thost:
            tlhost = thost.split(":")[0]
            tservers = [sr for sr in servers if sr.endswith("/%s" % tlhost)]
            if tservers:
                servers = tservers
            else:
                lhost = socket.gethostname()
                lservers = [sr for sr in servers if sr.endswith("/%s" % lhost)]
                if lservers:
                    servers = lservers
        if len(servers) > 1:
            sys.stderr.write(
                "Info: More than on %s " % name
                + "on the current host running. \n\n"
                + "    Please specify the server:"
                + "\n        %s\n\n" % "\n        ".join(servers))
            sys.stderr.flush()
            return ""
    return servers[0]


if __name__ == "__main__":
    pass
