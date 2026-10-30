"""Mixed-panel template: map + time series + vertical section.

Layout::

    +------------------+------------------+
    |  (a) regional    |  (b) time series |
    |      map         |                  |
    +------------------+------------------+
    |  (c) depth-time section (full width) |
    +---------------------------------------+

The data are synthetic.  Replace them and keep all design parameters at the
top of ``main()``.  Run the demo explicitly:

    python templates/mixed_panel_grid.py --demo

Requires: matplotlib, numpy, cartopy, cmocean.
"""

from __future__ import annotations

import sys
from pathlib import Path

if __name__ == "__main__" and "--demo" not in sys.argv:
    raise SystemExit(
        "This is a synthetic demo template. Pass --demo to render it; "
        "replace the synthetic fields before using it for a paper."
    )

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SKILL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_DIR / "scripts"))

try:
    import cartopy.crs as ccrs
except ModuleNotFoundError as exc:  # pragma: no cover - environment guard
    raise SystemExit(
        "This template needs cartopy and cmocean. "
        "Install them with: pip install cartopy cmocean"
    ) from exc

from ocean_plot import (  # noqa: E402
    add_colorbar,
    add_map_features,
    add_panel_label,
    auto_tick_step,
    auto_time_axis,
    check_figure,
    get_cmap,
    projection_for_region,
    save_figure,
    set_map_ticks,
    set_ocean_style,
    validate_grid,
)
from ocean_journal import apply_journal_style, get_journal  # noqa: E402


def main() -> None:
    # ========== 路径 ==========
    output_png = Path("figures/Fig_mixed.png")

    # ========== 区域 ==========
    lon_min, lon_max = 112.0, 132.0
    lat_min, lat_max = 17.0, 32.5

    # ========== 地图色标 ==========
    map_cmap_name = "cmo.dense"
    map_vmin, map_vmax = 0.0, 0.30
    map_extend = "neither"       # synthetic data stay inside [vmin, vmax]
    map_cbar_label = "SSH amplitude (m)"

    # ========== 剖面色标 ==========
    prof_cmap_name = "cmo.thermal"
    prof_vmin, prof_vmax = 2.0, 28.0
    prof_extend = "neither"
    prof_cbar_label = "Temperature (°C)"

    # ========== 版面 ==========
    journal_name = "agu"
    style = get_journal(journal_name)
    fig_width = style.width_in("double")
    fig_height = 5.8
    font_title, font_tick, font_label = style.title_pt, style.tick_pt, style.body_pt
    save_dpi = style.dpi
    map_scale = "50m"            # use "10m" for a single large map; 50m keeps PDFs small

    set_ocean_style(base_size=style.body_pt)
    apply_journal_style(journal_name)
    map_cmap = get_cmap(map_cmap_name)
    prof_cmap = get_cmap(prof_cmap_name)

    # ---- synthetic data: replace with real fields ----
    lon = np.arange(lon_min, lon_max + 0.01, 0.1)
    lat = np.arange(lat_min, lat_max + 0.01, 0.1)
    lon2d, lat2d = np.meshgrid(lon, lat)
    ssh = 0.24 * np.exp(
        -((lon2d - 122.0) ** 2 / 12.0 + (lat2d - 25.0) ** 2 / 8.0)
    )
    validate_grid(lon, lat, ssh, name="ssh")

    dates = np.arange("2020-01-01", "2020-03-01", dtype="datetime64[D]")
    t = np.arange(dates.size, dtype=float)
    series = 0.12 * np.sin(2 * np.pi * t / 30.0) + 0.03 * np.cos(2 * np.pi * t / 7.0)
    spread = 0.02 + 0.01 * np.sin(2 * np.pi * t / 45.0)

    depth = np.arange(0.0, 310.0, 10.0)
    temp = (
        22.0 * np.exp(-depth[None, :] / 90.0)
        + 4.0 * np.sin(2 * np.pi * t[:, None] / 45.0) * np.exp(-depth[None, :] / 200.0)
    )
    temp = np.clip(temp, prof_vmin, prof_vmax)

    # ---- layout ----
    map_spec = projection_for_region(
        lon_min, lon_max, lat_min, lat_max, kind="auto",
    )
    projection = map_spec.crs
    data_crs = ccrs.PlateCarree()
    fig = plt.figure(figsize=(fig_width, fig_height), layout="constrained")
    gs = fig.add_gridspec(
        2, 2, width_ratios=[1.2, 1.0], height_ratios=[1.0, 0.8],
        hspace=0.06, wspace=0.10,
    )

    ax_map = fig.add_subplot(gs[0, 0], projection=projection)
    ax_ts = fig.add_subplot(gs[0, 1])
    ax_prof = fig.add_subplot(gs[1, :])

    # ---- (a) map ----
    pcm = ax_map.pcolormesh(
        lon, lat, ssh, cmap=map_cmap,
        vmin=map_vmin, vmax=map_vmax, shading="auto",
        transform=data_crs, rasterized=True,
    )
    ax_map.set_extent([lon_min, lon_max, lat_min, lat_max], crs=data_crs)
    add_map_features(ax_map, scale=map_scale)
    ax_map.set_aspect("equal")
    lon_step, lat_step = auto_tick_step(
        lon_min, lon_max, lat_min, lat_max,
        figsize=(fig_width, fig_height), ncols=2, nrows=2,
        fontsize=font_tick,
    )
    set_map_ticks(
        ax_map, map_spec, [lon_min, lon_max, lat_min, lat_max],
        lon_step=lon_step, lat_step=lat_step, fontsize=font_tick,
    )
    ax_map.set_title("SSH amplitude", fontsize=font_title, fontweight="normal", pad=4)
    add_panel_label(ax_map, "(a)", fontsize=font_title)
    cbar_map = add_colorbar(
        fig, pcm, ax=ax_map, extend=map_extend,
        label=map_cbar_label, fontsize=font_label,
        orientation="horizontal", fraction=0.07, pad=0.10, aspect=30,
    )
    cbar_map.set_ticks([0.0, 0.1, 0.2, 0.3])

    # ---- (b) time series ----
    ax_ts.fill_between(
        dates, series - spread, series + spread,
        color="C0", alpha=0.22, linewidth=0,
    )
    ax_ts.plot(dates, series, color="C0", linewidth=1.2, label="SSH anomaly")
    ax_ts.set_ylabel("SSH (m)", fontsize=font_label)
    ax_ts.set_title("Time series", fontsize=font_title, fontweight="normal", pad=4)
    add_panel_label(ax_ts, "(b)", fontsize=font_title)
    ax_ts.legend(frameon=False, loc="upper right", fontsize=7)
    auto_time_axis(ax_ts, dates)
    ax_ts.tick_params(axis="both", labelsize=font_tick, labelbottom=False)

    # ---- (c) vertical section ----
    mesh = ax_prof.pcolormesh(
        dates, depth, temp.T, cmap=prof_cmap,
        vmin=prof_vmin, vmax=prof_vmax, shading="auto", rasterized=True,
    )
    ax_prof.invert_yaxis()
    ax_prof.set_ylabel("Depth (m)", fontsize=font_label)
    ax_prof.set_xlabel("Time", fontsize=font_label)
    ax_prof.set_title("Temperature section", fontsize=font_title, fontweight="normal", pad=4)
    add_panel_label(ax_prof, "(c)", fontsize=font_title)
    auto_time_axis(ax_prof, dates)
    ax_prof.tick_params(axis="both", labelsize=font_tick)

    cbar_prof = add_colorbar(
        fig, mesh, ax=ax_prof, extend=prof_extend,
        label=prof_cbar_label, fontsize=font_label,
        fraction=0.06, pad=0.02,
    )
    cbar_prof.set_ticks([5, 10, 15, 20, 25])

    for issue in check_figure(fig, check_bounds=True):
        print("layout warning:", issue)
    written = save_figure(
        fig, output_png, dpi=save_dpi, also_pdf=True, tight=False,
    )
    print("saved:", ", ".join(str(p) for p in written))


if __name__ == "__main__":
    main()
