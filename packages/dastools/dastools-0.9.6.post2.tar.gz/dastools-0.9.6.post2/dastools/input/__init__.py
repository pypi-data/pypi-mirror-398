from pathlib import Path
from dastools.input.optodas import OptoDASDetector
from dastools.input.tdms import TDMSDetector
from dastools.input.optasense import OptaSenseDetector
from dastools.input.optasense import OptaSenseReader
from dastools.input.febus import FebusDetector
from dastools.input.optodas import OptoDASReader
from dastools.input.tdms import TDMSReader
from dastools.input.febus import FebusReader
from typing import Type
from typing import Union
from typing import Literal


def str2class(name: str) -> Type[Union[TDMSReader, OptoDASReader, FebusReader, OptaSenseReader]]:
    if name.lower() == 'tdms':
        return TDMSReader
    if name.lower() == 'optodas':
        return OptoDASReader
    if name.lower() == 'optasense':
        return OptaSenseReader
    if name.lower() == 'febus':
        return FebusReader
    raise Exception('Unknown class %s!' % name)


def checkDASdata(experiment: str, directory: Path = '.',
                 mode: Literal['1D', '2D'] = '1D') -> Type[Union[TDMSReader, OptoDASReader, FebusReader, OptaSenseReader]]:
    # Check data format from the dataset (if any)
    if TDMSDetector().checkDASdata(experiment, directory):
        return TDMSReader

    if OptoDASDetector().checkDASdata(experiment, directory):
        return OptoDASReader
        # return OptoDASReader if mode == '1D' else OptoDAS2D

    if OptaSenseDetector().checkDASdata(experiment, directory):
        return OptaSenseReader
        # return OptaSenseReader if mode == '1D' else OptaSense2D

    if FebusDetector().checkDASdata(experiment, directory):
        return FebusReader
        # return FebusReader if mode == '1D' else Febus2D

    raise Exception('Input format cannot be guessed from the files found in the directory')
