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

"""Tests to check that dasws.py is working

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

from datetime import datetime
from datetime import timedelta
import numpy as np
from obspy import read
import configparser
import os
from io import BytesIO
from fastapi.testclient import TestClient
from dastools.server import __version__
from dastools.server.dasws import stationws
from dastools.server.dasws import dataselect

"""Test the functionality of dasws.py

"""

# Files needed to run the tests for TDMS
# files = dict()
# files['PDN_1km_UTC_20180905_095503.298.tdms'] = 'https://nextcloud.gfz-potsdam.de/s/ro286WKCxpP6o4b/download/PDN_1km_UTC_20180905_095503.298.tdms'
# files['PDN_1km_UTC_20180905_095533.298.tdms'] = 'https://nextcloud.gfz-potsdam.de/s/zyQZ6wNHCBnQt8J/download/PDN_1km_UTC_20180905_095533.298.tdms'
# files['PDN_1km_UTC_20180905_095633.298.tdms'] = 'https://nextcloud.gfz-potsdam.de/s/ggGk3EYTQcknoxs/download/PDN_1km_UTC_20180905_095633.298.tdms'
#
# for file, url in files.items():
#     if file not in os.listdir('.'):
#         downloadfile(file, url)

# Read configuration
config = configparser.RawConfigParser()
# Create default sections and options for the configfile
here = os.path.dirname(__file__)
config['General'] = {'experiment': 'PDN_1km', 'directory': '.', 'format': 'TDMS',
                     'loglevel': 'INFO', 'sitename': 'Site description for StationWS'}
config['NSLC'] = {'net': 'XX', 'loc': '', 'cha': 'HSF'}
# Write to dasws.cfg
with open('dasws.cfg', 'w') as configfile:
    config.write(configfile)

# Define the tests for StationWS
clientSWS = TestClient(stationws)
# Define the tests for Dataselect
clientDS = TestClient(dataselect)


def test_stationws_root():
    response = clientSWS.get("/")
    assert response.status_code == 200
    assert response.headers['content-type'].startswith('text/html')


def test_dataselect_root():
    response = clientDS.get("/")
    assert response.status_code == 200
    assert response.headers['content-type'].startswith('text/html')


def test_stationws_version():
    response = clientSWS.get("/version")
    assert response.status_code == 200
    assert response.headers['content-type'].startswith('text/plain')
    assert response.content.decode('utf8') == __version__


def test_dataselect_version():
    response = clientDS.get("/version")
    assert response.status_code == 200
    assert response.headers['content-type'].startswith('text/plain')
    assert response.content.decode('utf8') == __version__


def test_stationws_applicationwadl():
    response = clientSWS.get("/application.wadl")
    assert response.status_code == 200
    assert response.headers['content-type'].startswith('application/xml')
    assert response.content.decode('utf8').find('resources base="/fdsnws/station/1"') > 0


def test_dataselect_applicationwadl():
    response = clientDS.get("/application.wadl")
    assert response.status_code == 200
    assert response.headers['content-type'].startswith('application/xml')
    assert response.content.decode('utf8').find('resources base="/fdsnws/dataselect/1"') > 0


def test_stationws_xml():
    response = clientSWS.get("/query")
    assert response.status_code == 400
    assert response.headers['content-type'].startswith('text/plain')
    assert response.content.decode('utf8').find('format=text') > 0


def test_stationws_xml2():
    response = clientSWS.get("/query?format=xml")
    assert response.status_code == 400
    assert response.headers['content-type'].startswith('text/plain')
    assert response.content.decode('utf8').find('format=text') > 0


def test_stationws_levelnotsupported():
    response = clientSWS.get("/query?net=XX&format=text&level=response")
    assert response.status_code == 400
    assert response.headers['content-type'].startswith('text/plain')
    assert response.content.decode('utf8').find('Usage details') > 0


def test_stationws_network():
    response = clientSWS.get("/query?net=XX&format=text&level=network")
    assert response.status_code == 200
    assert response.headers['content-type'].startswith('text/plain')
    textnet = response.content.decode('utf8')
    lines = textnet.splitlines()
    # There are only two lines
    assert len(lines) == 2
    line0 = lines[0].split('|')
    line1 = lines[1].split('|')
    # First line is a comment with headers
    assert line0[0].startswith('#')
    # First and second lines have 5 components separated by a '|'
    assert len(line0) == 5
    assert len(line1) == 5
    # Check network code and number of stations
    assert line1[0] == 'XX'
    assert line1[1] == config['General']['sitename']
    assert line1[2].startswith('2018-09-05T09:55:03.298')
    assert line1[3].startswith('2018-09-05T09:57:03')
    assert line1[4] == '768'


def test_stationws_station():
    response = clientSWS.get("/query?net=XX&format=text")
    assert response.status_code == 200
    assert response.headers['content-type'].startswith('text/plain')
    textnet = response.content.decode('utf8')
    lines = textnet.splitlines()
    line0 = lines[0].split('|')
    line1 = lines[1].split('|')
    # There are only two lines
    assert len(lines) == 769
    # First line is a comment with headers
    assert line0[0].startswith('#')
    # First and second lines have 8 components separated by a '|'
    assert len(line0) == 8
    assert len(line1) == 8
    # Check network code and number of stations
    assert line1[0] == 'XX'
    assert line1[1] == 'A0000'
    assert line1[5] == config['General']['sitename']
    assert line1[6].startswith('2018-09-05T09:55:03.298')
    assert line1[7].startswith('2018-09-05T09:57:03')


def test_stationws_channel():
    response = clientSWS.get("/query?net=XX&format=text&level=channel")
    assert response.status_code == 200
    assert response.headers['content-type'].startswith('text/plain')
    textnet = response.content.decode('utf8')
    lines = textnet.splitlines()
    line0 = lines[0].split('|')
    line1 = lines[1].split('|')
    # There are only 769 lines
    assert len(lines) == 769
    # First line is a comment with headers
    assert line0[0].startswith('#')
    # First and second lines have 17 components separated by a '|'
    assert len(line0) == 17
    assert len(line1) == 17
    # Check network code and number of stations
    assert line1[0] == 'XX'
    assert line1[1] == 'A0000'
    assert line1[3] == 'HSF'
    assert line1[15].startswith('2018-09-05T09:55:03.298')
    assert line1[16].startswith('2018-09-05T09:57:03')


def test_dataselect_query():
    response = clientDS.get("/query?net=XX&sta=00100&start=2018-09-05T09:56:00&end=2018-09-05T09:56:00.250000")
    assert response.status_code == 200
    assert response.headers['content-type'] == 'application/vnd.fdsn.mseed'

    # Read the result of the query and compare with the precalculated one
    auxin = BytesIO(response.content)
    conv = read(auxin)
    orig = read('./tests/testOneChannel.mseed')

    # Check the data
    assert np.array_equal(orig[0].data, conv[0].data)

    # Check the first level attributes
    for item in conv[0].stats:
        if item != 'mseed':
            assert orig[0].stats[item] == conv[0].stats[item]

    # check the attributes within 'mseed'
    for item in conv[0].stats['mseed']:
        if item != 'blkt1001':
            assert orig[0].stats['mseed'][item] == conv[0].stats['mseed'][item]


# def testDSChstopUndefined():
#     """chstop undefined via Dataselect"""
#
#     # TODO Duplicate this test for all other waveform conversion
#     # Start of the time window close to the beginning of the file
#     # FIXME Check start and endtime
#     stt = datetime(2018, 9, 5, 9, 54, 3)
#     # Take only 1 second
#     ett = stt + timedelta(seconds=1)
#
#     params = 'station=%s&start=%s&end=%s' % (766, stt.isoformat(), ett.isoformat())
#     waveform = __callURL('http://localhost:8080/fdsnws/dataselect/1/query?%s' % params, decode=None)
#
#     with open('testChstopUndefined.mseed', 'rb') as fin:
#         orig = fin.read()
#
#     # FIXME Most probably the headers differ. Check!
#     # return
#     assert orig == waveform
