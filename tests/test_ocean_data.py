from __future__ import annotations

import numpy as np
import pytest

xr = pytest.importorskip("xarray")

import ocean_data as od


def make_ds(lon, lat, name="ssh"):
    data = np.arange(lat.size * lon.size, dtype=float).reshape(lat.size, lon.size)
    return xr.Dataset(
        {name: (("lat", "lon"), data)},
        coords={"lon": lon, "lat": lat},
    )


def test_canonicalize_dims():
    ds = xr.Dataset(
        {"ssh": (("latitude", "longitude"), np.ones((4, 3)))},
        coords={"latitude": np.arange(4.0), "longitude": np.arange(3.0)},
    )
    out = od.canonicalize_dims(ds)
    assert set(out.dims) == {"lat", "lon"}


def test_subset_region_regular():
    ds = make_ds(np.arange(0, 360, 2.0), np.arange(30, -1, -1.0))
    out = od.subset_region(ds, (112, 132), (10, 25))
    assert out.sizes["lon"] == 11
    assert out.sizes["lat"] == 16
    assert np.all(np.diff(out["lon"].values) > 0)
    assert np.all(np.diff(out["lat"].values) > 0)


def test_subset_region_dateline_is_monotonic():
    ds = make_ds(np.arange(0, 360, 2.0), np.arange(-20, 21, 2.0))
    out = od.subset_region(ds, (170, -170), (-10, 10))
    lon = out["lon"].values
    assert lon.min() == 170
    assert lon.max() == 190
    assert np.all(np.diff(lon) > 0)


def test_subset_region_negative_bounds():
    ds = make_ds(np.arange(0, 360, 2.0), np.arange(-20, 21, 2.0))
    out = od.subset_region(ds, (-10, 10), (-10, 10))
    lon = out["lon"].values
    assert np.all(np.diff(lon) > 0)
    assert lon.min() >= 350
    assert lon.max() >= 360


def test_subset_region_empty_raises():
    ds = make_ds(np.arange(0, 10, 1.0), np.arange(0, 10, 1.0))
    with pytest.raises(ValueError, match="empty"):
        od.subset_region(ds, (100, 110), (0, 5))


def test_subset_region_2d():
    lon2, lat2 = np.meshgrid(np.arange(0, 360, 10.0), np.arange(0, 31, 5.0))
    ds = xr.Dataset(
        {"ssh": (("y", "x"), np.ones(lon2.shape))},
        coords={"lon": (("y", "x"), lon2), "lat": (("y", "x"), lat2)},
    )
    out = od.subset_region(ds, (170, -170), (0, 20))
    assert out.sizes["y"] > 0 and out.sizes["x"] > 0


def test_pick_var_aliases():
    ds = xr.Dataset({"zos": (("lat", "lon"), np.ones((2, 2)))},
                    coords={"lat": [0, 1], "lon": [0, 1]})
    assert od.pick_var(ds, "ssh").name == "zos"
    with pytest.raises(KeyError):
        od.pick_var(ds, "temp")


def test_grid_arrays_transposes():
    lon = np.arange(3.0)
    lat = np.arange(4.0)
    da = xr.DataArray(
        np.ones((2, 3, 4)),
        dims=("time", "lon", "lat"),
        coords={"time": [0, 1], "lon": lon, "lat": lat},
    )
    lon_out, lat_out, data = od.grid_arrays(da)
    assert lon_out.shape == (3,)
    assert lat_out.shape == (4,)
    assert data.shape == (2, 4, 3)
