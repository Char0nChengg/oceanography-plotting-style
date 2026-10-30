# 剖面与 Hovmöller 配方

> 通用参数块见 [recipes/README.md](README.md#0-通用参数块)；
> 图型总目录见 [figure-catalog.md](../figure-catalog.md)。

## 1. Hovmöller 图

数据契约：`ssh` 形状为 `(distance, time)`，画图时转置为 `(time, distance)`。

```python
import matplotlib.pyplot as plt
import numpy as np

from ocean_plot import (
    auto_time_axis, check_figure, get_cmap, save_figure, set_ocean_style,
)

set_ocean_style(base_size=9)
ssh = np.asarray(ssh)
if ssh.shape != (distance.size, time.size):
    raise ValueError(f"ssh should be (distance, time), got {ssh.shape}")

vmax = float(np.nanpercentile(np.abs(ssh), 99))
if not np.isfinite(vmax) or vmax <= 0:
    raise ValueError("ssh is all zero or NaN; cannot set a symmetric range")
levels = np.unique(np.linspace(-vmax, vmax, 25))

fig, ax = plt.subplots(figsize=(fig_width, 3.4), constrained_layout=True)
cf = ax.contourf(time, distance, ssh.T, levels=levels,
                 cmap=get_cmap("cmo.balance"), extend="both")
ax.set_ylabel("Distance along section (km)", fontsize=font_label)
ax.set_xlabel("Time", fontsize=font_label)
auto_time_axis(ax, time)
ax.tick_params(labelsize=font_tick)

cbar = fig.colorbar(cf, ax=ax, extend="both", fraction=0.05, pad=0.02)
cbar.set_label("SSH anomaly (m)", fontsize=font_label)
cbar.set_ticks(np.linspace(-vmax, vmax, 5))
cbar.ax.tick_params(labelsize=font_tick)

for issue in check_figure(fig, check_bounds=True):
    print("layout warning:", issue)
save_figure(fig, output_png, dpi=save_dpi, also_pdf=True, tight=False)
```

注意：

- `ssh.T` 只在 `ssh` 是 `(distance, time)` 时成立；先断言形状，不要凭感觉转置。
- `levels` 用 `np.unique` 去重；`vmax=0` 时 `linspace` 会退化，需要先检查。
- 色标刻度只取 5 个代表值，不要 25 个。

## 2. 垂向剖面

数据契约：`temp` 形状为 `(time, depth)`，画图时转置为 `(depth, time)`；确认 `depth` 的正方向。

```python
import matplotlib.pyplot as plt
import numpy as np

from ocean_plot import auto_time_axis, check_figure, get_cmap, save_figure

prof_vmin, prof_vmax = 2.0, 28.0
fig, ax = plt.subplots(figsize=(fig_width, 3.2), constrained_layout=True)
mesh = ax.pcolormesh(
    time, depth, temp.T, cmap=get_cmap("cmo.thermal"),
    vmin=prof_vmin, vmax=prof_vmax, shading="auto", rasterized=True,
)
if np.nanmin(depth) >= 0:
    ax.invert_yaxis()             # 正深度向下
ax.set_ylabel("Depth (m)", fontsize=font_label)
ax.set_xlabel("Time", fontsize=font_label)
auto_time_axis(ax, time)
ax.tick_params(labelsize=font_tick)

cbar = fig.colorbar(mesh, ax=ax, extend="neither", fraction=0.04, pad=0.02)
cbar.set_label("Temperature (°C)", fontsize=font_label)
cbar.ax.tick_params(labelsize=font_tick)

for issue in check_figure(fig, check_bounds=True):
    print("layout warning:", issue)
save_figure(fig, output_png, dpi=save_dpi, also_pdf=True, tight=False)
```

如果 `depth` 是负值（海洋模式常见），先确认方向；负深度向下增大时不要再 `invert_yaxis()`。
