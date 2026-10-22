---
name: oceanography-plotting-style
description: "绘制或修改物理海洋学论文图时使用：区域经纬度地图、多面板地图、垂向剖面、Hovmöller 图、FFT 频谱、时间序列、quiver/粒子轨迹，以及 cmocean 配色、色标、期刊版式、自动布局检查和 PNG/PDF 交付。"
whenToUse: "用户要画海洋学数据图、重排多面板图、统一论文图风格、选择色标/色标范围，或检查成图是否适合投稿时加载。"
---

# 物理海洋学论文绘图

## 目标

产出一张**能直接放进论文**的图，而不只是“能跑”的图：数据形状正确、地图要素完整、色标含义明确、字号在最终印刷宽度下可读、输出可复现。

本 skill 默认使用 Matplotlib + Cartopy + cmocean。所有代码片段都是起点，必须按当前数据修改；**最终脚本里不允许留下 `...`、`TODO` 或未定义的模板变量**。

## 先确认（只问会改变图的）

按影响从大到小确认；用户没给就采用括号内默认值，并在最终回复中写明假设：

1. **最终尺寸/期刊**：单栏、1.5 栏还是双栏？（默认双栏 7.2 in 宽）
2. **区域与投影**：经纬度范围、是否跨日界线、是否需要保角/等面积？（默认 PlateCarree + 数据范围）
3. **变量与单位**：变量名、单位、正负号约定、是否异常值/距平？（默认按数据 1–99% 分位定范围）
4. **时间处理**：画单帧、时间平均、时间序列还是 Hovmöller？（默认保留时间维，不擅自取 `time=0`）
5. **输出**：PNG 300 dpi、600 dpi，还是 PDF/SVG 矢量？（默认 PNG 300 dpi + 同名 PDF）

不要一次问十个问题；能从数据判断的就先判断。

## 工作流

1. **检查数据**：维度顺序、坐标名、单位、范围、NaN/陆地掩膜、经度约定（0–360 或 −180–180）、纬度升/降序、时间 calendar。
2. **规范化**：统一为 `time, depth, lat, lon`；经度转成图件约定并排序；验证形状。优先用 `ocean_data`，细节见 `references/data-prep.md`。
3. **选图型**：地图 / 多面板地图 / 垂向剖面 / Hovmöller / 时间序列 / FFT / quiver / 轨迹。参考 `references/figure-recipes.md`。
4. **搭 `main()`**：先写参数块，再写绘图。参数块只放本图需要的项；期刊宽度/字号从 `ocean_journal` 取。
5. **绘图**：优先复用 `scripts/ocean_plot.py` 的刻度、字体、色标、校验函数；模板从 `templates/` 复制后再改。
6. **验证**：按检查表逐项过；运行 `check_figure()` 并实际打开渲染后的 PNG，不能只看代码。
7. **交付**：保存 PNG（和 PDF），报告路径、实际使用的范围/色标、以及所有假设。

## 硬规则

- **参数集中**：`output_path`、区域、色标名、`vmin/vmax`、`extend`、字号、`figsize`、`dpi`、面板标签全部放在 `main()` 开头；循环内只放该面板的数据和标题。
- **按最终物理尺寸设计**：不要先画 22×24 in 再把字号设成 22 pt。双栏图通常 7.0–7.2 in 宽，正文 7–9 pt、刻度 7–9 pt、标题 9–11 pt；面板字母 8–10 pt 加粗。
- **字体先验证**：`Arial` 不存在时自动回退并警告；中文标签需要 CJK 字体，不能靠 Arial 硬撑。设置 `axes.unicode_minus=False`，避免负号变成方框。PDF 嵌入字体（`pdf.fonttype=42`）。
- **地图必须显式坐标变换**：`transform=ccrs.PlateCarree()` 不要依赖默认值；`set_extent`、经纬度 formatter、海岸线/陆地、刻度方向要成套出现。
- **地图比例**：默认 `ax.set_aspect("equal")`，避免 `"auto"` 把经纬度拉变形；只有版面确实需要时才用 `"auto"`，并在图注/回复中说明。
- **网格绘制**：`pcolormesh(..., shading="auto")`；中心坐标不要当边界坐标用。大网格加 `rasterized=True` 控制 PDF 体积。
- **色标诚实**：`extend` 表示“数据超出色标范围”，不是“数据有正负”。正负对称的距平用 `balance` + 对称 `vmin/vmax` + `extend="both"`；有界正值用 `extend="neither"`，不要无脑 `"max"`。
- **色标可读**：色标必须有变量名和单位；刻度不超过约 7 个；同一变量、同一范围的多面板共用一条色标。
- **时间轴**：优先 `AutoDateLocator`/`ConciseDateFormatter` 或 `auto_time_axis()`；跨年不要用 `%m-%d`，跨月不要用 `%Y` 硬套。
- **不要原地改数据**：滤波、掩膜、裁剪默认返回副本；IQR 在 `IQR=0` 时必须跳过，防止把有效数据全清空。
- **先验证再画**：1D 坐标 + 2D 数据、2D 坐标 + 2D 数据、`data.shape[-2:]` 必须与 `(lat, lon)` 对齐；经度跨 0°/360° 要处理。
- **成图检查**：面板字母放在坐标区左上角外侧，不要塞进居中标题；检查标签裁切、色标三角、刻度重叠、字体缺字。

## 代码骨架

```python
from pathlib import Path

import matplotlib
matplotlib.use("Agg")          # 服务器/批处理无显示环境
import matplotlib.pyplot as plt
import numpy as np

from ocean_plot import (       # scripts/ocean_plot.py
    add_map_features, add_panel_label, auto_time_axis, check_figure,
    get_cmap, save_figure, set_degree_ticks, set_ocean_style, validate_grid,
)
from ocean_journal import apply_journal_style, get_journal


def main():
    # ========== 路径 ==========
    output_png = Path("figures/Fig_01.png")

    # ========== 区域 ==========
    lon_min, lon_max = 112, 132
    lat_min, lat_max = 17, 32.5

    # ========== 数据/色标 ==========
    cmap_name = "cmo.dense"
    cmap = get_cmap(cmap_name)
    vmin, vmax = 0.0, 0.30
    cbar_extend = "max"
    cbar_label = "SSH amplitude (m)"

    # ========== 版面 ==========
    journal_name = "agu"
    style = get_journal(journal_name)
    fig_width = style.width_in("double")
    fig_height = 4.8
    font_tick, font_label, font_title = style.tick_pt, style.body_pt, style.title_pt
    save_dpi = style.dpi

    set_ocean_style(base_size=style.body_pt)
    apply_journal_style(journal_name)
    # 读取/规范化数据，然后 validate_grid(lon, lat, data)
    # 绘图：所有 GeoAxes 显式 transform=ccrs.PlateCarree()
    # 布局检查：check_figure(fig, check_bounds=True)
    # save_figure(fig, output_png, dpi=save_dpi, also_pdf=True)


if __name__ == "__main__":
    main()
```

`ocean_plot` 不保证在每个环境里都已安装；当前 DSH 环境已做 editable 安装。模板仍会自动把 `scripts/` 加入 `sys.path`；如果在新项目里使用，复制 `ocean_plot.py`、`pip install -e .` 或显式设置 `PYTHONPATH`，不要假定当前工作目录就是 skill 目录。

## 默认风格速查

| 项目 | 默认值 | 说明 |
|---|---|---|
| 投影 | `ccrs.PlateCarree()` | 高纬/保角需求改用 Mercator、LCC 等并说明 |
| 陆地 | `lightgray` | 海岸线黑色 0.6–0.8 pt |
| 地图精度 | `10m`（单图）/ `50m`（多面板） | 首次运行会下载 Natural Earth；10m 海岸线会让 PDF 很大 |
| 刻度 | 向内、四边、0.8 pt | 经度 `LongitudeFormatter`，纬度 `LatitudeFormatter` |
| 字体 | Arial（回退 DejaVu Sans） | 中文另配 CJK 字体 |
| 色标 | cmocean 感知均匀色标 | 不用 jet/rainbow |
| 图片 | PNG 300 dpi + PDF | 线图优先 PDF/SVG |
| 面板字母 | `(a)` 左上外侧、加粗 | 不放进居中标题 |

**变量 → 色标**（完整表见 `references/style-reference.md`）：

| 变量 | 色标 | 范围/映射 |
|---|---|---|
| SSH 振幅、RMSE（正值） | `cmo.cm.dense` | `0..p99`，`extend="max"` |
| SSH 距平/差值 | `cmo.cm.balance` | 对称 `±p99`，`extend="both"` |
| 温度 | `cmo.cm.thermal` | 1–99% 分位，按需 `both` |
| 盐度 | `cmo.cm.haline` | 1–99% 分位 |
| 水深/地形 | `cmo.cm.deep` | `TwoSlopeNorm` 突出陆架坡折 |
| 相位 | `cmo.cm.phase` | `0..360` |
| 速度 | `cmo.cm.speed` | `0..p99` |
| 相关系数 | `cmo.cm.balance` | `-1..1`，`extend="neither"` |

## 期刊、QA 与可访问性

- **期刊预设**：`ocean_journal.get_journal("agu"|"ams"|"elsevier"|"nature"|"generic")`；用 `style.width_in("double")` 定成品宽度，`apply_journal_style()` 设字号。数值是经验默认值，投稿前核对最新 author guidelines。
- **布局 QA**：出图前调用 `check_figure(fig, check_bounds=True)`，检查刻度标签重叠和画布越界；不要只靠肉眼。
- **可访问性**：`ocean_access.accessibility_report("cmo.balance")` 做灰度亮度间隔和近似 deuteranopia/protanopia 筛查；报告有 warning 就换色标或加等值线/纹理。
- **谱分析**：`ocean_spectral.fft_amplitude()` + `ar1_threshold()` 给出明确的 AR(1) 红噪声阈值；没有定义零假设就不要画“confidence line”。
- **数据准备**：优先用 `ocean_data.load_for_plot()` / `canonicalize_dims()` / `subset_region()`，不要手写一套 `isel` 布尔裁剪。

## 出图前检查表

- [ ] 坐标与数据形状匹配；没有把 `(lat,)` 和 `(lon,)` 广播成错误矩阵。
- [ ] 经度约定统一；跨日界线/0° 没有断裂；纬度升降序已处理。
- [ ] 地图范围、投影、刻度、海岸线、陆地都正确；比例没有被人为拉扁。
- [ ] 色标有标签/单位；`vmin/vmax` 与数据范围相符；`extend` 与是否截断一致。
- [ ] 多面板同变量共用色标；不同变量没有误共用。
- [ ] 字号按最终宽度可读；没有缺字/方框；负号正常。
- [ ] 面板字母在左上外侧；标题、轴标签、图例没有被裁切。
- [ ] 时间轴刻度不重叠；跨年/跨月格式正确。
- [ ] 输出文件存在且非空；PNG 已实际打开检查；PDF 字体已嵌入。
- [ ] 最终回复写明输出路径、色标范围、数据假设和未解决项。

## 资源

- `references/style-reference.md`：字体/版面/地图/色标/各类图的详细规则与代码。
- `references/data-prep.md`：xarray 维度统一、区域裁剪、经度/纬度处理、滤波与形状校验。
- `references/figure-recipes.md`：Hovmöller、垂向剖面、FFT、quiver、时间序列等配方。
- `scripts/ocean_plot.py`：刻度、地图、色标、布局检查、保存；`python scripts/ocean_plot.py --self-test` 自检。
- `scripts/ocean_data.py`：维度统一、区域裁剪、跨日界线、变量别名、`load_for_plot()`。
- `scripts/ocean_spectral.py`：FFT 振幅谱与 AR(1) 红噪声阈值。
- `scripts/ocean_journal.py`：AGU/AMS/Elsevier/Nature 栏宽与字号预设。
- `scripts/ocean_access.py`：灰度与近似 CVD 可访问性筛查。
- `templates/map_panel_grid.py`：3×2 区域地图模板；必须用 `--demo` 运行。
- `templates/mixed_panel_grid.py`：地图 + 时间序列 + 垂向剖面模板；必须用 `--demo` 运行。
- `tests/`：pytest 测试；`README.md`：安装、示例与已知边界。

路径均相对本 skill 目录。模板中的合成数据仅用于演示版式，交付前必须替换为真实数据。`--demo` 开关就是为了防止把合成图误当结果图。
