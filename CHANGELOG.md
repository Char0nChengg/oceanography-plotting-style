# Changelog

All notable changes to this project are documented here.  The format follows
Keep a Changelog; versions use semantic versioning.

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
