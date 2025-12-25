"""Parallelization module from dastools.

This file is part of dastools.

dastools is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

dastools is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If
not, see https://www.gnu.org/licenses/.

   :Copyright:
       2021 Helmholtz Centre Potsdam GFZ German Research Centre for Geosciences, Potsdam, Germany
   :License:
       GPLv3
   :Platform:
       Linux

.. moduleauthor:: Javier Quinteros <javier@gfz-potsdam.de>, GEOFON, GFZ Potsdam
"""
import datetime
import logging
import sys
from typing import Union
from dastools.input.das import Das
from dastools.input.tdms import TDMS
from dastools.input.optodas import OptoDAS
from dastools.input.tdms import TDMSReader
from dastools.input.optodas import OptoDASReader
from datetime import timedelta
from abc import ABCMeta
from abc import abstractmethod


class Split(metaclass=ABCMeta):
    """Base class for the different parallelization approaches an archive can have"""

    @abstractmethod
    def __init__(self, dasfiles: Das, outputfmt: str = 'SDS', starttime=None, endtime=None):
        """Get parameters to define a batch of the DAS dataset

        """
        pass

    @abstractmethod
    def getbatch(self) -> list:
        """Create a batch of tasks"""
        pass


class SplitTDMS(Split):
    """Class to separate a TDMS dataset in a batch which could be parallelized"""
    def __init__(self, dasfiles: Union[TDMS, TDMSReader], outputfmt: str = 'SDS', starttime=None, endtime=None):
        """Get parameters to define a batch of the TDMS dataset

        """
        self.dasfiles = dasfiles
        self.outputfmt = outputfmt
        self.__tasks = list()
        # List of available files in the directory
        self.__files = list()
        for f in dasfiles:
            if (starttime is not None) and (starttime > f['dt']):
                f['dt'] = starttime
            if (endtime is not None) and (endtime < f['dtend']):
                f['dtend'] = endtime
            self.__files.append(f)

        if not len(self.__files):
            logging.error('No files found with proper filename')
            sys.exit(-2)

    def getbatch(self) -> list:
        """Create a batch of tasks
        """
        logs = logging.getLogger('SDS')
        if self.outputfmt == 'StreamBasedHour':
            # Split in hours
            dtstart = self.__files[0]['dt']

            while dtstart < self.__files[-1]['dtend']:
                dtend = dtstart + timedelta(hours=1)
                dtend = datetime.datetime.strptime(dtend.strftime('%Y-%m-%dT%H:00:00'),
                                                   '%Y-%m-%dT%H:00:00')
                if dtend > self.__files[-1]['dtend']:
                    dtend = self.__files[-1]['dtend']
                self.__tasks.append((self.dasfiles.channels, dtstart, dtend))
                dtstart = dtend

        elif self.outputfmt == 'StreamBased':
            # Difficult to split. Just split in two groups of channels
            if len(self.dasfiles.channels) > 1:
                aux = int(len(self.dasfiles.channels)/2)
                # Split in two set of channels
                self.__tasks.append((self.dasfiles.channels[:aux], self.__files[0]['dt'], self.__files[-1]['dtend']))
                self.__tasks.append((self.dasfiles.channels[aux:], self.__files[0]['dt'], self.__files[-1]['dtend']))
            else:
                self.__tasks.append((self.dasfiles.channels, self.__files[0]['dt'], self.__files[-1]['dtend']))

        elif self.outputfmt == 'SDS':
            # Keep the maximum between requested and available
            dtstart = self.__files[0]['dt']

            # Split the requested time in days
            while dtstart < self.__files[-1]['dtend']:
                endSDS = dtstart + timedelta(days=1)
                endSDS = datetime.datetime.strptime(endSDS.strftime('%Y-%m-%dT00:00:00'), '%Y-%m-%dT00:00:00')
                self.__tasks.append((self.dasfiles.channels, dtstart, min(endSDS, self.__files[-1]['dtend'])))
                dtstart = min(endSDS, self.__files[-1]['dtend'])

        else:
            logging.error('Unknown output format: %s' % self.outputfmt)
            sys.exit(-2)

        return self.__tasks


class SplitOptoDAS(Split):
    """Class to separate an OptoDAS dataset in a batch which could be parallelized"""
    def __init__(self, dasfiles: Union[OptoDAS, OptoDASReader], outputfmt: str = 'SDS', starttime=None, endtime=None):
        """Get parameters to define a batch of the TDMS dataset

        """

        self.dasfiles = dasfiles
        self.outputfmt = outputfmt
        self.__tasks = list()
        # List of available files in the directory
        self.__files = list()
        for f in dasfiles:
            if (starttime is not None) and (starttime > f['dt']):
                f['dt'] = starttime
            if (endtime is not None) and (endtime < f['dtend']):
                f['dtend'] = endtime
            self.__files.append(f)

        if not len(self.__files):
            logging.error('No files found with proper filename')
            sys.exit(-2)

    def getbatch(self) -> list:
        """Create a batch of tasks
        """
        logs = logging.getLogger('SplitOptoDAS')
        # if self.outputfmt in ('StreamBasedHour', 'StreamBased'):
        # Difficult to split. Just split in two groups of channels
        if len(self.dasfiles.channels) > 1:
            aux = int(len(self.dasfiles.channels)/2)
            # Split in two set of channels
            self.__tasks.append((self.dasfiles.channels[:aux], self.__files[0].dt, self.__files[-1].dtend))
            self.__tasks.append((self.dasfiles.channels[aux:], self.__files[0].dt, self.__files[-1].dtend))
        else:
            self.__tasks.append((self.dasfiles.channels, self.__files[0].dt, self.__files[-1].dtend))

        return self.__tasks
