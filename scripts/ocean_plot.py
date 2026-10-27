"""Reusable helpers for publication-quality oceanography figures.

The module deliberately keeps Cartopy and cmocean imports lazy, so it can be
imported and self-tested in a minimal Matplotlib environment.

Run the self-test with::

    python scripts/ocean_plot.py --self-test
"""

from __future__ import annotations

import datetime as _dt
import math
import warnings
from pathlib import Path
from typing import Iterable, Sequence

import matplotlib as mpl

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from matplotlib.colors import LinearSegmentedColormap

__version__ = "0.2.1"


# ---------------------------------------------------------------------------
# Style and typography
# ---------------------------------------------------------------------------

def _font_names() -> set[str]:
    return {f.name for f in font_manager.fontManager.ttflist}


def set_ocean_style(
    font_family: str = "Arial",
    base_size: float = 9,
    cjk_font: str | None = None,
    fallback: str = "DejaVu Sans",
) -> str:
    """Set a compact, print-oriented Matplotlib style.

    Returns the font family actually selected.  A missing preferred font is
    reported with a warning instead of silently producing tofu boxes.
    """
    names = _font_names()
    if font_family not in names:
        warnings.warn(
            f"Font {font_family!r} is not installed; falling back to {fallback!r}. "
            "Install Arial or set font_family explicitly.",
            RuntimeWarning,
            stacklevel=2,
        )
        chosen = fallback
    else:
        chosen = font_family

    sans = [chosen, fallback, "Liberation Sans", "Arial"]
    if cjk_font:
        if cjk_font not in names:
            warnings.warn(
                f"CJK font {cjk_font!r} is not installed; Chinese labels may show boxes.",
                RuntimeWarning,
                stacklevel=2,
            )
        sans.insert(1, cjk_font)

    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": list(dict.fromkeys(sans)),
        "font.size": base_size,
        "axes.titlesize": base_size + 1,
        "axes.labelsize": base_size,
        "xtick.labelsize": max(base_size - 1, 5),
        "ytick.labelsize": max(base_size - 1, 5),
        "legend.fontsize": max(base_size - 1, 5),
        "figure.titlesize": base_size + 2,
        "axes.unicode_minus": False,
        "axes.linewidth": 0.8,
        "axes.titleweight": "normal",
        "axes.titlepad": 5,
        "axes.grid": False,
        "xtick.direction": "in",
        "ytick.direction": "in",
        "xtick.top": True,
        "ytick.right": True,
        "xtick.major.size": 3.5,
        "ytick.major.size": 3.5,
        "xtick.major.width": 0.8,
        "ytick.major.width": 0.8,
        "lines.linewidth": 1.2,
        "legend.frameon": False,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })
    return chosen


# ---------------------------------------------------------------------------
# Ticks and labels
# ---------------------------------------------------------------------------

_NICE_STEPS = (
    0.05, 0.1, 0.2, 0.25, 0.5, 1, 2, 2.5, 3, 4, 5,
    10, 15, 20, 30, 45, 60, 90, 180,
)


def degree_step(span: float, target_ticks: int = 6) -> float:
    """Return a readable lon/lat tick step for a span in degrees."""
    span = abs(float(span))
    if not np.isfinite(span) or span <= 0:
        raise ValueError(f"span must be positive and finite, got {span!r}")
    target_ticks = max(int(target_ticks), 2)
    raw = span / target_ticks
    for step in _NICE_STEPS:
        if step >= raw:
            return float(step)
    return 360.0


def auto_tick_step(
    lon_min: float,
    lon_max: float,
    lat_min: float,
    lat_max: float,
    figsize: tuple[float, float],
    ncols: int = 1,
    nrows: int = 1,
    fontsize: float = 8.0,
    max_ticks: int = 8,
    min_spacing_in: float = 0.55,
) -> tuple[float, float]:
    """Estimate lon/lat tick steps from subplot size and label font size.

    This is still a heuristic: it reserves at least five character widths per
    label, then rounds to a readable degree step.  Run ``check_figure`` after
    rendering to catch actual overlap.
    """
    if ncols < 1 or nrows < 1:
        raise ValueError("ncols and nrows must be >= 1")
    panel_w = max(float(figsize[0]) / ncols, 1.0)
    panel_h = max(float(figsize[1]) / nrows, 1.0)
    max_ticks = max(int(max_ticks), 3)
    spacing = max(float(min_spacing_in), 5.0 * float(fontsize) / 72.0)

    target_lon = int(np.clip(round(panel_w / spacing), 3, max_ticks))
    target_lat = int(np.clip(round(panel_h / spacing), 3, max_ticks))
    lon_step = degree_step(abs(lon_max - lon_min), target_lon)
    lat_step = degree_step(abs(lat_max - lat_min), target_lat)
    return lon_step, lat_step


def degree_ticks(vmin: float, vmax: float, step: float) -> np.ndarray:
    """Nice tick values inside [vmin, vmax]; returns one midpoint if none fit."""
    step = float(step)
    if not np.isfinite(step) or step <= 0:
        raise ValueError(f"step must be positive and finite, got {step!r}")
    lo, hi = sorted((float(vmin), float(vmax)))
    start = math.ceil((lo - 1e-9) / step) * step
    stop = math.floor((hi + 1e-9) / step) * step
    if stop < start:
        return np.array([(lo + hi) / 2.0])
    vals = np.arange(start, stop + step * 0.5, step)
    return np.round(vals, 10)


def set_degree_ticks(
    ax,
    extent: Sequence[float],
    lon_step: float | None = None,
    lat_step: float | None = None,
    crs=None,
    fontsize: float | None = None,
    target_ticks: int = 6,
) -> tuple[np.ndarray, np.ndarray]:
    """Set degree ticks and formatters on a map axis.

    ``extent`` is ``[lon_min, lon_max, lat_min, lat_max]``.  GeoAxes default to
    ``crs=PlateCarree()`` because otherwise Mercator tick positions are
    interpreted as projected metres.  Cartopy's longitude/latitude formatters
    only support rectangular projections; for Lambert, Robinson and similar
    projections this raises ``NotImplementedError`` and callers should use
    ``ax.gridlines(draw_labels=True, xlocs=[110, 120, 130])`` instead.
    """
    import cartopy.crs as ccrs
    from cartopy.mpl.ticker import LatitudeFormatter, LongitudeFormatter

    lon_min, lon_max, lat_min, lat_max = map(float, extent)
    if lon_step is None:
        lon_step = degree_step(abs(lon_max - lon_min), target_ticks)
    if lat_step is None:
        lat_step = degree_step(abs(lat_max - lat_min), target_ticks)

    xticks = degree_ticks(lon_min, lon_max, lon_step)
    yticks = degree_ticks(lat_min, lat_max, lat_step)

    is_geo = hasattr(ax, "projection") and hasattr(ax, "set_extent")
    if is_geo:
        if crs is None:
            crs = ccrs.PlateCarree()
        projection = ax.projection
        rectangular = isinstance(
            projection, (ccrs._RectangularProjection, ccrs.Mercator),
        )
        if not rectangular:
            raise NotImplementedError(
                "set_degree_ticks supports rectangular projections only; "
                "for this projection use ax.gridlines(draw_labels=True, "
                "xlocs=[110, 120, 130], ylocs=[20, 30], crs=ccrs.PlateCarree())."
            )
        ax.set_xticks(xticks, crs=crs)
        ax.set_yticks(yticks, crs=crs)
    else:
        ax.set_xticks(xticks)
        ax.set_yticks(yticks)

    ax.xaxis.set_major_formatter(LongitudeFormatter())
    ax.yaxis.set_major_formatter(LatitudeFormatter())
    ax.tick_params(
        axis="both", which="major", direction="in", length=3.5,
        width=0.8, labelsize=fontsize,
    )
    return xticks, yticks


def add_map_features(
    ax,
    scale: str = "10m",
    land_color: str = "lightgray",
    coastline_color: str = "black",
    coastline_width: float = 0.7,
    zorder: float = 2,
) -> None:
    """Add land and coastlines above the data.

    Natural Earth downloads on first use.  For offline/slow jobs use
    ``scale="50m"`` and cache the Cartopy data directory beforehand.
    """
    import cartopy.feature as cfeature

    ax.add_feature(
        cfeature.LAND.with_scale(scale),
        facecolor=land_color, edgecolor="none", zorder=zorder,
    )
    ax.add_feature(
        cfeature.COASTLINE.with_scale(scale),
        edgecolor=coastline_color, linewidth=coastline_width,
        zorder=zorder + 1,
    )


def add_panel_label(
    ax,
    label: str,
    x: float = -0.08,
    y: float = 1.02,
    fontsize: float | None = None,
    fontweight: str = "bold",
    **kwargs,
):
    """Place ``(a)`` outside the upper-left corner of an axes."""
    if fontsize is None:
        fontsize = mpl.rcParams["font.size"] + 0.5
    return ax.text(
        x, y, label, transform=ax.transAxes, ha="left", va="bottom",
        fontsize=fontsize, fontweight=fontweight, clip_on=False, **kwargs,
    )


# ---------------------------------------------------------------------------
# Colormaps and colorbars
# ---------------------------------------------------------------------------

def get_cmap(name):
    """Resolve ``"cmo.dense"``, a Matplotlib name, or an existing colormap."""
    if isinstance(name, mpl.colors.Colormap):
        return name
    if not isinstance(name, str):
        raise TypeError(f"cmap must be a string or Colormap, got {type(name)!r}")
    if name.startswith("cmo."):
        try:
            import cmocean as cmo
        except ImportError as exc:
            raise ImportError(
                "cmocean is required for 'cmo.*' colormaps; pip install cmocean"
            ) from exc
        attr = name.split(".", 1)[1]
        try:
            return getattr(cmo.cm, attr)
        except AttributeError as exc:
            raise ValueError(f"Unknown cmocean colormap: {name!r}") from exc
    return plt.get_cmap(name)


def truncate_colormap(cmap, fraction: float = 0.75, name: str | None = None):
    """Use only the first ``fraction`` of a colormap."""
    cmap = get_cmap(cmap)
    fraction = float(fraction)
    if not 0 < fraction <= 1:
        raise ValueError("fraction must be in (0, 1]")
    if fraction == 1:
        return cmap
    label = name or f"{cmap.name}_{int(round(fraction * 100)):03d}"
    return LinearSegmentedColormap.from_list(
        label, cmap(np.linspace(0.0, fraction, 256)),
    )


def robust_limits(
    data,
    symmetric: bool = False,
    percentiles: tuple[float, float] = (1, 99),
    pad: float = 0.02,
    include_zero: bool = False,
) -> tuple[float, float]:
    """Percentile-based limits with guards for constant/all-NaN data."""
    arr = np.asarray(data, dtype=float)
    finite = arr[np.isfinite(arr)]
    if finite.size == 0:
        return (-1.0, 1.0) if symmetric else (0.0, 1.0)

    if symmetric:
        vmax = float(np.percentile(np.abs(finite), percentiles[1]))
        if vmax <= 0:
            vmax = 1.0
        return -vmax * (1 + pad), vmax * (1 + pad)

    lo, hi = (float(v) for v in np.percentile(finite, percentiles))
    if include_zero:
        lo, hi = min(lo, 0.0), max(hi, 0.0)
    if not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo:
        center = lo if np.isfinite(lo) else 0.0
        return center - 1.0, center + 1.0
    span = hi - lo
    lower, upper = lo - pad * span, hi + pad * span
    if include_zero:
        if lo >= 0:
            lower = max(lower, 0.0)
        if hi <= 0:
            upper = min(upper, 0.0)
    return lower, upper


def colorbar_ticks(
    vmin: float, vmax: float, n: int = 5, symmetric: bool = False,
) -> np.ndarray:
    """Four to seven readable colorbar ticks (one for a constant range)."""
    n = int(np.clip(int(n), 4, 7))
    if symmetric:
        vmax = max(abs(float(vmin)), abs(float(vmax)))
        return np.linspace(-vmax, vmax, n)
    if float(vmin) == float(vmax):
        return np.array([float(vmin)])
    locator = mpl.ticker.MaxNLocator(nbins=n, steps=[1, 2, 2.5, 5, 10])
    vals = locator.tick_values(float(vmin), float(vmax))
    vals = vals[(vals >= vmin - 1e-12) & (vals <= vmax + 1e-12)]
    if vals.size < 2:
        vals = np.linspace(float(vmin), float(vmax), max(int(n), 3))
    return np.unique(vals)


def add_colorbar(
    fig,
    mappable,
    ax=None,
    cax=None,
    label: str | None = None,
    ticks: Iterable[float] | None = None,
    extend: str | None = None,
    fontsize: float | None = None,
    labelpad: float = 8,
    **kwargs,
):
    """Add a colorbar and apply the labels/ticks used in this style."""
    if cax is not None:
        cbar = fig.colorbar(mappable, cax=cax, extend=extend, **kwargs)
    else:
        cbar = fig.colorbar(mappable, ax=ax, extend=extend, **kwargs)
    if ticks is not None:
        cbar.set_ticks(list(ticks))
    if label:
        cbar.set_label(label, fontsize=fontsize, labelpad=labelpad)
    if fontsize is not None:
        cbar.ax.tick_params(labelsize=fontsize)
    return cbar


# ---------------------------------------------------------------------------
# Grid validation and filtering
# ---------------------------------------------------------------------------

def _coordinate_order(values: np.ndarray) -> str:
    diff = np.diff(values)
    if diff.size == 0:
        return "single"
    if np.all(diff > 0):
        return "ascending"
    if np.all(diff < 0):
        return "descending"
    return "non-monotonic"


def _as_float_array(value) -> np.ndarray:
    arr = getattr(value, "values", value)
    if np.ma.isMaskedArray(arr):
        arr = np.ma.filled(arr, np.nan)
    return np.asarray(arr, dtype=float)


def validate_grid(lon, lat, data, name: str = "data") -> dict:
    """Validate 1D/2D coordinate shapes before plotting.

    Returns a small diagnostic dictionary.  Raises ``ValueError`` with an
    actionable message instead of letting Matplotlib broadcast silently.
    """
    lon = _as_float_array(lon)
    lat = _as_float_array(lat)
    data = _as_float_array(data)

    if lon.ndim not in (1, 2) or lat.ndim not in (1, 2):
        raise ValueError(f"lon/lat must be 1D or 2D, got {lon.shape} and {lat.shape}")
    if lon.ndim != lat.ndim:
        raise ValueError(f"lon/lat dimensionality differs: {lon.shape} vs {lat.shape}")
    if data.ndim < 2:
        raise ValueError(f"{name} must be at least 2D (lat, lon), got {data.shape}")
    if not np.isfinite(lon).all() or not np.isfinite(lat).all():
        raise ValueError("lon/lat contain NaN or Inf")

    if lon.ndim == 1:
        expected = (lat.size, lon.size)
        if data.shape[-2:] != expected:
            raise ValueError(
                f"{name}.shape[-2:]={data.shape[-2:]} does not match "
                f"(lat, lon)={(lat.size, lon.size)}"
            )
        lon_order = _coordinate_order(lon)
        lat_order = _coordinate_order(lat)
    else:
        if lon.shape != lat.shape:
            raise ValueError(f"2D lon/lat shape mismatch: {lon.shape} vs {lat.shape}")
        if data.shape[-2:] != lon.shape:
            raise ValueError(
                f"{name}.shape[-2:]={data.shape[-2:]} does not match "
                f"2D lon/lat shape={lon.shape}"
            )
        lon_order = lat_order = "2d"

    if float(np.nanmax(lon) - np.nanmin(lon)) > 360.0 + 1e-6:
        raise ValueError("longitude span exceeds 360 degrees; check lon convention")
    if float(np.nanmin(lat)) < -90.0 - 1e-6 or float(np.nanmax(lat)) > 90.0 + 1e-6:
        raise ValueError("latitude outside [-90, 90]; check for swapped lon/lat")

    finite_fraction = float(np.isfinite(data).mean())
    lon_convention = "0..360" if float(np.nanmin(lon)) >= 0 and float(np.nanmax(lon)) > 180 else "-180..180"
    return {
        "name": name,
        "lon_shape": lon.shape,
        "lat_shape": lat.shape,
        "data_shape": data.shape,
        "lon_order": lon_order,
        "lat_order": lat_order,
        "lon_convention": lon_convention,
        "finite_fraction": finite_fraction,
    }


def iqr_filter(values, factor: float = 1.5, copy: bool = True) -> np.ndarray:
    """Mask IQR outliers with NaNs; constant/quantized fields are untouched."""
    arr = np.array(values, dtype=float, copy=True) if copy else np.asarray(values, dtype=float)
    finite = arr[np.isfinite(arr)]
    if finite.size == 0:
        return arr
    q1, q3 = np.percentile(finite, [25, 75])
    iqr = q3 - q1
    if not np.isfinite(iqr) or iqr <= 0:
        return arr
    lower, upper = q1 - factor * iqr, q3 + factor * iqr
    arr[(arr < lower) | (arr > upper)] = np.nan
    return arr


def keep_largest_region(values, connectivity: int = 2, copy: bool = True) -> np.ndarray:
    """Keep the largest finite connected component; 8-connected by default."""
    from scipy.ndimage import label

    if connectivity not in {1, 2, 4, 8}:
        raise ValueError("connectivity must be 1, 2, 4, or 8")
    arr = np.array(values, dtype=float, copy=True) if copy else np.asarray(values, dtype=float)
    mask = np.isfinite(arr)
    if not mask.any():
        return arr
    structure = np.ones((3, 3), dtype=int) if connectivity in {2, 8} else None
    lab, n = label(mask, structure=structure)
    if n == 0:
        return arr
    sizes = np.bincount(lab.ravel())
    sizes[0] = 0
    arr[lab != sizes.argmax()] = np.nan
    return arr


# ---------------------------------------------------------------------------
# Time axis
# ---------------------------------------------------------------------------

def _as_datetime(value) -> _dt.datetime:
    if isinstance(value, _dt.datetime):
        return value
    if isinstance(value, _dt.date):
        return _dt.datetime.combine(value, _dt.time())
    if isinstance(value, np.datetime64):
        if np.isnat(value):
            raise ValueError("time contains NaT")
        return _dt.datetime.fromisoformat(np.datetime_as_string(value, unit="s"))
    if hasattr(value, "year") and hasattr(value, "month") and hasattr(value, "day"):
        # cftime and similar objects; non-standard calendars are approximated
        return _dt.datetime(
            int(value.year), int(value.month), int(value.day),
            int(getattr(value, "hour", 0)),
            int(getattr(value, "minute", 0)),
            int(getattr(value, "second", 0)),
        )
    raise TypeError(f"unsupported time value: {value!r} ({type(value)!r})")


def auto_time_axis(ax, time_values, max_ticks: int = 7):
    """Choose a readable time locator/formatter for an axis.

    Supports numeric axes, ``datetime64``, ``datetime``/``date``, pandas
    Timestamps and common cftime objects.  Time should be sorted; the span is
    estimated from the first and last values.
    """
    arr = np.asarray(time_values).ravel()
    if arr.size == 0:
        raise ValueError("time_values is empty")
    max_ticks = max(int(max_ticks), 2)

    first = arr[0]
    calendar = getattr(first, "calendar", None)
    if calendar and str(calendar).lower() not in {
        "standard", "gregorian", "proleptic_gregorian",
    }:
        warnings.warn(
            f"Non-standard calendar {calendar!r} is approximated with Gregorian dates; "
            "use nc_time_axis for calendar-exact axes.",
            RuntimeWarning,
            stacklevel=2,
        )

    if arr.dtype.kind == "m":
        raise TypeError(
            "timedelta values are not a time axis; convert them to datetimes "
            "or plot them on a numeric duration axis"
        )

    if np.issubdtype(arr.dtype, np.number):
        locator = mpl.ticker.MaxNLocator(nbins=max_ticks)
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(mpl.ticker.ScalarFormatter())
        return locator, None

    if arr.dtype.kind in {"O", "M"}:
        t0, t1 = sorted((_as_datetime(arr[0]), _as_datetime(arr[-1])))
        span_seconds = (t1 - t0).total_seconds()
    else:
        raise TypeError(f"unsupported time dtype: {arr.dtype}")

    if span_seconds <= 0:
        return None, None
    span_days = span_seconds / 86400.0

    if span_days >= 730:
        years = max(1, math.ceil(span_days / 365.25 / max_ticks))
        locator = mdates.YearLocator(years)
        formatter = mdates.DateFormatter("%Y")
        rotation = 0
    elif span_days >= 365:
        months = max(1, math.ceil(span_days / 30.44 / max_ticks))
        locator = mdates.MonthLocator(interval=months)
        formatter = mdates.DateFormatter("%Y-%m")
        rotation = 30
    elif span_days >= 90:
        months = max(1, math.ceil(span_days / 30.44 / max_ticks))
        locator = mdates.MonthLocator(interval=months)
        formatter = mdates.DateFormatter("%Y-%m")
        rotation = 30
    elif span_days >= 2:
        days = max(1, math.ceil(span_days / max_ticks))
        locator = mdates.DayLocator(interval=days)
        formatter = mdates.DateFormatter("%m-%d")
        rotation = 30
    elif span_seconds >= 3600:
        hours = max(1, math.ceil(span_seconds / 3600 / max_ticks))
        locator = mdates.HourLocator(interval=hours)
        formatter = mdates.DateFormatter("%m-%d %H:%M")
        rotation = 30
    else:
        minutes = max(1, math.ceil(span_seconds / 60 / max_ticks))
        locator = mdates.MinuteLocator(interval=minutes)
        formatter = mdates.DateFormatter("%H:%M")
        rotation = 30

    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)
    for label in ax.get_xticklabels():
        label.set_rotation(rotation)
        if rotation:
            label.set_ha("right")
    return locator, formatter


# ---------------------------------------------------------------------------
# Figure QA
# ---------------------------------------------------------------------------

def _bbox_overlap(a, b, pad: float = 0.5) -> bool:
    return not (
        a.x1 + pad <= b.x0 or b.x1 + pad <= a.x0
        or a.y1 + pad <= b.y0 or b.y1 + pad <= a.y0
    )


def _outside(bbox, canvas, tol: float = 4.0) -> bool:
    return (
        bbox.x0 < canvas.x0 - tol or bbox.y0 < canvas.y0 - tol
        or bbox.x1 > canvas.x1 + tol or bbox.y1 > canvas.y1 + tol
    )


def check_figure(fig, max_issues: int = 30, check_bounds: bool = False) -> list[str]:
    """Draw the figure and report tick-label overlap / out-of-canvas text.

    The check is deliberately conservative and catches the most common
    publication failures: overlapping tick labels and, when ``check_bounds`` is
    true, titles/labels clipped by the canvas.  It is not an image-comparison
    test.  Bounds are off by default because ``bbox_inches="tight"`` legitimately
    expands the saved canvas beyond ``fig.bbox``.
    """
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    canvas = fig.bbox
    issues: list[str] = []

    for ax_index, ax in enumerate(fig.axes):
        for axis_name, labels in (
            ("x", ax.get_xticklabels()),
            ("y", ax.get_yticklabels()),
        ):
            boxes: list[tuple[str, object]] = []
            for label in labels:
                if not label.get_visible():
                    continue
                text = label.get_text().strip()
                if not text:
                    continue
                bbox = label.get_window_extent(renderer)
                if bbox.width <= 0 or bbox.height <= 0:
                    continue
                boxes.append((text, bbox))
                if check_bounds and _outside(bbox, canvas):
                    issues.append(
                        f"axes[{ax_index}] {axis_name} tick label {text!r} "
                        "extends outside the canvas"
                    )
            for i in range(len(boxes)):
                for j in range(i + 1, len(boxes)):
                    if _bbox_overlap(boxes[i][1], boxes[j][1]):
                        issues.append(
                            f"axes[{ax_index}] {axis_name} tick labels overlap: "
                            f"{boxes[i][0]!r} / {boxes[j][0]!r}"
                        )

        if check_bounds:
            texts = [ax.title, ax.xaxis.label, ax.yaxis.label, *ax.texts]
            for text in texts:
                if not text.get_visible() or not text.get_text().strip():
                    continue
                bbox = text.get_window_extent(renderer)
                if bbox.width <= 0 or bbox.height <= 0:
                    continue
                if _outside(bbox, canvas):
                    issues.append(
                        f"axes[{ax_index}] text {text.get_text()!r} extends outside the canvas"
                    )

            legend = ax.get_legend()
            if legend is not None:
                bbox = legend.get_window_extent(renderer)
                if _outside(bbox, canvas):
                    issues.append(f"axes[{ax_index}] legend extends outside the canvas")

    if check_bounds:
        for text in fig.texts:
            if text.get_visible() and text.get_text().strip():
                bbox = text.get_window_extent(renderer)
                if _outside(bbox, canvas):
                    issues.append(f"figure text {text.get_text()!r} extends outside the canvas")

    # Keep the report useful rather than repeating hundreds of overlaps.
    return list(dict.fromkeys(issues))[:max_issues]


# ---------------------------------------------------------------------------
# Saving
# ---------------------------------------------------------------------------

def save_figure(
    fig,
    path,
    dpi: int = 300,
    also_pdf: bool = False,
    tight: bool = True,
    pad_inches: float = 0.02,
    facecolor: str = "white",
    close: bool = False,
    check: bool = False,
) -> list[Path]:
    """Save a figure and return every path written.

    With ``check=True``, the layout QA report is emitted as warnings before
    writing.  Canvas-bound checks are enabled when ``tight=False``; a tight
    bounding box deliberately expands the canvas, so bounds are not meaningful
    in that mode.

    ``tight=True`` crops to the artists and therefore changes the final physical
    size.  For a journal figure whose ``figsize`` is already the required width,
    pass ``tight=False``.
    """
    if dpi <= 0:
        raise ValueError(f"dpi must be positive, got {dpi!r}")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if check:
        for issue in check_figure(fig, check_bounds=not tight):
            warnings.warn(issue, RuntimeWarning, stacklevel=2)
    if path.suffix.lower() in {".png", ".jpg", ".jpeg"} and dpi < 300:
        warnings.warn(f"Raster output at {dpi} dpi is below the 300 dpi default.", RuntimeWarning, stacklevel=2)

    kwargs = {"dpi": dpi, "facecolor": facecolor}
    if tight:
        kwargs.update({"bbox_inches": "tight", "pad_inches": pad_inches})
    fig.savefig(path, **kwargs)
    written = [path]

    if also_pdf and path.suffix.lower() != ".pdf":
        pdf_path = path.with_suffix(".pdf")
        pdf_kwargs = {"facecolor": facecolor, "dpi": dpi}
        if tight:
            pdf_kwargs.update({"bbox_inches": "tight", "pad_inches": pad_inches})
        fig.savefig(pdf_path, **pdf_kwargs)
        written.append(pdf_path)

    if close:
        plt.close(fig)
    return written


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

def _self_test() -> None:
    import tempfile

    set_ocean_style(base_size=8)
    lon = np.arange(112, 132.01, 0.5)
    lat = np.arange(17, 32.51, 0.5)
    data = np.exp(-((lon[None, :] - 122) ** 2 + (lat[:, None] - 25) ** 2) / 20)
    info = validate_grid(lon, lat, data)
    assert info["data_shape"] == (lat.size, lon.size)
    assert info["lon_order"] == "ascending"

    assert degree_step(20, 6) == 4
    ticks = degree_ticks(112, 132, 5)
    assert ticks[0] == 115 and ticks[-1] == 130

    constant = iqr_filter(np.ones((4, 4)))
    assert np.isfinite(constant).all(), "constant field must survive IQR filter"

    try:
        import scipy  # noqa: F401 - optional dependency
    except ImportError:
        print("self-test: scipy not installed; skipping largest-region check")
    else:
        blobs = np.full((20, 20), np.nan)
        blobs[1:4, 1:4] = 1.0
        blobs[10:18, 10:18] = 2.0
        one = keep_largest_region(blobs)
        assert np.isfinite(one[10:18, 10:18]).all()
        assert np.isnan(one[1:4, 1:4]).all()

    dates = np.arange("2020-01-01", "2021-01-01", dtype="datetime64[D]")
    fig, ax = plt.subplots(figsize=(4, 2.5), constrained_layout=True)
    ax.plot(dates, np.sin(np.linspace(0, 6 * np.pi, dates.size)))
    auto_time_axis(ax, dates)
    assert ax.xaxis.get_major_locator() is not None

    ax.set_title("self-test")
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "selftest.png"
        written = save_figure(fig, out, dpi=300, also_pdf=True)
        assert out.exists() and out.stat().st_size > 0
        assert out.with_suffix(".pdf").exists()
        print(f"self-test OK: {[str(p) for p in written]}")
    plt.close(fig)


def cli(argv=None) -> int:
    """Command-line entry point for the helper package."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="ocean-plot",
        description="Helpers for publication-quality oceanography figures.",
    )
    parser.add_argument("--self-test", action="store_true", help="run built-in smoke tests")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args(argv)
    if args.self_test:
        _self_test()
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
