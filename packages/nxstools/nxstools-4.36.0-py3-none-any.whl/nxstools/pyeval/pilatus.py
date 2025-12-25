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

"""  pyeval helper functions for pilatus """


def mxparameters_cb(commonblock, mxparameters, name,
                    entryname="scan", insname="instrument"):
    """ code for mxparameters_cb  datasource

    :param commonblock: commonblock of nxswriter
    :type commonblock: :obj:`dict`<:obj:`str`, `any`>
    :param mxparameters:  mx parameters string
    :type mxparameters: :obj:`str`
    :param name: detector name
    :type name: :obj:`str`
    :param entryname: entry name
    :type entryname: :obj:`str`
    :param insname: instrument name
    :type instruement_str: :obj:`str`
    :returns: file start number  - number of frames
    :rtype: :obj:`str`
    """
    pars = mxparameters
    # pars = "# Wavelength 1.03320 A\r\n" \
    #      + "# Detector_distance 0.32200 m\r\n" \
    #      + "# Beam_xy (1261.00, 1242.00) pixels\r\n" \
    #      + "# Filter_transmission 0.1000\r\n" \
    #      + "# Start_angle 204.9240 deg.\r\n" \
    #      + "# Angle_increment 0.1000 deg.\r\n# Phi 404.0470 deg.\r"
    result = pars
    try:
        spars = pars.split("\n")
        tpars = [pr.replace("# ", "").replace("\r", "") for pr in spars]
        tspars = [pr.split(" ") for pr in tpars]
        res = {}
        params = {
            "wavelength": "wavelength",
            "detector_distance": "distance",
            "beam_x": "beam_center_x",
            "beam_y": "beam_center_y",
            "beam_xy": ["beam_center_x", "beam_center_y"]
        }
        for pr in tspars:
            try:
                res[pr[0].lower()] = eval(" ".join(pr[1:]))
            except Exception:
                try:
                    res[pr[0].lower()] = tuple(
                        [eval(" ".join(pr[1:-1])), pr[-1]])
                except Exception:
                    res[pr[0].lower()] = tuple(
                        [" ".join(pr[1:-1]), pr[-1]])
        if res and "__root__" in commonblock.keys():
            root = commonblock["__root__"]
            en = root.open(entryname)
            ins = en.open(insname)
            det = ins.open(name)
            for pname, fname in params.items():
                if pname in res.keys():
                    val = res[pname]
                    if isinstance(val, tuple):
                        val, units = val
                    else:
                        units = ""
                    if not isinstance(val, tuple) and \
                       not isinstance(val, list):
                        fld = det.create_field(fname, "float64")
                        fld.write(val)
                        if units:
                            fld.attributes.create(
                                "units", "string").write(units)
                    elif isinstance(fname, tuple) or isinstance(fname, list):
                        if len(fname) == len(val):
                            for i, fn in enumerate(fname):
                                fld = det.create_field(str(fn), "float64")
                                vl = val[i]
                                fld.write(float(vl))
                                if units:
                                    fld.attributes.create(
                                        "units", "string").write(units)
    except Exception as e:
        # pass
        result += str(e)
    return result


def postrun(commonblock, filestartnum, filedir, nbframes,
            filepostfix, fileprefix,
            filestartnum_str):
    """ code for postrun  datasource

    :param commonblock: commonblock of nxswriter
    :type commonblock: :obj:`dict`<:obj:`str`, `any`>
    :param filestartnum:  file start number
    :type filestartnum: :obj:`int`
    :param filedir: file directorentry name
    :type filedir: :obj:`str`
    :param nbframes: number of frams
    :type nbframes: :obj:`int`
    :param filepostfix: file postfix
    :type filepostfix: :obj:`str`
    :param fileprefix: file prefix
    :type fileprefix: :obj:`str`
    :param filestartnum_str: filestartnum string
    :type filestartnum_str: :obj:`str`
    :returns: postrun string
    :rtype: :obj:`str`
    """
    unixdir = (filedir).replace("\\", "/")
    if len(unixdir) > 1 and unixdir[1] == ":":
        unixdir = "/data" + unixdir[2:]
    if unixdir and unixdir[-1] == "/":
        unixdir = unixdir[:-1]
    filestartnumber = commonblock[filestartnum_str] - 1
    result = "" + unixdir + "/" + fileprefix + "%05d"
    result += filepostfix + ":"
    filelastnumber = filestartnum - 1
    if "__root__" in commonblock.keys():
        root = commonblock["__root__"]
        if hasattr(root, "currentfileid") and hasattr(root, "stepsperfile"):
            spf = root.stepsperfile
            cfid = root.currentfileid
            if spf > 0 and cfid > 0:
                filelastnumber = min(
                    filestartnum + cfid * nbframes * spf - 1, filelastnumber)
                filestartnumber = filestartnumber + (cfid - 1) * nbframes * spf
    result += str(filestartnumber) + ":" + str(filelastnumber)
    return result
