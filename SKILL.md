---
name: oceanography-plotting-style
description: "绘制或修改物理海洋学论文图时使用：区域经纬度地图、多面板地图、垂向剖面、Hovmöller 图、FFT 频谱、时间序列、quiver/粒子轨迹，以及 cmocean 配色、色标、期刊版式、自动布局检查和 PNG/PDF 交付。"
whenToUse: "用户要画海洋学数据图、重排多面板图、统一论文图风格、选择色标/色标范围，或检查成图是否适合投稿时加载。"
---

# 物理海洋学论文绘图

## 目标

产出一张**能直接放进论文**的图：数据形状正确、地图要素完整、色标含义明确、字号在最终印刷宽度下可读、输出可复现。默认使用 Matplotlib + Cartopy + cmocean；最终脚本不允许留下 `...`、`TODO` 或未定义的变量。

## 设计立场

本 skill 的视觉语言服务于作者的个人绘图偏好，不是期刊官方模板：

- **只用 cmocean**，不用 jet/rainbow；色标由变量属性决定。
- **图优先、文字克制**：不设整张图的主标题，只用子图副标题和 `(a)`/`(b)` 面板字母；能共享的横纵坐标就共享。
- **colorbar 清晰但不占主图**：优先外置列、图下横条或 inset；刻度 4–7 个，`extend` 必须诚实。
- **分析图同源**：CCA、小波、谱分析、EMD 也使用同一套克制、可验证的语言。

这只是作者的选择，不评判其他作者；投稿前仍须核对期刊最新指南。完整说明见 [docs/style-philosophy.md](docs/style-philosophy.md)。

## 先确认（只问会改变图的）

按影响从大到小确认；用户没给就采用括号内默认值，并在最终回复中写明假设：

1. **最终尺寸/期刊**：单栏、1.5 栏还是双栏？（默认双栏 7.2 in 宽，最终以期刊 preset 为准）
2. **区域与投影**：经纬度范围、是否跨日界线、是否需要保角/等面积？（默认 PlateCarree + 数据范围）
3. **变量与单位**：变量名、单位、正负号约定、是否异常值/距平？（默认按数据 1–99% 分位定范围）
4. **时间处理**：单帧、时间平均、时间序列还是 Hovmöller？（默认保留时间维，不擅自取 `time=0`）
5. **输出**：PNG 300 dpi、600 dpi，还是 PDF/SVG 矢量？（默认 PNG 300 dpi + 同名 PDF）

能从数据判断的先判断；不要一次问十个问题。

## 工作流

1. **检查数据**：维度顺序、坐标名、单位、范围、NaN/陆地掩膜、经度约定、纬度升降序、时间 calendar。
2. **规范化**：统一为 `time, depth, lat, lon`；经度按图件约定处理并排序；用 `validate_grid` 验证形状。优先用 `ocean_data`，细节见 [data-prep](references/data-prep.md)。
3. **选图型**：地图 / 多面板地图 / 垂向剖面 / Hovmöller / 时间序列 / FFT / quiver / 轨迹；配方见 [figure-recipes](references/figure-recipes.md)。
4. **搭 `main()`**：参数块放在开头；期刊宽度、字号从 `ocean_journal` 取；先 `set_ocean_style`，再 `apply_journal_style`，避免线宽被覆盖。
5. **绘图**：优先复用 `ocean_plot` 的刻度、字体、色标、校验函数；模板从 `templates/` 复制后再改。
6. **验证**：运行 `check_figure(fig, check_bounds=True)`，并实际打开渲染后的 PNG；不能只看代码。
7. **交付**：保存 PNG 和 PDF，报告路径、实际范围/色标、以及所有假设。

## 硬规则

- **参数集中**：`output_path`、区域、色标名、`vmin/vmax`、`extend`、字号、`figsize`、`dpi`、面板标签放在 `main()` 开头。
- **按最终物理尺寸设计**：不要先画 22×24 in 再缩字号。双栏通常 7.0–7.5 in 宽；正文/刻度约 6–10 pt，具体以期刊 preset 为准，Nature 等例外必须核对指南。
- **字体先验证**：`Arial` 不存在时自动回退并警告；中文标签需要 CJK 字体；设置 `axes.unicode_minus=False`，PDF 使用 `pdf.fonttype=42`。
- **地图显式坐标变换**：`transform=ccrs.PlateCarree()`；`set_extent`、经纬度 formatter、海岸线/陆地、刻度方向成套出现。非矩形投影不能用 Cartopy 的经纬度 formatter，改用 `gridlines(draw_labels=True)`。
- **地图比例**：默认 `ax.set_aspect("equal")`；只有版面确实需要时才用 `"auto"`，并在图注或回复中说明。
- **网格绘制**：`pcolormesh` 显式使用 `shading="auto"`；中心坐标不要当边界坐标；大网格加 `rasterized=True`。
- **色标诚实**：`extend` 表示数据真的超出色标范围，不是变量正负。对称距平用 `balance` + 对称 `vmin/vmax`；有界数据用 `"neither"`；p99 截断才用 `"max"`/`"both"`。
- **色标可读**：必须有变量名和单位；刻度 4–7 个；同变量、同范围的多面板共用一条色标。
- **时间轴**：优先 `auto_time_axis`；跨年不用 `%m-%d`，跨月不用单一 `%Y`。
- **不要原地改数据**：滤波、掩膜、裁剪默认返回副本；IQR 在 `IQR=0` 时跳过。
- **先验证再画**：1D 坐标 + 2D 数据、2D 坐标 + 2D 数据、`data.shape[-2:]` 必须与经纬度对齐；跨 0°/360° 要处理。
- **成图检查**：面板字母在坐标区左上外侧；检查标签裁切、色标三角、刻度重叠、字形缺失；`save_figure` 设 `tight=False` 才能保持 `figsize` 的最终宽度。

## API 顺序

| 步骤 | 调用 |
|---|---|
| 读取/规范化 | `load_for_plot` → `grid_arrays` → `validate_grid` |
| 样式 | `set_ocean_style` → `apply_journal_style`（顺序不能反） |
| 地图 | `add_map_features`；`set_degree_ticks`（仅矩形投影）；非矩形用 `ax.gridlines(draw_labels=True)` |
| 色标 | `get_cmap("cmo.dense")` → `colorbar_ticks` → `add_colorbar` |
| 布局 QA | `check_figure(fig, check_bounds=True)` |
| 保存 | `save_figure(fig, path, dpi=300, also_pdf=True, tight=False)` |

常用预设：`get_journal("agu"|"ams"|"elsevier"|"nature"|"generic")`。这些数值是经验值，必须核对最新 author guidelines。

## 出图前检查表

- [ ] 坐标与数据形状匹配；没有把 `(lat,)` 和 `(lon,)` 广播成错误矩阵。
- [ ] 经度约定统一；跨日界线/0° 没有断裂；纬度升降序已处理。
- [ ] 地图范围、投影、刻度、海岸线、陆地正确；比例没有被拉扁。
- [ ] 色标有标签/单位；`vmin/vmax` 与数据范围相符；`extend` 与截断一致。
- [ ] 多面板同变量共用色标；不同变量没有误共用。
- [ ] 字号按最终宽度可读；没有缺字/方框；负号正常。
- [ ] 面板字母在左上外侧；标题、轴标签、图例没有被裁切。
- [ ] 时间轴刻度不重叠；跨年/跨月格式正确。
- [ ] 输出文件存在且非空；PNG 已实际打开检查；PDF 字体已嵌入。
- [ ] 最终回复写明输出路径、色标范围、数据假设和未解决项。

## 资源

- [style-reference](references/style-reference.md)：字体、版面、地图、色标、验收与失败案例。
- [data-prep](references/data-prep.md)：xarray 维度、区域裁剪、经度/纬度、滤波与形状校验。
- [figure-recipes](references/figure-recipes.md)：Hovmöller、垂向剖面、FFT、quiver、时间序列等配方。
- [ocean_plot.py](scripts/ocean_plot.py)：刻度、地图、色标、布局检查、保存；`--self-test` 自检。
- [ocean_data.py](scripts/ocean_data.py)：维度统一、区域裁剪、跨日界线、`grid_arrays()`。
- [ocean_spectral.py](scripts/ocean_spectral.py)：FFT 振幅谱与 AR(1) 红噪声阈值。
- [ocean_journal.py](scripts/ocean_journal.py)：期刊栏宽与字号预设。
- [ocean_access.py](scripts/ocean_access.py)：灰度与近似 CVD 筛查。
- [templates/](templates/)：两个可运行的合成数据模板，必须加 `--demo`。
- [docs/style-philosophy.md](docs/style-philosophy.md)：完整设计立场。

模板中的合成数据仅用于演示版式，交付前必须替换为真实数据。仓库开发验收：`python -m pytest -q` 与 `python scripts/ocean_plot.py --self-test`。
