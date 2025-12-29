# -*- coding: utf-8 -*-
"""
Main module of the mumott package.
"""

import logging
import sys
from importlib.metadata import metadata
from .core.numba_setup import numba_setup
from .core.geometry import Geometry
from .core.probed_coordinates import ProbedCoordinates
from .core.spherical_harmonic_mapper import SphericalHarmonicMapper
from .data_handling.data_container import DataContainer
from .core.simulator import Simulator

mumott_metadata = metadata(__name__)

__version__ = '2.2'

__all__ = [
    'Geometry',
    'ProbedCoordinates',
    'DataContainer',
    'Simulator',
    'SphericalHarmonicMapper',
]

logging.basicConfig(format='%(levelname)s:%(message)s',
                    level=logging.INFO,
                    stream=sys.stdout)
numba_setup()
