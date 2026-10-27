# Changelog

All notable changes to this project are documented here.  The format follows
Keep a Changelog; versions use semantic versioning.

## [0.2.1] - 2026-10-27

### Added

- Bilingual design-stance pages and README sections describing the author's
  cmocean-only, figure-first, restrained-text, and external-colorbar choices.
- `references/style-reference.md` acceptance commands, visual criteria, and a
  concrete failure-case table.
- Regression tests for full-globe subsetting, 2-D `grid_arrays()`, Mercator and
  non-rectangular tick handling, exact saved dimensions, AR(1) metadata, and
  template widths.
- CI packaging job (wheel + sdist, `twine check`, wheel install smoke test) and
  a tag-triggered GitHub Release workflow.

### Changed

- `set_degree_ticks()` now defaults GeoAxes to `PlateCarree` and raises a clear
  `NotImplementedError` for non-rectangular projections; use gridline labels
  for LCC/Robinson-style maps.
- Full-globe `subset_region()` requests no longer collapse to one meridian;
  1-D output is normalized to 0–360 when bounds require it, while 2-D
  curvilinear coordinates stay native and are masked in place.
- `grid_arrays()` derives transpose order from coordinate dimensions, so 1-D
  `lon(x)`/`lat(y)` and 2-D curvilinear coordinates work without renaming dims.
- `ar1_threshold()` initializes simulations from the stationary AR(1)
  distribution and returns `n_sim`, `seed`, `detrend`, and `window` metadata.
  Threshold values will change slightly; this is a correctness fix.
- `auto_time_axis()` uses daily ticks for 31–89 day spans (month ticks start at
  90 days), resets numeric formatters, and rejects timedelta axes explicitly.
- `save_figure(check=True)` now enables canvas-bound checks when `tight=False`;
  `tight=True` remains available for previews but changes physical size.
- `ocean_plot` no longer forces the Agg backend at import time. Templates and
  the CLI keep headless output deterministic.
- `colorbar_ticks()` caps symmetric ticks at 4–7; `robust_limits()` no longer
  invents a negative lower bound for positive data with `include_zero=True`.
- Journal guidance now treats presets as empirical and allows the 6–10 pt /
  7.0–7.5 in range used by the presets; numeric column widths are accepted.
- Template interiors use `tight=False` for exact delivery widths, honest
  `extend="neither"` for the synthetic fields, and a tighter mixed layout.
- `ocean_access` wording now explicitly describes screening, not certification.

### Fixed

- Map template PNG/PDF width no longer shrinks from 7.09 in to 6.37 in under
  `bbox_inches="tight"`.
- Mercator degree labels no longer all read `120.001°E`; LCC no longer fails
  with an opaque formatter traceback.
- 2-D `grid_arrays()` no longer raises `Dimensions {'lat','lon'} do not exist`.
- `dominant_period()` rejects NaN/inf, shape mismatches, and negative `fmin`
  instead of returning a misleading period or `inf`.
- `figure_size()` rejects non-positive heights/aspects; `width_mm(1.0)` and
  `width_mm(2.0)` work.
- Invalid `keep_largest_region()` connectivity and accessibility sampling
  counts now raise actionable errors.
- The FFT recipe no longer silently compresses gaps before spectral analysis.
- `ocean-plot --self-test` now skips the optional SciPy connected-region check
  when SciPy is not installed, so the minimal wheel smoke test passes.

### Documentation

- Trimmed `SKILL.md`, removed the dead code skeleton and stale editable-install
  claim, and linked the references through an explicit API order.
- Removed duplicated implementations from `references/`; data-preparation rules
  now point at the tested `ocean_data` API, and recipes include their imports.
- README quick start now applies style in the correct order and saves with
  `tight=False`; both language versions document the same boundaries.

## [0.2.0] - 2026-10-21

### Added

- `ocean_data.py`: canonical dimension names, region subsetting (including
  dateline and 2-D coordinates), variable aliases, explicit time selection,
  `grid_arrays()`.
- `ocean_spectral.py`: one-sided FFT amplitude, Hann/Hamming/Blackman windows,
  AR(1) red-noise Monte-Carlo thresholds, dominant-period helper.
- `ocean_journal.py`: AGU / AMS / Elsevier / Nature / generic width and font
  presets; `figure_size()` and `apply_journal_style()`.
- `ocean_access.py`: grayscale luminance and approximate deuteranopia /
  protanopia screening.
- `check_figure()` layout QA (tick-label overlap, optional canvas bounds).
- `--demo` guards and synthetic-data warnings in both templates.
- Journal-aware template sizing, explicit full-height colorbar column, shared
  axis labels, and `check_figure()` before saving.
- pytest suite, CI workflow, `environment.yml`, requirements files, README,
  demo assets, changelog and MIT license.
- `pyproject.toml` with optional `full` and `test` dependency groups.

### Changed

- `auto_tick_step()` now uses font size and a configurable maximum tick count.
- `save_figure()` can emit layout QA warnings via `check=True`.
- `validate_grid()` handles masked arrays.
- `colorbar_ticks()` handles constant ranges.
- Default map scale is `50m` for multipanel/PDF output; `10m` remains available
  for single large maps.
- `ocean_plot` now exposes a `cli()` entry point (`ocean-plot --self-test`).

### Fixed

- Unwrapped dateline subsets remain monotonic.
- Empty 2-D subsets are detected correctly.
- 2-D accessibility checks use representative levels instead of 256 adjacent
  samples that are naturally nearly identical.

## [0.1.0] - 2026-10-21

### Added

- Initial DSH/Agent Skill package: monolithic `SKILL.md`, style/data/figure
  references, plotting helper, and two runnable templates.
