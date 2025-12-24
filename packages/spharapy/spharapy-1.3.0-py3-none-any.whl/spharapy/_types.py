# spharapy/_types.py
from __future__ import annotations

from typing import TypeAlias

import numpy as np
from numpy.typing import ArrayLike, NDArray

FloatArray: TypeAlias = NDArray[np.floating]
IntArray: TypeAlias = NDArray[np.integer]
ArrayLikeF: TypeAlias = ArrayLike  # array-like of float-ish values
