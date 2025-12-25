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
#

"""  PaNET ontology dictionary """

import json
import os


def read_techniques():
    """ read PaNET ontology techniques to dictionary

    :returns: techniques id:label
    :rtype: :obj:`dict` <:obj:`str`,:obj:`str`>
    """
    result = {}
    with open(os.path.join(os.path.dirname(__file__), "ontology.json")) as fp:
        ont = json.loads(fp.read())
    ott = [on for on in ont
           if "@type" in on
           and 'http://www.w3.org/2002/07/owl#Class' in on["@type"]
           and "@id" in on and
           on["@id"].startswith("http://purl.org/pan-science/PaNET/PaNET")]
    result = {
        ot["@id"]: ot['http://www.w3.org/2000/01/rdf-schema#label'][0][
            "@value"] for ot in ott}
    return result


#: (:obj:`dict` <:obj:`str`,:obj:`str` >)
#:     techniques id:label
id_techniques = read_techniques()

#: (:obj:`dict` <:obj:`str`,:obj:`str` >)
#:     nexus application  to PaNET
nexus_panet = {
    "saxs": "http://purl.org/pan-science/PaNET/PaNET01188",
    "waxs": "http://purl.org/pan-science/PaNET/PaNET01191",
    #     This is a definition for data to be archived by ICAT
    # (http://www.icatproject.org/).
    # "archive": "",
    #     This is an application definition for angular
    # resolved photo electron spectroscopy.
    # "arpes": "",
    #     Implementation of the canSAS standard to store
    # reduced small-angle scattering data of any dimension.
    # "canSAS": "",
    #     This is a application definition for raw data
    # from a direct geometry TOF spectrometer
    # "directtof": "",
    #     This is an application definition for raw data from an
    # X-ray fluorescence experiment
    # "fluo": "",
    #     This is a application definition for raw data from a
    # direct geometry TOF spectrometer
    # "indirecttof": "",
    #     Application definition for any data.
    # "iqproc": "",
    #     This is the application definition for a TOF laue diffractometer
    # "lauetof": "",
    #     Monochromatic Neutron and X-Ray Powder diffractometer
    # "monopd": "",
    #     functional application definition for macromolecular crystallography
    # "mx": "",
    #     This is an application definition for a monochromatic
    # scanning reflectometer.
    # "refscan": "",
    #     This is an application definition for raw data from
    # a TOF reflectometer.
    # "reftof": "",
    #     raw, monochromatic 2-D SAS data with an area detector
    # "sas": "",
    #     raw, 2-D SAS data with an area detector with a time-of-flight source
    # "sastof": "",
    #     Application definition for a generic scan instrument.
    # "scan": "",
    #     NXSPE Inelastic Format. Application definition for NXSPE file format.
    # "spe": "",
    #     This is the application definition for S(Q,OM) processed data.
    # "sqom": "",
    #     Application definition for a STXM instrument.
    # "stxm": "",
    #     This is an application definition for a triple axis spectrometer.
    # "tas": "",
    #     This is a application definition for raw data from
    # a TOF neutron powder diffractometer
    # "tofnpd": "",
    #     This is an application definition for raw data from
    # a generic TOF instrument
    # "tofraw": "",
    #     This is a application definition for raw data from
    # a generic TOF instrument
    # "tofsingle": "",
    #     This is the application definition for x-ray
    # or neutron tomography raw data.
    # "tomo": "",
    #     This is the application definition for x-ray or neutron tomography
    # raw data with phase contrast variation at each point.
    # "tomophase": "",
    #     This is an application definition for the final result of
    # a tomography experiment: a 3D construction of some volume of physical
    # properties.
    # "tomoproc": "",
    #     This is an application definition for raw data from an X-ray
    # absorption spectroscopy experiment.
    # "xas": "",
    #     Processed data from XAS. This is energy versus
    # I(incoming)/I(absorbed).
    # "xasproc": "",
    #     This definition covers the common parts of all monochromatic
    # single crystal raw data application definitions.
    # "xbase": "",
    #     raw data from a four-circle diffractometer with an eulerian
    # cradle, extends xbase
    # "xeuler": "",
    #     raw data from a kappa geometry (CAD4) single crystal
    # diffractometer, extends NXxbase
    # "xkappa": "",
    #     raw data from a single crystal laue camera, extends NXxrot
    # "xlaue": "",
    #     raw data from a single crystal Laue camera, extends NXxlaue
    # "xlaueplate": "",
    #     raw data from a single crystal diffractometer, extends NXxbase
    # "xnb": "",
    #     raw data from a rotation camera, extends NXxbase
    # "xrot": "",
}
