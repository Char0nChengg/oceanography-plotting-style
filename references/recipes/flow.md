# 流场与轨迹配方

> 通用参数块见 [recipes/README.md](README.md#0-通用参数块)；
> 图型总目录见 [figure-catalog.md](../figure-catalog.md)。

## 1. Quiver（流场/力场）

数据契约：`u`、`v` 为 `(lat, lon)`，`lon`/`lat` 为 1D 且跳过步长后仍与 `u`/`v` 对齐。

```python
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import numpy as np

from ocean_plot import (
    check_figure, projection_for_region, save_figure, set_map_ticks,
)

map_spec = projection_for_region(lon_min, lon_max, lat_min, lat_max, kind="auto")
data_crs = ccrs.PlateCarree()
fig, ax = plt.subplots(
    figsize=(fig_width, 4.0), constrained_layout=True,
    subplot_kw={"projection": map_spec.crs},
)
ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=data_crs)
set_map_ticks(ax, map_spec, [lon_min, lon_max, lat_min, lat_max])
mag = np.hypot(u, v)
umax = float(np.nanpercentile(mag, 99))
if not np.isfinite(umax) or umax <= 0:
    raise ValueError("u/v are all zero or NaN; cannot set a quiver scale")

# 目标每面板约 18 个箭头
sx = max(1, lon.size // 18)
sy = max(1, lat.size // 14)
arrow_len_in = 0.55

q = ax.quiver(
    lon[::sx], lat[::sy], u[::sy, ::sx], v[::sy, ::sx],
    transform=data_crs, scale_units="inches",
    scale=umax / arrow_len_in, width=0.0022,
    headwidth=3.5, headlength=4.5, pivot="middle",
)
ax.quiverkey(q, X=0.90, Y=1.02, U=umax,
             label=f"{umax:.2g} m s$^{{-1}}$",
             labelpos="E", coordinates="axes",
             fontproperties={"size": font_tick})

for issue in check_figure(fig, check_bounds=True):
    print("layout warning:", issue)
save_figure(fig, output_png, dpi=save_dpi, also_pdf=True, tight=False)
```

- 不要用 `scale = 30 * vmax` 这类公式；它不能保证不同面板/不同变量下箭头长度一致。
- `scale_units="inches"` 让箭头长度与版面英寸绑定，适合多面板；`scale_units="xy"` 适合需要按地图距离比较的场景，但要单独说明。
- 箭头太密会糊成一片；先减 stride，不要先减箭头宽度。

## 2. 粒子轨迹 / LineCollection

数据契约：`trajectories` 是 `(lon_i, lat_i)` 序列的列表，`values` 长度等于轨迹条数。

```python
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.colors import Normalize

from ocean_plot import (
    check_figure, get_cmap, projection_for_region, save_figure, set_map_ticks,
)

map_spec = projection_for_region(lon_min, lon_max, lat_min, lat_max, kind="auto")
data_crs = ccrs.PlateCarree()
fig, ax = plt.subplots(
    figsize=(fig_width, 4.0), constrained_layout=True,
    subplot_kw={"projection": map_spec.crs},
)
ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=data_crs)
set_map_ticks(ax, map_spec, [lon_min, lon_max, lat_min, lat_max])
segments = [np.column_stack([lon_i, lat_i]) for lon_i, lat_i in trajectories]
norm = Normalize(vmin=float(np.nanmin(values)), vmax=float(np.nanmax(values)))
lc = LineCollection(
    segments, cmap=get_cmap("cmo.thermal"), norm=norm,
    linewidths=0.7, alpha=0.75, rasterized=True,
)
lc.set_array(np.asarray(values))
lc.set_transform(data_crs)
ax.add_collection(lc)
ax.autoscale_view()

cbar = fig.colorbar(lc, ax=ax, extend="neither")
cbar.set_label("Value", fontsize=font_label)

for issue in check_figure(fig, check_bounds=True):
    print("layout warning:", issue)
save_figure(fig, output_png, dpi=save_dpi, also_pdf=True, tight=False)
```

轨迹很长时，`LineCollection` 比逐条 `plot` 快；颜色值个数必须等于 `segments` 个数，不是点数。
