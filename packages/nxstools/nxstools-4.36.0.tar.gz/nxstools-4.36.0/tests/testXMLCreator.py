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
# \package ndtstools tools for ndts
# \file testXMLCreator.py
# test of XML file creator

from nxstools.nxsxml import (
    XMLFile, NGroup, NDSource, NField, NDimensions, NDeviceGroup)


# the main function
def main():
    df = XMLFile("MNI.xml")

    en = NGroup(df, "entry2", "NXentry")

    ins = NGroup(en, "instrument", "NXinstrument")
#    NXsource
    src = NGroup(ins, "source", "NXsource")
    f = NField(src, "distance", "NX_FLOAT")
    f.setUnits("m")
    f.setText("100.")
    f = NField(src, "db_devices", "NX_CHAR")
    d = NDimensions(f, "2")
    d.dim("1", "151")
    d.dim("2", "2")
    f.setStrategy("STEP")
    sr = NDSource(f)
    sr.initDBase(
        "db_devices", "MYSQL",
        "SELECT name, pid FROM device limit 151", "tango", "IMAGE",
        host="haso228k.desy.de")
    f = NField(src, "type", "NX_CHAR")
    f.setText("Synchrotron X-ray Source")
    f = NField(src, "name", "NX_CHAR")
    f.setText("PETRA-III")
    f.addAttr("short_name", "NX_CHAR", "P3")
    f = NField(src, "probe", "NX_CHAR")
    f.setText("x-ray")
    f = NField(src, "power", "NX_FLOAT")
    f.setUnits("W")
    f.setText("1")
#    sr = NDSource(f)
#    sr.initTango("p09/motor/exp.01","p09/motor/exp.01", "attribute",
#                 "power", host="haso228k.desy.de", port="10000")
    f = NField(src, "emittance_x", "NX_FLOAT")
    f.setUnits("nm rad")
    f.setText("0.2")
    f.setStrategy("STEP")
    sr = NDSource(f)
    sr.initClient("emittance_x", "emittance_x")
    f = NField(src, "emittance_y", "NX_FLOAT")
    f.setUnits("nm rad")
    f.setText("0.2")
#    sr = NDSource(f)
#    f.setStrategy("STEP")
#    sr.initSardana("door1","door1", "emittance_y",
#             host="haso228k.desy.de", port="10000");
    f = NField(src, "sigma_x", "NX_FLOAT")
    f.setUnits("nm")
    f.setText("0.1")
    f = NField(src, "sigma_y", "NX_FLOAT")
    f.setUnits("nm")
    f.setText("0.1")
    f = NField(src, "flux", "NX_FLOAT")
    f.setUnits("s-1 cm-2")
    f.setText("0.1")
    f = NField(src, "energy", "NX_FLOAT")
    f.setUnits("GeV")
    f.setText("0.1")
    f = NField(src, "current", "NX_FLOAT")
    f.setUnits("A")
    f.setText("10")
    f = NField(src, "voltage", "NX_FLOAT")
    f.setUnits("V")
    f.setText("10")
    f = NField(src, "period", "NX_FLOAT")
    f.setUnits("microseconds")
    f.setText("1")
    f = NField(src, "target_material", "NX_CHAR")
    f.setText("C")
# any source/facility related messages/events
# that occurred during the experiment
    # g =
    NGroup(src, "notes", "NXnote")
# For storage rings, description of the bunch
# pattern. This is useful to describe irregular
# bunch patterns.
# See table: NXsource: NXsource/bunch_pattern:NXdata
    # g =
    NGroup(src, "bunch_pattern", "NXdata")
    f = NField(src, "number_of_bunches", "NX_INT")
    f.setText("1")
    f = NField(src, "bunch_length", "NX_FLOAT")
    f.setUnits("s")
    f.setText("1")
    f = NField(src, "bunch_distantce", "NX_FLOAT")
    f.setUnits("s")
    f.setText("1")
    f = NField(src, "bunch_width", "NX_FLOAT")
    f.setUnits("s")
    f.setText("2")
    # source pulse shape
    # g =
    NGroup(src, "pulse_shape", "NXdata")
    f = NField(src, "mode", "NX_CHAR")
    f.setText("Single Bunch")
    f = NField(src, "top_up", "NX_BOOLEAN")
    f.setText("1")

    src.setText("My source")
    #    mot1 = NDeviceGroup(ins, "p09/motor/exp.01", "motor1",
    #                  "NXpositioner", commands=False)
    mot1 = NDeviceGroup(ins, "p09/motor/exp.01", "motor1", "NXpositioner",
                        commands=False,
                        blackAttrs=["PositionEncoder", "PositionEncoderRaw"])
    mot2 = NDeviceGroup(ins, "p09/motor/exp.02", "motor2", "NXpositioner",
                        commands=False,
                        blackAttrs=["PositionEncoder", "PositionEncoderRaw"])
    # mca =
    NDeviceGroup(ins, "p09/mca/exp.02", "mca2", "NXdetector")
    # cnt =
    NDeviceGroup(ins, "p09/counter/exp.02", "counter", "NXmonitor")
    # dac =
    NDeviceGroup(ins, "p09/dac/exp.02", "dac", "NXsensor")
    # adc =
    NDeviceGroup(ins, "p09/adc/exp.02", "adc", "NXsensor")
    # vfc =
    NDeviceGroup(ins, "p09/vfc/exp.02", "vfcadc", "NXsensor")
    # dgg2 =
    NDeviceGroup(ins, "p09/dgg2/exp.01", "dgg2", "NXmonitor")
    tst = NGroup(en, "tst", "NXinstrument")
    mot1.setText("My motor1")
    mot2.setText("My motor1")

    NDeviceGroup(tst, "p09/tst/exp.01", "Tst", "NXmonitor")

    df.dump()


if __name__ == "__main__":
    main()
