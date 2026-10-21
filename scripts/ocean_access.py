"""Approximate grayscale and colour-vision-deficiency (CVD) checks.

These are screening checks, not a replacement for a dedicated accessibility
review.  CVD matrices are the commonly used Viénot–Brettel approximations in
linear sRGB.
"""

from __future__ import annotations

import numpy as np

from ocean_plot import get_cmap

_CVD_MATRICES = {
    "deuteranopia": np.array([
        [0.367322, 0.860646, -0.227968],
        [0.280085, 0.672501, 0.047413],
        [-0.011820, 0.042940, 0.968881],
    ]),
    "protanopia": np.array([
        [0.152286, 1.052583, -0.204868],
        [0.114503, 0.786281, 0.099216],
        [-0.003882, -0.048116, 1.051998],
    ]),
    "tritanopia": np.array([
        [1.255528, -0.076749, -0.178779],
        [-0.078411, 0.930809, 0.147602],
        [0.004733, 0.691367, 0.303900],
    ]),
}


def _srgb_to_linear(rgb: np.ndarray) -> np.ndarray:
    rgb = np.clip(np.asarray(rgb, dtype=float), 0.0, 1.0)
    return np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)


def _linear_to_srgb(rgb: np.ndarray) -> np.ndarray:
    rgb = np.clip(np.asarray(rgb, dtype=float), 0.0, 1.0)
    return np.where(rgb <= 0.0031308, 12.92 * rgb, 1.055 * rgb ** (1 / 2.4) - 0.055)


def _sample(cmap, n: int) -> np.ndarray:
    cmap = get_cmap(cmap)
    return np.asarray(cmap(np.linspace(0.0, 1.0, int(n))), dtype=float)[:, :3]


def simulate_cvd(cmap, kind: str = "deuteranopia", n: int = 256) -> np.ndarray:
    """Return approximate sRGB colours as seen with a dichromatic deficiency.

    Supported kinds: ``deuteranopia``, ``protanopia``, ``tritanopia``.
    """
    key = str(kind).lower().strip()
    if key not in _CVD_MATRICES:
        raise ValueError(f"unknown CVD kind {kind!r}; choose from {sorted(_CVD_MATRICES)}")
    rgb = _sample(cmap, n)
    linear = _srgb_to_linear(rgb)
    simulated = np.clip(linear @ _CVD_MATRICES[key].T, 0.0, 1.0)
    return _linear_to_srgb(simulated)


def grayscale_luminance(cmap, n: int = 256) -> np.ndarray:
    """ITU-R BT.709 relative luminance of sampled sRGB colours."""
    rgb = _sample(cmap, n)
    linear = _srgb_to_linear(rgb)
    return linear @ np.array([0.2126, 0.7152, 0.0722])


def accessibility_report(
    cmap,
    n: int = 256,
    levels: int = 16,
    min_gray_step: float = 0.004,
    min_cvd_distance: float = 0.015,
    kinds: tuple[str, ...] = ("deuteranopia", "protanopia"),
) -> dict:
    """Screen a colormap for grayscale separation and approximate CVD issues.

    Separation is measured over ``levels`` representative colour bins rather
    than 256 adjacent samples, because adjacent 8-bit colours are legitimately
    almost identical.  The returned ``warnings`` list is meant to trigger a
    manual look at the rendered figure, not to certify accessibility.
    """
    levels = max(int(levels), 2)
    idx = np.linspace(0, int(n) - 1, levels).astype(int)
    gray = grayscale_luminance(cmap, n)
    gray_steps = np.abs(np.diff(gray[idx]))
    cvd = {}
    problems: list[str] = []

    for kind in kinds:
        rgb = _srgb_to_linear(simulate_cvd(cmap, kind=kind, n=n))
        steps = np.linalg.norm(np.diff(rgb[idx], axis=0), axis=1)
        cvd[kind] = {
            "min_step": float(steps.min()) if steps.size else 0.0,
            "median_step": float(np.median(steps)) if steps.size else 0.0,
        }
        if cvd[kind]["min_step"] < min_cvd_distance:
            problems.append(
                f"{kind}: adjacent colours are very close "
                f"(min ΔRGB={cvd[kind]['min_step']:.4f})"
            )

    report = {
        "levels": levels,
        "grayscale_min_step": float(gray_steps.min()) if gray_steps.size else 0.0,
        "grayscale_range": (float(gray.min()), float(gray.max())),
        "cvd": cvd,
        "warnings": problems,
    }
    if report["grayscale_min_step"] < min_gray_step:
        report["warnings"].append(
            "grayscale: adjacent colours are nearly indistinguishable "
            f"(min ΔL={report['grayscale_min_step']:.4f})"
        )
    return report
