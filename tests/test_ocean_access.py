from __future__ import annotations

import numpy as np
import pytest

import ocean_access as oa


@pytest.mark.parametrize("cmap", ["cmo.balance", "cmo.dense", "cmo.thermal"])
def test_accessibility_report(cmap):
    report = oa.accessibility_report(cmap)
    assert "grayscale_min_step" in report
    assert "cvd" in report
    assert np.isfinite(report["grayscale_min_step"])
    assert all(np.isfinite(v["min_step"]) for v in report["cvd"].values())


def test_simulate_cvd_shape_and_range():
    rgb = oa.simulate_cvd("cmo.balance", kind="deuteranopia", n=64)
    assert rgb.shape == (64, 3)
    assert np.all((rgb >= 0) & (rgb <= 1))


def test_unknown_cvd_kind():
    with pytest.raises(ValueError, match="unknown CVD"):
        oa.simulate_cvd("cmo.balance", kind="not-a-kind")
