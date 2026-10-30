from __future__ import annotations

import numpy as np
import pytest

xr = pytest.importorskip("xarray")

import ocean_data as od
import ocean_vocab as ov


def make_dataset():
    time = np.array(["2020-01-01", "2020-01-02"], dtype="datetime64[D]")
    return xr.Dataset(
        {
            "uos": (("valid_time", "latitude", "longitude"), np.ones((2, 3, 4))),
            "vos": (("valid_time", "latitude", "longitude"), np.ones((2, 3, 4))),
            "thetao": (
                ("valid_time", "depth", "latitude", "longitude"),
                np.ones((2, 3, 3, 4)),
            ),
            "siconc": (("valid_time", "latitude", "longitude"), np.ones((2, 3, 4))),
        },
        coords={
            "valid_time": time,
            "latitude": [0.0, 1.0, 2.0],
            "longitude": [110.0, 111.0, 112.0, 113.0],
            "depth": [0.0, 10.0, 20.0],
        },
    )


def test_inspect_dataset_detects_aliases_and_time():
    report = ov.inspect_dataset(make_dataset())
    assert report.coords["time"] == "valid_time"
    assert report.coords["lon"] == "longitude"
    assert report.coords["lat"] == "latitude"
    assert report.coords["depth"] == "depth"
    assert report.variables["u_surface"] == ("uos",)
    assert report.variables["temp"] == ("thetao",)
    assert report.time["name"] == "valid_time"


def test_canonicalize_and_pick_glorys_style_variable():
    ds = od.canonicalize_dims(make_dataset())
    assert set(ds.dims) == {"time", "lat", "lon", "depth"}
    assert od.pick_var(ds, "u_surface").name == "uos"


def test_ambiguous_semantic_key_is_not_silently_resolved():
    ds = xr.Dataset(
        {
            "u": (("lat", "lon"), np.ones((3, 4))),
            "uo": (("lat", "lon"), np.ones((3, 4))),
        },
        coords={"lat": [0, 1, 2], "lon": [0, 1, 2, 3]},
    )
    with pytest.raises(ValueError, match="ambiguous"):
        ov.resolve_variable(ds, "u")


def test_inspect_dataset_warns_on_projected_coordinates():
    ds = xr.Dataset(
        {"ssh": (("y", "x"), np.ones((2, 2)))},
        coords={"x": ("x", [0.0, 1.0]), "y": ("y", [0.0, 1.0])},
    )
    ds["x"].attrs["units"] = "m"
    ds["y"].attrs["units"] = "m"
    report = ov.inspect_dataset(ds)
    assert any("projected units" in warning for warning in report.warnings)
