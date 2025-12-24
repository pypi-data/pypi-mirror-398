from __future__ import annotations

import numpy as np
import pytest

from spharapy.spectral_filters import (
    as_bandpass,
    as_highpass,
    transfer_func_butterworth_bandpass,
    transfer_func_butterworth_highpass,
    transfer_func_butterworth_lowpass,
    transfer_func_gaussian_bandpass,
    transfer_func_gaussian_highpass,
    transfer_func_gaussian_lowpass,
    transfer_func_ideal_bandpass,
    transfer_func_ideal_highpass,
    transfer_func_ideal_lowpass,
)


def grid(n=257, fmax=1.0):
    """Generate a symmetric SPHARA frequency grid."""
    return np.linspace(-fmax, fmax, n)


# -------------------------------------------------------------------------
# Basic helpers
# -------------------------------------------------------------------------

def test_as_highpass_and_bandpass_identities():
    lp = np.array([1.0, 0.5, 0.0])
    hp = as_highpass(lp)
    np.testing.assert_allclose(hp, np.array([0.0, 0.5, 1.0]))

    bp = as_bandpass(np.array([0., 0.3, 1.]), np.array([0., 1., 1.]))
    np.testing.assert_allclose(bp, np.array([0., 0.7, 0.]))


# -------------------------------------------------------------------------
# Ideal filters
# -------------------------------------------------------------------------

def test_ideal_lowpass_relative_equals_absolute():
    f = grid()
    lp_abs = transfer_func_ideal_lowpass(f, fc=0.5)
    lp_rel = transfer_func_ideal_lowpass(f, fc=0.5, relative=True)  # max|f|=1
    np.testing.assert_allclose(lp_abs, lp_rel)


def test_ideal_highpass_identity():
    f = grid()
    lp = transfer_func_ideal_lowpass(f, 0.4)
    hp = transfer_func_ideal_highpass(f, 0.4)
    np.testing.assert_allclose(hp, 1 - lp)


def test_ideal_bandpass_matches_difference():
    f = grid()
    bp = transfer_func_ideal_bandpass(f, low=0.2, high=0.6)
    lp_lo = transfer_func_ideal_lowpass(f, 0.2)
    lp_hi = transfer_func_ideal_lowpass(f, 0.6)
    np.testing.assert_allclose(bp, lp_hi - lp_lo)


# -------------------------------------------------------------------------
# Gaussian filters
# -------------------------------------------------------------------------

def test_gaussian_hits_target_at_fc():
    fc = 0.3
    dB = -3.01029995664

    # Evaluate exactly at f = fc (no grid approximation)
    H_fc = transfer_func_gaussian_lowpass(np.array([fc]), fc=fc, dB=dB)[0]

    np.testing.assert_allclose(
        H_fc,
        1 / np.sqrt(2),
        rtol=1e-9,
        atol=1e-9,
    )


def test_gaussian_high_and_bandpass_rel():
    f = grid()
    lp = transfer_func_gaussian_lowpass(f, fc=0.4, dB=-3.0, relative=True)
    hp = transfer_func_gaussian_highpass(f, fc=0.4, dB=-3.0, relative=True)
    np.testing.assert_allclose(hp, 1 - lp)

    bp = transfer_func_gaussian_bandpass(f, low=0.2, high=0.6, dB=-3.0, relative=True)
    lp_lo = transfer_func_gaussian_lowpass(f, fc=0.2, dB=-3.0)
    lp_hi = transfer_func_gaussian_lowpass(f, fc=0.6, dB=-3.0)
    np.testing.assert_allclose(bp, lp_hi - lp_lo)


# -------------------------------------------------------------------------
# Butterworth filters
# -------------------------------------------------------------------------

@pytest.mark.parametrize("order", [1, 2, 4, 8])
def test_butterworth_half_power(order):
    fc = 0.4
    dB = -3.01029995664

    # Evaluate exactly at f = fc (no grid approximation)
    H_fc = transfer_func_butterworth_lowpass(
        np.array([fc]),
        fc=fc,
        order=order,
        dB=dB,
    )[0]

    np.testing.assert_allclose(
        H_fc,
        1 / np.sqrt(2),
        rtol=1e-9,
        atol=1e-9,
    )


def test_butterworth_rel_high_and_bandpass():
    f = grid()
    lp = transfer_func_butterworth_lowpass(f, fc=0.4, order=4, dB=-3.0, relative=True)
    hp = transfer_func_butterworth_highpass(f, fc=0.4, order=4, dB=-3.0, relative=True)
    bp = transfer_func_butterworth_bandpass(f, low=0.2, high=0.6, order=4, dB=-3.0, relative=True)

    np.testing.assert_allclose(hp, 1 - lp)

    lp_lo = transfer_func_butterworth_lowpass(f, fc=0.2, order=4, dB=-3.0)
    lp_hi = transfer_func_butterworth_lowpass(f, fc=0.6, order=4, dB=-3.0)
    np.testing.assert_allclose(bp, lp_hi - lp_lo)


# -------------------------------------------------------------------------
# Error conditions
# -------------------------------------------------------------------------

def test_invalid_params():
    f = grid()
    with pytest.raises(ValueError):
        transfer_func_ideal_lowpass(f, fc=0.0)
    with pytest.raises(ValueError):
        transfer_func_gaussian_lowpass(f, fc=-1.0)
    with pytest.raises(ValueError):
        transfer_func_gaussian_lowpass(f, fc=0.3, dB=0.0)
    with pytest.raises(ValueError):
        transfer_func_butterworth_lowpass(f, fc=0.3, order=0)
    with pytest.raises(ValueError):
        transfer_func_ideal_bandpass(f, low=0.6, high=0.2)
