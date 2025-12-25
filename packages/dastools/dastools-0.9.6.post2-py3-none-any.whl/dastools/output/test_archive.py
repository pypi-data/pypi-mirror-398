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

"""Tests to check that archive.py is working

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
import os.path
from datetime import datetime
from obspy.core.trace import Stats
from obspy import read
from dastools.output.archive import StreamBasedHour
from dastools.output.archive import StreamBased
from dastools.output.archive import SDS

"""Test the functionality of archive.py

"""

def test_StreamBased():
    st = read('./tests/testChstopUndefined-OptoDAS.mseed')
    sb = StreamBased(experiment='deleteme')
    sb.archive(st[0])
    assert os.path.isdir('./2022')
    assert os.path.isfile('./2022/deleteme.05597.2022.01.10.09.28.59.mseed')
    os.remove('./2022/deleteme.05597.2022.01.10.09.28.59.mseed')


def test_SDS():
    st = read('./tests/testChstopUndefined-OptoDAS.mseed')
    sb = SDS(experiment='deleteme')
    sb.archive(st[0])
    assert os.path.isdir('./2022/XX/05597/HSF.D')
    assert os.path.isfile('./2022/XX/05597/HSF.D/XX.05597..HSF.D.2022.010')
    os.remove('./2022/XX/05597/HSF.D/XX.05597..HSF.D.2022.010')
    os.removedirs('2022/XX/05597/HSF.D')
