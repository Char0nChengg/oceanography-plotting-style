# 地图配方

> 通用参数块见 [recipes/README.md](README.md#0-通用参数块)；
> 图型总目录见 [figure-catalog.md](../figure-catalog.md)。

## 1. 单张区域地图

数据契约：`lon`、`lat` 为 1D 或 2D，`ssh.shape[-2:]` 与之匹配。

```python
import cartopy.crs as ccrs
import matplotlib.pyplot as plt

from ocean_plot import (
    add_map_features, add_panel_label, auto_tick_step, check_figure,
    get_cmap, projection_for_region, save_figure, set_map_ticks,
    set_ocean_style, validate_grid,
)

set_ocean_style(base_size=9)
map_spec = projection_for_region(lon_min, lon_max, lat_min, lat_max, kind="auto")
projection = map_spec.crs
data_crs = ccrs.PlateCarree()
validate_grid(lon, lat, ssh)

fig, ax = plt.subplots(
    figsize=(fig_width, fig_height),
    subplot_kw={"projection": projection},
    constrained_layout=True,
)

mesh = ax.pcolormesh(
    lon, lat, ssh, cmap=get_cmap(cmap_name), vmin=vmin, vmax=vmax,
    shading="auto", transform=data_crs, rasterized=True,
)
ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=data_crs)
add_map_features(ax, scale="10m")
lon_step, lat_step = auto_tick_step(
    lon_min, lon_max, lat_min, lat_max,
    figsize=(fig_width, fig_height),
)
set_map_ticks(ax, map_spec, [lon_min, lon_max, lat_min, lat_max],
              lon_step=lon_step, lat_step=lat_step)
ax.set_aspect("equal")
add_panel_label(ax, "(a)", fontsize=font_title)

cbar = fig.colorbar(mesh, ax=ax, extend=cbar_extend,
                    fraction=0.035, pad=0.02)
cbar.set_label(cbar_label, fontsize=font_label)
cbar.ax.tick_params(labelsize=font_tick)

for issue in check_figure(fig, check_bounds=True):
    print("layout warning:", issue)
save_figure(fig, output_png, dpi=save_dpi, also_pdf=True, tight=False)
```

## 2. 多面板地图（共用色标）

关键：所有面板共用同一 `vmin/vmax/cmap`，只画一条外置 colorbar。

```python
import cartopy.crs as ccrs
import matplotlib.pyplot as plt

from ocean_plot import (
    add_map_features, add_panel_label, auto_tick_step, check_figure,
    get_cmap, projection_for_region, save_figure, set_map_ticks,
    set_ocean_style, validate_grid,
)

set_ocean_style(base_size=9)
map_spec = projection_for_region(lon_min, lon_max, lat_min, lat_max, kind="auto")
projection = map_spec.crs
data_crs = ccrs.PlateCarree()
fig, axes = plt.subplots(
    3, 2, figsize=(fig_width, 8.4),
    subplot_kw={"projection": projection},
    constrained_layout=True,
)
axes = axes.ravel()
lon_step, lat_step = auto_tick_step(
    lon_min, lon_max, lat_min, lat_max,
    figsize=(fig_width, 8.4), ncols=2, nrows=3, fontsize=font_tick,
)

assert len(axes) == len(months) == len(panel_labels) == 6
for ax, month, label in zip(axes, months, panel_labels):
    data = ssh_by_month[month]
    validate_grid(lon, lat, data)
    pcm = ax.pcolormesh(
        lon, lat, data, cmap=get_cmap(cmap_name),
        vmin=vmin, vmax=vmax, shading="auto",
        transform=data_crs, rasterized=True,
    )
    ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=data_crs)
    add_map_features(ax, scale="50m")
    set_map_ticks(ax, map_spec, [lon_min, lon_max, lat_min, lat_max],
                  lon_step=lon_step, lat_step=lat_step,
                  fontsize=font_tick)
    ax.set_aspect("equal")
    add_panel_label(ax, f"({label})", fontsize=font_title)
    ax.set_title(month, fontsize=font_title, fontweight="normal", pad=4)

cbar = fig.colorbar(pcm, ax=axes, extend=cbar_extend,
                    fraction=0.025, pad=0.02)
cbar.set_label(cbar_label, fontsize=font_label)
cbar.ax.tick_params(labelsize=font_tick)

for issue in check_figure(fig, check_bounds=True):
    print("layout warning:", issue)
save_figure(fig, output_png, dpi=save_dpi, also_pdf=True, tight=False)
```

`months`、`panel_labels`（如 `"abcdef"`）和 `ssh_by_month` 必须由调用方定义；长度必须一致。

## 3. 相位

数据契约：`phase_rad` 与 `lon/lat` 的形状按 `validate_grid` 对齐。

```python
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import numpy as np

from ocean_plot import (
    check_figure, get_cmap, projection_for_region, save_figure, set_map_ticks,
)

map_spec = projection_for_region(lon_min, lon_max, lat_min, lat_max, kind="auto")
data_crs = ccrs.PlateCarree()
fig, ax = plt.subplots(
    figsize=(fig_width, 4.0), constrained_layout=True,
    subplot_kw={"projection": map_spec.crs},
)
phase_deg = (np.rad2deg(phase_rad) + 360.0) % 360.0
mesh = ax.pcolormesh(
    lon, lat, phase_deg, cmap=get_cmap("cmo.phase"),
    vmin=0, vmax=360, shading="auto",
    transform=data_crs, rasterized=True,
)
ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=data_crs)
set_map_ticks(ax, map_spec, [lon_min, lon_max, lat_min, lat_max])
cbar = fig.colorbar(mesh, ax=ax, extend="neither")
cbar.set_label("Phase (degrees)", fontsize=font_label)
cbar.set_ticks([0, 90, 180, 270, 360])

for issue in check_figure(fig, check_bounds=True):
    print("layout warning:", issue)
save_figure(fig, output_png, dpi=save_dpi, also_pdf=True, tight=False)
```

相位是循环量：0° 和 360° 是同一点，色标首尾颜色一致；不要用 `balance` 把 0° 放在中间。

## 4. 地形 + 陆架坡折

数据契约：`depth` 为米，陆架坡折中心按研究区设置，不固定为 200 m。

```python
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import TwoSlopeNorm

from ocean_plot import (
    check_figure, get_cmap, projection_for_region, save_figure, set_map_ticks,
)

map_spec = projection_for_region(lon_min, lon_max, lat_min, lat_max, kind="auto")
data_crs = ccrs.PlateCarree()
fig, ax = plt.subplots(
    figsize=(fig_width, 4.0), constrained_layout=True,
    subplot_kw={"projection": map_spec.crs},
)
vcenter = 200.0
vmax_depth = max(5500.0, float(np.nanmax(depth)))
mesh = ax.pcolormesh(
    lon, lat, depth, cmap=get_cmap("cmo.deep"),
    norm=TwoSlopeNorm(vmin=0, vcenter=vcenter, vmax=vmax_depth),
    shading="auto", transform=data_crs, rasterized=True,
)
ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=data_crs)
set_map_ticks(ax, map_spec, [lon_min, lon_max, lat_min, lat_max])
cbar = fig.colorbar(mesh, ax=ax, extend="neither")
cbar.set_label("Depth (m)", fontsize=font_label)
cbar.set_ticks([0, 50, 200, 1000, 3000, 5500])

for issue in check_figure(fig, check_bounds=True):
    print("layout warning:", issue)
save_figure(fig, output_png, dpi=save_dpi, also_pdf=True, tight=False)
```

- `vcenter=200` 是陆架坡折的例子，按研究区调整；不要对所有海区都用 200 m。
- 等值线级别与 `norm` 不要互相打架；`TwoSlopeNorm` 配 `pcolormesh` 通常比配大量 `contourf` 级别更稳。
- `TwoSlopeNorm` 需要 `vmin < vcenter < vmax`；上面的 `max(5500, vmax_depth)` 只是示例，实际要保证数据范围与 norm 一致。
