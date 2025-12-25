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
# \package ndtstools tools for nxs
# \file nxsxml.py
# creator of XML files

"""  Creator of XML configuration files """


from nxstools.nxsxml import (
    XMLFile, NGroup, NDSource, NField, NDimensions, NLink)


# the main function
def main():
    # handler to XML file
    df = XMLFile("test.xml")
    # entry
    en = NGroup(df, "entry1", "NXentry")
    # instrument
    ins = NGroup(en, "instrument", "NXinstrument")
    #    NXsource
    src = NGroup(ins, "source", "NXsource")
    # field
    f = NField(src, "distance", "NX_FLOAT")
    f.setUnits("m")
    f.setText("100.")

    f = NField(src, "single_mysql_record_string", "NX_CHAR")
    # dimensions
    d = NDimensions(f, "1")
    d.dim("1", "1")
    # source
    f.setStrategy("STEP")
    sr = NDSource(f)
    sr.initDBase("single_mysql_record_string", "MYSQL",
                 "SELECT pid FROM device limit 1", "tango",
                 "SPECTRUM", host="haso228k.desy.de")

    f = NField(src, "single_mysql_record_int", "NX_INT")
    # dimensions
    d = NDimensions(f, "1")
    d.dim("1", "1")
    # source
    f.setStrategy("STEP")
    sr = NDSource(f)
    sr.initDBase("single_mysql_record_int", "MYSQL",
                 "SELECT pid FROM device limit 1", "tango",
                 "SPECTRUM", host="haso228k.desy.de")

    f = NField(src, "mysql_record", "NX_CHAR")
    # dimensions
    d = NDimensions(f, "2")
    d.dim("1", "151")
    d.dim("2", "2")
    # source
    f.setStrategy("STEP")
    sr = NDSource(f)
    sr.initDBase("mysql_record", "MYSQL",
                 "SELECT name, pid FROM device limit 151",
                 "tango", "IMAGE", host="haso228k.desy.de")

    f = NField(src, "pgsql_record", "NX_CHAR")
    # dimensions
    d = NDimensions(f, "2")
    d.dim("1", "3")
    d.dim("2", "5")
    # source
    f.setStrategy("STEP")
    sr = NDSource(f)
    sr.initDBase("pgsql_record", "PGSQL", "SELECT * FROM weather limit 3",
                 "mydb", "IMAGE")

    f = NField(src, "oracle_record", "NX_CHAR")
    # dimensions
    d = NDimensions(f, "1")
    d.dim("1", "19")
    # source
    f.setStrategy("STEP")
    sr = NDSource(f)
    sr.initDBase(
        "oracle_record", "ORACLE",
        "select * from (select * from telefonbuch) where ROWNUM <= 19",
        user='read', passwd='****', rank="SPECTRUM",
        dsn='(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=dbsrv01.desy.de)'
        '(PORT=1521))(LOAD_BALANCE=yes)(CONNECT_DATA=(SERVER=DEDICATED)'
        '(SERVICE_NAME=desy_db.desy.de)(FAILOVER_MODE=(TYPE=NONE)'
        '(METHOD=BASIC)(RETRIES=180)(DELAY=5))))',
        host="haso228k.desy.de")
    f = NField(src, "type", "NX_CHAR")
    f.setText("Synchrotron X-ray Source")
    f = NField(src, "name", "NX_CHAR")
    f.setText("PETRA-III")
    f.addAttr("short_name", "NX_CHAR", "P3")
#    sr = NDSource(a)
#    sr.initClient("emittance_x", "emittance_x")
    f = NField(src, "probe", "NX_CHAR")
    f.setText("x-ray")
    f = NField(src, "power", "NX_FLOAT")
    f.setUnits("W")
    f.setText("1")
    f.setStrategy("INIT")
    sr = NDSource(f)
    sr.initTango("p09/motor/exp.01", "p09/motor/exp.01", "attribute",
                 "Position", host="haso228k.desy.de", port="10000")
    f = NField(src, "emittance_x", "NX_FLOAT")
    f.setUnits("nm rad")
    f.setText("0.2")
    f.setStrategy("STEP")
    sr = NDSource(f)
    sr.initClient("emittance_x", "emittance_x")
    f = NField(src, "emittance_y", "NX_FLOAT")
    f.setUnits("nm rad")
    f.setText("0.2")
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

    #       NXcrystal
    cr = NGroup(ins, "crystal", "NXcrystal")
    f = NField(cr, "distance", "NX_FLOAT")
    f.setUnits("A")
    f.addDoc("Optimum diffracted wavelength")
    d = NDimensions(f, "1")
    d.dim("1", "10")
    f.setText("1 2 3 4 5 6 7 8 10 12")
    #       NXdetector
    de = NGroup(ins, "detector", "NXdetector")
    f = NField(de, "azimuthal_angle", "NX_FLOAT")
    f.setText("0.1")
    f = NField(de, "beam_center_x", "NX_FLOAT")
    f.setText("0.0001")
    f = NField(de, "beam_center_y", "NX_FLOAT")
    f.setText("-0.00012")
#    f = NField(de, "data", "NX_FLOAT")
    f = NField(de, "data", "NX_UINT32")
    d = NDimensions(f, "2")
#    d.dim("1", "100")
#    d.dim("2", "100")
    d.dim("1", "2")
    d.dim("2", "2")
    f.setStrategy("FINAL")
    sr = NDSource(f)
    sr.initTango("p09/tst/exp.01", "p09/tst/exp.01", "attribute",
                 "MyImageAttribute", host="haso228k.desy.de", port="10000")
    f = NField(de, "distance", "NX_FLOAT")
    f.setText("10.00012")
    f = NField(de, "polar_angle", "NX_FLOAT")
    f.addDoc(""" Optional rotation angle for the case when """
             + """the powder diagram has been obtained"""
             + """through an omega-2theta scan like from a traditional """
             + """single detector powder
      diffractometer""")
    d = NDimensions(f, "1")
    d.dim("1", "100")
    f.setText(" ".join([str(il) for il in range(100)]))
    f = NField(de, "rotation_angle", "NX_FLOAT")
    f.setText("0.0")
    f = NField(de, "x_pixel_size", "NX_FLOAT")
    f.setText("0.01")
    f = NField(de, "y_pixel_size", "NX_FLOAT")
    f.setText("0.01")
    f.setStrategy("FINAL")
    sr = NDSource(f)
    sr.initTango("p09/motor/exp.01", "p09/motor/exp.01", "attribute",
                 "Position", host="haso228k.desy.de", port="10000")

    #    NXdata
    da = NGroup(en, "data", "NXdata")
    # link
    ln = NLink(da, "polar_angle",
               "/NXentry/NXinstrument/NXdetector/polar_angle")
    ln.addDoc("Link to polar angle in /NXentry/NXinstrument/NXdetector")
    ln = NLink(da, "data", "/NXentry/NXinstrument/NXdetector/data")
    ln.addDoc("Link to data in /NXentry/NXinstrument/NXdetector")

    df.dump()


if __name__ == "__main__":
    main()

#  LocalWords:  usr
