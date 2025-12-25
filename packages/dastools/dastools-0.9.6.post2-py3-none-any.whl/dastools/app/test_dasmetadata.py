#!/usr/bin/env python3

###################################################################################################
# (C) 2021 Helmholtz Centre Potsdam GFZ German Research Centre for Geosciences, Potsdam, Germany  #
#                                                                                                 #
# This file is part of dastools.                                                                  #
#                                                                                                 #
# dastools is free software: you can redistribute it and/or modify it under the terms of the GNU  #
# General Public License as published by the Free Software Foundation, either version 3 of the    #
# License, or (at your option) any later version.                                                 #
#                                                                                                 #
# dastools is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without   #
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU   #
# General Public License for more details.                                                        #
#                                                                                                 #
# You should have received a copy of the GNU General Public License along with this program. If   #
# not, see https://www.gnu.org/licenses/.                                                         #
###################################################################################################

"""Tests to check that dasmetadata.py is working

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.

   :Copyright:
       2019-2025 GFZ Helmholtz Centre for Geosciences, Potsdam, Germany
   :License:
       GPLv3
   :Platform:
       Linux

.. moduleauthor:: Javier Quinteros <javier@gfz.de>, GEOFON, GFZ Potsdam
"""
import datetime
from click.testing import CliRunner
from dastools.app.dasmetadata import printmetadata
from dastools.app.dasmetadata import create
import json
import xml.etree.ElementTree as ET
import os
from io import StringIO

"""Test the functionality of dasmetadata.py

"""


def test_create_optodas_json():
    """Create a JSON metadata structure for an OptoDAS dataset"""
    # runner = CliRunner()
    output = os.popen('dasmetadata create --directory . --experiment example --inputfmt optodas').read()
    # result = runner.invoke(create, ['--directory', '.', '--experiment', 'example', '--inputfmt', 'optodas'])
    # assert result.exit_code == 0
    data = json.loads(output)
    assert data['network_code'] == 'XX'
    assert data['start_date'] == "2022-04-22"
    assert data['end_date'] == "2022-04-22"
    assert data['interrogators'][0]['manufacturer'] == 'Alcatel'
    assert data['interrogators'][0]['acquisitions'][0]["acquisition_start_time"] == "2022-04-22T07:55:50"
    assert data['interrogators'][0]['acquisitions'][0]["acquisition_end_time"] == "2022-04-22T07:55:59.987500"
    # Test ChannelGroup
    acq = data['interrogators'][0]['acquisitions'][0]
    assert len(acq['channel_groups']) == 1
    chgrp = acq['channel_groups'][0]
    assert chgrp['coordinate_generation_date'][:10] == datetime.date.today().isoformat()[:10]
    assert len(chgrp['channels']) == 12500
    # Check that the distance is close to 1.0213001907746815
    assert 1.021 <= chgrp['channels'][1]['distance_along_fiber'] <= 1.022


def test_create_febus_json():
    """Create a JSON metadata structure for a Febus dataset"""
    # runner = CliRunner()
    output = os.popen('dasmetadata create --directory febus --experiment SR_DS --inputfmt febus').read()
    # result = runner.invoke(create, ['--directory', '.', '--experiment', 'example', '--inputfmt', 'optodas'])
    # assert result.exit_code == 0
    data = json.loads(output)
    assert data['network_code'] == 'XX'
    assert data['start_date'] == "2024-02-16"
    assert data['end_date'] == "2024-02-16"
    assert data['interrogators'][0]['manufacturer'] == 'Febus'
    assert data['interrogators'][0]['acquisitions'][0]["acquisition_start_time"] == "2024-02-16T13:45:47"
    assert data['interrogators'][0]['acquisitions'][0]["acquisition_end_time"] == "2024-02-16T14:04:19.999900"
    # Test ChannelGroup
    acq = data['interrogators'][0]['acquisitions'][0]
    assert len(acq['channel_groups']) == 1
    chgrp = acq['channel_groups'][0]
    assert chgrp['coordinate_generation_date'][:10] == datetime.date.today().isoformat()[:10]
    assert len(chgrp['channels']) == 100
    # Check that the distance is close to 1.0213001907746815
    assert 9.59 <= chgrp['channels'][1]['distance_along_fiber'] <= 9.61


def test_create_optodas_xml():
    """Create StationXML metadata for an OptoDAS dataset"""
    # runner = CliRunner()
    output = os.popen('dasmetadata create --directory . --experiment example --inputfmt optodas --outputfmt stationxml').read()
    root = ET.fromstring(output)

    ns = {'fdsn': 'http://www.fdsn.org/xml/station/1'}
    net = root.find('fdsn:Network', ns)
    assert net.attrib['code'] == 'XX'
    assert net.attrib['startDate'] == "2022-04-22"
    assert net.attrib['endDate'] == "2022-04-22"

    sta = net.find('fdsn:Station', ns)
    assert sta.attrib['code'] == 'A0000'
    assert sta.attrib['startDate'].startswith('2022-04-22T07')
    assert sta.find('fdsn:Latitude', ns).text == '0.0'

    doi = net.find('fdsn:Identifier', ns)
    assert doi.attrib['type'] == 'DOI'
    assert doi.text == '10.XXXX/COMPLETE!'


def test_create_tdms_json():
    """Create a JSON metadata structure for a TDSM dataset"""
    # runner = CliRunner()
    output = os.popen('dasmetadata create --directory . --experiment PDN_1km --inputfmt tdms').read()
    data = json.loads(output)
    assert data['network_code'] == 'XX'
    assert data['start_date'] == "2018-09-05"
    assert data['end_date'] == "2018-09-05"
    assert data['interrogators'][0]['manufacturer'] == 'Silixa'
    assert data['interrogators'][0]['acquisitions'][0]["acquisition_start_time"] == "2018-09-05T09:55:03.298000"
    assert data['interrogators'][0]['acquisitions'][0]["acquisition_end_time"] == "2018-09-05T09:57:03.297000"
    # Test ChannelGroup
    acq = data['interrogators'][0]['acquisitions'][0]
    assert len(acq['channel_groups']) == 1
    chgrp = acq['channel_groups'][0]
    assert chgrp['coordinate_generation_date'][:10] == datetime.date.today().isoformat()[:10]
    assert len(chgrp['channels']) == 768
    # Check that the distance is close to 121.024209
    assert 121.02 <= chgrp['channels'][1]['distance_along_fiber'] <= 121.03


def test_create_tdms_xml():
    """Create StationXML metadata for a TDMS dataset"""
    # runner = CliRunner()
    output = os.popen('dasmetadata create --directory . --experiment PDN_1km --inputfmt tdms --outputfmt stationxml').read()
    root = ET.fromstring(output)
    ns = {'fdsn': 'http://www.fdsn.org/xml/station/1'}

    net = root.find('fdsn:Network', ns)
    assert net.attrib['code'] == 'XX'
    assert net.attrib['startDate'] == "2018-09-05"
    assert net.attrib['endDate'] == "2018-09-05"

    sta = net.find('fdsn:Station', ns)
    assert sta.attrib['code'] == 'A0000'
    assert sta.find('fdsn:Latitude', ns).text == '37.7659174'
    assert sta.find('fdsn:Longitude', ns).text == '15.0168435'

    doi = net.find('fdsn:Identifier', ns)
    assert doi.attrib['type'] == 'DOI'
    assert doi.text == '10.XXXX/COMPLETE!'


def test_create_empty():
    """Create an empty JSON metadata structure"""
    # runner = CliRunner()
    # result = runner.invoke(create, ['--empty'])
    output = os.popen('dasmetadata create --empty').read()
    data = json.loads(output)
    assert 'network_code' in data.keys()
    assert 'principal_investigator' in data.keys()
    assert 'interrogators' in data.keys()
    assert 'acquisitions' in data['interrogators'][0]
    assert 'cables' in data.keys()
    assert 'fibers' in data['cables'][0]


def test_showraw_optodas():
    """Print raw metadata from an OptoDAS dataset"""
    output = os.popen('dasmetadata showraw --directory . --experiment example --inputfmt optodas').read()
    for line in output.splitlines():
        if "'dimensionSizes': array([  800, 12500])" in line:
            break
    else:
        raise Exception('dimensionSizes has a wrong value')

    for line in output.splitlines():
        if "'dt': np.float64(0.0125)" in line:
            break
    else:
        raise Exception('dimensionSizes has a wrong value')


def test_showraw_tdms():
    """Print raw metadata from an TDMS dataset"""
    output = os.popen('dasmetadata showraw --directory . --experiment PDN_1km --inputfmt tdms').read()
    for line in output.splitlines():
        if "'StartPosition[m]': 119." in line:
            break
    else:
        raise Exception('StartPosition has a wrong value')

    for line in output.splitlines():
        if "'name': 'PDN_1km_UTC" in line:
            break
    else:
        raise Exception('name has a wrong value')


def test_add_datacite():
    """Add datacite information"""
    output = os.popen('dasmetadata create --empty | dasmetadata add-datacite 10.5880/GFZ.2.2.2023.001').read()
    data = json.loads(output)
    assert data['purpose_of_data_collection'].startswith('Global DAS')
    assert data['digital_object_identifier'] == "10.5880/GFZ.2.2.2023.001"
    assert 'Wollin' in data['principal_investigator'][0]['name']
    assert 52.2 <= data['cables'][0]['cable_bounding_box'][0] <= 52.3
    assert 52.3 <= data['cables'][0]['cable_bounding_box'][1] <= 52.4
    assert 12.9 <= data['cables'][0]['cable_bounding_box'][2] <= 13.0
    assert 13.0 <= data['cables'][0]['cable_bounding_box'][3] <= 13.1


def test_add_coords_tdms_csv():
    """Add coordinates"""
    output = os.popen('dasmetadata create --directory . --experiment PDN_1km --inputfmt tdms | dasmetadata add-coords tests/tdms.csv').read()
    data = json.loads(output)
    channels = data['interrogators'][0]['acquisitions'][0]['channel_groups'][0]['channels']
    assert channels[0]['channel_id'] == 'A0000'
    assert channels[1]['y_coordinate'] == 0.1
    assert channels[2]['x_coordinate'] == -0.2
    assert channels[3]['elevation_above_sea_level'] == 6.0
    # This actually comes from the TDMS, not from the coordinates
    assert channels[4]['distance_along_fiber'] == 127.024209

# TODO Add a test for OptoDAS with coordinates in a KML file


def test_json2datacite():
    output = os.popen('dasmetadata create --empty | dasmetadata add-datacite 10.5880/GFZ.2.2.2023.001 | dasmetadata json2datacite').read()
    root = ET.fromstring(output)
    ns = {'dc': 'http://datacite.org/schema/kernel-4'}
    doi = root.find('dc:identifier', ns)
    assert doi.attrib['identifierType'] == 'DOI'
    assert doi.text == '10.5880/GFZ.2.2.2023.001'
    creators = root.find('dc:creators', ns)
    creator = creators.find('dc:creator', ns)
    cn = creator.find('dc:creatorName', ns)
    assert 'Wollin' in cn.text
    titles = root.find('dc:titles', ns)
    title = titles.find('dc:title', ns)
    assert title.text.startswith('Global DAS')


def test_json2stationxml():
    """Create StationXML metadata from a TDMS dataset"""
    # runner = CliRunner()
    output = os.popen('dasmetadata create --directory . --experiment PDN_1km --inputfmt tdms | dasmetadata add-coords tests/tdms.csv | dasmetadata json2stationxml').read()
    root = ET.fromstring(output)
    ns = {'fdsn': 'http://www.fdsn.org/xml/station/1'}

    net = root.find('fdsn:Network', ns)
    assert net.attrib['code'] == 'XX'
    assert net.attrib['startDate'].startswith("2018-09-05")
    assert net.attrib['endDate'].startswith("2018-09-05")

    for sta in net.findall('fdsn:Station', ns):
        if sta.attrib['code'] == 'A0000':
            continue
        elif sta.attrib['code'] == 'A0001':
            assert sta.find('fdsn:Latitude', ns).text == '0.1'
        elif sta.attrib['code'] == 'A0002':
            assert sta.find('fdsn:Longitude', ns).text == '-0.2'
        elif sta.attrib['code'] == 'A0003':
            assert sta.find('fdsn:Elevation', ns).text == '6.0'
        elif sta.attrib['code'] == 'A0004':
            break

    doi = net.find('fdsn:Identifier', ns)
    assert doi.attrib['type'] == 'DOI'
    assert doi.text == '10.XXXX/COMPLETE!'


def test_printmetadata(capsys):
    out = StringIO()
    printmetadata(('Sampling Rate', '1000'), stream=out)
    assert out.getvalue() == "('Sampling Rate', '1000')\n"

    out = StringIO()
    printmetadata({'Sampling Rate': '1000'}, stream=out)
    assert out.getvalue() == "{'Sampling Rate': '1000'}\n"
