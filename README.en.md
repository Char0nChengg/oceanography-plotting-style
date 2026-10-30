# Oceanography Plotting Style

> A reusable plotting standard and code toolkit for physical-oceanography figures. It works as a DeepSeek Harness / Agent Skill and as a standalone Python package.

**English** | [中文](README.md)

[![CI](https://github.com/Char0nChengg/oceanography-plotting-style/actions/workflows/ci.yml/badge.svg)](https://github.com/Char0nChengg/oceanography-plotting-style/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## What is this?

When preparing an oceanography paper, the hard part is rarely the `pcolormesh` call. The recurring problems are:

- longitude/latitude order is reversed, or 1-D/2-D coordinates are broadcast incorrectly;
- 0–360° and −180–180° conventions are mixed, so dateline-crossing maps split apart;
- the colorbar `extend` flag does not match how the data were clipped;
- font sizes look fine on a 22-inch canvas but become unreadable at final print width;
- `set_aspect("auto")` stretches the map;
- 10 m coastlines turn a six-panel PDF into tens of megabytes;
- a multi-year time axis still uses `%m-%d`;
- the figure runs, but labels are clipped, ticks overlap, and the colorbar has no units.

This project turns those lessons into a **loadable Agent Skill** plus importable Python utilities, runnable templates, tests, and CI. The goal is not merely “a figure that runs”; it is **a figure that can go into a paper**.

---

## Design stance

The visual style of this project is the author's personal preference, not an official journal template. Authors, journals, and reviewers have different visual traditions. Some common submission figures devote more attention to decoration, saturation, or stacked text than to the data itself, which can make the science harder to read. This project chooses a more restrained, information-dense approach without judging other authors; the target journal's latest guidelines always take precedence.

- **cmocean only**: no jet/rainbow maps; choose sequential, diverging, or cyclic maps according to the variable.
- **Figure first, text restrained**: no overall figure title, only panel subtitles and `(a)`/`(b)` labels; share axes and labels whenever possible.
- **A clear colorbar without taking over the map**: prefer an outer column, a strip below the figure, or an inset; segmented/composite colorbars are allowed when useful, with 4–7 ticks and honest `extend`.
- **A consistent language for analysis figures**: CCA, wavelet, spectral, and EMD figures use the same author style. These choices have been used in the author's own submissions and revisions and have been examined through journal editing and peer review; a question-driven ocean/atmosphere statistics tutorial is planned.

Read the full [design stance](docs/style-philosophy.en.md). It is a repeatable, checkable personal workflow, not a claim to the only valid aesthetic.

---

## Examples

3 × 2 regional maps (synthetic data, layout/colormap demo only):

![3x2 map demo](docs/assets/map_panel_grid.png)

Map + time series + vertical section (synthetic data):

![mixed panel demo](docs/assets/mixed_panel_grid.png)

> Templates default to `50m` coastlines to keep PDFs small; use `10m` for a single large map. Every template requires an explicit `--demo` flag so synthetic data cannot silently become a result figure.

---

## Features

| Capability | Description |
|---|---|
| Regional maps | Regional Mercator default; Robinson for global, PolarStereo for polar; formatter/gridline labels and adaptive ticks |
| NetCDF adaptation | `valid_time`/`nav_lon`/`uos/vos` aliases, CF/profiles, ambiguity reports, `ocean-plot --inspect` |
| Figure catalog | Catalog-first routing; recipes split by maps/sections/time/statistics/spectral/flow, with planned status |
| Multi-panel layouts | Shared colorbars, hidden inner labels, panel letters, GridSpec / explicit colorbar column |
| Vertical sections / Hovmöller | Depth direction, time axis, symmetric/asymmetric limits, transpose checks |
| Time series | Mean ± standard deviation, rolling statistics, automatic time locators |
| FFT | Detrending, windows, one-sided amplitude, AR(1) red-noise Monte-Carlo threshold |
| Quiver | Arrow length in layout inches, `quiverkey`, density-aware stride |
| Colormaps | cmocean, `TwoSlopeNorm`, `LogNorm`, `BoundaryNorm`, truncation |
| Data preparation | xarray dimension normalization, region subsetting, dateline, descending latitude, 2-D coordinates |
| Journal presets | AGU / AMS / Elsevier / Nature / generic widths and font sizes |
| Figure QA | Tick-overlap checks, optional canvas-bound checks, approximate CVD/grayscale screening |
| Reproducibility | `--self-test`, pytest, GitHub Actions, dependency files |

---

## Installation

### Option A: as a DSH / Agent Skill

DSH discovers skills from directories; **do not** use `dsh plugin add` for a skill.

```text
<project>/.dsh/skills/oceanography-plotting-style/SKILL.md
```

or globally:

```text
~/.dsh/skills/oceanography-plotting-style/SKILL.md
```

Clone/copy this repository to that directory. `SKILL.md` is at the repository root, so the repository itself can serve as the skill directory.

```bash
git clone https://github.com/Char0nChengg/oceanography-plotting-style.git \
  .dsh/skills/oceanography-plotting-style
```

After loading, invoke `/oceanography-plotting-style` where supported; the model can also route to it from the `description`.

### Option B: as a Python package

```bash
python -m pip install -e ".[full]"
```

Minimal install (only the base `ocean_plot` helpers):

```bash
python -m pip install -e .
```

On Windows, Cartopy is easiest through conda:

```bash
conda env create -f environment.yml
conda activate oceanography-plotting-style
```

---

## Quick start

The example below uses the `.[full]` dependencies (Cartopy, cmocean, xarray).

```python
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

from ocean_data import grid_arrays, load_for_plot
from ocean_plot import (
    add_map_features, add_panel_label, auto_tick_step, check_figure,
    get_cmap, projection_for_region, save_figure, set_map_ticks,
    set_ocean_style, validate_grid,
)
from ocean_journal import get_journal, apply_journal_style

journal = get_journal("agu")
set_ocean_style(base_size=journal.body_pt)
apply_journal_style(journal.key)   # order matters: journal line widths win

lon_min, lon_max = 112.0, 132.0
lat_min, lat_max = 17.0, 32.5
fig_width = journal.width_in("double")

# Replace with your file; the map explicitly uses the first frame
da = load_for_plot(
    "data/ssh.nc", "ssh",
    region={"lon": (lon_min, lon_max), "lat": (lat_min, lat_max)},
)
frame = da.isel(time=0) if "time" in da.dims else da
lon, lat, ssh = grid_arrays(frame)
validate_grid(lon, lat, ssh)

map_spec = projection_for_region(lon_min, lon_max, lat_min, lat_max, kind="auto")
data_crs = ccrs.PlateCarree()
fig, ax = plt.subplots(
    figsize=(fig_width, 4.8),
    subplot_kw={"projection": map_spec.crs},
    constrained_layout=True,
)
mesh = ax.pcolormesh(
    lon, lat, ssh, cmap=get_cmap("cmo.dense"),
    vmin=0, vmax=0.3, shading="auto",
    transform=data_crs, rasterized=True,
)
ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=data_crs)
add_map_features(ax, scale="50m")
step_x, step_y = auto_tick_step(
    lon_min, lon_max, lat_min, lat_max,
    figsize=(fig_width, 4.8), fontsize=journal.tick_pt,
)
set_map_ticks(ax, map_spec, [lon_min, lon_max, lat_min, lat_max],
              lon_step=step_x, lat_step=step_y)
ax.set_aspect("equal")
add_panel_label(ax, "(a)")

cbar = fig.colorbar(mesh, ax=ax, extend="neither")
cbar.set_label("SSH amplitude (m)")

for issue in check_figure(fig, check_bounds=True):
    print("layout warning:", issue)
save_figure(
    fig, Path("figures/Fig_01.png"), dpi=journal.dpi,
    also_pdf=True, tight=False,
)
```

> The snippet assumes `data/ssh.nc` and explicitly takes the first frame; replace both with your own file and time selection. See `templates/map_panel_grid.py` for the template version.

---

## Templates

```bash
# 3 x 2 maps
python templates/map_panel_grid.py --demo

# map + time series + vertical section
python templates/mixed_panel_grid.py --demo
```

Without `--demo`, the templates exit immediately and remind you to replace the synthetic data.

---

## Data preparation

```python
from ocean_vocab import inspect_dataset
from ocean_data import canonicalize_dims, subset_region, pick_var, grid_arrays

print(inspect_dataset(ds).as_dict())   # coordinates and variable candidates first
ds = canonicalize_dims(ds)              # valid_time/nav_lon etc.
ds = subset_region(ds, lon_bounds=(112, 132), lat_bounds=(17, 32.5))
da = pick_var(ds, "ssh")                # semantic key, not a guessed name
lon, lat, data = grid_arrays(da)
```

Or inspect from the CLI:

```bash
ocean-plot --inspect data.nc
```

- Supports 1-D regular and 2-D curvilinear longitude/latitude; `grid_arrays()` does not require coordinate names to equal dimension names.
- Recognizes `valid_time`, `nav_lon/nav_lat`, `uos/vos`, `siconc/sithick`, and similar conventions; ambiguity is reported instead of silently choosing the first variable.
- 1-D dateline-crossing and negative-longitude boxes return monotonic unwrapped 0–360° coordinates (possibly > 360). Use `central_longitude=180` or an equivalent projection.
- 2-D curvilinear coordinates are masked in place and keep their native longitudes; they are never unwrapped or sorted.
- Full-globe boxes `(-180, 180)` / `(0, 360)` do not drop longitudes.
- `load_for_plot()` preserves the time dimension unless you explicitly select a time; it never silently takes `time=0`.

Naming and diagnostics: [netcdf-profiles.md](references/netcdf-profiles.md).

## Projection

- Regional mid/low latitudes: **Mercator** (default)
- Global: Robinson / EqualEarth
- Polar: North/SouthPolarStereo
- High-latitude regional: LambertConformal
- Data transform is always `ccrs.PlateCarree()`

`projection_for_region()` chooses the axes projection and `set_map_ticks()` chooses longitude/latitude formatters or gridline labels. See the [figure catalog](references/figure-catalog.md) and [tutorials](docs/tutorials/README.md).

---

## Spectral analysis

```python
from ocean_spectral import fft_amplitude, ar1_threshold, dominant_period

freq, amp = fft_amplitude(x, dt=1.0, detrend="linear", window="hann")
result = ar1_threshold(x, dt=1.0, confidence=0.95, n_sim=500, seed=0)
period = dominant_period(freq, amp)
```

The AR(1) threshold is an explicit null hypothesis: fit a red-noise model, then Monte-Carlo the amplitude spectrum. It is not a universal significance test; document `n_sim`, `confidence`, the window, and the detrending method.

---

## Colormaps and accessibility

```python
from ocean_access import accessibility_report

report = accessibility_report("cmo.balance")
print(report["warnings"])
```

- Grayscale luminance separation.
- Approximate deuteranopia / protanopia simulation.
- The result is a screening aid, not an accessibility certification.

---

## Journal presets

| key | Intended use | Single column | Double column | Body text |
|---|---|---:|---:|---:|
| `generic` | General manuscript | 89 mm | 183 mm | 8 pt |
| `agu` | AGU / JGR / GRL | 89 mm | 180 mm | 8 pt |
| `ams` | AMS | 85 mm | 178 mm | 8 pt |
| `elsevier` | Elsevier | 90 mm | 190 mm | 8 pt |
| `nature` | Nature portfolio | 89 mm | 183 mm | 6 pt |

These are practical defaults from the author's workflow, not official journal templates. Requirements change across journals and years (Nature's 6 pt is one example); check the latest author guidelines before submission.

```python
from ocean_journal import get_journal, figure_size, apply_journal_style

style = get_journal("ams")
w, h = figure_size("ams", "double", height_mm=200)
apply_journal_style("ams")
```

---

## Project structure

```text
.
├── SKILL.md                  # Agent Skill entry point
├── README.md                 # Chinese introduction
├── README.en.md              # English introduction
├── CHANGELOG.md
├── references/
│   ├── figure-catalog.md     # Figure index: variables, projection, recipe, status
│   ├── style-reference.md    # Typography, layout, maps, colormaps, acceptance
│   ├── data-prep.md          # xarray, regions, longitude, filtering
│   ├── netcdf-profiles.md    # CF/product names and dataset diagnostics
│   ├── figure-recipes.md     # Compatibility entry
│   └── recipes/              # Domain-specific recipes
├── scripts/
│   ├── ocean_plot.py         # Projection, ticks, maps, colormaps, QA, saving
│   ├── ocean_vocab.py        # Variable/coordinate aliases, CF, diagnostics
│   ├── ocean_data.py         # Dimension normalization, regions, variables
│   ├── ocean_spectral.py     # FFT + AR(1) thresholds
│   ├── ocean_journal.py      # Journal presets
│   └── ocean_access.py       # Grayscale/CVD screening
├── templates/
│   ├── map_panel_grid.py
│   └── mixed_panel_grid.py
├── tests/
├── docs/
│   ├── style-philosophy.en.md
│   ├── style-philosophy.md
│   ├── tutorials/            # Human tutorials; ignored by default for plotting
│   └── assets/
└── .github/workflows/
    ├── ci.yml
    └── release.yml
```

---

## Tests and validation

```bash
python scripts/ocean_plot.py --self-test
python -m pytest -q
```

Rendered and verified locally with:

- Python 3.13.9 (Anaconda base)
- Matplotlib 3.10.6
- Cartopy 0.25.0
- cmocean 3.0.3
- xarray 2025.10.1 / scipy 1.16.3 / pandas 2.3.3

CI installs Cartopy on Ubuntu with Python 3.10/3.12/3.13, runs the tests, self-test, both templates, and wheel/sdist checks.

---

## Known boundaries

- Focused on regular 1-D and curvilinear 2-D longitude/latitude grids. It does **not** automatically convert ROMS staggered grids, unstructured triangular meshes, or projected coordinates in metres/kilometres.
- Journal widths and font sizes are practical defaults, not a substitute for current author guidelines.
- `auto_tick_step()` is still a heuristic; `check_figure()` catches actual tick overlap, but this is not pixel-level image regression.
- `set_degree_ticks()` supports rectangular projections only (PlateCarree, Mercator, and similar); use the gridlines mode of `set_map_ticks()` for LCC/Robinson-style maps.
- Regional maps default to Mercator; global maps use Robinson, polar maps use PolarStereo, and high-latitude regions can use Lambert explicitly.
- `ocean_vocab` reports ambiguity instead of silently choosing among multiple variable candidates; add a profile and a synthetic test for a new convention.
- `docs/tutorials/` is human-facing; AI plotting tasks ignore it by default.
- CVD matrices are approximations; use a dedicated tool for final accessibility review.
- The AR(1) threshold assumes a single red-noise null hypothesis; complex spectral peaks need problem-specific tests.
- Natural Earth data are downloaded on first use; cache them for offline work.
- All template data are synthetic and must be replaced; `--demo` is a safety switch.
- `pip install` provides the Python modules; `SKILL.md`, `references/`, and `templates/` are distributed through the repository/skill directory and are not included in the wheel.
- `tight=True` changes the final physical size. Use `tight=False` for journal delivery and run the canvas check before saving.

---

## Contributing

Issues and pull requests are welcome, especially:

- new journal presets;
- unstructured-grid or projected-coordinate examples;
- end-to-end examples with public real data;
- visual-regression baselines.

Please make sure `python -m pytest -q` passes and include the rendered PNG with visual changes.

---

## License

MIT. See [LICENSE](LICENSE). Version history: [CHANGELOG.md](CHANGELOG.md).

## Citation

If this project helps your paper, you may mention it in the methods or acknowledgements:

> Figures were prepared with the `oceanography-plotting-style` toolkit (Char0nChengg, 2026), built on Matplotlib, Cartopy and cmocean.
