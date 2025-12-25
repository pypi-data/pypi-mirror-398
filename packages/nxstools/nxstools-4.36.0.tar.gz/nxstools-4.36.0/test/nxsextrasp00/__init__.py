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

"""  xml templates """


#: (:obj:`dict` <:obj:`str` , :obj:`dict` <:obj:`str` , :obj:`str` > >)
#:     standard component template variables
#:     and its [default value, doc string]
standardComponentVariables = {
    'collect4': {
        'first': {
            'default': None,
            'doc': "name of the first component to collect MANDATORY"
            " (datasource)"
        },
        'second': {
            'default': None,
            'doc': "name of the second component to collect MANDATORY"
            " (datasource)"
        },
        'third': {
            'default': None,
            'doc': "name of the third component to collect MANDATORY"
            " (datasource)"
        },
        'fourth': {
            'default': None,
            'doc': "name of the fourth component to collect MANDATORY"
            " (datasource)"
        }
    },
    'common4': {
        'dds': {
            'default': None,
            'doc': "default read datasource name MANDATORY (datasource)"
        },
        'ods1': {
            'default': None,
            'doc': "fist optional detasource name MANDATORY (datasource)"
        },
        'ods2': {
            'default': None,
            'doc': "second optional detasource name MANDATORY (datasource)"
        },
        'ods3': {
            'default': None,
            'doc': "third optional detasource name MANDATORY (datasource)"
        }
    },
}

#: (:obj:`dict` <:obj:`str` , :obj:`list` <:obj:`str`> >)
#:     xml template files of modules
standardComponentTemplateFiles = {
    'collect4': [
        'collect4.xml',
    ],
    'common4': [
        'common4_common.ds.xml',
    ],
}

#: (:obj:`dict` <:obj:`str` , :obj:`list` <:obj:`str`> >)
#:     xml template files of modules
moduleTemplateFiles = {
}

#: (:obj:`dict` <:obj:`str` , :obj:`list` <:obj:`str`> >)
#:     important attributes of modules
moduleMultiAttributes = {
    'mca_xia_test': [
        'ICR', 'OCR',
    ],
    'mca_xia@pool_test': [
        'CountsRoI', 'RoIEnd', 'RoIStart',
    ],
    'limaccd_test': [
        'camera_type', 'camera_pixelsize', 'camera_model',
        'acq_mode', 'acq_nb_frames', 'acq_trigger_mode',
        'last_image_saved',
        'latency_time',  'acc_max_expo_time',
        'acc_expo_time', 'acc_time_mode',
        'acc_dead_time', 'acc_live_time',
        'image_width',
        'image_height',
        'image_sizes',
        'image_roi',
        'image_bin',
        'image_flip',
        'image_rotation',
        'shutter_mode',
        'shutter_open_time',
    ],
    'limaccds_test': [
        'camera_type', 'camera_pixelsize', 'camera_model',
        'acq_mode', 'acq_nb_frames', 'acq_trigger_mode',
        'last_image_saved',
        'latency_time', 'acc_max_expo_time',
        'acc_expo_time',  'acc_time_mode',
        'image_type',
        'image_width',
        'image_height',
        'image_sizes',
        'image_roi',
        'image_bin',
        'image_flip',
        'image_rotation',
        'shutter_mode',
        'shutter_open_time',
    ],
    'pco_test': [
        'DelayTime', 'ExposureTime', 'NbFrames', 'TriggerMode',
        'FileDir', 'FilePostfix', 'FilePrefix', 'FileStartNum',
        'CoolingTemp', 'CoolingTempSet', 'ImageTimeStamp',
        'RecorderMode',
    ],
}

#: (:obj:`dict` <:obj:`str` , :obj:`list` <:obj:`str`> >)
#:     xml template files of modules
moduleTemplateFiles = {
    'mymca': [
        'mymca.xml'
    ],
}


#: (:obj:`dict` <:obj:`str` , :obj:`list` <:obj:`str`> >)
#:     important attributes of modules
moduleMultiAttributes = {
    'mymca': [
        'Data', 'Mode',
    ],
}
