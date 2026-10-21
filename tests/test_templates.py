from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HAS_CARTOPY = importlib.util.find_spec("cartopy") is not None
HAS_CMOCEAN = importlib.util.find_spec("cmocean") is not None


@pytest.mark.slow
@pytest.mark.skipif(not (HAS_CARTOPY and HAS_CMOCEAN), reason="Cartopy/cmocean not installed")
@pytest.mark.parametrize(
    ("script", "output"),
    [
        ("templates/map_panel_grid.py", "figures/Fig_map_3x2.png"),
        ("templates/mixed_panel_grid.py", "figures/Fig_mixed.png"),
    ],
)
def test_template_renders(tmp_path, script, output):
    env = os.environ.copy()
    env["MPLBACKEND"] = "Agg"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        [sys.executable, str(ROOT / script), "--demo"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=240,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    png = tmp_path / output
    assert png.exists()
    assert png.stat().st_size > 10_000
    assert png.with_suffix(".pdf").exists()
