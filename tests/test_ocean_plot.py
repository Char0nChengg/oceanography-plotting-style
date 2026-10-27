from __future__ import annotations

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pytest

import ocean_plot as op


def test_degree_step_and_ticks():
    assert op.degree_step(20, 6) == 4
    ticks = op.degree_ticks(112, 132, 5)
    assert ticks[0] == 115
    assert ticks[-1] == 130
    assert np.all(np.diff(ticks) > 0)


def test_auto_tick_step_uses_font_and_caps():
    lon_step, lat_step = op.auto_tick_step(
        112, 132, 17, 32.5, (7.2, 8.4), ncols=2, nrows=3, fontsize=8,
    )
    assert lon_step > 0 and lat_step > 0
    small_lon, small_lat = op.auto_tick_step(
        112, 132, 17, 32.5, (3.5, 2.6), ncols=1, nrows=1, fontsize=8,
    )
    assert small_lon >= lon_step
    assert small_lat >= lat_step


def test_validate_grid_and_errors():
    lon = np.arange(112, 132.1, 0.5)
    lat = np.arange(17, 32.6, 0.5)
    data = np.ones((lat.size, lon.size))
    info = op.validate_grid(lon, lat, data)
    assert info["data_shape"] == data.shape
    with pytest.raises(ValueError, match="does not match"):
        op.validate_grid(lon, lat, data[:, :-1])


def test_validate_masked_array():
    lon = np.arange(3.0)
    lat = np.arange(4.0)
    data = np.ma.array(np.ones((4, 3)), mask=[[False, True, False]] * 4)
    info = op.validate_grid(lon, lat, data)
    assert 0 < info["finite_fraction"] < 1


def test_iqr_constant_is_untouched():
    arr = np.ones((5, 5))
    out = op.iqr_filter(arr)
    assert np.isfinite(out).all()
    assert out is not arr


def test_keep_largest_region():
    arr = np.full((20, 20), np.nan)
    arr[1:4, 1:4] = 1
    arr[10:18, 10:18] = 2
    out = op.keep_largest_region(arr)
    assert np.isfinite(out[10:18, 10:18]).all()
    assert np.isnan(out[1:4, 1:4]).all()


def test_colormap_resolution():
    cmap = op.get_cmap("cmo.balance")
    assert cmap.name == "balance"
    truncated = op.truncate_colormap(cmap, 0.75)
    assert truncated.N == 256


def test_colorbar_ticks_constant():
    ticks = op.colorbar_ticks(0.2, 0.2, 5)
    assert ticks.size == 1
    assert ticks[0] == 0.2


def test_check_figure_detects_overlap():
    fig, ax = plt.subplots(figsize=(4, 3), constrained_layout=True)
    ax.plot(np.arange(10))
    ax.set_xticks(np.arange(10))
    ax.set_xticklabels([f"label-{i}" for i in range(10)])
    issues = op.check_figure(fig)
    assert any("overlap" in issue for issue in issues)


def test_check_figure_clean():
    fig, ax = plt.subplots(figsize=(4, 3), constrained_layout=True)
    ax.plot(np.arange(10))
    ax.set_title("clean")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    assert op.check_figure(fig) == []


def test_set_degree_ticks_uses_platecarree_for_mercator():
    ccrs = pytest.importorskip("cartopy.crs")
    fig, ax = plt.subplots(subplot_kw={"projection": ccrs.Mercator()})
    ax.set_extent([112, 132, 17, 32.5], crs=ccrs.PlateCarree())
    op.set_degree_ticks(ax, [112, 132, 17, 32.5], lon_step=4, lat_step=4)
    fig.canvas.draw()
    labels = [label.get_text() for label in ax.get_xticklabels()]
    assert labels[0] == "112°E"
    assert labels[-1] == "132°E"
    assert len(set(labels)) == len(labels)
    plt.close(fig)


def test_set_degree_ticks_rejects_non_rectangular_projection():
    ccrs = pytest.importorskip("cartopy.crs")
    fig, ax = plt.subplots(
        subplot_kw={"projection": ccrs.LambertConformal(
            central_longitude=120, central_latitude=25,
        )},
    )
    ax.set_extent([112, 132, 17, 32.5], crs=ccrs.PlateCarree())
    with pytest.raises(NotImplementedError, match="rectangular"):
        op.set_degree_ticks(ax, [112, 132, 17, 32.5], lon_step=4, lat_step=4)
    plt.close(fig)


def test_auto_time_axis_spans():
    fig, ax = plt.subplots()
    yearly = np.arange("2018-01-01", "2022-01-01", dtype="datetime64[D]")
    locator, formatter = op.auto_time_axis(ax, yearly)
    assert locator is not None
    assert formatter is not None
    plt.close(fig)

    fig, ax = plt.subplots()
    hourly = np.arange("2020-01-01", "2020-01-03", dtype="datetime64[h]")
    locator, formatter = op.auto_time_axis(ax, hourly)
    assert locator is not None
    assert "%H" in formatter.fmt


def test_save_figure(tmp_path):
    fig, ax = plt.subplots(figsize=(4, 2.5))
    ax.plot([0, 1], [0, 1])
    out = tmp_path / "fig.png"
    written = op.save_figure(fig, out, dpi=300, also_pdf=True)
    assert out.exists() and out.stat().st_size > 0
    assert out.with_suffix(".pdf").exists()
    assert len(written) == 2


def test_save_figure_preserves_figsize_when_tight_off(tmp_path):
    fig, ax = plt.subplots(figsize=(3.2, 2.4))
    ax.plot([0, 1], [0, 1])
    out = tmp_path / "exact.png"
    op.save_figure(fig, out, dpi=300, tight=False)
    pixels = plt.imread(out)
    assert pixels.shape[1] == 960
    assert pixels.shape[0] == 720


def test_save_figure_check_bounds_warns_when_tight_off(tmp_path):
    fig, ax = plt.subplots(figsize=(3, 2))
    ax.plot([0, 1], [0, 1])
    fig.text(1.3, 0.5, "outside")
    with pytest.warns(RuntimeWarning, match="outside"):
        op.save_figure(fig, tmp_path / "clipped.png", dpi=300, tight=False, check=True)


def test_auto_time_axis_resets_numeric_formatter():
    fig, ax = plt.subplots()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    op.auto_time_axis(ax, np.arange(4.0))
    assert not isinstance(ax.xaxis.get_major_formatter(), mdates.DateFormatter)
    plt.close(fig)


def test_auto_time_axis_sixty_days_uses_day_locator():
    fig, ax = plt.subplots()
    dates = np.arange("2020-01-01", "2020-03-01", dtype="datetime64[D]")
    locator, _ = op.auto_time_axis(ax, dates)
    assert isinstance(locator, mdates.DayLocator)
    plt.close(fig)


def test_auto_time_axis_rejects_timedelta():
    fig, ax = plt.subplots()
    with pytest.raises(TypeError, match="timedelta"):
        op.auto_time_axis(ax, np.array([0, 1, 2], dtype="timedelta64[D]"))
    plt.close(fig)


def test_colorbar_ticks_caps_symmetric_count():
    ticks = op.colorbar_ticks(-1, 1, n=9, symmetric=True)
    assert 4 <= ticks.size <= 7


def test_robust_limits_include_zero_does_not_invent_negative_range():
    lo, hi = op.robust_limits([1, 2, 3], include_zero=True)
    assert lo == 0.0
    assert hi > 3.0


def test_keep_largest_region_rejects_unknown_connectivity():
    with pytest.raises(ValueError, match="connectivity"):
        op.keep_largest_region(np.ones((3, 3)), connectivity=3)
