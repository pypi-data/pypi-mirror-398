r"""
Spectral filter design utilities for SPHARA-based spatial filtering.

This module provides small helper functions to design transfer functions
in the SPHARA spectral domain. The resulting arrays are typically passed to
the :class:`spharapy.spharafilter.SpharaFilter` class as the
``specification`` argument, i.e. as a diagonal transfer vector in the
SPHARA basis.

The design functions are purely *spectral* (they only see the frequency
grid ``f`` and return a real-valued magnitude response ``H(f)``). They do
not depend on any mesh or SPHARA basis object and therefore can be used
for arbitrary SPHARA spectra.

Main use cases
--------------

* Ideal (brick-wall) filters
* Gaussian filters (amplitude-based dB specification at the cutoff)
* Butterworth filters (order ``N`` and amplitude-based dB specification)

For convenience, each family provides

* low-pass
* high-pass
* band-pass

variants, where the high-pass and band-pass functions are built from the
low-pass prototypes.

All filter families support both

* **absolute** cutoffs in the same units as the SPHARA frequency axis, and
* **relative** cutoffs expressed as fractions of ``max(|f|)`` via
  ``relative=True``.

Notes
-----
The input ``f`` is typically the vector of SPHARA "spatial frequencies"
(e.g. :math:`\sqrt{\boldsymbol{\tau}}` for FEM-based bases) ordered in the
same way as the columns of the SPHARA basis used by
:class:`spharapy.spharafilter.SpharaFilter`.

Examples
--------
Design an ideal SPHARA low-pass and apply it via
:class:`spharapy.spharafilter.SpharaFilter`::

    import numpy as np
    import spharapy.spharafilter as sf
    from spharapy.spectral_filters import transfer_func_ideal_lowpass

    # frequencies obtained from a SPHARA basis (e.g. FEM-based)
    f = np.linspace(0.0, 50.0, 256)

    # design an ideal low-pass with cutoff at 10 spatial frequency units
    h_lp = transfer_func_ideal_lowpass(f, fc=10.0)

    # use as "specification" in a SpharaFilter (example: simple mesh)
    # sphara_filter = sf.SpharaFilter(trimesh, mode="fem", specification=h_lp)

"""

from __future__ import annotations

import warnings

import numpy as np
from numpy.typing import ArrayLike, NDArray

FloatArray = NDArray[np.floating]


# ---------------------------------------------------------------------------
# Public helper utilities
# ---------------------------------------------------------------------------


def as_highpass(h_lowpass: ArrayLike) -> FloatArray:
    r"""
    Convert a low-pass transfer function into a high-pass transfer function.

    For a given low-pass magnitude response :math:`H_\text{low}(f)`,
    the corresponding high-pass is defined as

    .. math::

        H_\text{high}(f) = 1 - H_\text{low}(f).

    Parameters
    ----------
    h_lowpass : ArrayLike
        Low-pass transfer function values. Can be any array-like object
        convertible to a 1D or ND :class:`numpy.ndarray` of ``float``.

    Returns
    -------
    FloatArray
        High-pass transfer function values with the same shape as
        ``h_lowpass``.

    Examples
    --------
    >>> import numpy as np
    >>> from spharapy.spectral_filters import as_highpass
    >>> as_highpass(np.array([1., 0.5, 0.]))
    array([0. , 0.5, 1. ])
    """
    h = np.asarray(h_lowpass, dtype=float)
    return 1.0 - h


def as_bandpass(h_lowpass_low: ArrayLike, h_lowpass_high: ArrayLike) -> FloatArray:
    r"""
    Construct a band-pass transfer function from two low-pass curves.

    Given two low-pass curves :math:`H_\text{low}(f; f_c^\text{low})`
    and :math:`H_\text{low}(f; f_c^\text{high})` with
    :math:`f_c^\text{high} \ge f_c^\text{low}`, the band-pass is
    defined as

    .. math::

        H_\text{bp}(f)
            = H_\text{low}(f; f_c^\text{high})
            - H_\text{low}(f; f_c^\text{low}).

    Parameters
    ----------
    h_lowpass_low : ArrayLike
        Low-pass curve corresponding to the lower cutoff.
    h_lowpass_high : ArrayLike
        Low-pass curve corresponding to the upper cutoff. Must have the
        same shape as ``h_lowpass_low``.

    Returns
    -------
    FloatArray
        Band-pass transfer function. The result has the same shape as
        the input curves.

    Raises
    ------
    ValueError
        If ``h_lowpass_low`` and ``h_lowpass_high`` do not have the same
        shape.

    Examples
    --------
    >>> import numpy as np
    >>> from spharapy.spectral_filters import as_bandpass
    >>> lo = np.array([0., 0.3, 1. ])
    >>> hi = np.array([0., 1. , 1. ])
    >>> as_bandpass(lo, hi)
    array([0. , 0.7, 0. ])
    """
    lo = np.asarray(h_lowpass_low, dtype=float)
    hi = np.asarray(h_lowpass_high, dtype=float)
    if lo.shape != hi.shape:
        raise ValueError("Low-pass curves must have the same shape.")
    return hi - lo


# ---------------------------------------------------------------------------
# Internal validation helpers
# ---------------------------------------------------------------------------


def _validate_f_and_fc(f: ArrayLike, fc: float, *, relative: bool) -> tuple[FloatArray, float]:
    """
    Validate a frequency grid and compute the absolute cutoff frequency.

    Parameters
    ----------
    f : ArrayLike
        Frequency grid, typically the SPHARA spectral axis.
    fc : float
        Cutoff frequency. Interpreted as absolute (same units as ``f``),
        unless ``relative=True`` is used.
    relative : bool
        If ``True``, interpret ``fc`` as a fraction of ``max(|f|)`` and
        convert it into an absolute value.

    Returns
    -------
    x : FloatArray
        Frequency grid as a 1D or ND floating array.
    fc_abs : float
        Absolute cutoff frequency, guaranteed to be positive and finite.

    Raises
    ------
    ValueError
        If any frequency value is non-finite, or if the resulting
        ``fc_abs`` is not a positive finite number.

    Warns
    -----
    UserWarning
        If ``fc_abs`` lies outside the range ``[min(f), max(f)]``. In
        that case, the resulting filter will be nearly flat for most
        practical SPHARA spectra.
    """
    x = np.asarray(f, dtype=float)
    if not np.all(np.isfinite(x)):
        raise ValueError("All frequency values must be finite.")

    if relative:
        fmax = float(np.max(np.abs(x)))
        if fmax == 0.0:
            raise ValueError("relative=True requires max(|f|) > 0.")
        fc_abs = float(fc) * fmax
    else:
        fc_abs = float(fc)

    if not np.isfinite(fc_abs) or fc_abs <= 0.0:
        raise ValueError("fc must be a finite positive number.")

    fmin, fmax = float(np.min(x)), float(np.max(x))
    if not (fmin <= fc_abs <= fmax):
        warnings.warn(
            (
                f"Cutoff fc={fc_abs} lies outside the SPHARA frequency range "
                f"[{fmin}, {fmax}]. The resulting filter will be nearly flat."
            ),
            stacklevel=2,
        )
    return x, fc_abs


def _validate_band(
    f: ArrayLike,
    low: float,
    high: float,
    *,
    relative: bool,
) -> tuple[FloatArray, float, float]:
    """
    Validate band-pass cutoff frequencies and convert them to absolute values.

    Parameters
    ----------
    f : ArrayLike
        Frequency grid, typically the SPHARA spectral axis.
    low : float
        Lower cutoff. Interpreted as absolute frequency or fraction of
        ``max(|f|)`` if ``relative=True``.
    high : float
        Upper cutoff. Must satisfy ``high > low``.
    relative : bool
        If ``True``, interpret both ``low`` and ``high`` as fractions of
        ``max(|f|)`` and convert them to absolute cutoffs.

    Returns
    -------
    x : FloatArray
        Frequency grid as a floating array.
    low_abs : float
        Lower cutoff as an absolute frequency > 0.
    high_abs : float
        Upper cutoff as an absolute frequency.

    Raises
    ------
    ValueError
        If ``high <= low``, if any frequency is non-finite, if any
        cutoff is non-finite, or if the lower cutoff is not strictly
        positive.

    Warns
    -----
    UserWarning
        If the band ``[low_abs, high_abs]`` lies partly outside the
        range ``[min(f), max(f)]``.
    """
    if high <= low:
        raise ValueError("Band edges must satisfy low < high.")

    x = np.asarray(f, dtype=float)
    if not np.all(np.isfinite(x)):
        raise ValueError("All frequency values must be finite.")

    fmax_abs = float(np.max(np.abs(x)))
    if relative:
        if fmax_abs == 0.0:
            raise ValueError("relative=True requires max(|f|) > 0.")
        low_abs = float(low) * fmax_abs
        high_abs = float(high) * fmax_abs
    else:
        low_abs = float(low)
        high_abs = float(high)

    if not (np.isfinite(low_abs) and np.isfinite(high_abs)):
        raise ValueError("Cutoff values must be finite numbers.")
    if low_abs <= 0.0:
        raise ValueError("The lower cutoff must be > 0.")

    fmin, fmax = float(np.min(x)), float(np.max(x))
    if not (fmin <= low_abs <= fmax) or not (fmin <= high_abs <= fmax):
        warnings.warn(
            (
                f"Band [{low_abs}, {high_abs}] lies partly outside the SPHARA "
                f"frequency range [{fmin}, {fmax}]."
            ),
            stacklevel=2,
        )
    return x, low_abs, high_abs


# ---------------------------------------------------------------------------
# Ideal (brick-wall) filter family
# ---------------------------------------------------------------------------


def transfer_func_ideal_lowpass(
    f: ArrayLike,
    fc: float,
    *,
    relative: bool = False,
) -> FloatArray:
    r"""
    Ideal (brick-wall) low-pass filter in the SPHARA domain.

    The ideal low-pass magnitude response is defined as

    .. math::

        H(f) = \begin{cases}
            1, & \text{if } |f| \le f_c,\\
            0, & \text{otherwise.}
        \end{cases}

    Parameters
    ----------
    f : ArrayLike
        SPHARA frequency axis (1D or ND). Typically contains non-negative
        spatial frequencies (e.g. :math:`\sqrt{\boldsymbol{\tau}}` of a
        FEM-based SPHARA basis), but negative values are supported.
    fc : float
        Cutoff frequency. If ``relative=False``, ``fc`` is interpreted as
        an absolute frequency in the same units as ``f``. If
        ``relative=True``, ``fc`` is interpreted as a fraction of
        ``max(|f|)``.
    relative : bool, optional
        If ``True``, interpret ``fc`` as relative cutoff
        ``f_c = fc * max(|f|)``. Default: ``False``.

    Returns
    -------
    FloatArray
        Ideal low-pass transfer function values with the same shape as
        ``f`` and values in ``{0.0, 1.0}``.

    Raises
    ------
    ValueError
        If the frequency grid contains non-finite values or the cutoff is
        not a finite positive number.

    Warns
    -----
    UserWarning
        If ``fc`` lies outside the range ``[min(f), max(f)]``. In that
        case, the filter will be effectively all-ones or all-zeros.

    Examples
    --------
    >>> import numpy as np
    >>> from spharapy.spectral_filters import transfer_func_ideal_lowpass
    >>> f = np.linspace(-1, 1, 5)
    >>> transfer_func_ideal_lowpass(f, fc=0.5)
    array([0., 1., 1., 1., 0.])
    """
    x, fc_abs = _validate_f_and_fc(f, fc, relative=relative)
    return (np.abs(x) <= fc_abs).astype(float)


def transfer_func_ideal_highpass(
    f: ArrayLike,
    fc: float,
    *,
    relative: bool = False,
) -> FloatArray:
    r"""
    Ideal high-pass filter in the SPHARA domain.

    This is defined as the complement of the ideal low-pass:

    .. math::

        H_\text{hp}(f) = 1 - H_\text{lp}(f; f_c).

    Parameters
    ----------
    f : ArrayLike
        SPHARA frequency axis.
    fc : float
        Cutoff frequency (absolute or relative, see ``relative``).
    relative : bool, optional
        If ``True``, interpret ``fc`` as a fraction of ``max(|f|)``.

    Returns
    -------
    FloatArray
        Ideal high-pass transfer function values.
    """
    return as_highpass(transfer_func_ideal_lowpass(f, fc, relative=relative))


def transfer_func_ideal_bandpass(
    f: ArrayLike,
    low: float,
    high: float,
    *,
    relative: bool = False,
) -> FloatArray:
    r"""
    Ideal band-pass filter in the SPHARA domain.

    The ideal band-pass is constructed from two ideal low-passes via

    .. math::

        H_\text{bp}(f)
            = H_\text{lp}(f; f_\text{high})
            - H_\text{lp}(f; f_\text{low}),

    where :math:`f_\text{low} < f_\text{high}`.

    Parameters
    ----------
    f : ArrayLike
        SPHARA frequency axis.
    low : float
        Lower cutoff (absolute or relative).
    high : float
        Upper cutoff (absolute or relative). Must satisfy ``high > low``.
    relative : bool, optional
        If ``True``, interpret ``low`` and ``high`` as fractions of
        ``max(|f|)``. Default: ``False``.

    Returns
    -------
    FloatArray
        Ideal band-pass transfer function.

    Raises
    ------
    ValueError
        If ``high <= low`` or if any cutoff is invalid.

    Warns
    ------
    UserWarning
        If the band lies (partly) outside the range of the SPHARA
        frequency axis.
    """
    x, low_abs, high_abs = _validate_band(f, low, high, relative=relative)
    h_lo = transfer_func_ideal_lowpass(x, low_abs)
    h_hi = transfer_func_ideal_lowpass(x, high_abs)
    return as_bandpass(h_lo, h_hi)


# ---------------------------------------------------------------------------
# Gaussian filter family
# ---------------------------------------------------------------------------


def transfer_func_gaussian_lowpass(
    f: ArrayLike,
    fc: float,
    dB: float = -3.0,
    *,
    relative: bool = False,
) -> FloatArray:
    r"""
    Gaussian low-pass filter with amplitude-based dB specification at ``fc``.

    The Gaussian low-pass magnitude response is given by

    .. math::

        H(f) = \exp\bigl(-\kappa \, (f / f_c)^2\bigr),

    where the parameter :math:`\kappa` is chosen such that

    .. math::

        |H(f_c)| = 10^{\text{dB} / 20}.

    Thus,

    .. math::

        \kappa = -\frac{\text{dB}}{20}\,\ln(10).

    Parameters
    ----------
    f : ArrayLike
        SPHARA frequency axis.
    fc : float
        Cutoff frequency. Interpreted as absolute or relative (see
        ``relative``).
    dB : float, optional
        Desired attenuation (in amplitude dB) at :math:`f = f_c`.
        Must be negative. For exact half-power,
        ``dB = -20*log10(1/sqrt(2)) ≈ -3.0103``.
    relative : bool, optional
        If ``True``, interpret ``fc`` as a fraction of ``max(|f|)``.

    Returns
    -------
    FloatArray
        Gaussian low-pass transfer function values.

    Raises
    ------
    ValueError
        If the frequency grid contains non-finite values or ``dB`` is not
        a finite negative number.

    Warns
    -----
    UserWarning
        If the cutoff lies outside the SPHARA frequency range.

    Examples
    --------
    >>> import numpy as np
    >>> from spharapy.spectral_filters import transfer_func_gaussian_lowpass
    >>> f = np.linspace(0.0, 50.0, 101)
    >>> H = transfer_func_gaussian_lowpass(f, fc=10.0, dB=-3.0)
    >>> H.shape
    (101,)
    """
    x, fc_abs = _validate_f_and_fc(f, fc, relative=relative)
    if not np.isfinite(dB) or dB >= 0.0:
        raise ValueError("dB must be a finite negative number (amplitude attenuation).")
    kappa = -(dB / 20.0) * np.log(10.0)
    r = x / fc_abs
    return np.exp(-kappa * np.square(r))


def transfer_func_gaussian_highpass(
    f: ArrayLike,
    fc: float,
    dB: float = -3.0,
    *,
    relative: bool = False,
) -> FloatArray:
    """
    Gaussian high-pass filter computed as the complement of a Gaussian low-pass.

    Parameters
    ----------
    f : ArrayLike
        SPHARA frequency axis.
    fc : float
        Cutoff frequency (absolute or relative).
    dB : float, optional
        Desired attenuation (amplitude dB) at the cutoff of the underlying
        low-pass.
    relative : bool, optional
        If ``True``, interpret ``fc`` as a fraction of ``max(|f|)``.

    Returns
    -------
    FloatArray
        Gaussian high-pass transfer function values.
    """
    lp = transfer_func_gaussian_lowpass(f, fc, dB=dB, relative=relative)
    return as_highpass(lp)


def transfer_func_gaussian_bandpass(
    f: ArrayLike,
    low: float,
    high: float,
    dB: float = -3.0,
    *,
    relative: bool = False,
) -> FloatArray:
    r"""
    Gaussian band-pass filter built from two Gaussian low-passes.

    The band-pass is defined as

    .. math::

        H_\text{bp}(f)
            = H_\text{lp}(f; f_\text{high})
            - H_\text{lp}(f; f_\text{low}),

    where both low-passes share the same ``dB`` specification.

    Parameters
    ----------
    f : ArrayLike
        SPHARA frequency axis.
    low : float
        Lower cutoff (absolute or relative).
    high : float
        Upper cutoff (absolute or relative). Must satisfy ``high > low``.
    dB : float, optional
        Desired attenuation (amplitude dB) at the respective cutoffs.
    relative : bool, optional
        If ``True``, interpret ``low`` and ``high`` as fractions of
        ``max(|f|)``.

    Returns
    -------
    FloatArray
        Gaussian band-pass transfer function values.
    """
    x, low_abs, high_abs = _validate_band(f, low, high, relative=relative)
    h_lo = transfer_func_gaussian_lowpass(x, low_abs, dB=dB)
    h_hi = transfer_func_gaussian_lowpass(x, high_abs, dB=dB)
    return as_bandpass(h_lo, h_hi)


# ---------------------------------------------------------------------------
# Butterworth filter family
# ---------------------------------------------------------------------------


def transfer_func_butterworth_lowpass(
    f: ArrayLike,
    fc: float,
    order: int,
    dB: float = -3.0,
    *,
    relative: bool = False,
) -> FloatArray:
    r"""
    Butterworth low-pass filter of order ``N``.

    The generalized Butterworth magnitude response with amplitude-based
    dB specification at the cutoff is defined by

    .. math::

        |H(f_c)| = 10^{\text{dB} / 20} = R,\\
        \kappa = \frac{1}{R^2} - 1,\\
        H(f) = \frac{1}{\sqrt{1 + \kappa (|f| / f_c)^{2N}}}.

    Parameters
    ----------
    f : ArrayLike
        SPHARA frequency axis.
    fc : float
        Cutoff frequency (absolute or relative).
    order : int
        Butterworth order :math:`N` (must be an integer >= 1).
    dB : float, optional
        Desired attenuation (amplitude dB) at :math:`f = f_c`. Must be
        negative. For a classic half-power Butterworth cutoff, use
        ``dB ≈ -3.0103``.
    relative : bool, optional
        If ``True``, interpret ``fc`` as a fraction of ``max(|f|)``.

    Returns
    -------
    FloatArray
        Butterworth low-pass transfer function values.

    Raises
    ------
    ValueError
        If ``order`` is not a valid integer >= 1 or if ``dB`` is not a
        finite negative number.

    Warns
    -----
    UserWarning
        If the cutoff lies outside the SPHARA frequency range.

    Examples
    --------
    >>> import numpy as np
    >>> from spharapy.spectral_filters import transfer_func_butterworth_lowpass
    >>> f = np.linspace(0.0, 1.0, 128)
    >>> H = transfer_func_butterworth_lowpass(f, fc=0.25, order=4, dB=-3.0103)
    >>> H.min() >= 0
    True
    """
    x, fc_abs = _validate_f_and_fc(f, fc, relative=relative)

    try:
        N = int(order)
    except Exception as e:  # pragma: no cover - defensive programming
        raise ValueError("order must be an integer >= 1.") from e
    if N < 1:
        raise ValueError("order must be an integer >= 1.")
    if not np.isfinite(dB) or dB >= 0.0:
        raise ValueError("dB must be a finite negative number (amplitude attenuation).")

    R = 10.0 ** (dB / 20.0)
    kappa = (1.0 / (R * R)) - 1.0
    r = np.abs(x) / fc_abs
    return 1.0 / np.sqrt(1.0 + kappa * np.power(r, 2 * N))


def transfer_func_butterworth_highpass(
    f: ArrayLike,
    fc: float,
    order: int,
    dB: float = -3.0,
    *,
    relative: bool = False,
) -> FloatArray:
    """
    Butterworth high-pass filter computed as the complement of a low-pass.

    Parameters
    ----------
    f : ArrayLike
        SPHARA frequency axis.
    fc : float
        Cutoff frequency.
    order : int
        Butterworth filter order.
    dB : float, optional
        Desired attenuation (amplitude dB) at the cutoff of the underlying
        low-pass.
    relative : bool, optional
        If ``True``, interpret ``fc`` as a fraction of ``max(|f|)``.

    Returns
    -------
    FloatArray
        Butterworth high-pass transfer function values.
    """
    lp = transfer_func_butterworth_lowpass(f, fc, order=order, dB=dB, relative=relative)
    return as_highpass(lp)


def transfer_func_butterworth_bandpass(
    f: ArrayLike,
    low: float,
    high: float,
    order: int,
    dB: float = -3.0,
    *,
    relative: bool = False,
) -> FloatArray:
    """
    Butterworth band-pass filter built from two Butterworth low-passes.

    Parameters
    ----------
    f : ArrayLike
        SPHARA frequency axis.
    low : float
        Lower cutoff (absolute or relative).
    high : float
        Upper cutoff (absolute or relative). Must satisfy ``high > low``.
    order : int
        Butterworth filter order.
    dB : float, optional
        Desired attenuation (amplitude dB) at the cutoffs.
    relative : bool, optional
        If ``True``, interpret ``low`` and ``high`` as fractions of
        ``max(|f|)``.

    Returns
    -------
    FloatArray
        Butterworth band-pass transfer function values.
    """
    x, low_abs, high_abs = _validate_band(f, low, high, relative=relative)
    h_lo = transfer_func_butterworth_lowpass(x, low_abs, order=order, dB=dB)
    h_hi = transfer_func_butterworth_lowpass(x, high_abs, order=order, dB=dB)
    return as_bandpass(h_lo, h_hi)
