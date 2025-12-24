"""
The :mod:`spharapy.datasets`: module includes utilities to provide
sample datasets.
"""

from .base import (
    load_eeg_256_channel_study,
    load_minimal_triangular_mesh,
    load_simple_triangular_mesh,
)

__author__ = "Uwe Graichen"
__copyright__ = "Copyright 2018-2025, Uwe Graichen"
__credits__ = ["Uwe Graichen"]
__license__ = "BSD-3-Clause"
__version__ = "1.2.0"
__maintainer__ = "Uwe Graichen"
__email__ = "uwe.graichen@tu-ilmenau.de, uwe.graichen@kl.ac.at"
__status__ = "Release"


__all__ = [
    "load_minimal_triangular_mesh",
    "load_simple_triangular_mesh",
    "load_eeg_256_channel_study",
]
