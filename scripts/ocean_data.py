"""Data preparation helpers for oceanographic plotting.

Only common regular/lat-lon and 2-D curvilinear cases are handled.  For ROMS
staggered grids, unstructured meshes, or projected coordinates, keep the native
coordinates and use the matching Cartopy projection instead of forcing lon/lat.
"""

from __future__ import annotations

import warnings

import numpy as np

from ocean_plot import iqr_filter, keep_largest_region, validate_grid  # re-export

DIM_ALIASES = {
    "lon": {"lon", "longitude", "xlon", "x"},
    "lat": {"lat", "latitude", "ylat", "y"},
    "time": {"time", "t", "date"},
    "depth": {"depth", "z", "lev", "level"},
}

VAR_ALIASES = {
    "ssh": ("ssh", "zos", "sla", "adt", "sea_surface_height"),
    "u": ("u", "uo", "water_u", "eastward_sea_water_velocity"),
    "v": ("v", "vo", "water_v", "northward_sea_water_velocity"),
    "temp": ("temp", "thetao", "temperature", "sea_water_temperature"),
    "salt": ("salt", "so", "salinity", "sea_water_salinity"),
}


def _xarray():
    try:
        import xarray as xr
    except ImportError as exc:
        raise ImportError("xarray is required; pip install xarray") from exc
    return xr


def to_minus180(lon):
    """Convert longitudes to the half-open interval [-180, 180)."""
    return ((np.asarray(lon) + 180.0) % 360.0) - 180.0


def to_0_360(lon):
    """Convert longitudes to [0, 360)."""
    return np.asarray(lon) % 360.0


def canonicalize_dims(ds):
    """Rename unambiguous lon/lat/time/depth aliases to canonical names.

    Existing canonical coordinates win; aliases are never renamed on top of a
    canonical name.  Projected ``x``/``y`` coordinates with metre units are left
    untouched.
    """
    names = list(ds.dims) + [c for c in ds.coords if c not in ds.dims]
    rename: dict[str, str] = {}
    for std, aliases in DIM_ALIASES.items():
        if std in ds.dims or std in ds.coords:
            continue
        alias_set = {a.lower() for a in aliases}
        matches = [n for n in names if n.lower() in alias_set and n not in rename]
        if not matches:
            continue
        source = matches[0]
        if source.lower() in {"x", "y"}:
            units = str(ds[source].attrs.get("units", "")).lower()
            if units in {"m", "km", "meter", "metre"}:
                continue
            if not units:
                warnings.warn(
                    f"Renaming {source!r} to {std!r}; verify it is longitude/latitude, "
                    "not a projected coordinate.",
                    RuntimeWarning,
                    stacklevel=2,
                )
        rename[source] = std
    return ds.rename(rename) if rename else ds


def subset_region(ds, lon_bounds, lat_bounds):
    """Subset a dataset to a lon/lat box.

    1D dateline-crossing and negative-longitude boxes are returned with
    unwrapped 0..360 longitudes (possibly >360) so the result stays monotonic.
    Full-globe boxes are not longitude-subset; with 1D coordinates they are
    normalized to 0..360 when the bounds use negative or >180 longitudes.
    2D curvilinear coordinates are masked in place and are never unwrapped or
    sorted; for dateline-crossing 2D data keep the native coordinates and use
    the matching projection.

    For unwrapped 0..360 output use ``ccrs.PlateCarree(central_longitude=180)``
    or an equivalent projection, and document the convention.
    """
    xr = _xarray()
    if "lon" not in ds.coords or "lat" not in ds.coords:
        raise KeyError("dataset must have lon and lat coordinates")

    lon_lo, lon_hi = map(float, lon_bounds)
    lat_lo, lat_hi = map(float, lat_bounds)
    if lat_lo > lat_hi:
        raise ValueError(f"lat_bounds must be ascending, got {(lat_lo, lat_hi)!r}")
    lon = ds["lon"]
    lat = ds["lat"]

    full_globe = abs(lon_hi - lon_lo) >= 360.0 - 1e-9
    needs_wrap = lon_lo > lon_hi or lon_lo < 0 or lon_hi > 180

    if lon.ndim == 1 and lat.ndim == 1:
        if full_globe:
            if needs_wrap:
                ds = ds.assign_coords(lon=to_0_360(ds["lon"]))
            ds = ds.sortby("lon").sortby("lat")
            ds = ds.sel(lat=slice(lat_lo, lat_hi))
            return _check_nonempty(ds, lon_bounds, lat_bounds, lon, lat)

        if needs_wrap:
            ds = ds.assign_coords(lon=to_0_360(ds["lon"])).sortby("lon")
            lo, hi = lon_lo % 360, lon_hi % 360
            if lo <= hi:
                ds = ds.sel(lon=slice(lo, hi))
            else:
                hi += 360
                first = ds.sel(lon=slice(lo, 360))
                second = ds.sel(lon=slice(0, hi - 360))
                second = second.assign_coords(lon=second["lon"] + 360.0)
                ds = xr.concat([first, second], dim="lon").sortby("lon")
        else:
            ds = ds.sortby("lon").sortby("lat")
            ds = ds.sel(lon=slice(lon_lo, lon_hi), lat=slice(lat_lo, lat_hi))
            return _check_nonempty(ds, lon_bounds, lat_bounds, lon, lat)

        ds = ds.sortby("lat").sel(lat=slice(lat_lo, lat_hi))
        return _check_nonempty(ds, lon_bounds, lat_bounds, lon, lat)

    if lon.ndim == 2 and lat.ndim == 2:
        if lon.shape != lat.shape:
            raise ValueError(f"2D lon/lat shape mismatch: {lon.shape} vs {lat.shape}")
        mask = (lat >= lat_lo) & (lat <= lat_hi)
        if not full_globe:
            lon_use = to_0_360(lon) if needs_wrap else lon
            lo, hi = lon_lo % 360, lon_hi % 360
            if lo <= hi:
                lon_mask = (lon_use >= lo) & (lon_use <= hi)
            else:
                lon_mask = (lon_use >= lo) | (lon_use <= hi)
            mask = mask & lon_mask
        ds = ds.where(mask, drop=True)
        return _check_nonempty(ds, lon_bounds, lat_bounds, lon, lat)

    raise ValueError("lon and lat must both be 1D or both be 2D")


def _check_nonempty(ds, lon_bounds, lat_bounds, lon, lat):
    if any(size == 0 for size in ds.sizes.values()):
        raise ValueError(
            f"region is empty: lon={lon_bounds}, lat={lat_bounds}; "
            f"data range lon={float(lon.min())}..{float(lon.max())}, "
            f"lat={float(lat.min())}..{float(lat.max())}"
        )
    return ds


def pick_var(ds, key: str):
    """Return a variable by canonical name or common CF alias."""
    for name in VAR_ALIASES.get(key, (key,)):
        if name in ds:
            return ds[name]
    raise KeyError(f"variable {key!r} not found; available: {list(ds.data_vars)}")


def load_for_plot(path, var: str, region=None, time_sel=None):
    """Load one variable for plotting, preserving time unless explicitly selected.

    ``time_sel`` may be an integer, slice, or label dict.  ``None`` keeps the
    whole time dimension, which is required for Hovmöller/time-series figures.
    """
    xr = _xarray()
    with xr.open_dataset(path, decode_times=True, mask_and_scale=True) as ds:
        ds = canonicalize_dims(ds)
        if region is not None:
            ds = subset_region(ds, region["lon"], region["lat"])
        da = pick_var(ds, var)
        if time_sel is not None and "time" in da.dims:
            if isinstance(time_sel, dict):
                da = da.sel(time_sel)
            else:
                da = da.isel(time=time_sel)
        da = da.load()
    return da


def grid_arrays(
    da, lon_name: str = "lon", lat_name: str = "lat",
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return ``(lon, lat, data)`` with the spatial dimensions last.

    Coordinate names and dimension names need not match: 1D ``lat(y)`` /
    ``lon(x)`` and 2D ``lat(y, x)`` / ``lon(y, x)`` are both supported.  The
    returned arrays are ready for ``validate_grid`` and ``pcolormesh``.
    """
    if lon_name not in da.coords or lat_name not in da.coords:
        raise KeyError(f"DataArray must have {lon_name!r} and {lat_name!r} coordinates")
    lon_da = da[lon_name]
    lat_da = da[lat_name]
    if not lon_da.dims or not lat_da.dims:
        raise ValueError("lon/lat must be dimension coordinates, not scalars")

    spatial_dims = tuple(dict.fromkeys((*lat_da.dims, *lon_da.dims)))
    missing = [dim for dim in spatial_dims if dim not in da.dims]
    if missing:
        raise ValueError(
            f"lon/lat dimensions {missing!r} are not dimensions of the data {da.dims!r}"
        )
    extra = [d for d in da.dims if d not in spatial_dims]
    da = da.transpose(*extra, *spatial_dims)
    lon = np.asarray(da[lon_name].values)
    lat = np.asarray(da[lat_name].values)
    data = np.asarray(da.values)
    validate_grid(lon, lat, data, name=str(da.name or "data"))
    return lon, lat, data
