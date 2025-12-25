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

"""Tests to check that febus.py is working

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
from dastools.input.febus import FebusReader
from dastools.utils import downloadfile
from pydantic import ValidationError

"""Test the functionality of febus.py

"""


# Files needed to run the tests (v7)
files = dict()
files['SR_DS_2024-02-16_13-45-47_UTC.h5'] = {'link': 'https://nextcloud.gfz.de/s/EtAdRZaoXRpBtD5/download/SR_DS_2024-02-16_13-45-47_UTC.h5',
                                             'dir': './febus'}

for file, urldir in files.items():
    os.makedirs(urldir['dir'], exist_ok=True)
    if file not in os.listdir(urldir['dir']):
        downloadfile(os.path.join(urldir['dir'], file), urldir['link'])


def testStarttimeTooEarlynew():
    """when starttime is before the start of the data (new)"""

    directory = './febus'
    # Start of the time window close to the beginning of the file
    stt = datetime(2010, 1, 1, 0, 0, 0)
    t = FebusReader('SR_DS', directory, channels=[0], starttime=stt)
    assert t.starttime > stt


def testChannelsTypesnew():
    """types of the parameters to select channels (new)"""

    directory = './febus'
    # Start of the time window close to the beginning of the file
    stt = datetime(2022, 1, 10, 9, 29, 0)
    # Take only 0.1 second
    ett = stt + timedelta(milliseconds=100)
    try:
        FebusReader('SR_DS', directory, channels=['a'], starttime=stt, endtime=ett)
        raise Exception('A TypeError was expected due to chstart not being a Number')
    except ValidationError:
        pass
    try:
        FebusReader('SR_DS', directory, channels=[0, 'a'], starttime=stt, endtime=ett)
        raise Exception('A TypeError was expected due to chstop not being a Number or None')
    except ValidationError:
        pass
    try:
        FebusReader('SR_DS', directory, channels='1,2', starttime=stt, endtime=ett)
        raise Exception('A TypeError was expected due to channels being a str')
    except ValidationError:
        pass
    try:
        FebusReader('SR_DS', directory, channels=1, starttime=stt, endtime=ett)
        raise Exception('A TypeError was expected due to channels being Number')
    except ValidationError:
        pass
    try:
        FebusReader('SR_DS', directory, channels=list(), starttime=stt, endtime=ett)
        assert list() != []
    except ValidationError:
        pass


def testNetworkChannelCodesnew():
    """format of the network and channel code (new)"""

    directory = './febus'
    # Start of the time window close to the beginning of the file
    stt = datetime(2022, 1, 10, 9, 29, 0)
    # Take only 0.1 second
    ett = stt + timedelta(milliseconds=100)
    try:
        FebusReader('SR_DS', directory, channels=[0], starttime=stt, endtime=ett, networkcode='A')
        raise Exception('A TypeError was expected due to wrong formatted network code')
    except ValidationError:
        pass
    try:
        FebusReader('SR_DS', directory, channels=[0], starttime=stt, endtime=ett, networkcode='AAA')
        raise Exception('A TypeError was expected due to wrong formatted network code')
    except ValidationError:
        pass
    try:
        FebusReader('SR_DS', directory, channels=[0], starttime=stt, endtime=ett, networkcode=1)
        raise Exception('A TypeError was expected due to wrong formatted network code')
    except ValidationError:
        pass

    try:
        FebusReader('SR_DS', directory, channels=[0], starttime=stt, endtime=ett, channelcode='AA')
        raise Exception('A TypeError was expected due to wrong formatted channel code')
    except ValidationError:
        pass
    try:
        FebusReader('SR_DS', directory, channels=[0], starttime=stt, endtime=ett, channelcode='AAAA')
        raise Exception('A TypeError was expected due to wrong formatted channel code')
    except ValidationError:
        pass
    try:
        FebusReader('SR_DS', directory, channels=[0], starttime=stt, endtime=ett, channelcode=1)
        raise Exception('A TypeError was expected due to wrong formatted channel code')
    except ValidationError:
        pass
