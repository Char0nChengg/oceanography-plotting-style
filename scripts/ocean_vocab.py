"""Vocabulary and lightweight schema inspection for ocean datasets.

The goal is not to guess every NetCDF dialect.  It is to combine common CF
metadata, explicit variable aliases, and optional product profiles, then report
ambiguity instead of silently picking a variable with the wrong meaning.

Typical use::

    from ocean_vocab import inspect_dataset, resolve_variable
    report = inspect_dataset(ds)
    name = resolve_variable(ds, "sst")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Coordinate aliases are deliberately conservative.  Sigma/sigma-like vertical
# coordinates (s_rho, siglay, ...) are not renamed to depth: that would make a
# terrain-following coordinate look like metres below the surface.
DIM_ALIASES: dict[str, set[str]] = {
    "lon": {"lon", "longitude", "xlon", "nav_lon", "lon_rho", "tlong", "x"},
    "lat": {"lat", "latitude", "ylat", "nav_lat", "lat_rho", "tlat", "y"},
    "time": {
        "time", "t", "date", "valid_time", "time_counter", "ocean_time",
    },
    "depth": {"depth", "z", "lev", "level", "deptht", "st_ocean"},
}

SIGMA_COORDS = {"s_rho", "siglay", "siglev", "sigma", "sigma_layer"}


@dataclass(frozen=True)
class VariableSpec:
    """Semantic definition of a plottable variable."""

    aliases: tuple[str, ...]
    standard_names: tuple[str, ...] = ()
    description: str = ""


VAR_SPECS: dict[str, VariableSpec] = {
    "ssh": VariableSpec(
        ("ssh", "zos", "sla", "adt", "sea_surface_height"),
        ("sea_surface_height_above_geoid", "sea_surface_height_above_reference_ellipsoid"),
        "sea surface height / absolute dynamic topography",
    ),
    "u_current": VariableSpec(
        ("u", "uo", "water_u", "eastward_sea_water_velocity"),
        ("eastward_sea_water_velocity",),
        "3-D or depth-resolved eastward ocean velocity",
    ),
    "v_current": VariableSpec(
        ("v", "vo", "water_v", "northward_sea_water_velocity"),
        ("northward_sea_water_velocity",),
        "3-D or depth-resolved northward ocean velocity",
    ),
    "u_surface": VariableSpec(
        ("uos", "usurface", "surface_u", "eastward_sea_water_velocity_surface"),
        ("surface_eastward_sea_water_velocity",),
        "surface eastward ocean velocity",
    ),
    "v_surface": VariableSpec(
        ("vos", "vsurface", "surface_v", "northward_sea_water_velocity_surface"),
        ("surface_northward_sea_water_velocity",),
        "surface northward ocean velocity",
    ),
    "u_wind": VariableSpec(
        ("u10", "u10m", "10u", "eastward_wind"),
        ("eastward_wind",),
        "10 m eastward wind",
    ),
    "v_wind": VariableSpec(
        ("v10", "v10m", "10v", "northward_wind"),
        ("northward_wind",),
        "10 m northward wind",
    ),
    "temp": VariableSpec(
        ("temp", "thetao", "temperature", "sea_water_temperature"),
        ("sea_water_temperature", "sea_water_potential_temperature"),
        "3-D ocean temperature",
    ),
    "sst": VariableSpec(
        ("sst", "tos", "sea_surface_temperature"),
        ("sea_surface_temperature",),
        "sea surface temperature",
    ),
    "salt": VariableSpec(
        ("salt", "so", "salinity", "sea_water_salinity"),
        ("sea_water_salinity", "sea_water_practical_salinity"),
        "3-D ocean salinity",
    ),
    "sss": VariableSpec(
        ("sss", "sos", "sea_surface_salinity"),
        ("sea_surface_salinity",),
        "sea surface salinity",
    ),
    "bathymetry": VariableSpec(
        ("deptho", "bathymetry", "topo", "topography"),
        ("sea_floor_depth_below_geoid", "bedrock_altitude"),
        "water depth / bottom topography",
    ),
    "mld": VariableSpec(
        ("mlotst", "mld", "mixed_layer_depth", "ocean_mixed_layer_thickness"),
        ("ocean_mixed_layer_thickness",),
        "mixed layer depth",
    ),
    "ice_concentration": VariableSpec(
        ("siconc", "icec", "ice_concentration", "sea_ice_area_fraction"),
        ("sea_ice_area_fraction",),
        "sea ice concentration (0-1 or percent; inspect units)",
    ),
    "ice_thickness": VariableSpec(
        ("sithick", "icetk", "ice_thickness", "sea_ice_thickness"),
        ("sea_ice_thickness",),
        "sea ice thickness",
    ),
    "ice_drift_u": VariableSpec(
        ("usi", "siu", "ice_drift_u", "sea_ice_x_velocity"),
        ("sea_ice_x_velocity",),
        "sea ice eastward drift",
    ),
    "ice_drift_v": VariableSpec(
        ("vsi", "siv", "ice_drift_v", "sea_ice_y_velocity"),
        ("sea_ice_y_velocity",),
        "sea ice northward drift",
    ),
    "chlorophyll": VariableSpec(
        ("chl", "chlorophyll", "totchl", "mass_concentration_of_chlorophyll_a"),
        ("mass_concentration_of_chlorophyll_a_in_sea_water",),
        "chlorophyll-a concentration",
    ),
}

# Backward-compatible semantic keys used by the pre-0.3 API.
ALIASED_KEYS = {
    "u": "u_current",
    "v": "v_current",
}

# Flat name map retained for callers that imported ``VAR_ALIASES`` from
# ``ocean_data``.  More specific keys are preferred for new code.
VAR_ALIASES = {
    key: spec.aliases for key, spec in VAR_SPECS.items()
}
VAR_ALIASES["u"] = VAR_SPECS["u_current"].aliases
VAR_ALIASES["v"] = VAR_SPECS["v_current"].aliases

# Product profiles are optional hints for known conventions that do not always
# carry complete CF metadata.  Generic aliases and CF names remain primary.
PRODUCT_PROFILES: dict[str, dict[str, tuple[str, ...]]] = {
    "era5": {
        "time": ("valid_time", "time"),
        "u_wind": ("u10", "10u"),
        "v_wind": ("v10", "10v"),
        "sst": ("sst",),
    },
    "glorys": {
        "u_surface": ("uos", "uo"),
        "v_surface": ("vos", "vo"),
        "temp": ("thetao",),
        "salt": ("so",),
        "ssh": ("zos",),
        "ice_concentration": ("siconc",),
        "ice_thickness": ("sithick",),
    },
    "nemo": {
        "lon": ("nav_lon",),
        "lat": ("nav_lat",),
        "time": ("time_counter",),
        "depth": ("deptht",),
    },
    "roms": {
        "lon": ("lon_rho",),
        "lat": ("lat_rho",),
        "time": ("ocean_time",),
    },
    "cmip6": {
        "temp": ("thetao",),
        "salt": ("so",),
        "ssh": ("zos",),
        "sst": ("tos",),
        "ice_concentration": ("siconc",),
        "ice_thickness": ("sithick",),
    },
}


@dataclass
class DatasetReport:
    """Human- and machine-readable summary of a dataset's vocabulary."""

    path: str | None = None
    dims: tuple[str, ...] = ()
    coords: dict[str, str | None] = field(default_factory=dict)
    coord_dims: dict[str, tuple[str, ...]] = field(default_factory=dict)
    time: dict[str, Any] | None = None
    variables: dict[str, tuple[str, ...]] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "dims": list(self.dims),
            "coords": self.coords,
            "coord_dims": {
                key: list(value) for key, value in self.coord_dims.items()
            },
            "time": self.time,
            "variables": {
                key: list(value) for key, value in self.variables.items()
            },
            "warnings": self.warnings,
        }


def _names(ds) -> list[str]:
    return list(ds.data_vars)


def _coord_candidates(ds, canonical: str) -> list[str]:
    aliases = {name.lower() for name in DIM_ALIASES[canonical]}
    candidates = [
        name for name in ds.coords
        if name.lower() in aliases or _standard_name(ds[name]) in aliases
    ]
    if canonical in ds.coords and canonical not in candidates:
        candidates.insert(0, canonical)
    return list(dict.fromkeys(candidates))


def _standard_name(obj) -> str:
    return str(obj.attrs.get("standard_name", "")).lower()


def _variable_candidates(ds, key: str, profile: str | None = None) -> list[str]:
    spec = VAR_SPECS.get(ALIASED_KEYS.get(key, key))
    if spec is None:
        return [key] if key in ds.data_vars else []

    aliases = {name.lower() for name in spec.aliases}
    aliases.update(name.lower() for name in spec.standard_names)
    if profile:
        for name in PRODUCT_PROFILES.get(profile.lower(), {}).get(key, ()):
            aliases.add(name.lower())

    found: list[str] = []
    for name in _names(ds):
        variable = ds[name]
        if (
            name.lower() in aliases
            or _standard_name(variable) in aliases
        ):
            found.append(name)
    if key in ds.data_vars and key not in found:
        found.insert(0, key)
    return list(dict.fromkeys(found))


def resolve_variable(ds, key: str, profile: str | None = None) -> str:
    """Resolve a semantic key to exactly one data variable.

    Ambiguous matches raise ``ValueError`` with the candidate names; missing
    matches raise ``KeyError`` with the available variables.
    """
    candidates = _variable_candidates(ds, key, profile=profile)
    if not candidates:
        raise KeyError(
            f"variable {key!r} not found; available: {list(ds.data_vars)}"
        )
    if len(candidates) > 1:
        raise ValueError(
            f"variable {key!r} is ambiguous: {candidates}; "
            "use the exact variable name or a more specific semantic key"
        )
    return candidates[0]


def inspect_dataset(ds, path: str | None = None) -> DatasetReport:
    """Inspect coordinates, time metadata, and semantic variable candidates."""
    report = DatasetReport(
        path=path,
        dims=tuple(str(dim) for dim in ds.dims),
        coords={key: None for key in DIM_ALIASES},
    )
    for canonical in ("lon", "lat", "time", "depth"):
        candidates = _coord_candidates(ds, canonical)
        if candidates:
            report.coords[canonical] = candidates[0]
            report.coord_dims[canonical] = tuple(ds[candidates[0]].dims)
        elif canonical in {"lon", "lat", "time"}:
            report.warnings.append(f"missing {canonical} coordinate")
        if len(candidates) > 1:
            report.warnings.append(
                f"multiple {canonical} coordinate candidates: {candidates}"
            )

    time_name = report.coords.get("time")
    if time_name:
        coord = ds[time_name]
        report.time = {
            "name": time_name,
            "dtype": str(coord.dtype),
            "calendar": coord.attrs.get("calendar"),
            "units": coord.attrs.get("units"),
        }

    for key in VAR_SPECS:
        candidates = _variable_candidates(ds, key)
        if candidates:
            report.variables[key] = tuple(candidates)
            if len(candidates) > 1:
                report.warnings.append(
                    f"{key} has multiple candidates: {candidates}"
                )

    for name in ds.coords:
        if name.lower() in SIGMA_COORDS or _standard_name(ds[name]) in SIGMA_COORDS:
            report.warnings.append(
                f"vertical coordinate {name!r} looks sigma-like; "
                "do not treat it as depth without conversion"
            )

    if report.coords["lon"] and report.coords["lat"]:
        lon = ds[report.coords["lon"]]
        lat = ds[report.coords["lat"]]
        if lon.ndim == 2 and lat.ndim == 2:
            report.warnings.append(
                "2-D curvilinear lon/lat detected; preserve native coordinates"
            )
        for name in (report.coords["lon"], report.coords["lat"]):
            units = str(ds[name].attrs.get("units", "")).lower()
            if units in {"m", "km", "meter", "metre"}:
                report.warnings.append(
                    f"coordinate {name!r} has projected units {units!r}; "
                    "use the native projected CRS, not lon/lat"
                )
    return report


def inspect_file(path: str) -> dict[str, Any]:
    """Open a NetCDF file read-only and return a serialisable report."""
    try:
        import xarray as xr
    except ImportError as exc:
        raise ImportError("xarray is required; pip install xarray") from exc

    with xr.open_dataset(path, decode_times=True, mask_and_scale=True) as ds:
        return inspect_dataset(ds, path=str(path)).as_dict()
