# 图型配方

每个配方只保留“能直接改”的骨架。参数块放在 `main()` 开头；这里用 `...` 表示必须替换的数据，交付前删除。

## 0. 通用参数块

```python
def main():
    # ---------- 输出 ----------
    output_png = Path("figures/Fig_01.png")
    output_pdf = output_png.with_suffix(".pdf")

    # ---------- 区域 ----------
    lon_min, lon_max = 112.0, 132.0
    lat_min, lat_max = 17.0, 32.5

    # ---------- 色标 ----------
    cmap_name = "cmo.balance"
    vmin, vmax = -0.25, 0.25
    cbar_extend = "both"
    cbar_label = "SSH anomaly (m)"

    # ---------- 版面 ----------
    fig_width, fig_height = 7.2, 5.0
    font_tick, font_label, font_title = 8, 9, 10
    save_dpi = 300
```

## 1. 单张区域地图

```python
import cartopy.crs as ccrs
import cmocean as cmo
import matplotlib.pyplot as plt
from ocean_plot import (
    add_map_features, auto_tick_step, get_cmap, save_figure,
    set_degree_ticks, set_ocean_style, validate_grid,
)

set_ocean_style(base_size=9)
projection = ccrs.PlateCarree()

fig, ax = plt.subplots(
    figsize=(fig_width, fig_height),
    subplot_kw={"projection": projection},
    constrained_layout=True,
)

validate_grid(lon, lat, ssh)
mesh = ax.pcolormesh(
    lon, lat, ssh, cmap=get_cmap(cmap_name), vmin=vmin, vmax=vmax,
    shading="auto", transform=projection, rasterized=True,
)
ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=projection)
add_map_features(ax, scale="10m")
lon_step, lat_step = auto_tick_step(
    lon_min, lon_max, lat_min, lat_max,
    figsize=(fig_width, fig_height),
)
set_degree_ticks(ax, [lon_min, lon_max, lat_min, lat_max],
                 lon_step=lon_step, lat_step=lat_step)
ax.set_title("SSH anomaly", fontsize=font_title, fontweight="normal", pad=6)
ax.set_aspect("equal")

cbar = fig.colorbar(mesh, ax=ax, extend=cbar_extend,
                    fraction=0.035, pad=0.02)
cbar.set_label(cbar_label, fontsize=font_label)
cbar.ax.tick_params(labelsize=font_tick)

save_figure(fig, output_png, dpi=save_dpi, also_pdf=True)
```

## 2. 多面板地图（共用色标）

关键：**所有面板共用同一 `vmin/vmax/cmap`**，只画一条 colorbar。

```python
fig, axes = plt.subplots(
    3, 2, figsize=(7.2, 8.4),
    subplot_kw={"projection": projection},
    constrained_layout=True,
)
axes = axes.ravel()

pcm = None
for ax, month, label in zip(axes, months, "abcdef"):
    data = ssh_by_month[month]
    validate_grid(lon, lat, data)
    pcm = ax.pcolormesh(
        lon, lat, data, cmap=get_cmap(cmap_name),
        vmin=vmin, vmax=vmax, shading="auto",
        transform=projection, rasterized=True,
    )
    ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=projection)
    add_map_features(ax)
    set_degree_ticks(ax, [lon_min, lon_max, lat_min, lat_max],
                     lon_step=lon_step, lat_step=lat_step)
    ax.set_aspect("equal")
    ax.text(-0.08, 1.02, f"({label})", transform=ax.transAxes,
            ha="left", va="bottom", fontsize=9, fontweight="bold",
            clip_on=False)
    ax.set_title(month, fontsize=font_title, fontweight="normal", pad=4)

cbar = fig.colorbar(pcm, ax=axes, extend=cbar_extend,
                    fraction=0.025, pad=0.02)
cbar.set_label(cbar_label, fontsize=font_label)
cbar.ax.tick_params(labelsize=font_tick)
save_figure(fig, output_png, dpi=save_dpi, also_pdf=True)
```

## 3. Hovmöller 图

```python
import numpy as np
import matplotlib.pyplot as plt
import cmocean as cmo
from ocean_plot import auto_time_axis, save_figure, set_ocean_style

set_ocean_style(base_size=9)

# ssh: (distance, time) -> 画图时转置为 (time, distance)
ssh = np.asarray(ssh)
if ssh.shape != (distance.size, time.size):
    raise ValueError(f"ssh 应为 (distance, time)，实际 {ssh.shape}")

vmax = float(np.nanpercentile(np.abs(ssh), 99))
if not np.isfinite(vmax) or vmax <= 0:
    raise ValueError("ssh 全为 0 或 NaN，无法确定对称色标范围")
levels = np.unique(np.linspace(-vmax, vmax, 25))

fig, ax = plt.subplots(figsize=(7.2, 3.4), constrained_layout=True)
cf = ax.contourf(time, distance, ssh.T, levels=levels,
                 cmap=cmo.cm.balance, extend="both")
ax.set_ylabel("Distance along section (km)", fontsize=9)
ax.set_xlabel("Time", fontsize=9)
auto_time_axis(ax, time)
ax.tick_params(labelsize=8)

cbar = fig.colorbar(cf, ax=ax, extend="both", fraction=0.05, pad=0.02)
cbar.set_label("SSH anomaly (m)", fontsize=9)
cbar.set_ticks(np.linspace(-vmax, vmax, 5))
cbar.ax.tick_params(labelsize=8)

save_figure(fig, output_png, dpi=save_dpi, also_pdf=True)
```

注意：

- `ssh.T` 只在 `ssh` 是 `(distance, time)` 时成立；先断言形状，不要凭感觉转置。
- `levels` 用 `np.unique` 去重；`vmax=0` 时 `linspace` 会退化，需要先检查。
- 色标刻度只取 5 个代表值，不要 25 个。

## 4. 垂向剖面

```python
import cmocean as cmo
fig, ax = plt.subplots(figsize=(7.2, 3.2), constrained_layout=True)

mesh = ax.pcolormesh(
    time, depth, temp.T, cmap=cmo.cm.thermal,
    vmin=vmin, vmax=vmax, shading="auto", rasterized=True,
)
ax.invert_yaxis()
ax.set_ylabel("Depth (m)", fontsize=9)
ax.set_xlabel("Time", fontsize=9)
auto_time_axis(ax, time)
ax.tick_params(labelsize=8)

cbar = fig.colorbar(mesh, ax=ax, extend="both", fraction=0.04, pad=0.02)
cbar.set_label("Temperature (°C)", fontsize=9)
cbar.ax.tick_params(labelsize=8)
save_figure(fig, output_png, dpi=save_dpi, also_pdf=True)
```

如果 `depth` 是负值（海洋模式常见），先确认方向：`depth` 已为负且向下增大时不要再 `invert_yaxis()`；正深度向下才翻转。

## 5. 时间序列 + 标准差

```python
fig, ax = plt.subplots(figsize=(7.2, 2.8), constrained_layout=True)

ax.fill_between(dates, mean - std, mean + std,
                color="C0", alpha=0.22, linewidth=0)
ax.plot(dates, mean, color="C0", linewidth=1.3, label="Ensemble mean")
ax.set_ylabel("SSH (m)", fontsize=9)
ax.legend(frameon=False, loc="upper right", fontsize=8)
auto_time_axis(ax, dates)
ax.tick_params(labelsize=8)
save_figure(fig, output_png, dpi=save_dpi, also_pdf=True)
```

- `mean`/`std` 必须已经按同一时间轴对齐；不要用不同长度的 `dates` 广播。
- 滚动统计的 `center=True` 会在两端产生 NaN；如果不想显示断头，明确用 `min_periods` 或裁掉两端，而不是偷偷 `interpolate()`。

## 6. 散点 / 属性图

```python
import cmocean as cmo
sc = ax.scatter(
    x, y, c=values, cmap=cmo.cm.dense,
    s=6, edgecolors="none", vmin=vmin, vmax=vmax,
)
cbar = fig.colorbar(sc, ax=ax, extend="max")
cbar.set_label("Amplitude (m)", fontsize=9)
```

- `cmap` 传的是 colormap 对象，不是字符串 `"cmo.dense"`。
- 散点太密时用 `rasterized=True` 或六边形分箱，不要靠把 `s` 调到 0.1 掩盖过绘制。

## 7. FFT 频谱

```python
from ocean_spectral import ar1_threshold

# 规则采样；time_seconds 是秒/天等单位，dt 与目标频率单位一致
dt = float(np.median(np.diff(time_seconds)))
result = ar1_threshold(
    x, dt=dt, confidence=0.95, n_sim=500, seed=0,
    detrend="linear", window="hann",
)
freq, amp = result["frequency"], result["amplitude"]
threshold = result["threshold"]

positive = freq > 0
fig, ax = plt.subplots(figsize=(7.2, 3.0), constrained_layout=True)
ax.plot(freq[positive], amp[positive], color="C0", linewidth=1.0, label="Amplitude")
ax.plot(freq[positive], threshold[positive], color="C3",
        linestyle="--", linewidth=1.0, label="AR(1) 95% threshold")
ax.set_xscale("log")
ax.set_xlabel("Frequency (cycles per day)", fontsize=9)
ax.set_ylabel("Amplitude", fontsize=9)
ax.tick_params(labelsize=8)
ax.legend(frameon=False, fontsize=7)

for period, color in zip([2, 5, 10, 20], ["0.6", "0.5", "0.4", "0.3"]):
    ax.axvline(1 / period, color=color, linestyle=":", linewidth=0.8)
    ax.text(1 / period, ax.get_ylim()[1] * 0.95, f"{period} d",
            rotation=90, va="top", ha="right", fontsize=7, color=color)

save_figure(fig, output_png, dpi=save_dpi, also_pdf=True)
```

说明：

- `dt` 必须来自规则采样；有缺测时先插值或改用 Lomb–Scargle，不要直接对不等间隔样本做 FFT。
- 窗函数和归一化方式会改变纵轴数值；图注写清楚。
- `ar1_threshold()` 是一个**明确的零假设检验**（AR(1) 红噪声 + Monte-Carlo），不是万能显著性；方法部分写清 `n_sim`、`confidence`、窗函数和去趋势方式。
- 频率轴用对数时，周期标注放在顶部要防止重叠。

## 8. Quiver（流场/力场）

```python
import cartopy.crs as ccrs
mag = np.hypot(u, v)
umax = float(np.nanpercentile(mag, 99))
if not np.isfinite(umax) or umax <= 0:
    raise ValueError("u/v 全为 0 或 NaN，无法确定 quiver 比例")

# 目标每面板约 18 个箭头
sx = max(1, lon.size // 18)
sy = max(1, lat.size // 14)
arrow_len_in = 0.55

q = ax.quiver(
    lon[::sx], lat[::sy], u[::sy, ::sx], v[::sy, ::sx],
    transform=ccrs.PlateCarree(), scale_units="inches",
    scale=umax / arrow_len_in, width=0.0022,
    headwidth=3.5, headlength=4.5, pivot="middle",
)
ax.quiverkey(q, X=0.90, Y=1.02, U=umax,
             label=f"{umax:.2g} m s$^{{-1}}$",
             labelpos="E", coordinates="axes",
             fontproperties={"size": 8})
```

- 不要用 `scale = 30 * vmax` 这类公式；它不能保证不同面板/不同变量下箭头长度一致。
- `scale_units="inches"` 让箭头长度与版面英寸绑定，适合多面板；`scale_units="xy"` 适合需要按地图距离比较的场景，但要单独说明。
- 箭头太密会糊成一片；先减 `stride`，不要先减箭头宽度。

## 9. 相位

```python
phase_deg = (np.rad2deg(phase_rad) + 360.0) % 360.0
mesh = ax.pcolormesh(
    lon, lat, phase_deg, cmap=cmo.cm.phase,
    vmin=0, vmax=360, shading="auto",
    transform=ccrs.PlateCarree(), rasterized=True,
)
cbar = fig.colorbar(mesh, ax=ax, extend="neither")
cbar.set_label("Phase (degrees)", fontsize=9)
cbar.set_ticks([0, 90, 180, 270, 360])
```

相位是循环量：0° 和 360° 是同一点，`phase` 色标首尾颜色一致；不要用 `balance` 把 0° 放在中间。

## 10. 地形 + 陆架坡折

```python
import cmocean as cmo
from matplotlib.colors import TwoSlopeNorm

norm = TwoSlopeNorm(vmin=0, vcenter=200, vmax=5500)
mesh = ax.pcolormesh(
    lon, lat, depth, cmap=cmo.cm.deep, norm=norm,
    shading="auto", transform=ccrs.PlateCarree(), rasterized=True,
)
cbar = fig.colorbar(mesh, ax=ax, extend="max")
cbar.set_label("Depth (m)", fontsize=9)
cbar.set_ticks([0, 50, 100, 200, 500, 1000, 2000, 4000, 5500])
```

- `vcenter=200` 是陆架坡折的例子，按研究区调整；不要对所有海区都用 200 m。
- 等值线级别与 `norm` 不要互相打架；`TwoSlopeNorm` 配 `pcolormesh` 通常比配大量 `contourf` 级别更稳。

## 11. 粒子轨迹 / LineCollection

```python
import cartopy.crs as ccrs
import cmocean as cmo
from matplotlib.collections import LineCollection

segments = [np.column_stack([lon_i, lat_i]) for lon_i, lat_i in trajectories]
lc = LineCollection(
    segments, cmap=cmo.cm.thermal, norm=norm,
    linewidths=0.7, alpha=0.75, rasterized=True,
)
lc.set_array(np.asarray(values))
lc.set_transform(ccrs.PlateCarree())
ax.add_collection(lc)
ax.autoscale_view()
```

轨迹很长时，`LineCollection` 比逐条 `plot` 快；颜色值个数必须等于 `segments` 个数，不是点数。
