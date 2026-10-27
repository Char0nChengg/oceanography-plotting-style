# 风格参考：字体、版面、地图、色标

本文件是 [SKILL.md](../SKILL.md) 的详细展开，并与 [data-prep](data-prep.md)、[figure-recipes](figure-recipes.md) 分工：这里只讲**风格与版面规则**，完整图型配方放在 figure-recipes。规则默认服务论文印刷版；网页/幻灯片可以放大字号，但比例关系仍适用。

> 本文的代码片段是风格示例，默认位于已读取数据、已有 `fig`/`ax` 的 `main()` 中；完整可运行版本见 [templates](../templates/)。项目风格是作者的个人偏好，不是期刊官方规范。

## 1. 先定最终物理尺寸

论文图的字号、线宽、刻度密度都应在**最终印刷宽度**下判断。先画大图再整体缩小，会让 9 pt 变成 5 pt，是最常见的“代码好看、印刷不可读”原因。

| 用途 | 成品宽度 | 建议 `figsize`（宽 × 高，in） | 正文字号 |
|---|---|---|---|
| 单栏小图 | 3.3–3.5 in | 3.5 × 2.6 | 7–8 pt |
| 1.5 栏 | 5.0–5.5 in | 5.2 × 4.0 | 8–9 pt |
| 双栏整幅 | 7.0–7.5 in | 7.0–7.5 × 5.0 | 6–10 pt |
| 双栏整页多面板 | 7.0–7.5 in | 7.0–7.5 × 8.0–9.2 | 7–9 pt |
| 单张大地图 | 6.5–7.2 in | 7.0 × 5.2 | 8–10 pt |

- `figsize` 是**成品尺寸**，不要再让 LaTeX 把图缩到 50%。
- 多面板图的高度由每行地图的经纬比决定；用 `ax.set_aspect("equal")` 后让布局引擎分配空间，不要用 `"auto"` 硬压。
- 300 dpi 的 7.2 × 9.2 in 图约 6600 × 8300 px，已经足够；不要为了“更清楚”把 22 × 24 in × 300 dpi 当成默认。
- 保存时用 `tight=False` 才能保持这个物理尺寸；`bbox_inches="tight"` 会改变成品宽度（见 §8）。

## 2. 字体与排版

```python
import matplotlib as mpl

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Liberation Sans", "DejaVu Sans"],
    "axes.unicode_minus": False,   # 负号用 ASCII hyphen，避免缺字方框
    "pdf.fonttype": 42,            # PDF 嵌入 TrueType，投稿系统可编辑
    "ps.fonttype": 42,
})
```

- **必须验证字体是否存在**：`ocean_plot.set_ocean_style()` 会检查并回退；不要假设每台机器都装了 Arial。
- **中文标签**：Arial 没有 CJK 字形。要么图内用英文，要么在 `font.sans-serif` 里加入 `Microsoft YaHei` / `SimHei` / `Noto Sans CJK SC`，并实际渲染检查。
- 标题 `fontweight="normal"`；面板字母 `fontweight="bold"`，放在坐标区左上外侧：
  ```python
  ax.text(-0.08, 1.02, "(a)", transform=ax.transAxes,
          ha="left", va="bottom", fontsize=9, fontweight="bold",
          clip_on=False)
  ```
- 轴标签必须带单位：`Depth (m)`、`Longitude`、`SSH (m)`、`Velocity (m s$^{-1}$)`。
- 图例不描边（`frameon=False`），放在不遮挡数据的位置；多线图用 `C0/C1/C2` 或 cmocean 的离散色。
- 线宽：数据线 1.0–1.5 pt；海岸线 0.6–0.8 pt；坐标轴 0.8 pt；网格线 0.4 pt、透明度 0.4–0.6。
- **不设整张图的 main title**。用子图 subtitle、面板字母和共享轴标签建立层级；主标题既占空间，也容易和 panel label 抢位置。

## 3. 布局

### 3.1 简单网格

```python
import cartopy.crs as ccrs
import matplotlib.pyplot as plt

fig, axes = plt.subplots(
    3, 2, figsize=(7.2, 8.4),
    subplot_kw={"projection": ccrs.PlateCarree()},
    constrained_layout=True,
)
axes = axes.ravel()
```

`constrained_layout=True` 比 `tight_layout()` 更适合带 colorbar 的多面板图；如果使用 `fig.add_axes` 手动放 colorbar，就不要同时开 constrained layout，改用显式 `subplots_adjust`。

### 3.2 GridSpec 混合面板

```python
import cartopy.crs as ccrs
import matplotlib.pyplot as plt

fig = plt.figure(figsize=(7.2, 5.2), layout="constrained")
gs = fig.add_gridspec(
    2, 2, width_ratios=[1.25, 1.0], height_ratios=[1, 1],
    hspace=0.06, wspace=0.08,
)
ax_map = fig.add_subplot(gs[:, 0], projection=ccrs.PlateCarree())
ax_ts = fig.add_subplot(gs[0, 1])
ax_prof = fig.add_subplot(gs[1, 1])
```

- 不要用 `KSIZE * 4.0` 这类含义不明的魔法数；直接写 `hspace`/`wspace`，并在参数块里命名。
- 共享轴时用 `sharex=True` / `sharey=True`，隐藏内侧标签用 `tick_params(labelleft=False)`，不要用 `set_yticklabels([])`（会触发 FixedFormatter 警告）。
- 能共享的横纵标签就共享：最左列保留纬度，最底行保留经度；混合面板的剖面与时间序列尽量共享时间基准。

## 4. 地图（Cartopy）

### 4.1 投影

- 默认 `ccrs.PlateCarree()`，适合低中纬区域图。
- 高纬、跨大范围经度或需要保角/等面积时，改用 `Mercator`、`LambertConformal`、`Robinson` 等；不要迷信“始终 PlateCarree”。
- 跨日界线时，先统一到一种经度约定。项目 `subset_region()` 的 1D 负经度/跨日界线输出是展开的 0–360，使用 `ccrs.PlateCarree(central_longitude=180)` 或等价投影；2D 曲线坐标保留原生经度。检查 `set_extent` 是否把图拉成全球。
- **Cartopy 的经纬度 formatter 只适用于矩形投影**。`set_degree_ticks()` 对 LCC/Robinson 等会明确抛 `NotImplementedError`；这些投影用 `gridlines(draw_labels=True)`。

### 4.2 地图要素

```python
import cartopy.crs as ccrs
import cartopy.feature as cfeature

ax.add_feature(cfeature.LAND.with_scale("50m"),
               facecolor="lightgray", edgecolor="none", zorder=2)
ax.add_feature(cfeature.COASTLINE.with_scale("50m"),
               linewidth=0.7, edgecolor="black", zorder=3)
ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=ccrs.PlateCarree())
ax.set_aspect("equal")
```

- `10m` 最清晰，但首次运行会下载 Natural Earth 数据，离线环境会失败；多面板图/PDF 优先用 `50m`，单张大图再用 `10m`，并提前缓存。
- 陆地放在数据之上、海岸线再之上；否则 `pcolormesh` 会盖住海岸线。
- 经纬度刻度用 `LongitudeFormatter` / `LatitudeFormatter`，不要手写 `112°E` 字符串；非矩形投影改用 gridline labels。
- 刻度：`direction="in"`、四边、`length=3.5`、`width=0.8`；经度标签太密时减少刻度数，而不是把字体缩到 5 pt。
- 需要网格线时：
  ```python
  gl = ax.gridlines(draw_labels=False, linewidth=0.4, color="gray",
                    alpha=0.45, linestyle=":")
  ```
  不要让网格线压过数据；标签已经由刻度 formatter 提供时，`draw_labels=False`。
- 非矩形投影的标签示例：
  ```python
  gl = ax.gridlines(
      crs=ccrs.PlateCarree(), draw_labels=True,
      xlocs=[110, 120, 130], ylocs=[20, 30],
      linewidth=0.4, color="gray", alpha=0.45, linestyle=":",
  )
  gl.top_labels = False
  gl.right_labels = False
  ```

### 4.3 自适应经纬度刻度

```python
from ocean_plot import auto_tick_step, set_degree_ticks

lon_step, lat_step = auto_tick_step(
    lon_min, lon_max, lat_min, lat_max,
    figsize=(fig_width, fig_height), ncols=2, nrows=3,
)
set_degree_ticks(ax, [lon_min, lon_max, lat_min, lat_max],
                 lon_step=lon_step, lat_step=lat_step)
```

原则：根据**子图物理尺寸**估算可容纳的标签数，再从“好看”的步长集合里选；不要固定 2°/3°/4°。跨日界线或 0–360 经度要先转换，再算步长。

## 5. 色标

### 5.1 选择规则

| 数据特征 | 色标 | 范围 | `extend` |
|---|---|---|---|
| SSH 振幅、RMSE、速度幅值 | `cmo.dense` / `cmo.speed` | `0..p99` | 数据被截断才 `"max"` |
| SSH 距平、差值 | `cmo.balance` | 对称 `±p99` | 数据被截断才 `"both"` |
| 温度 | `cmo.thermal` | 1–99% 分位 | 按截断情况 |
| 盐度 | `cmo.haline` | 1–99% 分位 | 按截断情况 |
| 水深 | `cmo.deep` | 0..max，`TwoSlopeNorm` | 数据被截断才 `"max"` |
| 相位 | `cmo.phase` | 0..360 | `"neither"` |
| 相关系数 | `cmo.balance` | −1..1 | `"neither"` |

**API 写法**：`get_cmap("cmo.dense")` 接收字符串；`cmocean.cm.dense` 是已导入的对象。不要写成 `get_cmap("cmo.cm.dense")`，后者会抛 `ValueError`。

**`extend` 的语义**：三角箭头表示“有数据落在色标范围外”。如果 `vmin/vmax` 已经覆盖全部有限值，就用 `"neither"`；不要因为变量是正的就必须 `"max"`。反过来，如果刻意用 99% 分位截断，应该加 `"max"`/`"both"` 并在图注说明。

### 5.2 色标刻度

- 色标标签必须含单位；刻度 4–7 个，不要把所有等值线级别都塞上去。
- 对称距平：`vmin=-vmax, vmax=+vmax`，`vcenter=0`，刻度包含 0。
- 有界量：`vmin`/`vmax` 取数据边界；不要用 `TwoSlopeNorm` 的 `vcenter` 去硬拗一个没有物理意义的中心。
- 同一变量、同一范围的多面板共用一条色标；不同变量不要共用。
- `colorbar_ticks()` 会把数量限制在 4–7；自定义刻度也要遵守。

### 5.3 常用 norm

```python
import cartopy.crs as ccrs
import cmocean as cmo
from matplotlib.colors import BoundaryNorm, LogNorm, TwoSlopeNorm

# 地形：突出 200 m 陆架坡折
norm = TwoSlopeNorm(vmin=0, vcenter=200, vmax=5500)
ax.pcolormesh(lon, lat, depth, cmap=cmo.cm.deep, norm=norm,
              shading="auto", transform=ccrs.PlateCarree())

# 跨数量级：先掩掉 <=0，再 LogNorm
norm = LogNorm(vmin=1e2, vmax=1e6)

# 离散分级：boundaries 必须单调递增且唯一
norm = BoundaryNorm(boundaries, ncolors=256, extend="both")
```

### 5.4 色标位置

```python
# 多面板共用（constrained layout）
cbar = fig.colorbar(pcm, ax=axes, orientation="vertical",
                    fraction=0.025, pad=0.02, extend=cbar_extend)
cbar.set_label(cbar_label, fontsize=font_label, labelpad=8)
cbar.ax.tick_params(labelsize=font_tick)

# 单图：外置列或图下横条
cbar = fig.colorbar(mesh, ax=ax, extend=cbar_extend)
```

手动 `fig.add_axes` 适合需要精确对齐的期刊图，但必须自己保证不压住面板。Colorbar 不占用主图空间：优先独立 `cax`/外置列、图下横条或 inset；多面板同变量只保留一条。

## 6. 常用图型

### 6.1 pcolormesh

```python
import cartopy.crs as ccrs

from ocean_plot import get_cmap

mesh = ax.pcolormesh(
    lon, lat, data, cmap=get_cmap("cmo.dense"), vmin=vmin, vmax=vmax,
    shading="auto", transform=ccrs.PlateCarree(),
    rasterized=True,
)
```

- 1D `lon/lat` 是**中心坐标**时，`shading="auto"` 让 Matplotlib 推断；不要手动把中心当边界。
- 2D `lon/lat` 必须与 `data.shape[-2:]` 完全一致。
- NaN 会被留空；如果 `contourf` 跨 NaN 连线，改用 `pcolormesh` 或掩膜。

### 6.2 contourf

```python
import numpy as np
import cartopy.crs as ccrs

from ocean_plot import get_cmap

if vmin == vmax:
    raise ValueError("vmin and vmax must differ for contourf")
levels = np.unique(np.linspace(vmin, vmax, 21))
cf = ax.contourf(lon, lat, data, levels=levels, cmap=get_cmap("cmo.dense"),
                 extend=cbar_extend, transform=ccrs.PlateCarree())
```

`levels` 必须严格递增且唯一；`cbar.set_ticks(levels)` 通常太密，改成 4–7 个代表值。

Hovmöller、垂向剖面、时间序列、散点、FFT、quiver、粒子轨迹等完整配方见 [figure-recipes](figure-recipes.md)，这里不重复维护第二份代码。

## 7. 坐标轴

### 7.1 时间轴

优先用 `ocean_plot.auto_time_axis(ax, time_values)`；它按跨度选择年/月/日/小时 locator，并处理 numpy datetime64、`datetime`、pandas Timestamp 和常见 cftime 对象。非标准日历会警告并按 Gregorian 近似；需要日历精确时用 `nc_time_axis`。

跨年图不要用 `%m-%d`；跨月图不要用单一 `%Y`。刻度标签旋转 30° 只作为最后手段，优先减少刻度数。

### 7.2 多面板共享标签

```python
if col == 0:
    ax.set_ylabel("Latitude", fontsize=font_label)
else:
    ax.tick_params(labelleft=False)

if row == n_rows - 1:
    ax.set_xlabel("Longitude", fontsize=font_label)
else:
    ax.tick_params(labelbottom=False)
```

### 7.3 科学计数法

```python
ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
```

Cartopy 的 GeoAxes 不要用 `ticklabel_format`，用经纬度 formatter 或 gridline labels。

## 8. 保存与导出

```python
from ocean_plot import save_figure

save_figure(
    fig, output_png, dpi=300, also_pdf=True,
    tight=False,             # 保持 figsize 的最终物理宽度
)
```

- 论文线图/等值线图优先 PDF/SVG；位图地图 300 dpi 足够，600 dpi 只在期刊明确要求时使用。
- `bbox_inches="tight"` 会改变画布边界；如果多面板需要严格对齐，改用 `constrained_layout` 或显式 `subplots_adjust`。它适合预览，不适合按期刊宽度交付。
- 大 pcolormesh 加 `rasterized=True`，避免 PDF 体积爆炸。
- 保存后必须打开 PNG 检查；不要只检查文件大小。
- 用 `check_figure(fig, check_bounds=True)` 检查画布越界；`save_figure(check=True, tight=False)` 会自动做同样的检查。

## 9. 期刊预设、QA 与可访问性

- **期刊宽度**：`ocean_journal.get_journal("agu")`，用 `width_in("double")` 定 figsize；`apply_journal_style()` 同步字号。数值是经验值，投稿前核对 author guidelines；Nature 的 6 pt 等例外必须单独确认。
- **顺序**：先 `set_ocean_style(base_size=8)`，再 `apply_journal_style(journal)`；后者应覆盖线宽和标题字号。
- **布局 QA**：`check_figure(fig, check_bounds=True)` 抓刻度重叠和画布越界；必须在保存前调用一次，并实际打开 PNG。
- **色标筛查**：`ocean_access.accessibility_report("cmo.balance")` 检查灰度间隔与近似 CVD；warning 只是提示，不等于“不可用”。先在实际尺寸和灰度下复核，再决定加等值线/纹理或换色标。
- **PDF 体积**：多面板优先 `50m` 海岸线；`10m` 用于单张大图。pcolormesh 加 `rasterized=True`，但海岸线/陆地仍可能是 PDF 体积主因。

## 10. 验收与失败案例

### 10.1 仓库级验收

```bash
python -m pytest -q
python scripts/ocean_plot.py --self-test
python templates/map_panel_grid.py --demo
python templates/mixed_panel_grid.py --demo
```

预期：

- 测试全绿、self-test 打印 `self-test OK`；
- 两个模板都生成 PNG 和 PDF，且 `check_figure` 无 warning；
- 地图/混合模板的 PNG 宽度约等于 AGU 双栏宽度 × 300 dpi（允许 1–2 px 取整）；
- 打开 PNG 检查面板字母、标题、轴标签和两条 colorbar 都不被裁切；
- PDF 中文字为嵌入字体（`pdf.fonttype=42`）。

### 10.2 成图验收

- **形状**：`validate_grid` 通过；2D 坐标没有转置错误。
- **地图**：经纬度标签正确；Mercator 不会出现所有标签同一个经度；LCC 用 gridline labels。
- **色标**：标签带单位；4–7 个刻度；`extend` 与数据范围一致；同变量多面板共用。
- **版面**：最终 `figsize` 未被 tight bbox 改变；panel label 在左上外侧；没有文字压色标或刻度。
- **时间**：跨年/跨月格式正确；45–60 天图能看到足够的时间刻度。
- **字体**：没有方框/缺字；负号正常；PDF 字体可嵌入。

### 10.3 失败案例

| 症状 | 根因 | 修正 |
|---|---|---|
| 地图 PNG 只有 6.37 in 宽，但 figsize 是 7.09 in | `save_figure` 使用 `bbox_inches="tight"`，裁掉了设计边距 | 传 `tight=False`；用像素宽度验收 |
| 色标顶端有三角，但数据最大 0.27 < vmax 0.30 | 无条件 `extend="max"` | 改 `"neither"`，或按真实截断设 `extend` |
| Mercator 所有经度标签都是 `120.001°E` | `set_degree_ticks` 未把经纬度传给 Cartopy | 默认 `crs=PlateCarree()`；非矩形投影用 gridlines |
| 全球图只剩一条经线 | 全图边界被 `% 360` 后 lo==hi | 修 `subset_region` 的全图分支；加 1D/2D 回归 |
| 2D 曲线坐标报 `Dimensions {'lat','lon'} do not exist` | `grid_arrays` 把坐标名当维度名 | 用坐标的 `.dims` 推导 transpose 顺序 |
| FFT 图看起来正常，但缺测被压成规则采样 | 直接 `x = x[np.isfinite(x)]` | 插值到规则时间，或改用 Lomb–Scargle；`fft_amplitude` 默认会拒绝 NaN |
| 9 个色标刻度挤在一起 | 把等值线级别直接当 colorbar ticks | 用 `colorbar_ticks()` 取 4–7 个 |

## 11. 常见错误清单

| 现象 | 常见原因 | 修正 |
|---|---|---|
| 地图被拉扁/拉长 | `set_aspect("auto")` | 改 `"equal"`，或调整 figsize/GridSpec |
| 经纬度标签重叠 | 固定 2°/3° 刻度 | `auto_tick_step` + 减少刻度 |
| 色标有三角但数据没截断 | 无脑 `extend="max"` | 用 `"neither"` |
| 色标没有单位 | 只写变量名 | `label="SSH (m)"` |
| 负号变方框 | 字体缺 U+2212 | `axes.unicode_minus=False` |
| 中文变方框 | 字体无 CJK | 加 CJK 字体并实测 |
| 散点报找不到 `cmo.dense` | 把字符串直接传给 `cmap=` | 用 `get_cmap("cmo.dense")` 或 `cmocean.cm.dense` 对象 |
| 时间轴挤成一团 | 跨年还用日刻度 | `auto_time_axis()` |
| 海岸线被数据盖住 | zorder 顺序错 | 陆地/海岸线 zorder 更高 |
| PDF 巨大 | pcolormesh 未栅格化 | `rasterized=True` |
| 多面板色标不一致 | 每面板各自 `vmin/vmax` | 共用参数与 colorbar |
