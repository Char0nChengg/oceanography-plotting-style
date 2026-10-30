"""3 x 2 regional-map template.

The data here are synthetic.  Replace ``synthetic_ssh`` with your own
(lat, lon) fields, keep the parameter block at the top of ``main()``, and
run the demo explicitly:

    python templates/map_panel_grid.py --demo

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
    add_map_features,
    add_panel_label,
    auto_tick_step,
    check_figure,
    colorbar_ticks,
    get_cmap,
    projection_for_region,
    save_figure,
    set_map_ticks,
    set_ocean_style,
    validate_grid,
)
from ocean_journal import apply_journal_style, get_journal  # noqa: E402


def synthetic_ssh(lon: np.ndarray, lat: np.ndarray, phase: float) -> np.ndarray:
    """Synthetic eddy-like field used only to demonstrate the layout."""
    lon2d, lat2d = np.meshgrid(lon, lat)
    eddy = 0.22 * np.exp(
        -((lon2d - 122.0 - 1.5 * np.sin(phase)) ** 2 / 16.0
          + (lat2d - 25.0) ** 2 / 9.0)
    )
    wave = 0.05 * np.cos(2 * np.pi * (lon2d - 112.0) / 12.0 + phase)
    return np.clip(eddy + wave, 0.0, None)


def main() -> None:
    # ========== 路径 ==========
    output_png = Path("figures/Fig_map_3x2.png")

    # ========== 区域 ==========
    lon_min, lon_max = 112.0, 132.0
    lat_min, lat_max = 17.0, 32.5

    # ========== 色标 ==========
    cmap_name = "cmo.dense"
    vmin, vmax = 0.0, 0.30
    cbar_extend = "neither"      # synthetic data stay inside [vmin, vmax]
    cbar_label = "SSH amplitude (m)"

    # ========== 版面 ==========
    journal_name = "agu"
    style = get_journal(journal_name)
    fig_width = style.width_in("double")
    fig_height = 7.2
    font_title, font_tick, font_label = style.title_pt, style.tick_pt, style.body_pt
    save_dpi = style.dpi
    map_scale = "50m"            # use "10m" for a single large map; 50m keeps PDFs small
    map_aspect = "equal"         # never "auto" unless intentionally distorting

    months = ("Jan", "Feb", "Mar", "Apr", "May", "Jun")
    panel_labels = tuple("abcdef")

    set_ocean_style(base_size=style.body_pt)
    apply_journal_style(journal_name)
    cmap = get_cmap(cmap_name)

    # ---- synthetic data: replace with real fields ----
    lon = np.arange(lon_min, lon_max + 0.01, 0.1)
    lat = np.arange(lat_min, lat_max + 0.01, 0.1)
    fields = [synthetic_ssh(lon, lat, phase=i * np.pi / 6) for i in range(6)]
    for field in fields:
        validate_grid(lon, lat, field, name="synthetic_ssh")

    map_spec = projection_for_region(
        lon_min, lon_max, lat_min, lat_max, kind="auto",
    )
    projection = map_spec.crs
    data_crs = ccrs.PlateCarree()
    lon_step, lat_step = auto_tick_step(
        lon_min, lon_max, lat_min, lat_max,
        figsize=(fig_width, fig_height), ncols=2, nrows=3,
        fontsize=font_tick,
    )
    fig = plt.figure(figsize=(fig_width, fig_height))
    gs = fig.add_gridspec(
        3, 3, width_ratios=[1, 1, 0.035],
        hspace=0.25, wspace=0.10,
    )
    axes = [
        fig.add_subplot(gs[row, col], projection=projection)
        for row in range(3) for col in range(2)
    ]
    cax = fig.add_subplot(gs[:, 2])
    fig.subplots_adjust(left=0.07, right=0.90, top=0.93, bottom=0.11)

    assert len(axes) == len(months) == len(panel_labels) == len(fields) == 6
    pcm = None
    for idx, (ax, month, label, field) in enumerate(
        zip(axes, months, panel_labels, fields)
    ):
        pcm = ax.pcolormesh(
            lon, lat, field,
            cmap=cmap, vmin=vmin, vmax=vmax,
            shading="auto", transform=data_crs, rasterized=True,
        )
        ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=data_crs)
        add_map_features(ax, scale=map_scale)
        ax.set_aspect(map_aspect)

        set_map_ticks(
            ax, map_spec, [lon_min, lon_max, lat_min, lat_max],
            lon_step=lon_step, lat_step=lat_step, fontsize=font_tick,
        )
        # shared labels: y only on the left column, x only on the bottom row
        if idx % 2 == 1:
            ax.tick_params(labelleft=False)
        if idx < 4:
            ax.tick_params(labelbottom=False)

        ax.set_title(month, fontsize=font_title, fontweight="normal", pad=4)
        add_panel_label(ax, f"({label})", fontsize=font_title)

    cbar = fig.colorbar(pcm, cax=cax, extend=cbar_extend)
    cbar.set_ticks(colorbar_ticks(vmin, vmax, 5))
    cbar.set_label(cbar_label, fontsize=font_label, labelpad=8)
    cbar.ax.tick_params(labelsize=font_tick)

    for issue in check_figure(fig, check_bounds=True):
        print("layout warning:", issue)
    written = save_figure(
        fig, output_png, dpi=save_dpi, also_pdf=True, tight=False,
    )
    print("saved:", ", ".join(str(p) for p in written))


if __name__ == "__main__":
    main()
