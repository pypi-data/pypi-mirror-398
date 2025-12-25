"""Febus module from dastools.

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
from typing import Iterable
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
from pydantic import StringConstraints
from typing_extensions import Annotated


# TODO Add function to loop through files
def filegenerator(experiment: str, directory: Path = '.'):
    # Loop through files to check that they are in Febus format
    if not os.path.isdir(directory):
        return

    for file in sorted(os.scandir(directory), key=lambda x: x.name):  # type: os.DirEntry
        # Entry must be a file and end with hdf5 file
        if file.is_dir() or not file.name.endswith('.h5'):
            continue

        # Check that the format of the filename is exactly as expected. Otherwise, send a warning
        try:
            dt = datetime.datetime.strptime(file.name, experiment + '_%Y-%m-%d_%H-%M-%S_UTC.h5')
        except ValueError:
            logging.warning('Unexpected format in file name! Time expected... (%s)' % file.name)
            continue

        # Read with h5py
        fname = os.path.join(directory, file.name)
        try:
            fin = File(fname)
            yield fname
        except Exception:
            continue
    return


class FebusDetector(DASDetector):
    def checkDASdata(self, experiment: str, directory: Path = '.') -> bool:
        log = logging.getLogger('OptoDASDetector')
        for aux in filegenerator(experiment, directory):
            return True
        return False


class FebusReader(Das):
    """Class to read seismic waveforms in Febus format"""

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
    def __init__(self, experiment: str, directory: DirectoryPath = Path('.'),
                 channels: Union[conlist(int, min_length=1), None] = None,
                 starttime: Union[datetime.datetime, None] = None, endtime: Union[datetime.datetime, None] = None,
                 networkcode: Annotated[str, StringConstraints(strip_whitespace=True, to_upper=True, min_length=2, max_length=2)] = 'XX',
                 channelcode: Annotated[str, StringConstraints(strip_whitespace=True, to_upper=True, min_length=3, max_length=3)] = 'HSF',
                 loglevel: str = 'INFO'):
        """Initialize the Febus object selecting the data and channels

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
        self.__logs = logging.getLogger('FebusReader.init')
        self.__logs.setLevel(loglevel)

        # Name of file
        self.__experiment = experiment
        self.__directory = directory
        self.__networkcode = networkcode
        self.__channelcode = channelcode
        self.channels = channels

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
                                  interrogators=[InterrogatorModel(manufacturer='Febus')])

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
        # Loop through files and load them in __available as 'EXPERIMENT_YYYY-MM-DD_HH-mm-SS_UTC.h5'
        self.__logs.debug('Experiment directory: %s' % self.__directory)
        if not os.path.isdir(self.__directory):
            raise NoData()

        result = list()  # type: List[DASFile]
        # Sort based on the name of the Direntry
        for file in sorted(os.scandir(self.__directory), key=lambda x: x.name):  # type: os.DirEntry
            # Entry must be a file
            if file.is_dir():
                continue

            # Check format of the directory name (YYYYMMDD)
            try:
                dt = datetime.datetime.strptime(file.name, self.__experiment + '_%Y-%m-%d_%H-%M-%S_UTC.h5')
            except ValueError:
                self.__logs.warning('Unexpected format in directory name! Date expected... (%s)' % file.name)
                continue

            # Read with h5py
            fname = os.path.join(self.__directory, file.name)
            # TODO Check if this is needed or we can skip it by using the part of the filename with the time
            self.__fi = File(fname)
            try:
                # Reset some properties before opening the new file. starttime will be completed in '__readmetadata'
                self.starttime = None
                self.__readmetadata()
            except PotentialGap:
                continue

            # Add only if this file lies within the requested time window
            # print(self.__twstart, self.__twend, self.starttime, self.endtime)
            if (self.__twstart is not None) and (self.endtime < self.__twstart):
                self.__logs.debug('File before the selected time window. Discarding...')
                # Skip to the next one
                continue
            if (self.__twend is not None) and (self.__twend < dt):
                # We are already after the endtime requested, so break the loop
                self.__logs.debug('File after the selected time window. Discarding...')
                break
            result.append(DASFile(dt=self.starttime, dtend=self.endtime, name=file.name, samples=self.__samples))

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
        for att in grp.attrs:
            grpdict[att] = grp.attrs[att]
        for k, v in grp.items():
            # print(v.name)
            if isinstance(v, Dataset):
                if k == 'StrainRate':
                    grpdict[k] = {'dtype': v.dtype, 'shape': v.shape}
                else:
                    # print(v[()][0], v[()][1], v[()][2], v[()][3], '...', v[()][-1])
                    grpdict[k] = v[()]
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

        # print(self.metadata)
        # TODO Check if the only chance is StrainRate
        firstKey = list(self.metadata.keys())[0]
        self.__datatype = self.metadata[firstKey]['Source1']['Zone1']['StrainRate']
        # Spacing[1] is in ms. Therefore, it should be scaled with 1000.
        tstep = self.metadata[firstKey]['Source1']['Zone1']['Spacing'][1]/1000
        spatialstep = self.metadata[firstKey]['Source1']['Zone1']['Spacing'][0]

        # Version number. Default is 1. Otherwise, it should appear in Source.Version
        self.metadata['version'] = self.metadata[firstKey]['Source1']['Version'] if 'Version' in self.metadata[firstKey]['Source1'] else 1

        try:
            # Save Spatial Resolution [m]
            self.dasrcn.interrogators[0].acquisitions[0].spatial_sampling_interval = spatialstep
            self.dasrcn.interrogators[0].acquisitions[0].spatial_sampling_interval_unit = 'meter'
        except KeyError:
            pass

        try:
            # Save GaugeLength
            self.dasrcn.interrogators[0].acquisitions[0].gauge_length = self.metadata[firstKey]['Source1']['Zone1']['GaugeLength'][0]
            self.dasrcn.interrogators[0].acquisitions[0].gauge_length_unit = 'meter'
        except KeyError:
            pass

        try:
            # Save pulse rate
            self.dasrcn.interrogators[0].acquisitions[0].pulse_rate = self.metadata[firstKey]['Source1']['Zone1']['PulseRateFreq'][0] / 1000
            self.dasrcn.interrogators[0].acquisitions[0].pulse_rate_unit = 'hertz'
        except KeyError:
            pass

        try:
            # Save pulse width
            self.dasrcn.interrogators[0].acquisitions[0].pulse_width = float(self.metadata[firstKey]['Source1']['Zone1']['PulseWidth'][0])
            self.dasrcn.interrogators[0].acquisitions[0].pulse_width_unit = 'nanoseconds'
        except KeyError:
            pass

        try:
            # Save Unit of measure
            self.dasrcn.interrogators[0].acquisitions[0].unit_of_measure = 'strain-rate' if 'StrainRate' in self.metadata[firstKey]['Source1']['Zone1'] else 'count'
        except KeyError:
            pass

        if self.sampling_rate is None:
            self.sampling_rate = 1.0/tstep
            # Set the sampling rate in the DAS-RCN metadata
            self.dasrcn.interrogators[0].acquisitions[0].acquisition_sample_rate_unit = 'hertz'

        curstarttime = datetime.datetime.utcfromtimestamp(self.metadata[firstKey]['Source1']['time'][0])
        if self.starttime is None:
            self.starttime = curstarttime

        # If channels were not selected we can safely set that here to all channels
        if self.channels is None:
            # TODO Check the channel selection
            self.channels = range(self.metadata[firstKey]['Source1']['Zone1']['StrainRate']['shape'][2])

        # Save the number of channels in DAS-RCN format
        self.dasrcn.interrogators[0].acquisitions[0].number_of_channels = len(self.channels)
        # Add ChannelGroup
        self.dasrcn.interrogators[0].acquisitions[0].channel_groups = [ChannelGroupModel()]
        aux = self.dasrcn.interrogators[0].acquisitions[0].channel_groups[0]
        aux.first_usable_channel_id = int2stationcode(self.channels[0])
        aux.last_usable_channel_id = int2stationcode(self.channels[-1])
        # And add the channels
        for idx, cha in enumerate(self.channels):
            daf = self.metadata[firstKey]['Source1']['Zone1']['Origin'][0] + idx * spatialstep
            aux.channels.append(ChannelModel(channel_id=int2stationcode(cha),
                                             distance_along_fiber=daf,
                                             x_coordinate=0,
                                             y_coordinate=0))

        # Create a mapping between channel ID and index
        # chmap = dict()
        # for idx, ch in enumerate(self.metadata['header']['channels']):
        #     chmap[ch] = idx

        # Keep the indexes of where the channels really are (column in 2D array)
        # self.__channelsidx = [chmap[ch] for ch in self.channels]
        # self.__logs.debug('From channels %s to %s' % (self.channels, self.__channelsidx))

        # FIXME Replace with real number of samples
        self.__samples = 0

        # Calculate endtime based on the number of samples declared and the sampling rate
        self.endtime = datetime.datetime.utcfromtimestamp(self.metadata[firstKey]['Source1']['time'][-1])

        if (self.__twstart is not None) and (self.endtime < self.__twstart):
            raise PotentialGap(self.endtime, (self.__twstart-self.endtime).total_seconds(),
                               'End time of file before of time window (%s < %s)' % (self.endtime, self.__twstart))

        if (self.__twend is not None) and (self.__twend < self.starttime):
            raise PotentialGap(self.__twend, (self.starttime-self.__twend).total_seconds(),
                               'Start time of file after time window (%s < %s)' % (self.__twend, self.starttime))

        # Sample to start extraction from based on the initial datetime of the file (__twstart)
        if self.__twstart is not None:
            self.__samplestart = max(
                floor((self.__twstart - self.starttime).total_seconds() / tstep), 0)
        else:
            self.__samplestart = 0

        # Should I readjust __twstart to align it exactly with the time of the samples?
        self.__twstart = self.starttime + datetime.timedelta(seconds=self.__samplestart * tstep)

        self.__samplecur = self.__samplestart

        # Open end or beyond this file: read until the last sample
        if (self.__twend is None) or (self.__twend >= self.endtime):
            self.__sampleend = self.__samples-1
        else:
            # Otherwise calculate which one is the last sample to read
            self.__sampleend = ceil((self.__twend - self.starttime).total_seconds() / tstep)

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
        raise NotImplementedError('Access to data is not yet implemented')

    def __iter_metadata__(self) -> Iterable[dict]:
        """Read metadata from files based on channel selection

        :return: Metadata from selected channels
        :rtype: dict
        """
        # Metadata
        self.__logs = logging.getLogger('Iterate Metadata')
        self.__logs.setLevel(self.__loglevel)

        while (self.__twend is None) or (self.__twstart < self.__twend):
            for k, v in self.metadata.items():
                yield {k: v}

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
