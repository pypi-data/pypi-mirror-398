from typing import Literal
from typing import Type
from datetime import datetime
from datetime import timedelta
import logging
from math import ceil
from pydantic import DirectoryPath
from pydantic import NonNegativeInt
from pydantic import PositiveInt
from pydantic import conlist
from pydantic import constr
from scipy.signal import remez
from scipy.signal import lfilter_zi
from scipy.signal import lfilter
import numpy as np
from dataclasses import dataclass
from obspy.core.trace import Stats


# Auxiliary class for the iteration of data (waveform) and its headers (stats)
@dataclass
class Waveform:
    data: np.array
    stats: Stats

    def __repr__(self):
        return '%s.%s.%s.%s: %s-%s %d samples' % (self.stats.network, self.stats.station, self.stats.location,
                                                  self.stats.channel, self.stats.starttime, self.stats.endtime,
                                                  len(self.data))


@dataclass
class Gap:
    start: datetime = None
    length: float = None

    def __repr__(self):
        return 'Gap of %f seconds at %s' % (self.length, self.start.isoformat())


class DasProc:
    """Class to read, process and export seismic waveforms in any format"""

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Method which close open resources after using the syntax 'with object:' and use it inside"""
        pass

    def __enter__(self):
        """Method which allows to use the syntax 'with object:' and use it inside

        Create a buffer space to store the signal coefficients to be convoluted during the decimation
        """
        for channel in self.channels:
            logging.debug('Create empty buffer for channel %s' % channel)
            self.__buffer[channel] = None

        return self

    # FIXME This is awful, but it works until I can refactor the "endtime" property
    @property
    def endexperiment(self):
        return self.__input.endexperiment

    @property
    def channels(self):
        return self.__input.channels

    def reset(self):
        return self.__input.reset()

    @property
    def sampling_rate(self):
        return self.__input.sampling_rate

    def __init__(self, dasformat: Type, experiment: str, directory: DirectoryPath = '.', chstart: NonNegativeInt = 0,
                 chstop: NonNegativeInt = None, chstep: PositiveInt = 1, channels: conlist(int, min_length=1) = None,
                 starttime: datetime = None, endtime: datetime = None, iterate: Literal['M', 'D'] = 'D',
                 networkcode: constr(strip_whitespace=True, to_upper=True, min_length=2, max_length=2) = 'XX',
                 channelcode: constr(strip_whitespace=True, to_upper=True, min_length=3, max_length=3) = 'HSF',
                 decimate: int = 1, loglevel: str = 'INFO'):
        """Initialize the object selecting the data, channels and decimation

        :param experiment: Experiment to read and process. Usually the first part of the filenames
        :type experiment: str
        :param directory: Directory where files are located
        :type directory: str
        :param chstart: First channel to select
        :type chstart: int
        :param chstop: Last channel to select
        :type chstop: int
        :param chstep: Step between channels in the selection
        :type chstep: int
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

        # :param firfilter: Filter to apply in case of decimation (fir235 is the only option)
        # :type firfilter: str

        # Log level
        self.__loglevel = loglevel
        logs = logging.getLogger('Init DasProc')
        logs.setLevel(loglevel)

        # Time window selection
        self.__twstart = starttime
        self.__twend = endtime

        # Create an auxiliary generic class providing the sampling rate
        auxiliarydas = dasformat(experiment, directory, chstart, chstop, chstep, channels, starttime, endtime,
                                 networkcode, channelcode, loglevel)
        sps = auxiliarydas.sampling_rate
        del auxiliarydas

        # Create filter to decimate
        if decimate > 1:
            newsampl = sps/decimate
            transwidth = int(3*newsampl/20)
            if transwidth > 40:
                transwidth = 40
            cutoff = newsampl/2-transwidth
            b, a = remez(235, [0, cutoff, cutoff+transwidth, 0.5*sps],
                         [1, 0], Hz=sps), 1.
            self.__filter = np.array(b)

            # Calculate the tap to be later discarded at the beginning and at the end
            self.tapsec = (len(self.__filter) - 1) / (2.0 * sps)
            self.tapsamples = ceil((len(self.__filter) - 1) / 2.0)
            # If there is decimation adjust the start and end times to include the tapering
            # and later keep exactly what user requests
            if starttime is not None:
                starttime -= timedelta(seconds=self.tapsec)
            if endtime is not None:
                endtime += timedelta(seconds=self.tapsec)
        else:
            self.tapsec = 0
            self.tapsamples = 0
            self.__filter = None
        logs.debug('FIR filter: %s' % self.__filter)

        # Create the generic class providing the sampling rate
        self.__input = dasformat(experiment, directory, chstart, chstop, chstep, channels, starttime, endtime,
                                 networkcode, channelcode, loglevel)

        # Decimation factor
        self.__decimate = decimate

        self.__chstart = chstart
        self.__chstop = chstop
        self.__chstep = chstep
        self.__networkcode = networkcode
        self.__channelcode = channelcode

        # Name of file
        self.__experiment = experiment
        self.__directory = directory

        # Dictionary to save the metadata defined in the file
        self.metadata = dict()

        # Define a buffer to store the window over the signal to be
        # convoluted with the FIR filter wile decimating
        # Keys will be channel number and the values will be np.arrays
        self.__buffer = dict()

    # def __iter_data__(self):
    #     """Read NON DECIMATED data from files based on channel selection
    #
    #     :return: Data and attributes for the header
    #     :rtype: tuple(numpy.array, obspy.core.trace.Stats)
    #     """
    #     # Data
    #     logs = logging.getLogger('Iterate Data')
    #
    #     while (self.__twend is None) or (self.__twstart < self.__twend):
    #         data = self.__readdata(channels=self.channels)
    #         # Loop through channels
    #         for ch in self.channels:
    #             stats = Stats()
    #             stats.network = self.__networkcode
    #             stats.station = '%05d' % ch
    #             stats.location = ''
    #             stats.channel = self.__channelcode
    #             stats.sampling_rate = self.sampling_rate
    #             stats.npts = len(data[ch])
    #             stats.starttime = UTCDateTime(self.__twstart)
    #             stats.mseed = AttribDict()
    #             stats.mseed.byteorder = self.__input.__endian
    #             stats.mseed.dataquality = 'D'
    #             stats.mseed.record_length = 512
    #             stats.mseed.blkt1001 = AttribDict()
    #             stats.mseed.blkt1001.timing_quality = 100
    #
    #             logs.debug('Data length: %d; First component: %s' % (len(data[ch]), data[ch][0]))
    #             logs.debug('Stats: %s' % (stats,))
    #             yield data[ch], stats

    # def __iter_metadata__(self) -> dict:
    #     """Read metadata from files based on channel selection
    #
    #     :return: Metadata from selected channels
    #     :rtype: dict
    #     """
    #     # Metadata
    #     # logs = logging.getLogger('Iterate Metadata')
    #
    #     # channels = list(range(self.__chstart, self.__chstop+1, self.__chstep))
    #
    #     while (self.__twend is None) or (self.__twstart < self.__twend):
    #         for obj in self.metadata:
    #             # if 'id' in self.metadata[obj] and self.metadata[obj]['id'] not in channels:
    #             if 'id' in self.metadata[obj] and self.metadata[obj]['id'] not in self.channels:
    #                 continue
    #             yield {obj: self.metadata[obj]}

    # def __readdata(self, channels: list = None) -> dict:
    #     """Read a chunk of data from the specified channels.
    #
    #     :param channels: List of channel numbers to read data from
    #     :type channels: list
    #     :return: Dictionary with channel number as key and a numpy array with data as value
    #     :rtype: dict
    #     :raise Exception: if trying to read data from an originally unselected channel
    #     """
    #
    #     logs = logging.getLogger('Read data')
    #     logs.setLevel(self.__loglevel)
    #
    #     # If there is no channel specified read from all selected channels
    #     if channels is None:
    #         channels = self.channels
    #     else:
    #         for ch in channels:
    #             # All channels must be within the originally selected channels
    #             if ch not in self.channels:
    #                 logs.error('Trying to read data from an unselected channel!')
    #                 raise Exception('Trying to read data from an unselected channel!')
    #
    #     result = self.__input.__readdata(channels)
    #
    #     return result

    def __iter__(self):
        """Iterate through data and filter and decimate if requested

        :returns: Data and attributes for the header
        :rtype: Waveform
        """
        # Create logger
        logs = logging.getLogger('__iter__')

        filterstate = dict()
        tapdiscarded = set()
        for wav in iter(self.__input):
            # If no decimation will take place just return what the underlying class reads
            if self.__decimate == 1:
                yield wav
                continue

            # Check approach of using a filter with state to allow chunks
            if wav.stats.station not in filterstate:
                filterstate[wav.stats.station] = lfilter_zi(self.__filter, 1) * wav.data[0]
            # print(filterstate)

            filtdata, z = lfilter(self.__filter, 1, wav.data, zi=filterstate[wav.stats.station])
            # Discard first part of the signal if we need to decimate
            if wav.stats.station not in tapdiscarded:
                # print('Discarding %d samples' % self.tapsamples)
                filtdata = filtdata[self.tapsamples:]
                tapdiscarded.add(wav.stats.station)
            else:
                wav.stats['starttime'] -= timedelta(seconds=self.tapsec)

            filterstate[wav.stats.station] = z
            # Adjust the sampling rate
            wav.stats['sampling_rate'] = wav.stats['sampling_rate'] / self.__decimate
            wav.stats['npts'] = len(filtdata[::self.__decimate])
            # Decimate and return result
            yield Waveform(filtdata[::self.__decimate], wav.stats)
