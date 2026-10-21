"""Spectral helpers with an explicit, reproducible AR(1) significance test."""

from __future__ import annotations

import numpy as np


def _window_values(n: int, window: str | None) -> np.ndarray:
    if window is None or str(window).lower() in {"none", "boxcar", "rectangular"}:
        return np.ones(n)
    name = str(window).lower()
    if name in {"hann", "hanning"}:
        return np.hanning(n)
    if name == "hamming":
        return np.hamming(n)
    if name == "blackman":
        return np.blackman(n)
    raise ValueError(f"unsupported window {window!r}; use hann, hamming, blackman, or None")


def fft_amplitude(
    x,
    dt: float = 1.0,
    detrend: str | None = "linear",
    window: str | None = "hann",
) -> tuple[np.ndarray, np.ndarray]:
    """One-sided amplitude spectrum of a uniformly sampled series.

    ``dt`` is the sample spacing in the units of the desired frequency axis.
    The series must be finite and uniformly sampled; use Lomb–Scargle for
    irregular sampling.
    """
    x = np.asarray(x, dtype=float).ravel()
    if x.size < 8:
        raise ValueError("at least 8 samples are required")
    if not np.isfinite(x).all():
        raise ValueError("x contains NaN/Inf; fill or mask before FFT")
    if not np.isfinite(dt) or dt <= 0:
        raise ValueError("dt must be positive and finite")

    n = x.size
    t = np.arange(n, dtype=float)
    if detrend == "linear":
        x = x - np.polyval(np.polyfit(t, x, 1), t)
    elif detrend in {None, "none", "constant"}:
        x = x - x.mean()
    else:
        raise ValueError("detrend must be 'linear', 'constant', or None")

    win = _window_values(n, window)
    scale = win.sum()
    if scale == 0:
        raise ValueError("window sums to zero")

    amp = 2.0 * np.abs(np.fft.rfft(x * win)) / scale
    amp[0] /= 2.0
    if n % 2 == 0:
        amp[-1] /= 2.0
    freq = np.fft.rfftfreq(n, d=dt)
    return freq, amp


def ar1_fit(x) -> tuple[float, float]:
    """Fit a zero-mean AR(1) model and return ``(rho, innovation_sigma)``."""
    x = np.asarray(x, dtype=float).ravel()
    x = x[np.isfinite(x)]
    if x.size < 8:
        raise ValueError("at least 8 finite samples are required")
    x = x - x.mean()
    denom = float(np.dot(x[:-1], x[:-1]))
    rho = float(np.dot(x[1:], x[:-1]) / denom) if denom > 0 else 0.0
    rho = float(np.clip(rho, -0.99, 0.99))
    sigma = float(np.std(x[1:] - rho * x[:-1]))
    return rho, sigma


def ar1_threshold(
    x,
    dt: float = 1.0,
    confidence: float = 0.95,
    n_sim: int = 500,
    seed: int = 0,
    detrend: str | None = "linear",
    window: str | None = "hann",
) -> dict:
    """Monte-Carlo AR(1) red-noise threshold for the amplitude spectrum.

    The returned threshold has the same shape as the observed amplitude.  This
    is a useful first-order test for a single red-noise null hypothesis; it is
    not a substitute for a problem-specific significance analysis.
    """
    if not 0 < confidence < 1:
        raise ValueError("confidence must be in (0, 1)")
    if n_sim < 10:
        raise ValueError("n_sim must be >= 10")

    x = np.asarray(x, dtype=float).ravel()
    freq, amp = fft_amplitude(x, dt=dt, detrend=detrend, window=window)
    rho, sigma = ar1_fit(x)
    n = x.size
    if sigma <= 0:
        return {
            "frequency": freq, "amplitude": amp, "threshold": np.zeros_like(amp),
            "rho": rho, "confidence": confidence,
        }

    rng = np.random.default_rng(seed)
    sim = np.empty((n_sim, n), dtype=float)
    sim[:, 0] = rng.normal(0.0, sigma, size=n_sim)
    innov = rng.normal(0.0, sigma, size=(n_sim, n - 1))
    for i in range(1, n):
        sim[:, i] = rho * sim[:, i - 1] + innov[:, i - 1]

    if detrend == "linear":
        t = np.arange(n, dtype=float)
        coeff = np.polyfit(t, sim.T, 1)
        sim = sim - (coeff[0][None, :] * t[:, None] + coeff[1][None, :]).T
    elif detrend in {None, "none", "constant"}:
        sim = sim - sim.mean(axis=1, keepdims=True)
    else:
        raise ValueError("detrend must be 'linear', 'constant', or None")

    win = _window_values(n, window)
    amp_sim = 2.0 * np.abs(np.fft.rfft(sim * win[None, :], axis=1)) / win.sum()
    amp_sim[:, 0] /= 2.0
    if n % 2 == 0:
        amp_sim[:, -1] /= 2.0
    threshold = np.quantile(amp_sim, confidence, axis=0)
    return {
        "frequency": freq,
        "amplitude": amp,
        "threshold": threshold,
        "rho": rho,
        "confidence": confidence,
    }


def dominant_period(freq, amplitude, fmin: float = 0.0):
    """Return the period of the largest non-DC spectral peak."""
    freq = np.asarray(freq, float)
    amplitude = np.asarray(amplitude, float)
    mask = freq > fmin
    if not mask.any():
        raise ValueError("no positive frequencies")
    idx = np.flatnonzero(mask)[np.argmax(amplitude[mask])]
    return 1.0 / freq[idx]
