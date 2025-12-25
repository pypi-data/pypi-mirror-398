"""OptoDAS module from dastools.

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
       2021-2025 GFZ Helmholtz Centre for Geosciences, Potsdam, Germany
   :License:
       GPLv3
   :Platform:
       Linux

.. moduleauthor:: Javier Quinteros <javier@gfz.de>, GEOFON, GFZ Potsdam
"""

import logging
import datetime
import os
from pathlib import Path
from h5py import File
from h5py import Group
from h5py import Dataset
from dastools.core import Waveform
from dastools.utils import int2stationcode
from dastools.input.das import Das
from dastools.input.das import DASDetector
from dastools.input.das import DASFile
from obspy import UTCDateTime
from obspy.core.trace import Stats
from obspy.core.util.attribdict import AttribDict
import numpy as np
from math import floor
from math import ceil
from dastools.input.das import PotentialGap
from dastools.input.das import NoData
from dastools.basemodels import DASMetadata
from dastools.basemodels import InterrogatorModel
from dastools.basemodels import ChannelGroupModel
from dastools.basemodels import ChannelModel
from typing import Union, Tuple
from typing import List
from pydantic import validate_call
from pydantic import DirectoryPath
from pydantic import conlist
from pydantic import constr
from warnings import warn


def unwrap(signal, wrapstep=2 * np.pi, axis=-1):
    """
    Unwrap phase phi by changing absolute jumps greater than wrapStep/2 to
    their wrapStep complement along the given axis. By default, (if wrapStep is
    None) standard unwrapping is performed with wrapStep=2*np.pi.

    (Note: "np.unwrap" in the numpy package has an optional "discont" parameter
    which does not give an expected (or useful) behavior when it deviates
    from default. Use this unwrap implementation instead of the numpy
    implementation if your signal is wrapped with discontinuities that deviate
    from 2*pi.)

    Original code from Alcatel Submarine Networks Norway AS!
    """
    scale = 2 * np.pi / wrapstep
    return (np.unwrap(signal * scale, axis=axis) / scale).astype(signal.dtype)


def filegenerator(experiment: str, directory: Path = '.'):
    log = logging.getLogger('OptoDAS.filegenerator')
    # Loop through files to check that they are in OptoDAS format
    experimentdir = os.path.join(directory, experiment)
    if not os.path.isdir(experimentdir):
        return

    # Sort based on the name of the Direntry
    for day in sorted(os.scandir(experimentdir), key=lambda x: x.name):  # type: os.DirEntry
        # Entry must be a directory
        if not day.is_dir():
            continue
        # Check format of the directory name (YYYYMMDD)
        try:
            dt = datetime.datetime.strptime(day.name, '%Y%m%d')
        except ValueError:
            log.warning('Unexpected format in directory name! Date expected... (%s)' % day.name)
            continue

        daydir = os.path.join(experimentdir, day.name, 'dphi')
        for file in sorted(os.scandir(daydir), key=lambda x: x.name):  # type: os.DirEntry
            # Entry must be a file and end with hdf5 file
            if file.is_dir() or not file.name.endswith('.hdf5'):
                continue

            # Check that the format of the filename is exactly as expected. Otherwise, send a warning
            try:
                dt = datetime.datetime.strptime(day.name + file.name[:-5], '%Y%m%d%H%M%S')
            except ValueError:
                log.warning('Unexpected format in file name! Time expected... (%s)' % file.name)
                continue

            # Read with h5py
            fname = os.path.join(daydir, file.name)
            fin = File(fname)
            try:
                # OptoDAS v7 and v8 are supported
                if fin['fileVersion'][()] in (7, 8):
                    yield fname
            except Exception:
                continue
    return


class OptoDASDetector(DASDetector):
    def checkDASdata(self, experiment: str, directory: Path = '.') -> bool:
        log = logging.getLogger('OptoDASDetector')
        for aux in filegenerator(experiment, directory):
            return True
        return False


class OptoDAS2D(Das):
    """Class to read seismic waveforms in OptoDAS format with a 2D approach

Files read in this format are read without time integration.
Therefore, the units of the output will be usually strain rate.
    """

    def __enter__(self):
        """Method which allows to use the syntax 'with object:' and use it inside"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Method which close open resources after using the syntax 'with object:' and use it inside"""
        if self.__fi is not None:
            self.__fi.close()

    def __iter__(self):
        """Iterate through HDF5 data files

        :returns: Raw data and some extra data about that
        :rtype: tuple(numpy.array, numpy.array, numpy.array)
        """
        # Create logger
        self.__logs = logging.getLogger('__iter__')
        self.__logs.setLevel(self.__loglevel)

        self.__currentfile = 0
        while True:
            try:
                self.__logs.debug('Moving to next file...')
                self.__search_data()
                yield self.__getalldata()
                # No more data in this file. Skip to the next one.
                self.__currentfile += 1
            except IndexError:
                break
        return

    @validate_call
    def __init__(self, experiment: str, directory: DirectoryPath = '.',
                 channels: Union[conlist(int, min_length=1), None] = None,
                 starttime: Union[datetime.datetime, None] = None, endtime: Union[datetime.datetime, None] = None,
                 networkcode: constr(strip_whitespace=True, to_upper=True, min_length=2, max_length=2) = 'XX',
                 channelcode: constr(strip_whitespace=True, to_upper=True, min_length=3, max_length=3) = 'HSF',
                 loglevel: str = 'INFO'):
        """Initialize the OptaDAS2D object selecting the data and channels

        :param experiment: Experiment to read and process. Usually the name of the root directory
        :type experiment: str
        :param directory: Directory where experiment is stored
        :type directory: str
        :param channels: Selection of channels to work with (list of integers)
        :type channels: list or NoneType
        :param starttime: Start of the selected time window
        :type starttime: datetime.datetime or NoneType
        :param endtime: End of the selected time window
        :type endtime: datetime.datetime or NoneType
        :param networkcode: Network code of the experiment. It has to be two alphanumeric characters
        :type networkcode: str
        :param channelcode: Channel code of the experiment. It has to be three alphanumeric characters
        :type channelcode: str
        :param loglevel: Verbosity in the output
        :type loglevel: str
        :raise TypeError: If chstart, or chstop, or chstep are not int. If channels is not a list, or networkcode is
        not a 2 characters code, or channelcode is not a 3 characters code.
        :raise Exception: If channels is empty.
        :raise NoData: If there is no more data available
        """

        # Log level
        self.__loglevel = loglevel
        self.__logs = logging.getLogger('OptoDAS2D.init')
        self.__logs.setLevel(loglevel)

        # Name of file
        self.__experiment = experiment
        self.__directory = directory
        self.__networkcode = networkcode
        self.__channelcode = channelcode
        self.channels = channels
        # channels has priority. Otherwise, chstart, chstop and chstep are used
        # if channels is not None and isinstance(channels, list):
        #     self.channels = channels
        #     # List of channels cannot be empty
        #     if not len(self.channels):
        #         raise Exception('Channel list is empty!')
        # else:
        #     # If chstart, chstop and chstep will define the selected channels we need to keep the three
        #     #  values (start, stop, step) and define the channels later in readmetadata
        #     self.channels = None
        #     # self.channels = list(range(chstart, chstop+1, chstep))

        # Time window selection
        self.__twstart = starttime
        self.__twend = endtime

        # Available time window
        self.starttime = None
        self.endtime = None

        # Sampling Rate
        self.sampling_rate = None

        # File currently being processed
        self.__currentfile = None

        # Other variables to be read from the headers
        self.__datatype = None
        self.__datatypesize = None
        # The result is always float32, because it has to be divided by the sensitivity and the scale factor
        # Watch out! The byte order is Little Endian! Not the best for miniseed
        self.__outdatatype = '<f4'
        self.numchannels = None
        self.__samples = None
        self.__samplestart = None
        self.__sampleend = None
        self.__samplecur = None

        # Dictionary to save the metadata defined in the file
        self.metadata = dict()

        # Keep the values in case we need to reset them
        self.__origstarttime = self.__twstart
        self.__origendtime = self.__twend

        # Create a DAS-RCN metadata object and retrieve the items from the "metadata" attribute
        self.dasrcn = DASMetadata(network_code=networkcode,
                                  interrogators=[InterrogatorModel(manufacturer='Alcatel')])

        # List of available files in the directory
        self.__available = self.__inspect_files()
        self.__logs.debug(str(self.__available))
        if not len(self.__available):
            self.__logs.warning('No files found with proper filename.')
            raise NoData()

        # Set the start and end of the experiment
        try:
            self.dasrcn.interrogators[0].acquisitions[0].acquisition_start_time = self.__available[0].dt
            self.dasrcn.start_date = self.__available[0].dt.date()
        except Exception:
            pass
        try:
            self.dasrcn.interrogators[0].acquisitions[0].acquisition_end_time = self.endexperiment
            self.dasrcn.end_date = self.endexperiment.date() if self.endexperiment is not None else self.endexperiment
        except Exception:
            pass

        # Set the time window selection to the minimum datetime found
        if (self.__twstart is None) or (self.__twstart < self.__available[0].dt):
            self.__twstart = self.__available[0].dt

        # Recover values of start and endtime
        self.reset()
        self.__logs.debug('Starttime: %s ; Endtime: %s' % (self.__twstart, self.__twend))

    def __inspect_files(self) -> List[DASFile]:
        """Loop through files and create a list with basic properties"""
        # Loop through files and load them in __available as 'YYYYMMDD/TTmmSS'
        experimentdir = os.path.join(self.__directory, self.__experiment)
        self.__logs.debug('Experiment directory: %s' % experimentdir)
        if not os.path.isdir(experimentdir):
            raise NoData()

        result = list()  # type: List[DASFile]
        # Sort based on the name of the Direntry
        for day in sorted(os.scandir(experimentdir), key=lambda x: x.name):  # type: os.DirEntry
            # Entry must be a directory
            if not day.is_dir():
                continue

            self.__logs.debug('Checking day: %s' % day.name)
            # Check format of the directory name (YYYYMMDD)
            try:
                dt = datetime.datetime.strptime(day.name, '%Y%m%d')
            except ValueError:
                self.__logs.warning('Unexpected format in directory name! Date expected... (%s)' % day.name)
                continue

            daydir = os.path.join(experimentdir, day.name, 'dphi')

            for file in sorted(os.scandir(daydir), key=lambda x: x.name):  # type: os.DirEntry
                # Entry must be a file
                if file.is_dir():
                    continue

                self.__logs.debug('Checking time: %s' % file.name)
                # Entry must be a hdf5 file
                if not file.name.endswith('.hdf5'):
                    continue

                # Check that the format of the filename is exactly as expected. Otherwise, send a warning
                try:
                    dt = datetime.datetime.strptime(day.name + file.name[:-5], '%Y%m%d%H%M%S')
                except ValueError:
                    self.__logs.warning('Unexpected format in file name! Time expected... (%s)' % file.name)
                    continue

                # Read with h5py
                fname = os.path.join(daydir, file.name)
                # TODO Check if this is needed or we can skip it by using the part of the filename with the time
                self.__fi = File(fname)
                try:
                    # Reset some properties before opening the new file. starttime will be completed in '__readmetadata'
                    self.starttime = None
                    self.__readmetadata()
                except PotentialGap:
                    continue

                # Add only if this file lies within the requested time window
                if (self.__twstart is not None) and (self.endtime < self.__twstart):
                    self.__logs.debug('File before the selected time window. Discarding...')
                    # Skip to the next one
                    continue
                if (self.__twend is not None) and (self.__twend < dt):
                    # We are already after the endtime requested, so break the loop
                    self.__logs.debug('File after the selected time window. Discarding...')
                    break
                result.append(DASFile(dt=self.starttime, dtend=self.endtime, name=fname, samples=self.__samples))

        result.sort(key=lambda x: x.dt)
        return result

    # FIXME This is awful, but it works until I can refactor the "endtime" property
    @property
    def endexperiment(self) -> Union[datetime.datetime, None]:
        try:
            return self.__available[-1].dtend
        except Exception:
            return None

    @property
    def shape(self) -> Tuple[int, int]:
        return sum([f.samples for f in self.__available]), len(self.channels)

    def __select_file(self):
        """Select a file from the experiment based on the status of the object

        :raise Exception: If data not available in the specified time window. If the header does not
        indicate that the file is a TDMS format
        :raise IndexError: If the last file has already been processed or the start is greater than end
        """
        self.__logs = logging.getLogger('Select file')
        self.__logs.setLevel(self.__loglevel)

        if self.__currentfile is None:
            if (self.__twstart is None) or (self.__twstart is not None and self.__twstart < self.__available[0].dt):
                self.__twstart = self.__available[0].dt
            for idx, fi in enumerate(self.__available):
                if fi.dt <= self.__twstart <= fi.dtend:
                    filename = os.path.join(self.__directory, self.__available[idx].name)
                    self.__currentfile = idx
                    self.__logs.debug(
                        'Opening %s; Starttime: %s' % (self.__available[self.__currentfile].name, self.__twstart))
                    break
            else:
                # raise Exception('Data not available in the specified time window')
                raise IndexError
        elif self.__currentfile >= len(self.__available):
            self.__logs.debug('Last file already processed')
            # No more data to iterate
            raise IndexError
        else:
            filename = self.__available[self.__currentfile].name
            self.__twstart = self.__available[self.__currentfile].dt
            if (self.__twend is not None) and (self.__twstart > self.__twend):
                self.__logs.debug('Start is greater than end. %s %s' % (self.__twstart, self.__twend))
                raise IndexError
            self.__logs.debug('Opening %s; Starttime: %s' % (self.__available[self.__currentfile].name, self.__twstart))

        # FIXME If we don't open the File before, we need to do it here and after that set starttime and endtime
        # Reset some properties before opening the new file
        self.starttime = self.__available[self.__currentfile].dt
        # print(self.starttime)
        # self.endtime = None
        self.endtime = self.__available[self.__currentfile].dtend
        self.metadata = dict()

        # Read with h5py
        self.__fi = File(filename)

        # TODO All input from now on will be formatted by this
        # For OptoDAS we hardcode this as little endian
        self.__endian = '>'

    def __search_data(self):
        """
        Select a file to work with, read its metadata and calculate samples to read

        :raise IndexError: If the last file has already been processed or the start is greater than end
        """
        while True:
            # Loop through files until there is nothing else (IndexError)
            try:
                self.__select_file()
            except IndexError:
                raise
            except Exception as e:
                self.__logs.warning('Skipping file because of %s' % str(e))
                self.__currentfile += 1
                continue

            # Read the metadata and calculate samples to read
            # Skip to the next file if there is a gap
            try:
                self.__readmetadata()
                return
            except NoData:
                self.__logs.error('No Data was found in the metadata definition')
                self.__currentfile += 1
            except PotentialGap:
                self.__logs.warning('Potential gap detected!')
                self.__currentfile += 1

    # Read all metadata from the HDF5 file
    def __readgroup(self, grp: Group):
        grpdict = dict()
        for k, v in grp.items():
            # print(v.name)
            if isinstance(v, Dataset) and v.name != '/data':
                grpdict[k] = v[()]
            elif isinstance(v, Dataset) and v.name == '/data':
                grpdict[k] = v.dtype
            elif isinstance(v, Group):
                grpdict[k] = self.__readgroup(v)
        return grpdict

    # Loads all metadata from the file in an attribute
    def __readmetadata(self):
        """This method sets the attribute endtime showing the expected time of last sample of the file"""
        self.__logs = logging.getLogger('Read metadata')
        self.__logs.setLevel(self.__loglevel)

        self.metadata = self.__readgroup(self.__fi)
        self.__datatype = self.metadata['data']
        # Check version and signature of the file
        if self.metadata['fileVersion'] not in (7, 8):
            self.__logs.warning('File version is not 7 or 8!')

        if self.sampling_rate is None:
            self.sampling_rate = 1.0/self.metadata['header']['dt']
            # Set the sampling rate in the DAS-RCN metadata
            self.dasrcn.interrogators[0].acquisitions[0].acquisition_sample_rate = self.sampling_rate
            self.dasrcn.interrogators[0].acquisitions[0].acquisition_sample_rate_unit = 'Hertz'

        try:
            # Save GaugeLength
            self.dasrcn.interrogators[0].acquisitions[0].gauge_length = self.metadata['header']['gaugeLength']
            self.dasrcn.interrogators[0].acquisitions[0].gauge_length_unit = 'meter'
        except KeyError:
            pass

        try:
            # Save Unit of measure
            self.dasrcn.interrogators[0].acquisitions[0].unit_of_measure = 'strain-rate' if self.metadata['header']['unit'].decode() in ('rad/(s·m)', 'rad/m/s') else 'count'
        except KeyError:
            pass

        try:
            # Save Spatial Resolution [m]
            self.dasrcn.interrogators[0].acquisitions[0].spatial_sampling_interval = self.metadata['header']['dx']
            self.dasrcn.interrogators[0].acquisitions[0].spatial_sampling_interval_unit = 'meter'
        except KeyError:
            pass

        try:
            # Save refraction index
            self.dasrcn.cables[0].fibers[0].fiber_refraction_index = self.metadata['cableSpec']['refractiveIndex']
        except KeyError:
            pass

        try:
            # Save version
            model = self.metadata['header']['instrument']
            self.dasrcn.interrogators[0].model = model.decode() if isinstance(model, bytes) else model
        except KeyError:
            pass

        curstarttime = datetime.datetime.utcfromtimestamp(self.metadata['header']['time'])
        if self.starttime is None:
            self.starttime = curstarttime
        # print(type(curstarttime), curstarttime)

        self.numchannels = self.metadata['header']['nChannels'] if self.metadata['fileVersion'] == 7 else \
            len(self.metadata['header']['channels'])
        # print(self.numchannels)

        # Save the number of channels in DAS-RCN format
        self.dasrcn.interrogators[0].acquisitions[0].number_of_channels = len(self.channels)

        # Keep the indexes of where the channels really are (column in 2D array)
        self.__channelsidx = [self.metadata['header']['channels'].tolist().index(ch) for ch in self.channels]
        self.__logs.debug('From channels %s to %s' % (self.channels, self.__channelsidx))

        # TODO In version 8 I should check in dimensionSizes
        self.__samples = self.metadata['header']['nSamples'] if self.metadata['fileVersion'] == 7 else \
            self.metadata['header']['dimensionSizes'][0]

        # Calculate endtime based on the number of samples declared and the sampling rate
        self.endtime = self.starttime + datetime.timedelta(seconds=(self.__samples-1) * self.metadata['header']['dt'])

        if (self.__twstart is not None) and (self.endtime < self.__twstart):
            raise PotentialGap(self.endtime, (self.__twstart-self.endtime).total_seconds(),
                               'End time of file before of time window (%s < %s)' % (self.endtime, self.__twstart))

        if (self.__twend is not None) and (self.__twend < self.starttime):
            raise PotentialGap(self.__twend, (self.starttime-self.__twend).total_seconds(),
                               'Start time of file after time window (%s < %s)' % (self.__twend, self.starttime))

        # Sample to start extraction from based on the initial datetime of the file (__twstart)
        if self.__twstart is not None:
            self.__samplestart = max(
                floor((self.__twstart - self.starttime).total_seconds() / self.metadata['header']['dt']), 0)
        else:
            self.__samplestart = 0

        # Should I readjust __twstart to align it exactly with the time of the samples?
        self.__twstart = self.starttime + datetime.timedelta(seconds=self.__samplestart * self.metadata['header']['dt'])

        self.__samplecur = self.__samplestart

        # Open end or beyond this file: read until the last sample
        if (self.__twend is None) or (self.__twend >= self.endtime):
            self.__sampleend = self.__samples-1
        else:
            # Otherwise calculate which one is the last sample to read
            self.__sampleend = ceil((self.__twend - self.starttime).total_seconds() / self.metadata['header']['dt'])

        self.__logs.debug('Samples: %s' % self.__samples)
        self.__logs.debug('Samples selected: %s-%s' % (self.__samplestart, self.__sampleend))

    def reset(self):
        """Reset the status of the object and start the read again

        :raise IndexError: If the last file has already been processed or the start is greater than end
        """
        self.__twstart = self.__origstarttime
        self.__twend = self.__origendtime
        self.__currentfile = None
        self.__search_data()

    def __getalldata(self) -> np.array:
        """Read data from current file based on channel and timewindow selection

        :return: Data and attributes for the header
        :rtype: tuple(numpy.array, obspy.core.trace.Stats)
        """
        # Data
        self.__logs = logging.getLogger('Iterate Data')
        self.__logs.setLevel(self.__loglevel)

        # Multiply by dataScale and unwrap signal
        # data = data * self.metadata['header']['dataScale']
        # data=unwrap(data, self.metadata['header']['spatialUnwrRange'], axis=1)
        auxdata = unwrap(self.__fi['data'] * self.metadata['header']['dataScale'],
                         self.metadata['header']['spatialUnwrRange'], axis=1)
        # print('After unwrap', auxdata[:10,0])
        # Keep only requested timewindow and channels
        auxdata2 = auxdata[self.__samplestart:self.__sampleend + 1, self.__channelsidx].astype(self.__outdatatype)
        del auxdata
        # WARNING ! Integration in time could be tricky. It needs to sum cumulatively the signal.
        # If there are gaps, the absolute value should be recovered from the metadata (meta['header']['phiOffs'])
        # where one can find a starting value for each selected channel.
        # auxdata2 = np.cumsum(auxdata2, axis=0) * self.metadata['header']['dt']
        # print('After cumsum', auxdata2[:10,0])
        # Use the sensitivity
        sensitivity = self.metadata['header']['sensitivity'] if self.metadata['fileVersion'] == 7\
            else self.metadata['header']['sensitivities'][0,0]
        auxdata2 /= sensitivity
        # print('After sensitivity', auxdata2[:10,0])
        # Keep only requested samples
        # auxdata2 = auxdata2[self.__samplestart:self.__sampleend + 1, :].astype(self.__outdatatype)

        # DO NOT transpose the matrix. Therefore, time is in the rows and channels in columns
        # newauxdata2 = auxdata2.T
        return auxdata2


class OptoDASReader(Das):
    """Class to read seismic waveforms in OptoDAS format

Files read in this format are read without time integration.
Therefore, the units of the output will be usually strain rate.
    """

    def __enter__(self):
        """Method which allows to use the syntax 'with object:' and use it inside

        Create a buffer space to store the signal coefficients to be convoluted during the decimation
        """
        for channel in self.channels:
            self.__logs.debug('Create empty buffer for channel %s' % channel)
            self.__buffer[channel] = None

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Method which close open resources after using the syntax 'with object:' and use it inside"""
        if self.__fi is not None:
            self.__fi.close()

    def __iter__(self):
        """Iterate through data (or metadata) and filter and decimate if requested

        :returns: Data and attributes for the header, or metadata
        :rtype: tuple(numpy.array, obspy.core.trace.Stats) or dict
        """
        # Create logger
        self.__logs = logging.getLogger('__iter__')
        self.__logs.setLevel(self.__loglevel)

        # In the case that we iterate to get data
        for waveform in self.__iter_data__():
            yield waveform
        return

    @validate_call
    def __init__(self, experiment: str, directory: DirectoryPath = '.',
                 channels: Union[conlist(int, min_length=1), None] = None,
                 starttime: Union[datetime.datetime, None] = None, endtime: Union[datetime.datetime, None] = None,
                 networkcode: constr(strip_whitespace=True, to_upper=True, min_length=2, max_length=2) = 'XX',
                 channelcode: constr(strip_whitespace=True, to_upper=True, min_length=3, max_length=3) = 'HSF',
                 loglevel: str = 'INFO'):
        """Initialize the OptaDAS object selecting the data and channels

        :param experiment: Experiment to read and process. Usually the name of the root directory
        :type experiment: str
        :param directory: Directory where experiment is stored
        :type directory: str
        :param channels: Selection of channels to work with (list of integers)
        :type channels: list or NoneType
        :param starttime: Start of the selected time window
        :type starttime: datetime.datetime or NoneType
        :param endtime: End of the selected time window
        :type endtime: datetime.datetime or NoneType
        :param networkcode: Network code of the experiment. It has to be two alphanumeric characters
        :type networkcode: str
        :param channelcode: Channel code of the experiment. It has to be three alphanumeric characters
        :type channelcode: str
        :param loglevel: Verbosity in the output
        :type loglevel: str
        :raise TypeError: If chstart, or chstop, or chstep are not int. If channels is not a list, or networkcode is
        not a 2 characters code, or channelcode is not a 3 characters code.
        :raise Exception: If channels is empty.
        :raise NoData: If there is no more data available
        """

        # Log level
        self.__loglevel = loglevel
        self.__logs = logging.getLogger('OptoDASReader.init')
        self.__logs.setLevel(loglevel)

        # Name of file
        self.__experiment = experiment
        self.__directory = directory
        self.__networkcode = networkcode
        self.__channelcode = channelcode
        self.channels = channels
        # channels has priority. Otherwise, chstart, chstop and chstep are used
        # if channels is not None and isinstance(channels, list):
        #     self.channels = channels
        #     # List of channels cannot be empty
        #     if not len(self.channels):
        #         raise Exception('Channel list is empty!')
        # else:
        #     # If chstart, chstop and chstep will define the selected channels we need to keep the three
        #     #  values (start, stop, step) and define the channels later in readmetadata
        #     self.channels = None
        #     # self.channels = list(range(chstart, chstop+1, chstep))

        # Time window selection
        self.__twstart = starttime
        self.__twend = endtime

        # Available time window
        self.starttime = None
        self.endtime = None

        # Sampling Rate
        self.sampling_rate = None

        # File currently being processed
        self.__currentfile = None

        # Other variables to be read from the headers
        self.__datatype = None
        self.__datatypesize = None
        self.__outdatatype = '>f4'
        self.numchannels = None
        self.__samples = None
        self.__samplestart = None
        self.__sampleend = None
        self.__samplecur = None

        # Dictionary to save the metadata defined in the file
        self.metadata = dict()

        # Keep the values in case we need to reset them
        self.__origstarttime = self.__twstart
        self.__origendtime = self.__twend

        # Create a DAS-RCN metadata object and retrieve the items from the "metadata" attribute
        self.dasrcn = DASMetadata(network_code=networkcode,
                                  interrogators=[InterrogatorModel(manufacturer='Alcatel')])

        # List of available files in the directory
        self.__available = self.__inspect_files()
        self.__logs.debug(str(self.__available))
        if not len(self.__available):
            self.__logs.warning('No files found with proper filename.')
            raise NoData()

        # Set the start and end of the experiment
        try:
            self.dasrcn.interrogators[0].acquisitions[0].acquisition_start_time = self.__available[0].dt
            self.dasrcn.start_date = self.__available[0].dt.date()
        except Exception:
            pass
        try:
            self.dasrcn.interrogators[0].acquisitions[0].acquisition_end_time = self.endexperiment
            self.dasrcn.end_date = self.endexperiment.date() if self.endexperiment is not None else self.endexperiment
        except Exception:
            pass

        # Set the time window selection to the minimum datetime found
        if (self.__twstart is None) or (self.__twstart < self.__available[0].dt):
            self.__twstart = self.__available[0].dt

        # Recover values of start and endtime
        self.reset()

        # Define a buffer to store the stream
        # Keys will be channel number and the values will be np.arrays
        self.__buffer = dict()

        self.__logs.debug('Starttime: %s ; Endtime: %s' % (self.__twstart, self.__twend))

    def __inspect_files(self) -> List[DASFile]:
        """Loop through files and create a list with basic properties"""
        # Loop through files and load them in __available as 'YYYYMMDD/TTmmSS'
        experimentdir = os.path.join(self.__directory, self.__experiment)
        self.__logs.debug('Experiment directory: %s' % experimentdir)
        if not os.path.isdir(experimentdir):
            raise NoData()

        result = list()  # type: List[DASFile]
        # Sort based on the name of the Direntry
        for day in sorted(os.scandir(experimentdir), key=lambda x: x.name):  # type: os.DirEntry
            # Entry must be a directory
            if not day.is_dir():
                continue

            self.__logs.debug('Checking day: %s' % day.name)
            # Check format of the directory name (YYYYMMDD)
            try:
                dt = datetime.datetime.strptime(day.name, '%Y%m%d')
            except ValueError:
                self.__logs.warning('Unexpected format in directory name! Date expected... (%s)' % day.name)
                continue

            daydir = os.path.join(experimentdir, day.name, 'dphi')

            for file in sorted(os.scandir(daydir), key=lambda x: x.name):  # type: os.DirEntry
                # Entry must be a file
                if file.is_dir():
                    continue

                self.__logs.debug('Checking time: %s' % file.name)
                # Entry must be a hdf5 file
                if not file.name.endswith('.hdf5'):
                    continue

                # Check that the format of the filename is exactly as expected. Otherwise, send a warning
                try:
                    dt = datetime.datetime.strptime(day.name + file.name[:-5], '%Y%m%d%H%M%S')
                except ValueError:
                    self.__logs.warning('Unexpected format in file name! Time expected... (%s)' % file.name)
                    continue

                # Read with h5py
                fname = os.path.join(daydir, file.name)
                # TODO Check if this is needed or we can skip it by using the part of the filename with the time
                self.__fi = File(fname)
                try:
                    # Reset some properties before opening the new file. starttime will be completed in '__readmetadata'
                    self.starttime = None
                    self.__readmetadata()
                except PotentialGap:
                    continue

                # Add only if this file lies within the requested time window
                if (self.__twstart is not None) and (self.endtime < self.__twstart):
                    self.__logs.debug('File before the selected time window. Discarding...')
                    # Skip to the next one
                    continue
                if (self.__twend is not None) and (self.__twend < dt):
                    # We are already after the endtime requested, so break the loop
                    self.__logs.debug('File after the selected time window. Discarding...')
                    break
                result.append(DASFile(dt=self.starttime, dtend=self.endtime, name=fname, samples=self.__samples))

        result.sort(key=lambda x: x.dt)
        return result

    # FIXME This is awful, but it works until I can refactor the "endtime" property
    @property
    def endexperiment(self) -> Union[datetime.datetime, None]:
        try:
            return self.__available[-1].dtend
        except Exception:
            return None

    @property
    def shape(self) -> Tuple[int, int]:
        return sum([f.samples for f in self.__available]), len(self.channels)

    def __select_file(self):
        """Select a file from the experiment based on the status of the object

        :raise Exception: If data not available in the specified time window. If the header does not
        indicate that the file is a TDMS format
        :raise IndexError: If the last file has already been processed or the start is greater than end
        """
        self.__logs = logging.getLogger('Select file')
        self.__logs.setLevel(self.__loglevel)

        if self.__currentfile is None:
            if (self.__twstart is None) or (self.__twstart is not None and self.__twstart < self.__available[0].dt):
                self.__twstart = self.__available[0].dt
            for idx, fi in enumerate(self.__available):
                if fi.dt <= self.__twstart <= fi.dtend:
                    filename = os.path.join(self.__directory, self.__available[idx].name)
                    self.__currentfile = idx
                    self.__logs.debug(
                        'Opening %s; Starttime: %s' % (self.__available[self.__currentfile].name, self.__twstart))
                    break
            else:
                # raise Exception('Data not available in the specified time window')
                raise IndexError
        elif self.__currentfile >= len(self.__available):
            self.__logs.debug('Last file already processed')
            # No more data to iterate
            raise IndexError
        else:
            filename = self.__available[self.__currentfile].name
            self.__twstart = self.__available[self.__currentfile].dt
            if (self.__twend is not None) and (self.__twstart > self.__twend):
                self.__logs.debug('Start is greater than end. %s %s' % (self.__twstart, self.__twend))
                raise IndexError
            self.__logs.debug('Opening %s; Starttime: %s' % (self.__available[self.__currentfile].name, self.__twstart))

        # FIXME If we don't open the File before, we need to do it here and after that set starttime and endtime
        # Reset some properties before opening the new file
        self.starttime = self.__available[self.__currentfile].dt
        # print(self.starttime)
        # self.endtime = None
        self.endtime = self.__available[self.__currentfile].dtend
        self.metadata = dict()

        # Read with h5py
        self.__fi = File(filename)

        # TODO All input from now on will be formatted by this
        # For OptoDAS we hardcode this as little endian
        self.__endian = '>'

    def __search_data(self):
        """
        Select a file to work with, read its metadata and calculate samples to read

        :raise IndexError: If the last file has already been processed or the start is greater than end
        """
        while True:
            # Loop through files until there is nothing else (IndexError)
            try:
                self.__select_file()
            except IndexError:
                raise
            except Exception as e:
                self.__logs.warning('Skipping file because of %s' % str(e))
                self.__currentfile += 1
                continue

            # Read the metadata and calculate samples to read
            # Skip to the next file if there is a gap
            try:
                self.__readmetadata()
                return
            except NoData:
                self.__logs.error('No Data was found in the metadata definition')
                self.__currentfile += 1
            except PotentialGap:
                self.__logs.warning('Potential gap detected!')
                self.__currentfile += 1

    # Read all metadata from the HDF5 file
    def __readgroup(self, grp: Group):
        grpdict = dict()
        for k, v in grp.items():
            # print(v.name)
            if isinstance(v, Dataset) and v.name != '/data':
                grpdict[k] = v[()]
            elif isinstance(v, Dataset) and v.name == '/data':
                grpdict[k] = v.dtype
            elif isinstance(v, Group):
                grpdict[k] = self.__readgroup(v)
        return grpdict

    # Loads all metadata from the file in an attribute
    def __readmetadata(self):
        """
        Read the metadata from the HDF5 file

        WARNING: This method sets the attribute "endtime" to show the expected time of last sample of the file.
        Also, in the case that "channels" has not been set it will be set here to the default value of all channels.
        """
        self.__logs = logging.getLogger('Read metadata')
        self.__logs.setLevel(self.__loglevel)

        self.metadata = self.__readgroup(self.__fi)
        self.__datatype = self.metadata['data']
        # Check version and signature of the file
        if self.metadata['fileVersion'] not in (7, 8):
            self.__logs.warning('File version is not 7 or 8!')

        if self.sampling_rate is None:
            self.sampling_rate = 1.0/self.metadata['header']['dt']
            # Set the sampling rate in the DAS-RCN metadata
            self.dasrcn.interrogators[0].acquisitions[0].acquisition_sample_rate = self.sampling_rate
            self.dasrcn.interrogators[0].acquisitions[0].acquisition_sample_rate_unit = 'Hertz'

        try:
            # Save GaugeLength
            self.dasrcn.interrogators[0].acquisitions[0].gauge_length = self.metadata['header']['gaugeLength']
            self.dasrcn.interrogators[0].acquisitions[0].gauge_length_unit = 'meter'
        except KeyError:
            pass

        try:
            # Save Unit of measure
            self.dasrcn.interrogators[0].acquisitions[0].unit_of_measure = 'strain-rate' if self.metadata['header']['unit'].decode() in ('rad/(s·m)', 'rad/m/s') else 'count'
        except KeyError:
            pass

        try:
            # Save Spatial Resolution [m]
            self.dasrcn.interrogators[0].acquisitions[0].spatial_sampling_interval = self.metadata['header']['dx']
            self.dasrcn.interrogators[0].acquisitions[0].spatial_sampling_interval_unit = 'meter'
        except KeyError:
            pass

        try:
            # Save refraction index
            self.dasrcn.cables[0].fibers[0].fiber_refraction_index = self.metadata['cableSpec']['refractiveIndex']
        except KeyError:
            pass

        try:
            # Save version
            model = self.metadata['header']['instrument']
            self.dasrcn.interrogators[0].model = model.decode() if isinstance(model, bytes) else model
        except KeyError:
            pass

        curstarttime = datetime.datetime.utcfromtimestamp(self.metadata['header']['time'])
        if self.starttime is None:
            self.starttime = curstarttime
        # print(type(curstarttime), curstarttime)
        # TODO Check if nChannels is available in version 8!
        self.numchannels = self.metadata['header']['nChannels'] if self.metadata['fileVersion'] == 7 else \
            len(self.metadata['header']['channels'])
        # print(self.metadata['fileVersion'])
        # print(self.metadata['header']['nChannels'] if self.metadata['fileVersion'] == 7 else self.metadata['header']['channels'])

        # If channels were not selected we can safely set that here to all channels
        if self.channels is None:
            self.channels = self.metadata['header']['channels']

        # Save the number of channels in DAS-RCN format
        self.dasrcn.interrogators[0].acquisitions[0].number_of_channels = len(self.channels)
        # Add ChannelGroup
        self.dasrcn.interrogators[0].acquisitions[0].channel_groups = [ChannelGroupModel()]
        aux = self.dasrcn.interrogators[0].acquisitions[0].channel_groups[0]
        aux.first_usable_channel_id = int2stationcode(self.channels[0])
        aux.last_usable_channel_id = int2stationcode(self.channels[-1])
        # And add the channels
        for idx, cha in enumerate(self.channels):
            aux.channels.append(ChannelModel(channel_id=int2stationcode(cha),
                                             distance_along_fiber=self.metadata['cableSpec']['sensorDistances'][idx],
                                             x_coordinate=0,
                                             y_coordinate=0))

        # Create a mapping between channel ID and index
        chmap = dict()
        for idx, ch in enumerate(self.metadata['header']['channels']):
            chmap[ch] = idx

        # Keep the indexes of where the channels really are (column in 2D array)
        self.__channelsidx = [chmap[ch] for ch in self.channels]
        self.__logs.debug('From channels %s to %s' % (self.channels, self.__channelsidx))

        # TODO In version 8 I should check in dimensionSizes
        self.__samples = self.metadata['header']['nSamples'] if self.metadata['fileVersion'] == 7 else \
            self.metadata['header']['dimensionSizes'][0]

        # Calculate endtime based on the number of samples declared and the sampling rate
        self.endtime = self.starttime + datetime.timedelta(seconds=(self.__samples-1) * self.metadata['header']['dt'])

        if (self.__twstart is not None) and (self.endtime < self.__twstart):
            raise PotentialGap(self.endtime, (self.__twstart-self.endtime).total_seconds(),
                               'End time of file before of time window (%s < %s)' % (self.endtime, self.__twstart))

        if (self.__twend is not None) and (self.__twend < self.starttime):
            raise PotentialGap(self.__twend, (self.starttime-self.__twend).total_seconds(),
                               'Start time of file after time window (%s < %s)' % (self.__twend, self.starttime))

        # Sample to start extraction from based on the initial datetime of the file (__twstart)
        if self.__twstart is not None:
            self.__samplestart = max(
                floor((self.__twstart - self.starttime).total_seconds() / self.metadata['header']['dt']), 0)
        else:
            self.__samplestart = 0

        # Should I readjust __twstart to align it exactly with the time of the samples?
        self.__twstart = self.starttime + datetime.timedelta(seconds=self.__samplestart * self.metadata['header']['dt'])

        self.__samplecur = self.__samplestart

        # Open end or beyond this file: read until the last sample
        if (self.__twend is None) or (self.__twend >= self.endtime):
            self.__sampleend = self.__samples-1
        else:
            # Otherwise calculate which one is the last sample to read
            self.__sampleend = ceil((self.__twend - self.starttime).total_seconds() / self.metadata['header']['dt'])

        self.__logs.debug('Samples: %s' % self.__samples)
        self.__logs.debug('Samples selected: %s-%s' % (self.__samplestart, self.__sampleend))

    def reset(self):
        """Reset the status of the object and start the read again

        :raise IndexError: If the last file has already been processed or the start is greater than end
        """
        self.__twstart = self.__origstarttime
        self.__twend = self.__origendtime
        self.__currentfile = None
        self.__search_data()

    def __iter_data__(self):
        """Read data from files based on channel selection

        :return: Data and attributes for the header
        :rtype: tuple(numpy.array, obspy.core.trace.Stats)
        """
        # Multiply by dataScale and unwrap signal
        # data = data * self.metadata['header']['dataScale']
        # data=unwrap(data, self.metadata['header']['spatialUnwrRange'], axis=1)
        auxdata = unwrap(self.__fi['data'] * self.metadata['header']['dataScale'],
                         self.metadata['header']['spatialUnwrRange'], axis=1)
        # print('After unwrap', auxdata[:10,0])
        # Keep only requested channels
        auxdata2 = auxdata[:, self.__channelsidx]
        del auxdata
        # WARNING ! Integration in time could be tricky. It needs to sum cumulatively the signal.
        # If there are gaps, the absolute value should be recovered from the metadaata (meta['header']['phiOffs'])
        # where one can find a starting value for each selected channel.
        # auxdata2 = np.cumsum(auxdata2, axis=0) * self.metadata['header']['dt']
        # print('After cumsum', auxdata2[:10,0])
        # Use the sensitivity
        sensitivity = self.metadata['header']['sensitivity'] if self.metadata['fileVersion'] == 7\
            else self.metadata['header']['sensitivities'][0,0]
        auxdata2 /= sensitivity
        # print('After sensitivity', auxdata2[:10,0])
        # Keep only requested samples
        auxdata2 = auxdata2[self.__samplestart:self.__sampleend + 1, :].astype(self.__outdatatype)
        # Transpose the matrix to loop through rows, not columns
        newauxdata2 = auxdata2.T
        del auxdata2

        # Data
        self.__logs = logging.getLogger('Iterate Data')
        self.__logs.setLevel(self.__loglevel)

        while (self.__twend is None) or (self.__twstart < self.__twend):
            # data = self.__readdata(channels=self.channels)
            # Loop through channels
            for idx, ch in enumerate(self.channels):
                # Get the real position as column in 2D array
                # data = self.__fi['data'][self.__samplestart:self.__sampleend + 1, self.__channelsidx[idx]]
                data = newauxdata2[idx, :]
                # Integrate in time
                # data = np.cumsum(data, axis=0) * self.metadata['header']['dt']
                # Use the sensitivity
                # data /= sensitivity

                stats = Stats()
                stats.network = self.__networkcode
                stats.station = '%05d' % ch
                stats.location = ''
                stats.channel = self.__channelcode
                stats.sampling_rate = self.sampling_rate
                stats.npts = len(data)
                stats.starttime = UTCDateTime(self.__twstart)
                # stats.mseed = AttribDict()
                # stats.mseed.byteorder = self.__endian
                # stats.mseed.dataquality = 'D'
                # stats.mseed.record_length = 512
                # stats.mseed.blkt1001 = AttribDict()
                # stats.mseed.blkt1001.timing_quality = 100

                self.__logs.debug('Data length: %d; First component: %s' % (len(data), data[0]))
                self.__logs.debug('Stats: %s' % (stats,))
                yield Waveform(data, stats)

            # No more data in this file. Skip to the next one.
            self.__currentfile += 1
            try:
                self.__logs.debug('Moving to next file...')
                self.__search_data()
                # Multiply by dataScale and unwrap signal
                auxdata = unwrap(self.__fi['data'] * self.metadata['header']['dataScale'],
                                 self.metadata['header']['spatialUnwrRange'], axis=1)
                # Keep only requested channels
                auxdata2 = auxdata[:, self.__channelsidx]
                del auxdata
                # Use the sensitivity
                sensitivity = self.metadata['header']['sensitivity'] if self.metadata['fileVersion'] == 7 \
                    else self.metadata['header']['sensitivities'][0, 0]
                auxdata2 /= sensitivity
                # Keep only requested samples
                auxdata2 = auxdata2[self.__samplestart:self.__sampleend + 1, :].astype(self.__outdatatype)
                # Transpose the matrix to loop through rows, not columns
                newauxdata2 = auxdata2.T
                del auxdata2
            except IndexError:
                break

    def __iter_metadata__(self) -> dict:
        """Read metadata from files based on channel selection

        :return: Metadata from selected channels
        :rtype: dict
        """
        # Metadata
        self.__logs = logging.getLogger('Iterate Metadata')
        self.__logs.setLevel(self.__loglevel)

        while (self.__twend is None) or (self.__twstart < self.__twend):
            for obj in self.metadata:
                # TODO Check if this is needed
                # if 'id' in self.metadata[obj] and self.metadata[obj]['id'] not in self.channels:
                #     continue
                yield {obj: self.metadata[obj]}

            # No more data in this file. Skip to the next one.
            self.__currentfile += 1
            try:
                self.__search_data()
            except IndexError:
                break

    def __iter_files__(self):
        """List files and basic properties based on selection

        :return: Properties of files
        :rtype: dict
        """
        # Files
        self.__logs = logging.getLogger('Iterate Files')
        self.__logs.setLevel(self.__loglevel)

        for av in self.__available:
            yield av


class OptoDAS(Das):
    """Class to read, process and export seismic waveforms in OptoDAS format

Files read in this format are converted to miniSEED without time integration.
Therefore, the units of the output will be usually strain rate.

    """

    def __enter__(self):
        """Method which allows to use the syntax 'with object:' and use it inside

        Create a buffer space to store the signal coefficients to be convoluted during the decimation
        """
        for channel in self.channels:
            self.__logs.debug('Create empty buffer for channel %s' % channel)
            self.__buffer[channel] = None

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Method which close open resources after using the syntax 'with object:' and use it inside"""
        if self.__fi is not None:
            self.__fi.close()

    def __iter__(self):
        """Iterate through data (or metadata) and filter and decimate if requested

        :returns: Data and attributes for the header, or metadata
        :rtype: tuple(numpy.array, obspy.core.trace.Stats) or dict
        """
        # Create logger
        self.__logs = logging.getLogger('__iter__')
        self.__logs.setLevel(self.__loglevel)

        if self.iterate == 'M':
            for info in self.__iter_metadata__():
                yield info
            return

        if self.iterate == 'F':
            for info in self.__iter_files__():
                yield info
            return

        # In the case that we iterate to get data
        # If no decimation is needed
        if self.__decimate == 1:
            for data, stats in self.__iter_data__():
                # yield data.astype(self.__outdatatype), stats
                yield data, stats
            return

        # Data has to be decimated
        # Use an input buffer to store the data coming in chunks from __iter_data__
        inbuf = dict()
        # Keep values in a buffer before returning them to be packed in miniSEED records
        # Otherwise, the chunks could be too short and the final size of the mSEED
        # would be too large
        outbuf = dict()
        # Keep filtered values which should be later decimated
        nodecimation = dict()
        # Time of the first sample in the next file
        expectedtime = dict()
        # Flag to know if we are at the beginning of the chunk
        # There should be one entry per channel with a default value of True
        startofchunk = dict()

        for data, stats in self.__iter_data__():
            ch = int(stats['station'])

            # Check expected time for each channel
            if ch in expectedtime:
                if expectedtime[ch] != stats['starttime']:
                    self.__logs.warning('GAP! Expected: %s ; Current: %s' % (expectedtime[ch], stats['starttime']))
                    # Gap!
                    if ch in inbuf:
                        self.__logs.debug('Remove last %s components of previous chunk' % len(inbuf[ch]['data']))
                        del inbuf[ch]

                    # Flush outbuf?
                    if ch in outbuf:
                        if 'data' in outbuf[ch]:
                            # Set number of points
                            outbuf[ch]['stats']['npts'] = len(outbuf[ch]['data'])
                            # outbuf[ch]['stats']['starttime'] += 1/outbuf[ch]['stats']['sampling_rate']
                            # outbuf[ch]['stats']['npts'] = 1
                            self.__logs.debug('Flushing: %s %s' % (outbuf[ch]['stats'], outbuf[ch]['data']))
                            yield outbuf[ch]['data'], outbuf[ch]['stats']
                        # Remove all data and stats from the output buffer after a GAP
                        del outbuf[ch]
                    else:
                        self.__logs.debug('Nothing to flush after GAP')
                    # self.__buffer[ch] = None
                    del expectedtime[ch]
                    # Start the processing of a new chunk after the gap
                    startofchunk[ch] = True

            expectedtime[ch] = stats['starttime'] + stats['npts']/self.sampling_rate

            # Store values coming from __iter_data__
            if ch not in inbuf:
                # Initialize an idx and array with the first chunk of data
                inbuf[ch] = {'data': np.array(data),
                             'stats': stats}
                # print('inbuf: %s' % inbuf[ch]['stats'])
            else:
                inbuf[ch]['data'] = np.append(inbuf[ch]['data'], data)

            # Set values of stats for the output buffer resulting from the convolution
            if ch not in outbuf:
                # Initialize an idx and array with the first chunk of data
                outbuf[ch] = {'stats': inbuf[ch]['stats'].copy()}

                # Modify the starting time only if it is the beginning of the signal
                if (ch not in startofchunk) or startofchunk[ch]:
                    outbuf[ch]['stats']['starttime'] += (len(self.__filter)-1)/(2 * outbuf[ch]['stats']['sampling_rate'])
                    startofchunk[ch] = False

                # Change the headers to reflect the decimation
                # Reduce the sampling rate by the decimation factor
                outbuf[ch]['stats']['sampling_rate'] = stats['sampling_rate']/self.__decimate
                # print('outbuf new: %s' % outbuf[ch]['stats'])

            # If there are not enough components move to the next chunk
            if len(inbuf[ch]['data']) < len(self.__filter):
                continue

            # Convolution of inbuf with filter and then leave the last 234 values (len(filter)-1)
            # This convolution is performed on a long array (inbuf) and a default filter with 235 components
            # We save the result of the convolution as int32 to be able to use STEIM2 later
            nodecimation[ch] = np.convolve(inbuf[ch]['data'], self.__filter, 'valid').astype(self.__outdatatype)
            self.__logs.debug('filtered: %d components' % len(nodecimation[ch]))
            self.__logs.debug('filtered[%d][:11] %s' % (ch, nodecimation[ch][:11]))
            self.__logs.debug('filtered[%d][-11:] %s' % (ch, nodecimation[ch][-11:]))

            # Check if we can copy as many components as a multiple of the decimation factor
            leftover = len(nodecimation[ch]) % self.__decimate
            self.__logs.debug('filtered: leave %d components for next iteration %s' %
                       (leftover, nodecimation[ch][-leftover:]))

            if leftover:
                if 'data' not in outbuf[ch]:
                    # Take samples each "self.__decimate" components
                    outbuf[ch]['data'] = nodecimation[ch][:-leftover:self.__decimate]
                else:
                    # Add samples each "self.__decimate" components
                    outbuf[ch]['data'] = np.append(outbuf[ch]['data'],
                                                   nodecimation[ch][:-leftover:self.__decimate])
            else:
                if 'data' not in outbuf[ch]:
                    # Take samples each "self.__decimate" components
                    outbuf[ch]['data'] = nodecimation[ch][::self.__decimate]
                else:
                    # Add samples each "self.__decimate" components
                    outbuf[ch]['data'] = np.append(outbuf[ch]['data'], nodecimation[ch][::self.__decimate])

            # Remove filtered signal after copying it to the output buffer
            del nodecimation[ch]

            self.__logs.debug('outbuf[%d][:11] %s' % (ch, outbuf[ch]['data'][:11]))
            self.__logs.debug('outbuf[%d][-11:] %s' % (ch, outbuf[ch]['data'][-11:]))

            # Keep values which will be needed to start again in the next file
            # to avoid boundary effects. leftover comes from the extra values we already calculated,
            # but we could not use because of decimation. Therefore, we will put them in the beginning
            # and calculate again
            valuesprocessed = len(inbuf[ch]['data']) - len(self.__filter) + 1 - leftover
            self.__logs.debug('values processed: %d' % valuesprocessed)
            inbuf[ch]['data'] = inbuf[ch]['data'][-len(self.__filter)+1-leftover:]
            inbuf[ch]['stats']['starttime'] += valuesprocessed / inbuf[ch]['stats']['sampling_rate']

            # If there is enough data
            if len(outbuf[ch]['data']) > 2000:
                outbuf[ch]['stats']['npts'] = len(outbuf[ch]['data'])
                self.__logs.debug('Sending: %s %s' % (outbuf[ch]['stats'], outbuf[ch]['data']))
                yield outbuf[ch]['data'], outbuf[ch]['stats']
                # Reset outbuf with an empty array and the next starttime (in headers)
                outbuf[ch]['stats']['starttime'] += len(outbuf[ch]['data']) / outbuf[ch]['stats']['sampling_rate']
                del outbuf[ch]['data']

        # Do I need here to flush all remaining components from outbuf?
        for ch in outbuf:
            if ('data' in outbuf[ch]) and len(outbuf[ch]['data']):
                outbuf[ch]['stats']['npts'] = len(outbuf[ch]['data'])
                self.__logs.debug('Sending: %s %s' % (outbuf[ch]['stats'], outbuf[ch]['data']))
                yield outbuf[ch]['data'], outbuf[ch]['stats']
                outbuf[ch]['stats']['starttime'] += len(outbuf[ch]['data']) / outbuf[ch]['stats']['sampling_rate']
                del outbuf[ch]['data']

    def __init__(self, experiment: str, directory: str = '.', channels: list = None,
                 starttime: datetime.datetime = None,
                 endtime: datetime.datetime = None, iterate: str = 'D', decimate: int = 1,
                 firfilter: str = 'fir235', networkcode: str = 'XX', channelcode: str = 'HSF',
                 loglevel: str = 'INFO'):
        """Initialize the OptaDAS object selecting the data, channels and decimation

        :param experiment: Experiment to read and process. Usually the name of the root directory
        :type experiment: str
        :param directory: Directory where experiment is stored
        :type directory: str
        :param channels: Selection of channels to work with (list of integers)
        :type channels: list or NoneType
        :param starttime: Start of the selected time window
        :type starttime: datetime.datetime or NoneType
        :param endtime: End of the selected time window
        :type endtime: datetime.datetime or NoneType
        :param iterate: Select either Data (D), or Metadata (M), or Files (F)
        :type iterate: str
        :param decimate: Factor by which the sampling rate is lowered by decimation
        :type decimate: int
        :param firfilter: Filter to apply in case of decimation (fir235 is the only option)
        :type firfilter: str
        :param networkcode: Network code of the experiment. It has to be two alphanumeric characters
        :type networkcode: str
        :param channelcode: Channel code of the experiment. It has to be three alphanumeric characters
        :type channelcode: str
        :param loglevel: Verbosity in the output
        :type loglevel: str
        :raise TypeError: If chstart, or chstop, or chstep are not int. If channels is not a list, or networkcode is
        not a 2 characters code, or channelcode is not a 3 characters code.
        :raise Exception: If channels is empty.
        :raise NoData: If there is no more data available
        """

        # Raise a Deprecation Warning!
        warn("OptoDAS has been deprecated. Please, use OptoDASReader instead", DeprecationWarning, 2)
        # Log level
        self.__loglevel = loglevel
        self.__logs = logging.getLogger('OptoDAS.init')
        self.__logs.setLevel(loglevel)
        self.__logs.info('Iterate through %s' % iterate)
        project_dir = os.path.join(os.path.dirname(__file__), '..')

        # Decimation factor
        self.__decimate = decimate

        # Selection of channels
        if not isinstance(channels, list) and channels is not None:
            self.__logs.error('channels must be a list of numbers or None')
            raise TypeError('channels must be a list of numbers or None')

        if not isinstance(networkcode, str) or len(networkcode) != 2:
            self.__logs.error('Network code has to be two alphanumeric characters')
            raise TypeError('Network code has to be two alphanumeric characters')

        if not isinstance(channelcode, str) or len(channelcode) != 3:
            self.__logs.error('Channel code has to be three alphanumeric characters')
            raise TypeError('Channel code has to be three alphanumeric characters')

        self.__networkcode = networkcode
        self.__channelcode = channelcode

        # channels has priority. Otherwise, chstart, chstop and chstep are used
        if channels is not None and isinstance(channels, list):
            self.channels = channels
            # List of channels cannot be empty
            if not len(self.channels):
                raise Exception('Channel list is empty!')

        else:
            # If chstart, chstop and chstep will define the selected channels we need to keep the three
            #  values (start, stop, step) and define the channels later in readmetadata
            self.channels = None
            # self.channels = list(range(chstart, chstop+1, chstep))

        # Time window selection
        self.__twstart = starttime
        self.__twend = endtime

        # Available time window
        self.starttime = None
        self.endtime = None

        # Sampling Rate
        self.sampling_rate = None

        # File currently being processed
        self.__currentfile = None

        # Name of file
        self.__experiment = experiment
        self.__directory = directory

        # What should we iterate? D: Data; M: Metadata
        self.iterate = iterate

        # Other variables to be read from the headers
        # self.__hasInterleavedData = None
        # self.__endian = None
        self.__datatype = None
        self.__datatypesize = None
        self.__outdatatype = '>f4'
        self.numchannels = None
        self.__samples = None
        self.__samplestart = None
        self.__sampleend = None
        self.__samplecur = None

        # Dictionary to save the metadata defined in the file
        self.metadata = dict()

        # Keep the values in case we need to reset them
        self.__origstarttime = self.__twstart
        self.__origendtime = self.__twend

        # Create a DAS-RCN metadata object and retrieve the items from the "metadata" attribute
        self.dasrcn = DASMetadata(network_code=networkcode,
                                  interrogators=[InterrogatorModel(manufacturer='Alcatel')])

        # List of available files in the directory
        self.__available = self.__inspect_files()
        self.__logs.debug(str(self.__available))
        if not len(self.__available):
            self.__logs.warning('No files found with proper filename.')
            raise NoData()

        # Set the start and end of the experiment
        try:
            self.dasrcn.interrogators[0].acquisitions[0].acquisition_start_time = self.__available[0].dt
            self.dasrcn.start_date = self.__available[0].dt.date()
        except Exception:
            pass
        try:
            self.dasrcn.interrogators[0].acquisitions[0].acquisition_end_time = self.endexperiment
            self.dasrcn.end_date = self.endexperiment.date() if self.endexperiment is not None else self.endexperiment
        except Exception:
            pass

        # print(self.__available)

        # Set the time window selection to the minimum datetime found
        if (self.__twstart is None) or (self.__twstart < self.__available[0].dt):
            self.__twstart = self.__available[0].dt

        # Recover values of start and endtime
        self.reset()

        # Define a buffer to store the window over the signal to be
        # convoluted with the FIR filter wile decimating
        # Keys will be channel number and the values will be np.arrays
        self.__buffer = dict()

        self.__logs.debug('Starttime: %s ; Endtime: %s' % (self.__twstart, self.__twend))

        # Read filter to decimate
        auxfilter = list()
        with open(os.path.join(project_dir, 'data/filters/%s.txt' % firfilter)) as fin:
            for line in fin.readlines():
                auxfilter.append(float(line))

        self.__filter = np.array(auxfilter)
        self.__logs.debug('FIR filter: %s' % (self.__filter[:5],))

    def __inspect_files(self) -> List[DASFile]:
        """Loop through files and create a list with basic properties"""
        # Loop through files and load them in __available as 'YYYYMMDD/TTmmSS'
        experimentdir = os.path.join(self.__directory, self.__experiment)
        self.__logs.debug('Experiment directory: %s' % experimentdir)
        if not os.path.isdir(experimentdir):
            raise NoData

        result = list()
        # Sort based on the name of the Direntry
        for day in sorted(os.scandir(experimentdir), key=lambda x: x.name):  # type: os.DirEntry
            # Entry must be a directory
            if not day.is_dir():
                continue

            self.__logs.debug('Checking day: %s' % day.name)
            # Check format of the directory name (YYYYMMDD)
            try:
                dt = datetime.datetime.strptime(day.name, '%Y%m%d')
            except ValueError:
                self.__logs.warning('Unexpected format in directory name! Date expected... (%s)' % day.name)
                continue

            daydir = os.path.join(experimentdir, day.name, 'dphi')

            for file in sorted(os.scandir(daydir), key=lambda x: x.name):  # type: os.DirEntry
                # Entry must be a file
                if file.is_dir():
                    continue

                self.__logs.debug('Checking time: %s' % file.name)
                # Entry must be a hdf5 file
                if not file.name.endswith('.hdf5'):
                    continue

                # Check that the format of the filename is exactly as expected. Otherwise, send a warning
                try:
                    dt = datetime.datetime.strptime(day.name + file.name[:-5], '%Y%m%d%H%M%S')
                except ValueError:
                    self.__logs.warning('Unexpected format in file name! Time expected... (%s)' % file.name)
                    continue

                # Read with h5py
                # self.__fi = File(os.path.join(experimentdir, day.name, file.name))
                fname = os.path.join(daydir, file.name)
                self.__fi = File(fname)
                try:
                    # Reset some properties before opening the new file. starttime will be completed in '__readmetadata'
                    self.starttime = None
                    self.__readmetadata()
                except PotentialGap:
                    continue

                # Add only if this file lies within the requested time window
                if (self.__twstart is not None) and (self.endtime < self.__twstart):
                    self.__logs.debug('File before the selected time window. Discarding...')
                    # Skip to the next one
                    continue
                if (self.__twend is not None) and (self.__twend < dt):
                    # We are already after the endtime requested, so break the loop
                    self.__logs.debug('File after the selected time window. Discarding...')
                    break
                result.append(DASFile(dt=self.starttime, dtend=self.endtime, name=fname, samples=self.__samples))

        result.sort(key=lambda x: x.dt)
        return result

    # FIXME This is awful, but it works until I can refactor the "endtime" property
    @property
    def endexperiment(self) -> Union[datetime.datetime, None]:
        try:
            return self.__available[-1].dtend
        except Exception:
            return None

    @property
    def shape(self) -> Tuple[int, int]:
        return sum([f.samples for f in self.__available]), len(self.channels)

    def __select_file(self):
        """Select a file from the experiment based on the status of the object

        :raise Exception: If data not available in the specified time window. If the header does not
        indicate that the file is a TDMS format
        :raise IndexError: If the last file has already been processed or the start is greater than end
        """
        self.__logs = logging.getLogger('Select file')
        self.__logs.setLevel(self.__loglevel)

        if self.__currentfile is None:
            if (self.__twstart is None) or (self.__twstart is not None and self.__twstart < self.__available[0].dt):
                self.__twstart = self.__available[0].dt
            for idx, fi in enumerate(self.__available):
                if fi.dt <= self.__twstart <= fi.dtend:
                    filename = os.path.join(self.__directory, self.__available[idx].name)
                    self.__currentfile = idx
                    self.__logs.debug(
                        'Opening %s; Starttime: %s' % (self.__available[self.__currentfile].name, self.__twstart))
                    break
            else:
                # raise Exception('Data not available in the specified time window')
                raise IndexError
        elif self.__currentfile >= len(self.__available):
            self.__logs.debug('Last file already processed')
            # No more data to iterate
            raise IndexError
        else:
            filename = self.__available[self.__currentfile].name
            self.__twstart = self.__available[self.__currentfile].dt
            if (self.__twend is not None) and (self.__twstart > self.__twend):
                self.__logs.debug('Start is greater than end. %s %s' % (self.__twstart, self.__twend))
                raise IndexError
            self.__logs.debug('Opening %s; Starttime: %s' % (self.__available[self.__currentfile].name, self.__twstart))

        # Reset some properties before opening the new file
        self.starttime = self.__available[self.__currentfile].dt
        # print(self.starttime)
        # self.endtime = None
        self.endtime = self.__available[self.__currentfile].dtend
        self.metadata = dict()

        # Read with h5py
        self.__fi = File(filename)

        # TODO All input from now on will be formatted by this
        # For OptoDAS we hardcode this as little endian
        self.__endian = '>'

    def __search_data(self):
        """
        Select a file to work with, read its metadata and calculate samples to read

        :raise IndexError: If the last file has already been processed or the start is greater than end
        """

        while True:
            # Loop through files until there is nothing else (IndexError)
            try:
                self.__select_file()
            except IndexError:
                raise
            except Exception as e:
                self.__logs.warning('Skipping file because of %s' % str(e))
                self.__currentfile += 1
                continue

            # Read the metadata and calculate samples to read
            # Skip to the next file if there is a gap
            try:
                self.__readmetadata()
                return
            except NoData:
                self.__logs.error('No Data was found in the metadata definition')
                self.__currentfile += 1
            except PotentialGap:
                self.__logs.warning('Potential gap detected!')
                self.__currentfile += 1

    # Read all metadata from the HDF5 file
    def __readgroup(self, grp: Group):
        grpdict = dict()
        for k, v in grp.items():
            # print(v.name)
            if isinstance(v, Dataset) and v.name != '/data':
                grpdict[k] = v[()]
            elif isinstance(v, Dataset) and v.name == '/data':
                grpdict[k] = v.dtype
            elif isinstance(v, Group):
                grpdict[k] = self.__readgroup(v)
        return grpdict

    # Loads all metadata from the file in an attribute
    def __readmetadata(self):
        """This method sets the attribute endtime showing the expected time of last sample of the file"""
        self.__logs = logging.getLogger('Read metadata')
        self.__logs.setLevel(self.__loglevel)

        self.metadata = self.__readgroup(self.__fi)
        self.__datatype = self.metadata['data']
        # Check version and signature of the file
        if self.metadata['fileVersion'] not in (7, 8):
            self.__logs.warning('File version is not 7 or 8!')

        if self.sampling_rate is None:
            self.sampling_rate = 1.0/self.metadata['header']['dt']
            # Set the sampling rate in the DAS-RCN metadata
            self.dasrcn.interrogators[0].acquisitions[0].acquisition_sample_rate = self.sampling_rate
            self.dasrcn.interrogators[0].acquisitions[0].acquisition_sample_rate_unit = 'Hertz'
            # Check for decimation and take into account the filter length
            if self.__decimate != 1:
                tap = (len(self.__filter) - 1) / (2.0 * self.sampling_rate)
                # If there is decimation adjust the start and end times to include the tapering
                # and later keep exactly what user requests
                self.__twstart -= datetime.timedelta(seconds=tap)
                if self.__twend is not None:
                    self.__twend += datetime.timedelta(seconds=tap)
                self.__logs.debug('Readjust start and end time to accommodate the filter length: %s - %s' %
                                  (self.__twstart, self.__twend))

        try:
            # Save GaugeLength
            self.dasrcn.interrogators[0].acquisitions[0].gauge_length = self.metadata['header']['gaugeLength']
            self.dasrcn.interrogators[0].acquisitions[0].gauge_length_unit = 'meter'
        except KeyError:
            pass

        try:
            # Save Unit of measure
            self.dasrcn.interrogators[0].acquisitions[0].unit_of_measure = 'strain-rate' if self.metadata['header']['unit'].decode() in ('rad/(s·m)', 'rad/m/s') else 'count'
        except KeyError:
            pass

        try:
            # Save Spatial Resolution [m]
            self.dasrcn.interrogators[0].acquisitions[0].spatial_sampling_interval = self.metadata['header']['dx']
            self.dasrcn.interrogators[0].acquisitions[0].spatial_sampling_interval_unit = 'meter'
        except KeyError:
            pass

        try:
            # Save refraction index
            self.dasrcn.cables[0].fibers[0].fiber_refraction_index = self.metadata['cableSpec']['refractiveIndex']
        except KeyError:
            pass

        try:
            # Save version
            model = self.metadata['header']['instrument']
            self.dasrcn.interrogators[0].model = model.decode() if isinstance(model, bytes) else model
        except KeyError:
            pass

        curstarttime = datetime.datetime.utcfromtimestamp(self.metadata['header']['time'])
        if self.starttime is None:
            self.starttime = curstarttime
        # print(type(curstarttime), curstarttime)
        # TODO Check if nChannels is available in version 8!
        self.numchannels = self.metadata['header']['nChannels'] if self.metadata['fileVersion'] == 7 else \
            len(self.metadata['header']['channels'])
        # print(self.numchannels)

        # Save the number of channels in DAS-RCN format
        self.dasrcn.interrogators[0].acquisitions[0].number_of_channels = len(self.channels)

        # Keep the indexes of where the channels really are (column in 2D array)
        self.__channelsidx = [self.metadata['header']['channels'].tolist().index(ch) for ch in self.channels]
        self.__logs.debug('From channels %s to %s' % (self.channels, self.__channelsidx))

        # TODO In version 8 I should check in dimensionSizes
        self.__samples = self.metadata['header']['nSamples'] if self.metadata['fileVersion'] == 7 else \
            self.metadata['header']['dimensionSizes'][0]

        # Calculate endtime based on the number of samples declared and the sampling rate
        self.endtime = self.starttime + datetime.timedelta(seconds=(self.__samples-1) * self.metadata['header']['dt'])

        if (self.__twstart is not None) and (self.endtime < self.__twstart):
            raise PotentialGap(start=self.endtime,
                               length=(self.__twstart-self.endtime).total_seconds(),
                               message='End time of file before of time window (%s < %s)' % (self.endtime, self.__twstart))

        if (self.__twend is not None) and (self.__twend < self.starttime):
            raise PotentialGap(start=self.__twend,
                               length=(self.starttime-self.__twend).total_seconds(),
                               message='Start time of file after time window (%s < %s)' % (self.__twend, self.starttime))

        # Sample to start extraction from based on the initial datetime of the file (__twstart)
        if self.__twstart is not None:
            self.__samplestart = max(
                floor((self.__twstart - self.starttime).total_seconds() / self.metadata['header']['dt']), 0)
        else:
            self.__samplestart = 0

        # if self.__samplestart >= self.__samples:
        #     raise PotentialGap('Start reading at %s, but only %s samples' % (self.__samplestart, self.__samples))

        # Should I readjust __twstart to align it exactly with the time of the samples?
        self.__twstart = self.starttime + datetime.timedelta(seconds=self.__samplestart * self.metadata['header']['dt'])

        self.__samplecur = self.__samplestart

        # Open end or beyond this file: read until the last sample
        if (self.__twend is None) or (self.__twend >= self.endtime):
            self.__sampleend = self.__samples-1
        else:
            # Otherwise calculate which one is the last sample to read
            self.__sampleend = ceil((self.__twend - self.starttime).total_seconds() / self.metadata['header']['dt'])
            # print(self.__twend, self.starttime, (self.__twend - self.starttime).total_seconds(), self.__sampleend)

        self.__logs.debug('Samples: %s' % self.__samples)
        self.__logs.debug('Samples selected: %s-%s' % (self.__samplestart, self.__sampleend))
        # print('Samples: %s' % self.__samples)
        # print('Samples selected: %s-%s' % (self.__samplestart, self.__sampleend))

    def reset(self):
        """Reset the status of the object and start the read again

        :raise IndexError: If the last file has already been processed or the start is greater than end
        """
        self.__twstart = self.__origstarttime
        self.__twend = self.__origendtime
        self.__currentfile = None
        self.__search_data()

    def __iter_data__(self):
        """Read data from files based on channel selection

        :return: Data and attributes for the header
        :rtype: tuple(numpy.array, obspy.core.trace.Stats)
        """
        # Multiply by dataScale and unwrap signal
        # data = data * self.metadata['header']['dataScale']
        # data=unwrap(data, self.metadata['header']['spatialUnwrRange'], axis=1)
        auxdata = unwrap(self.__fi['data'] * self.metadata['header']['dataScale'],
                         self.metadata['header']['spatialUnwrRange'], axis=1)
        # print('After unwrap', auxdata[:10,0])
        # Keep only requested channels
        auxdata2 = auxdata[:, self.__channelsidx]
        del auxdata
        # WARNING ! Integration in time could be tricky. It needs to sum cumulatively the signal.
        # If there are gaps, the absolute value should be recovered from the metadaata (meta['header']['phiOffs'])
        # where one can find a starting value for each selected channel.
        # auxdata2 = np.cumsum(auxdata2, axis=0) * self.metadata['header']['dt']
        # print('After cumsum', auxdata2[:10,0])
        # Use the sensitivity
        sensitivity = self.metadata['header']['sensitivity'] if self.metadata['fileVersion'] == 7\
            else self.metadata['header']['sensitivities'][0,0]
        auxdata2 /= sensitivity
        # print('After sensitivity', auxdata2[:10,0])
        # Keep only requested samples
        auxdata2 = auxdata2[self.__samplestart:self.__sampleend + 1, :].astype(self.__outdatatype)

        # Data
        self.__logs = logging.getLogger('Iterate Data')
        self.__logs.setLevel(self.__loglevel)

        while (self.__twend is None) or (self.__twstart < self.__twend):
            # data = self.__readdata(channels=self.channels)
            # Loop through channels
            for idx, ch in enumerate(self.channels):
                # Get the real position as column in 2D array
                # data = self.__fi['data'][self.__samplestart:self.__sampleend + 1, self.__channelsidx[idx]]
                data = auxdata2[:, idx]
                # Integrate in time
                # data = np.cumsum(data, axis=0) * self.metadata['header']['dt']
                # Use the sensitivity
                # data /= sensitivity

                stats = Stats()
                stats.network = self.__networkcode
                stats.station = '%05d' % ch
                stats.location = ''
                stats.channel = self.__channelcode
                stats.sampling_rate = self.sampling_rate
                stats.npts = len(data)
                stats.starttime = UTCDateTime(self.__twstart)
                stats.mseed = AttribDict()
                stats.mseed.byteorder = self.__endian
                stats.mseed.dataquality = 'D'
                stats.mseed.record_length = 512
                stats.mseed.blkt1001 = AttribDict()
                stats.mseed.blkt1001.timing_quality = 100

                self.__logs.debug('Data length: %d; First component: %s' % (len(data), data[0]))
                self.__logs.debug('Stats: %s' % (stats,))
                yield data, stats

            # No more data in this file. Skip to the next one.
            self.__currentfile += 1
            try:
                self.__logs.debug('Moving to next file...')
                self.__search_data()
                # Multiply by dataScale and Unwrap
                # auxdata = unwrap(self.__fi['data'] * self.metadata['header']['dataScale'],
                #                  self.metadata['header']['spatialUnwrRange'], axis=1)
                # auxdata2 = auxdata[self.__samplestart:self.__sampleend + 1, self.__channelsidx]
                # del auxdata
            except IndexError:
                break

    def __iter_metadata__(self) -> dict:
        """Read metadata from files based on channel selection

        :return: Metadata from selected channels
        :rtype: dict
        """
        # Metadata
        self.__logs = logging.getLogger('Iterate Metadata')
        self.__logs.setLevel(self.__loglevel)

        while (self.__twend is None) or (self.__twstart < self.__twend):
            for obj in self.metadata:
                # TODO Check if this is needed
                # if 'id' in self.metadata[obj] and self.metadata[obj]['id'] not in self.channels:
                #     continue
                yield {obj: self.metadata[obj]}

            # No more data in this file. Skip to the next one.
            self.__currentfile += 1
            try:
                self.__search_data()
            except IndexError:
                break

    def __iter_files__(self):
        """List files and basic properties based on selection

        :return: Properties of files
        :rtype: dict
        """
        # Files
        self.__logs = logging.getLogger('Iterate Files')
        self.__logs.setLevel(self.__loglevel)

        for av in self.__available:
            yield av
