from __future__ import annotations

import numpy as np
import pytest

import ocean_spectral as sp


def test_sine_peak_period():
    n = 365
    t = np.arange(n, dtype=float)
    x = 0.6 * np.sin(2 * np.pi * t / 20.0)
    freq, amp = sp.fft_amplitude(x, dt=1.0)
    period = sp.dominant_period(freq, amp)
    assert period == pytest.approx(20.0, rel=0.1)


def test_ar1_threshold_is_finite_and_shape():
    rng = np.random.default_rng(2)
    x = 0.6 * np.sin(2 * np.pi * np.arange(365) / 20.0) + rng.normal(0, 0.2, 365)
    result = sp.ar1_threshold(x, dt=1.0, n_sim=50, seed=1)
    assert result["threshold"].shape == result["amplitude"].shape
    assert np.isfinite(result["threshold"]).all()
    assert -1 < result["rho"] < 1


def test_fft_requires_finite_uniform_input():
    with pytest.raises(ValueError):
        sp.fft_amplitude(np.arange(5))
    with pytest.raises(ValueError):
        sp.fft_amplitude(np.r_[np.arange(10), np.nan])
