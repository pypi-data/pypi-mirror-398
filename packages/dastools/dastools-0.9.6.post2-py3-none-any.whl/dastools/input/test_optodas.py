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

"""Tests to check that optodas.py is working

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

import os
from datetime import datetime
from datetime import timedelta
import numpy as np
from dastools.input.das import NoData
from obspy import Trace
from obspy import Stream
from obspy import read
from dastools.input.optodas import OptoDASReader
from dastools.utils import downloadfile
from pydantic import ValidationError

"""Test the functionality of optodas.py

"""


# Files needed to run the tests (v7)
files = dict()
files['092853.hdf5'] = {'link': 'https://nextcloud.gfz-potsdam.de/s/jW7t85d53ntNNWe/download/092853.hdf5',
                        'dir': './SineWave/20220110/dphi'}
# Files needed to run the tests (v8)
files['075550.hdf5'] = {'link': 'https://nextcloud.gfz-potsdam.de/s/9cbKTw59ZHSPxCs/download/075550.hdf5',
                        'dir': './example/20220422/dphi'}

for file, urldir in files.items():
    os.makedirs(urldir['dir'], exist_ok=True)
    if file not in os.listdir(urldir['dir']):
        downloadfile(os.path.join(urldir['dir'], file), urldir['link'])


# TODO We need a test for decimation=5

def testConversionv8new():
    """Conversion of a stream in v8 format (new)"""

    directory = '.'
    # Start of the time window close to the beginning of the file
    stt = datetime(2022, 4, 22, 7, 55, 51)
    # Take 7 seconds
    ett = stt + timedelta(seconds=7)

    orig = read('./tests/testConversion-OptoDASv8.mseed')

    t = OptoDASReader('example', directory, channels=[4400], starttime=stt, endtime=ett)
    with t:
        for wav in t:
            aux = Trace(data=wav.data, header=wav.stats)
            conv = Stream([aux])

    # Save in BigEndian
    conv.write('deleteme.mseed', format='MSEED', byteorder='>')
    stconv = read('deleteme.mseed')
    os.remove('deleteme.mseed')

    # Check the data
    assert np.allclose(orig[0].data, stconv[0].data)

    # Check the first level attributes
    for item in stconv[0].stats:
        if item != 'mseed':
            assert orig[0].stats[item] == stconv[0].stats[item]

    # # check the attributes within 'mseed'
    # for item in stconv[0].stats['mseed']:
    #     if item != 'blkt1001':
    #         assert orig[0].stats['mseed'][item] == stconv[0].stats['mseed'][item]


def testNoDataFoundnew():
    """when no data is found (new)"""

    directory = '.'
    # Start of the time window close to the beginning of the file
    stt = datetime(2022, 1, 10, 9, 29, 0)
    # Take only 1 second
    ett = stt + timedelta(seconds=1)

    try:
        OptoDASReader('Wrong-Name', directory, channels=[5597], starttime=stt, endtime=ett)
        raise Exception('A NoData exception was expected due to a wrong name of the experiment (filename)')
    except NoData:
        pass


def testStarttimeTooEarlynew():
    """when starttime is before the start of the data (new)"""

    directory = '.'
    # Start of the time window close to the beginning of the file
    stt = datetime(2022, 1, 1, 0, 0, 0)
    t = OptoDASReader('SineWave', directory, channels=[5597], starttime=stt)
    assert t.starttime > stt


def testChannelsTypesnew():
    """types of the parameters to select channels (new)"""

    directory = '.'
    # Start of the time window close to the beginning of the file
    stt = datetime(2022, 1, 10, 9, 29, 0)
    # Take only 0.1 second
    ett = stt + timedelta(milliseconds=100)
    try:
        OptoDASReader('SineWave', directory, channels=['a'], starttime=stt, endtime=ett)
        raise Exception('A TypeError was expected due to chstart not being a Number')
    except ValidationError:
        pass
    try:
        OptoDASReader('SineWave', directory, channels=[5597, 'a'], starttime=stt, endtime=ett)
        raise Exception('A TypeError was expected due to chstop not being a Number or None')
    except ValidationError:
        pass
    try:
        OptoDASReader('SineWave', directory, channels='1,2', starttime=stt, endtime=ett)
        raise Exception('A TypeError was expected due to channels being a str')
    except ValidationError:
        pass
    try:
        OptoDASReader('SineWave', directory, channels=1, starttime=stt, endtime=ett)
        raise Exception('A TypeError was expected due to channels being Number')
    except ValidationError:
        pass
    try:
        OptoDASReader('SineWave', directory, channels=list(), starttime=stt, endtime=ett)
        assert list() != []
    except ValidationError:
        pass


def testNetworkChannelCodesnew():
    """format of the network and channel code (new)"""

    directory = '.'
    # Start of the time window close to the beginning of the file
    stt = datetime(2022, 1, 10, 9, 29, 0)
    # Take only 0.1 second
    ett = stt + timedelta(milliseconds=100)
    try:
        OptoDASReader('SineWave', directory, channels=[5597], starttime=stt, endtime=ett, networkcode='A')
        raise Exception('A TypeError was expected due to wrong formatted network code')
    except ValidationError:
        pass
    try:
        OptoDASReader('SineWave', directory, channels=[5597], starttime=stt, endtime=ett, networkcode='AAA')
        raise Exception('A TypeError was expected due to wrong formatted network code')
    except ValidationError:
        pass
    try:
        OptoDASReader('SineWave', directory, channels=[5597], starttime=stt, endtime=ett, networkcode=1)
        raise Exception('A TypeError was expected due to wrong formatted network code')
    except ValidationError:
        pass

    try:
        OptoDASReader('SineWave', directory, channels=[5597], starttime=stt, endtime=ett, channelcode='AA')
        raise Exception('A TypeError was expected due to wrong formatted channel code')
    except ValidationError:
        pass
    try:
        OptoDASReader('SineWave', directory, channels=[5597], starttime=stt, endtime=ett, channelcode='AAAA')
        raise Exception('A TypeError was expected due to wrong formatted channel code')
    except ValidationError:
        pass
    try:
        OptoDASReader('SineWave', directory, channels=[5597], starttime=stt, endtime=ett, channelcode=1)
        raise Exception('A TypeError was expected due to wrong formatted channel code')
    except ValidationError:
        pass


def testChstopUndefinednew():
    """chstop undefined (new)"""

    directory = '.'
    # Start of the time window close to the beginning of the file
    stt = datetime(2022, 1, 10, 9, 29, 0)
    # Take only 0.1 second
    ett = stt + timedelta(milliseconds=100)

    orig = read('./tests/testChstopUndefined-OptoDAS.mseed')
    conv = Stream()

    t = OptoDASReader('SineWave', directory, channels=[5597], starttime=stt, endtime=ett)
    with t:
        for wav in t:
            aux = Trace(data=wav.data, header=wav.stats)
            conv += aux

    # Merge Traces
    conv.merge()

    assert len(orig[0].data) == len(conv[0].data)
    # Save in BigEndian
    conv.write('deleteme.mseed', format='MSEED', byteorder='>')
    stconv = read('deleteme.mseed')
    os.remove('deleteme.mseed')
    assert np.allclose(orig[0].data, stconv[0].data)

    # Check the first level attributes
    for item in stconv[0].stats:
        if item != 'mseed':
            assert orig[0].stats[item] == stconv[0].stats[item]


def testOneChannelnew():
    """One record from one channel"""

    directory = '.'
    # Start of the time window close to the beginning of the file
    stt = datetime(2022, 1, 10, 9, 29, 0)
    # Take only 250 samples
    ett = stt + timedelta(milliseconds=50)

    orig = read('./tests/testOneChannel-OptoDAS.mseed')

    t = OptoDASReader('SineWave', directory, channels=[5000], starttime=stt, endtime=ett)
    with t:
        for wav in t:
            aux = Trace(data=wav.data, header=wav.stats)
            conv = Stream([aux])

    # Save in BigEndian
    conv.write('deleteme.mseed', format='MSEED', byteorder='>')
    stconv = read('deleteme.mseed')
    os.remove('deleteme.mseed')

    # Check the data
    assert np.allclose(orig[0].data, stconv[0].data)

    # Check the first level attributes
    for item in stconv[0].stats:
        if item != 'mseed':
            assert orig[0].stats[item] == stconv[0].stats[item]


def testOneChannel2new():
    """One record from one channel defined by list of channels"""

    directory = '.'
    # Start of the time window close to the beginning of the file
    stt = datetime(2022, 1, 10, 9, 29, 0)
    # Take only 250 samples
    ett = stt + timedelta(milliseconds=50)

    orig = read('./tests/testOneChannel-OptoDAS.mseed')

    t = OptoDASReader('SineWave', directory, channels=[5000], starttime=stt, endtime=ett)
    with t:
        for wav in t:
            aux = Trace(data=wav.data, header=wav.stats)
            conv = Stream([aux])

    # Save in BigEndian
    conv.write('deleteme.mseed', format='MSEED', byteorder='>')
    stconv = read('deleteme.mseed')
    os.remove('deleteme.mseed')

    assert np.allclose(orig[0].data, stconv[0].data)


# def testTwoFiles():
#     """One record from one channel originally split in two files"""
#
#     directory = '.'
#     # Start of the time window close to the beginning of the file
#     stt = datetime(2018, 9, 5, 9, 55, 33)
#     # Take only 1000 samples
#     ett = stt + timedelta(seconds=1)
#
#     orig = read('./tests/testTwoFiles.mseed')
#
#     t = TDMS('PDN_1km', directory, chstart=99, chstop=99, starttime=stt, endtime=ett)
#     with t:
#         conv = Stream()
#         for data in t:
#             aux = Trace(data=data[0], header=data[1])
#             conv += aux
#
#     # Merge all Traces with same NSLC code
#     conv.merge()
#
#     # Check the data
#     assert np.allclose(orig[0].data, conv[0].data)
#
#     # Check the first level attributes
#     for item in conv[0].stats:
#         if item != 'mseed':
#             assert orig[0].stats[item] == conv[0].stats[item]
#
#     # check the attributes within 'mseed'
#     for item in conv[0].stats['mseed']:
#         if item != 'blkt1001':
#             assert orig[0].stats['mseed'][item] == conv[0].stats['mseed'][item]


def testTwoChannelsnew():
    """One record from two channels"""

    directory = '.'
    # Start of the time window close to the beginning of the file
    stt = datetime(2022, 1, 10, 9, 29, 0)
    # Take only 50 milliseconds
    ett = stt + timedelta(milliseconds=50)

    orig = read('./tests/testTwoChannels-OptoDAS.mseed')

    t = OptoDASReader('SineWave', directory, channels=[5000, 5001], starttime=stt, endtime=ett)
    with t:
        conv = Stream()
        for wav in t:
            aux = Trace(data=wav.data, header=wav.stats)
            conv += aux

    # Save in BigEndian
    conv.write('deleteme.mseed', format='MSEED', byteorder='>')
    stconv = read('deleteme.mseed')
    os.remove('deleteme.mseed')

    # Check the data
    assert np.allclose(orig[0].data, stconv[0].data)
    assert np.allclose(orig[1].data, stconv[1].data)

    # Check the first level attributes
    for item in stconv[0].stats:
        if item != 'mseed':
            assert orig[0].stats[item] == stconv[0].stats[item]
            assert orig[1].stats[item] == stconv[1].stats[item]


def testTwoChannels2new():
    """One record from two channels defined by list of channels"""

    directory = '.'
    # Start of the time window close to the beginning of the file
    stt = datetime(2022, 1, 10, 9, 29, 0)
    # Take only 50 milliseconds
    ett = stt + timedelta(milliseconds=50)

    orig = read('./tests/testTwoChannels-OptoDAS.mseed')

    t = OptoDASReader('SineWave', directory, channels=[5000, 5001], starttime=stt, endtime=ett)
    with t:
        conv = Stream()
        for wav in t:
            aux = Trace(data=wav.data, header=wav.stats)
            conv += aux

    # Save in BigEndian
    conv.write('deleteme.mseed', format='MSEED', byteorder='>')
    stconv = read('deleteme.mseed')
    os.remove('deleteme.mseed')

    # Check the data
    assert np.allclose(orig[0].data, stconv[0].data)
    assert np.allclose(orig[1].data, stconv[1].data)

    # Check the first level attributes
    for item in stconv[0].stats:
        if item != 'mseed':
            assert orig[0].stats[item] == stconv[0].stats[item]
            assert orig[1].stats[item] == stconv[1].stats[item]
